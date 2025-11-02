# -*- coding: utf-8 -*-
from datasets import load_dataset
from pathlib import Path
from typing import Dict, Optional


class HuggingFaceManager:
    def __init__(self, cache_dir: str = "hf_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.datasets: Dict[str, object] = {}

    def add_dataset(self, name: str, subset: Optional[str] = None, split: str = "train"):
        key = f"{name}:{subset or 'default'}:{split}"
        try:
            if subset:
                dataset = load_dataset(name, subset, split=split, cache_dir=self.cache_dir)
            else:
                dataset = load_dataset(name, split=split, cache_dir=self.cache_dir)
            self.datasets[key] = dataset
        except Exception:
            pass

    def get_dataset(self, key: str) -> Optional[object]:
        return self.datasets.get(key)

    def list_datasets(self):
        if not self.datasets:
            return {}
        return {name: len(ds) for name, ds in self.datasets.items()}

    def preview(self, key: str, n: int = 3):
        dataset = self.get_dataset(key)
        if not dataset:
            return None
        return [dataset[i] for i in range(min(n, len(dataset)))]

    def save_dataset(self, key: str, output_dir: str):
        dataset = self.get_dataset(key)
        if not dataset:
            return
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        out_file = Path(output_dir) / f"{key.replace('/', '_').replace(':', '_')}.json"
        dataset.to_json(out_file)

    def clear(self):
        self.datasets.clear()
