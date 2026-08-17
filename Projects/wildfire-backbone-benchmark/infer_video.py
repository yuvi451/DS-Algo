import argparse
import os

import cv2
import timm
import torch
from PIL import Image

from models.build_model import build_model

CLASS_NAMES = ["fire", "no_fire", "start_fire"]
BOX_COLOR = {"fire": (0, 0, 255), "no_fire": (0, 200, 0), "start_fire": (0, 165, 255)}


def annotate_video(backbone_name, input_path, output_path, freq=12):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = build_model(backbone_name)
    model.load_state_dict(torch.load(f"results/checkpoints/{backbone_name}.pt", map_location=device))
    model.to(device).eval()

    cfg = timm.data.resolve_data_config({}, model=model)
    transform = timm.data.create_transform(**cfg, is_training=False)

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"could not open {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    last_label, last_conf = "unknown", 0.0
    frame_idx = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if frame_idx % freq == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            tensor = transform(pil_img).unsqueeze(0).to(device)
            with torch.no_grad():
                probs = torch.softmax(model(tensor), dim=1)[0].cpu()
            pred_idx = probs.argmax().item()
            last_label, last_conf = CLASS_NAMES[pred_idx], probs[pred_idx].item()

        color = BOX_COLOR.get(last_label, (255, 255, 255))
        text = f"{last_label}: {last_conf*100:.1f}%"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
        cv2.rectangle(frame, (10, 10), (20 + tw, 40 + th), (0, 0, 0), cv2.FILLED)
        cv2.putText(frame, text, (15, 35 + th), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        writer.write(frame)
        frame_idx += 1

    cap.release()
    writer.release()
    print(f"wrote {output_path} ({frame_idx} frames, backbone={backbone_name}, freq={freq})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backbone", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="results/videos/annotated.mp4")
    parser.add_argument("--freq", type=int, default=12)
    args = parser.parse_args()
    annotate_video(args.backbone, args.input, args.output, args.freq)
