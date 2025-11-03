# -*- coding: utf-8 -*-
import re
from pathlib import Path
from typing import List, Optional
from huggingface.huggingfacemanager import HuggingFaceManager


class CorpusManager:
    def __init__(self, hf_manager: HuggingFaceManager, corpus_dir: str = "corpora"):
        self.hf_manager = hf_manager
        self.corpus_dir = Path(corpus_dir)
        self.corpus_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def clean_text(text: str) -> str:
        text = text.replace("\n", " ").replace("\r", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def build_corpus(
            self,
            dataset_key: str,
            output_name: str,
            text_field: str = "text",
            limit: Optional[int] = None,
    ):
        dataset = self.hf_manager.get_dataset(dataset_key)
        if not dataset:
            print(f"[❌] Dataset not found: {dataset_key}")
            return

        output_file = self.corpus_dir / f"{output_name}.txt"
        written = 0

        print(f"[🧠] Building corpus '{output_name}' from {dataset_key} ...")
        with open(output_file, "w", encoding="utf-8") as f:
            for i, item in enumerate(dataset):
                if limit and i >= limit:
                    break
                text = item.get(text_field, "")
                text = self.clean_text(text)
                if text:
                    f.write(text + "\n")
                    written += 1

        print(f"[✅] Corpus '{output_name}' created successfully ({written} lines).")

    def preview(self, output_name: str, n: int = 5):
        file_path = self.corpus_dir / f"{output_name}.txt"
        if not file_path.exists():
            print(f"[❌] Corpus not found: {output_name}")
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [next(f).strip() for _ in range(n)]
        return lines

    def list_corpora(self):
        return [p.name for p in self.corpus_dir.glob("*.txt")]
