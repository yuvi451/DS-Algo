# Wildfire Backbone Benchmark

A controlled benchmark comparing three CNN/ViT backbones — ResNet50, EfficientNet-B0, and
ViT-Tiny/16 — for wildfire image classification (`fire` / `no_fire` / `start_fire`), designed
for a fair, apples-to-apples comparison: identical stratified train/val/test split across all
models, frozen-backbone linear probing, and a held-out test set touched only once per model.

Beyond accuracy, each model is scored on inference latency and parameter count to surface real
deployment tradeoffs, not just leaderboard numbers. Evaluation includes automated **hard-example
mining** — misclassified and low-confidence test images are saved per class, enabling a concrete
error analysis of the dataset's known weak point (`start_fire`, where smoke-only frames are
easily confused with `no_fire`) rather than just reporting an F1 number. The best-performing
model is deployed on a short video clip via a frame-sampling inference pipeline that overlays
live predictions, demonstrating the model beyond static test-set metrics.

This project is a differentiated build on the same idea as
[Skar0/fire-detection](https://github.com/Skar0/fire-detection): instead of one InceptionV3
model, it benchmarks three modern backbones head-to-head, and it turns error analysis and video
demo into first-class deliverables rather than an afterthought.

## Dataset

The reference project's own `fire` / `no_fire` / `start_fire` dataset (~6,000 images) was never
publicly released — no download link exists anywhere in its repo or docs. This benchmark instead
uses the [DeepQuestAI Fire-Smoke-Dataset](https://github.com/DeepQuestAI/Fire-Smoke-Dataset)
(3,000 real photos, CC-licensed, downloaded directly from its GitHub release — no account or API
key needed), mapped 1:1 onto the same three classes:

| DeepQuestAI class | Mapped to | Rationale |
|---|---|---|
| `Fire` | `fire` | Visible flame |
| `Neutral` | `no_fire` | No fire/smoke indicators |
| `Smoke` | `start_fire` | Smoke-only, pre-flame — the same "early onset" concept the reference project calls `start_fire` |

1,000 images/class, balanced. `data/prepare_split.py` builds one **stratified 70/15/15
train/val/test split** (seed 42), saved to `data/split.json` and reused identically by all three
training runs so the comparison is apples-to-apples.

## Backbone substitution: ViT-Tiny instead of DeiT-Tiny

The original plan called for `deit_tiny_patch16_224`. This sandboxed build environment's network
egress policy blocks `huggingface.co` and `dl.fbaipublicfiles.com` (where `timm` hosts DeiT's
ImageNet weights) but allows `github.com` and `storage.googleapis.com`. `timm`'s own older
checkpoint URLs for ResNet50 and EfficientNet-B0 still live on GitHub Releases, and Google's
official AugReg ViT-Tiny/16 weights live on GCS — all reachable. `models/build_model.py` forces
`timm` to use those non-Hub URLs instead of failing on the blocked Hub download. DeiT-Tiny was
swapped for **`vit_tiny_patch16_224`** (AugReg-in21k, fine-tuned on ImageNet-1k) — same ViT-Tiny/16
architecture family, ~5.5M params, functionally the equivalent comparison point.

## Results

*(Test set, n=450, 150/class. Frozen-backbone linear probe, 6 epochs, AdamW lr=1e-3, batch 32.
CPU-only training — no GPU was available in this build environment.)*

<!-- RESULTS_TABLE -->

![Comparison](results/plots/comparison.png)
![Confusion matrices](results/plots/confusion_matrices.png)

## Hard-example analysis

<!-- HARD_EXAMPLE_ANALYSIS -->

## Video demo

<!-- VIDEO_SECTION -->

## Project structure

```
wildfire-backbone-benchmark/
├── README.md
├── requirements.txt
├── configs/config.yaml
├── data/
│   ├── prepare_split.py         # stratified train/val/test split
│   └── dataset.py                # PyTorch Dataset class
├── models/build_model.py         # loads any timm backbone w/ custom head
├── train.py                      # trains one backbone, saves checkpoint
├── evaluate.py                   # metrics + confusion matrix + latency + hard-example mining
├── infer_video.py                # annotates an mp4 with the best model's predictions
├── compare_results.py            # aggregates all 3 models into one table/plot
├── notebooks/colab_runner.ipynb  # orchestrates everything on Colab GPU
├── results/
│   ├── checkpoints/               # .pt files per model (gitignored, regenerate via train.py)
│   ├── metrics/                   # per-model JSON metrics + comparison.csv
│   ├── hard_examples/             # misclassified images per model, per class (gitignored)
│   ├── videos/                    # annotated demo video
│   └── plots/                     # confusion matrices, comparison charts
└── detection/                     # stretch goal, not run in this build (no bbox dataset available)
    ├── prepare_dfire.py
    └── train_yolo.py
```

## Reproducing

```bash
pip install -r requirements.txt

# 1. Populate data/raw/{fire,no_fire,start_fire}/ with your images, then:
python data/prepare_split.py

# 2. Train each backbone (checkpoints saved to results/checkpoints/)
python train.py --backbone resnet50 --epochs 6
python train.py --backbone efficientnet_b0 --epochs 6
python train.py --backbone vit_tiny_patch16_224 --epochs 6

# 3. Evaluate all three (metrics, confusion matrices, latency, hard-example mining)
python evaluate.py

# 4. Aggregate into a comparison table + plots
python compare_results.py

# 5. Annotate a demo video with the winning backbone
python infer_video.py --backbone <winner> --input clip.mp4 --output results/videos/annotated.mp4
```

On Colab: `Runtime → Change runtime type → T4 GPU`, then run `notebooks/colab_runner.ipynb` top
to bottom.

## Stretch goal: detection

`detection/prepare_dfire.py` and `detection/train_yolo.py` scaffold a YOLOv8n bounding-box
detector on the D-Fire dataset, following the same idea as the reference project's leap from
classification to detection. Not run in this build — no bounding-box dataset was available in
this environment — but the scripts are ready to point at a downloaded copy of D-Fire.
