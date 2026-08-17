import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BACKBONES = ["resnet50", "efficientnet_b0", "vit_tiny_patch16_224"]
DISPLAY_NAMES = {"resnet50": "ResNet50", "efficientnet_b0": "EfficientNet-B0",
                  "vit_tiny_patch16_224": "ViT-Tiny"}
CLASS_NAMES = ["fire", "no_fire", "start_fire"]


def load_results():
    rows = []
    for name in BACKBONES:
        with open(f"results/metrics/{name}.json") as f:
            r = json.load(f)
        rows.append({
            "Model": DISPLAY_NAMES[name],
            "Test Acc": r["report"]["accuracy"],
            "F1 (start_fire)": r["report"]["start_fire"]["f1-score"],
            "Latency (ms)": r["latency_ms"],
            "Params (M)": r["params"] / 1e6,
            "Hard Examples": r["n_hard_examples"],
        })
    return pd.DataFrame(rows)


def plot_comparison(df, out_path="results/plots/comparison.png"):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    axes[0].bar(df["Model"], df["Test Acc"], color="#3b82f6")
    axes[0].set_title("Test Accuracy")
    axes[0].set_ylim(0, 1)

    axes[1].bar(df["Model"], df["Latency (ms)"], color="#f97316")
    axes[1].set_title("Latency (ms/image, CPU)")

    axes[2].bar(df["Model"], df["Params (M)"], color="#10b981")
    axes[2].set_title("Params (M)")

    for ax in axes:
        ax.tick_params(axis="x", rotation=20)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"wrote {out_path}")


def plot_confusion_matrices():
    fig, axes = plt.subplots(1, len(BACKBONES), figsize=(5 * len(BACKBONES), 4.5))
    for ax, name in zip(axes, BACKBONES):
        with open(f"results/metrics/{name}.json") as f:
            r = json.load(f)
        cm = np.array(r["confusion_matrix"])
        cm_norm = cm / cm.sum(axis=1, keepdims=True)

        im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)
        ax.set_xticks(range(len(CLASS_NAMES)))
        ax.set_yticks(range(len(CLASS_NAMES)))
        ax.set_xticklabels(CLASS_NAMES, rotation=30, ha="right")
        ax.set_yticklabels(CLASS_NAMES)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title(DISPLAY_NAMES[name])
        for i in range(len(CLASS_NAMES)):
            for j in range(len(CLASS_NAMES)):
                ax.text(j, i, f"{cm[i, j]}\n({cm_norm[i, j]:.0%})",
                        ha="center", va="center",
                        color="white" if cm_norm[i, j] > 0.5 else "black", fontsize=9)
    fig.tight_layout()
    fig.savefig("results/plots/confusion_matrices.png", dpi=150)
    print("wrote results/plots/confusion_matrices.png")


if __name__ == "__main__":
    df = load_results()
    print(df.to_string(index=False))
    df.to_csv("results/metrics/comparison.csv", index=False)
    plot_comparison(df)
    plot_confusion_matrices()
