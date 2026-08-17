import json

from PIL import Image
from torch.utils.data import Dataset


class FireDataset(Dataset):
    def __init__(self, split_name, transform, split_file="data/split.json"):
        with open(split_file) as f:
            data = json.load(f)[split_name]
        self.samples = data
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        return self.transform(img), label
