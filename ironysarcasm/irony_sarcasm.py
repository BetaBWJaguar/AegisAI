import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class IronySarcasmLabel:
    IRONY = "irony"
    SARCASM = "sarcasm"
    LITERAL = "literal"


@dataclass
class IronySarcasmExample:
    text: str
    label: str

    def to_dict(self) -> dict:
        return {"text": self.text, "label": self.label}


@dataclass
class IronySarcasmDataset:
    examples: List[IronySarcasmExample] = field(default_factory=list)

    def add(self, text: str, label: str) -> IronySarcasmExample:
        example = IronySarcasmExample(text=text, label=label)
        self.examples.append(example)
        logger.debug("Added example with label '%s'.", label)
        return example

    def label_distribution(self) -> dict:
        counts: dict = {}
        for ex in self.examples:
            counts[ex.label] = counts.get(ex.label, 0) + 1
        return counts

    def export_jsonl(self, output_path: str) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            for ex in self.examples:
                f.write(json.dumps(ex.to_dict(), ensure_ascii=False) + "\n")

        logger.info("Exported %d examples to %s", len(self.examples), path)
        return str(path)

    @staticmethod
    def load_jsonl(input_path: str) -> "IronySarcasmDataset":
        dataset = IronySarcasmDataset()
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                dataset.add(item["text"], item["label"])
        return dataset
