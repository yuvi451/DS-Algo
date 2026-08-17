import argparse
import json
import os

from sklearn.model_selection import train_test_split

CLASS_NAMES = ["fire", "no_fire", "start_fire"]


def build_split(data_dir, out_path, seed=42):
    samples = []
    for label, cls in enumerate(CLASS_NAMES):
        cls_dir = os.path.join(data_dir, cls)
        for fname in sorted(os.listdir(cls_dir)):
            samples.append((os.path.join(cls_dir, fname), label))

    paths, labels = zip(*samples)
    train_p, temp_p, train_l, temp_l = train_test_split(
        paths, labels, test_size=0.3, stratify=labels, random_state=seed)
    val_p, test_p, val_l, test_l = train_test_split(
        temp_p, temp_l, test_size=0.5, stratify=temp_l, random_state=seed)

    split = {
        "train": list(zip(train_p, train_l)),
        "val": list(zip(val_p, val_l)),
        "test": list(zip(test_p, test_l)),
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(split, f)
    print({k: len(v) for k, v in split.items()})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data/raw")
    parser.add_argument("--out", default="data/split.json")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    build_split(args.data_dir, args.out, args.seed)
