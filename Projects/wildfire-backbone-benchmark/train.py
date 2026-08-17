import argparse
import time

import timm
import torch
from torch.utils.data import DataLoader

from data.dataset import FireDataset
from models.build_model import build_model


def train(backbone_name, epochs=6, batch_size=32, lr=1e-3, num_workers=2):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[{backbone_name}] device={device}")
    model = build_model(backbone_name).to(device)

    cfg = timm.data.resolve_data_config({}, model=model)
    transform = timm.data.create_transform(**cfg, is_training=True)
    val_transform = timm.data.create_transform(**cfg, is_training=False)

    train_ds = FireDataset("train", transform)
    val_ds = FireDataset("val", val_transform)
    train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_dl = DataLoader(val_ds, batch_size=batch_size, num_workers=num_workers)

    optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=lr)
    criterion = torch.nn.CrossEntropyLoss()
    use_amp = device == "cuda"
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

    best_val_acc = 0
    for epoch in range(epochs):
        t0 = time.time()
        model.train()
        total_loss = 0.0
        for imgs, labels in train_dl:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            with torch.cuda.amp.autocast(enabled=use_amp):
                out = model(imgs)
                loss = criterion(out, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            total_loss += loss.item() * imgs.size(0)

        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for imgs, labels in val_dl:
                imgs, labels = imgs.to(device), labels.to(device)
                preds = model(imgs).argmax(1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)
        val_acc = correct / total
        dt = time.time() - t0
        print(f"[{backbone_name}] epoch {epoch}: train_loss={total_loss/len(train_ds):.4f} "
              f"val_acc={val_acc:.4f} ({dt:.1f}s)")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), f"results/checkpoints/{backbone_name}.pt")
            print(f"[{backbone_name}] saved new best checkpoint (val_acc={val_acc:.4f})")

    print(f"[{backbone_name}] done. best_val_acc={best_val_acc:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backbone", required=True)
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--num_workers", type=int, default=2)
    args = parser.parse_args()
    train(args.backbone, epochs=args.epochs, batch_size=args.batch_size,
          lr=args.lr, num_workers=args.num_workers)
