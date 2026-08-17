import json
import os
import shutil
import time

import timm
import torch
from sklearn.metrics import classification_report, confusion_matrix
from torch.utils.data import DataLoader

from data.dataset import FireDataset
from models.build_model import build_model

CLASS_NAMES = ["fire", "no_fire", "start_fire"]


def evaluate(backbone_name, hard_example_conf_threshold=0.5, latency_runs=50):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = build_model(backbone_name)
    model.load_state_dict(torch.load(f"results/checkpoints/{backbone_name}.pt", map_location=device))
    model.to(device).eval()

    cfg = timm.data.resolve_data_config({}, model=model)
    transform = timm.data.create_transform(**cfg, is_training=False)
    test_ds = FireDataset("test", transform)
    test_dl = DataLoader(test_ds, batch_size=32, shuffle=False)

    # prep hard-example output dirs, wiped fresh each run
    hard_dir = f"results/hard_examples/{backbone_name}"
    if os.path.exists(hard_dir):
        shutil.rmtree(hard_dir)
    for cls in CLASS_NAMES:
        os.makedirs(f"{hard_dir}/{cls}", exist_ok=True)

    all_preds, all_labels = [], []
    sample_idx = 0
    with torch.no_grad():
        for imgs, labels in test_dl:
            imgs = imgs.to(device)
            logits = model(imgs)
            probs = torch.softmax(logits, dim=1).cpu()
            preds = probs.argmax(1)

            for i in range(len(labels)):
                true_label = labels[i].item()
                pred_label = preds[i].item()
                confidence_for_true_class = probs[i, true_label].item()

                # misclassified, or classified correctly but with low confidence:
                # both are "hard" cases worth inspecting
                if pred_label != true_label or confidence_for_true_class < hard_example_conf_threshold:
                    src_path, _ = test_ds.samples[sample_idx]
                    fname = os.path.basename(src_path)
                    true_cls = CLASS_NAMES[true_label]
                    pred_cls = CLASS_NAMES[pred_label]
                    dst_name = f"pred-{pred_cls}_conf-{confidence_for_true_class:.2f}_{fname}"
                    shutil.copy(src_path, f"{hard_dir}/{true_cls}/{dst_name}")

                sample_idx += 1

            all_preds.extend(preds.tolist())
            all_labels.extend(labels.tolist())

    report = classification_report(all_labels, all_preds,
                                    target_names=CLASS_NAMES, output_dict=True)
    cm = confusion_matrix(all_labels, all_preds).tolist()

    model.eval()
    dummy = torch.randn(1, 3, cfg["input_size"][1], cfg["input_size"][2]).to(device)
    times = []
    for _ in range(latency_runs):
        t0 = time.time()
        with torch.no_grad():
            model(dummy)
        times.append(time.time() - t0)
    latency_ms = sum(times) / len(times) * 1000

    n_params = sum(p.numel() for p in model.parameters())
    n_hard_examples = sum(len(os.listdir(f"{hard_dir}/{c}")) for c in CLASS_NAMES)

    result = {"model": backbone_name, "report": report, "confusion_matrix": cm,
              "latency_ms": latency_ms, "params": n_params,
              "n_hard_examples": n_hard_examples}
    os.makedirs("results/metrics", exist_ok=True)
    with open(f"results/metrics/{backbone_name}.json", "w") as f:
        json.dump(result, f, indent=2)
    print(backbone_name, "acc:", report["accuracy"], "latency:", latency_ms,
          "ms | hard examples saved:", n_hard_examples)


if __name__ == "__main__":
    for name in ["resnet50", "efficientnet_b0", "vit_tiny_patch16_224"]:
        evaluate(name)
