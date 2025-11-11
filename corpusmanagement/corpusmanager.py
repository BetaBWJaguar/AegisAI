# -*- coding: utf-8 -*-
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from huggingface.huggingfacemanager import HuggingFaceManager


class CorpusManager:
    def __init__(self, hf_manager: HuggingFaceManager, corpus_dir: str = "corpora"):
        self.hf_manager = hf_manager
        self.corpus_dir = Path(corpus_dir)
        self.corpus_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def clean_text(text: str) -> str:
        if not isinstance(text, str):
            return ""
        text = text.replace("\n", " ").replace("\r", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def build_corpus(
            self,
            dataset_key: str,
            output_name: str,
            text_field: str = "text",
            limit: Optional[int] = None,
            filters: Optional[List[Callable[[str], bool]]] = None,
            transformers: Optional[List[Callable[[str], str]]] = None,
            append: bool = False,
    ) -> Dict[str, Any]:

        dataset = self.hf_manager.get(dataset_key)
        if not dataset:
            return {"success": False, "error": f"Dataset not found: {dataset_key}"}

        output_file = self.corpus_dir / f"{output_name}.txt"
        mode = "a" if append else "w"
        written = 0
        lengths = []

        with open(output_file, mode, encoding="utf-8") as f:
            for i, item in enumerate(dataset):
                if limit and i >= limit:
                    break
                text = item.get(text_field, "")
                text = self.clean_text(text)
                if not text:
                    continue

                if filters and not all(f(text) for f in filters):
                    continue
                if transformers:
                    for t in transformers:
                        text = t(text)

                f.write(text + "\n")
                written += 1
                lengths.append(len(text))

        avg_len = round(sum(lengths) / len(lengths), 2) if lengths else 0

        metadata = {
            "success": True,
            "dataset_key": dataset_key,
            "output_name": output_name,
            "lines": written,
            "avg_length": avg_len,
            "created": datetime.utcnow().isoformat() + "Z",
        }

        self._write_metadata(output_name, metadata)
        return metadata

    def _metadata_path(self, output_name: str) -> Path:
        return self.corpus_dir / f"{output_name}.meta.json"

    def _write_metadata(self, output_name: str, data: Dict[str, Any]):
        path = self._metadata_path(output_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_metadata(self, output_name: str) -> Optional[Dict[str, Any]]:
        path = self._metadata_path(output_name)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def preview(self, output_name: str, n: int = 5) -> List[str]:
        file_path = self.corpus_dir / f"{output_name}.txt"
        if not file_path.exists():
            return []
        lines = []
        with open(file_path, "r", encoding="utf-8") as f:
            for _ in range(n):
                try:
                    lines.append(next(f).strip())
                except StopIteration:
                    break
        return lines

    def list_corpora(self) -> List[str]:
        return [p.stem for p in self.corpus_dir.glob("*.txt")]

    def delete_corpus(self, output_name: str) -> bool:
        txt_path = self.corpus_dir / f"{output_name}.txt"
        meta_path = self._metadata_path(output_name)
        deleted = False
        for p in [txt_path, meta_path]:
            if p.exists():
                p.unlink()
                deleted = True
        return deleted

    def merge_corpora(self, corpus_names: List[str], output_name: str) -> Dict[str, Any]:
        output_file = self.corpus_dir / f"{output_name}.txt"
        total = 0
        for name in corpus_names:
            path = self.corpus_dir / f"{name}.txt"
            if not path.exists():
                continue
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            total += len(lines)
            with open(output_file, "a", encoding="utf-8") as out_f:
                out_f.writelines(lines)

        return {"output_name": output_name, "merged_from": corpus_names, "lines": total}

    def split_corpus(self, output_name: str, parts: int = 2) -> List[str]:
        src_path = self.corpus_dir / f"{output_name}.txt"
        if not src_path.exists():
            return []

        with open(src_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        chunk_size = len(lines) // parts
        out_files = []

        for i in range(parts):
            part_lines = lines[i * chunk_size: (i + 1) * chunk_size]
            out_path = self.corpus_dir / f"{output_name}_part{i + 1}.txt"
            with open(out_path, "w", encoding="utf-8") as out_f:
                out_f.writelines(part_lines)
            out_files.append(out_path.name)

        return out_files

    def analyze(self, output_name: str) -> Dict[str, Any]:
        path = self.corpus_dir / f"{output_name}.txt"
        if not path.exists():
            return {}

        with open(path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        words = []
        for l in lines:
            words.extend(re.findall(r"\w+", l.lower()))

        unique_words = set(words)
        return {
            "lines": len(lines),
            "avg_length": round(sum(len(l) for l in lines) / len(lines), 2) if lines else 0,
            "vocab_size": len(unique_words),
            "unique_ratio": round(len(unique_words) / len(words), 4) if words else 0,
        }
