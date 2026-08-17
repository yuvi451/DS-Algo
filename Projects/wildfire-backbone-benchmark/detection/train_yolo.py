"""Stretch goal: train a YOLOv8n detector on the prepared D-Fire data.

Not run as part of the core benchmark (no bounding-box dataset available in this
environment). Run detection/prepare_dfire.py first, then:
    python detection/train_yolo.py --data detection/dfire_prepared/dfire.yaml
"""
import argparse

from ultralytics import YOLO


def train(data_yaml, epochs=20, imgsz=416, batch=16):
    model = YOLO("yolov8n.pt")
    model.train(data=data_yaml, epochs=epochs, imgsz=imgsz, batch=batch)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--imgsz", type=int, default=416)
    parser.add_argument("--batch", type=int, default=16)
    args = parser.parse_args()
    train(args.data, args.epochs, args.imgsz, args.batch)
