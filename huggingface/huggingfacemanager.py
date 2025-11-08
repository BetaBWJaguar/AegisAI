# -*- coding: utf-8 -*-
from datasets import load_dataset
from pathlib import Path
from typing import Dict, Optional


class HuggingFaceManager:
    def __init__(self, cache_dir: str = "hf_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.datasets: Dict[str, object] = {}

    def load(self, name: str, subset: Optional[str] = None, split: str = "train"):
        key = f"{name}:{subset or 'default'}:{split}"
        try:
            if subset:
                dataset = load_dataset(name, subset, split=split, cache_dir=str(self.cache_dir))
            else:
                dataset = load_dataset(name, split=split, cache_dir=str(self.cache_dir))

            self.datasets[key] = dataset
            print(f"[HF] Loaded dataset → {key} ({len(dataset)} records)")
        except Exception as e:
            print(f"[HF ERROR] Failed to load dataset ({name}, {subset}, {split}) → {e}")

    def get(self, key: str) -> Optional[object]:
        return self.datasets.get(key)

    def list(self):
        return {name: len(ds) for name, ds in self.datasets.items()}

    def preview(self, key: str, n: int = 3):
        dataset = self.get(key)
        if not dataset:
            print(f"[HF ERROR] Preview failed → Dataset not found → {key}")
            return None
        return [dataset[i] for i in range(min(n, len(dataset)))]

    def save(self, key: str, output_dir: str = "saved_datasets"):
        dataset = self.get(key)
        if not dataset:
            print(f"[HF ERROR] Save failed → Dataset not found → {key}")
            return

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        out_file = Path(output_dir) / f"{key.replace('/', '_').replace(':', '_')}.json"
        dataset.to_json(str(out_file))

        print(f"[HF] Saved dataset → {out_file}")

    def clear(self):
        self.datasets.clear()
        print("[HF] Cleared all loaded datasets.")
