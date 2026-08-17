"""Stretch goal: prepare the D-Fire dataset (YOLO-format bbox labels) for ultralytics training.

Not run as part of the core benchmark. Download D-Fire from its GitHub repo, then point
--data_dir at the extracted folder (expects images/ and labels/ subfolders, YOLO txt format).
"""
import argparse
import os
import random
import shutil

CLASSES = ["smoke", "fire"]


def prepare(data_dir, out_dir, val_ratio=0.15, seed=42):
    images_dir = os.path.join(data_dir, "images")
    labels_dir = os.path.join(data_dir, "labels")
    stems = sorted(os.path.splitext(f)[0] for f in os.listdir(images_dir))

    random.Random(seed).shuffle(stems)
    n_val = int(len(stems) * val_ratio)
    val_stems, train_stems = set(stems[:n_val]), set(stems[n_val:])

    for split, split_stems in [("train", train_stems), ("val", val_stems)]:
        for sub in ["images", "labels"]:
            os.makedirs(os.path.join(out_dir, split, sub), exist_ok=True)
        for stem in split_stems:
            img_src = next((os.path.join(images_dir, f) for f in os.listdir(images_dir)
                             if os.path.splitext(f)[0] == stem), None)
            lbl_src = os.path.join(labels_dir, f"{stem}.txt")
            if img_src and os.path.exists(img_src):
                shutil.copy(img_src, os.path.join(out_dir, split, "images"))
            if os.path.exists(lbl_src):
                shutil.copy(lbl_src, os.path.join(out_dir, split, "labels"))

    yaml_path = os.path.join(out_dir, "dfire.yaml")
    with open(yaml_path, "w") as f:
        f.write(f"path: {os.path.abspath(out_dir)}\n")
        f.write("train: train/images\n")
        f.write("val: val/images\n")
        f.write(f"names: {CLASSES}\n")
    print(f"wrote {yaml_path}, train={len(train_stems)} val={len(val_stems)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", required=True)
    parser.add_argument("--out_dir", default="detection/dfire_prepared")
    args = parser.parse_args()
    prepare(args.data_dir, args.out_dir)
