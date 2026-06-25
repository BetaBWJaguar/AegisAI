import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

class IronySarcasmLabel:
    IRONY = "irony"
    SARCASM = "sarcasm"
    LITERAL = "literal"

class IronySarcasmCue:
    QUOTATION = "quotation"
    ELLIPSIS = "ellipsis"
    EXCLAMATION = "exclamation"
    QUESTION = "question"
    EMPHASIS = "emphasis"
    EMOJI = "emoji"

@dataclass
class IronySarcasmExample:
    text: str
    label: str

    def to_dict(self) -> dict:
        return {"text": self.text, "label": self.label}

@dataclass
class IronySarcasmAnnotation:
    text: str
    label: str
    cues: List[str] = field(default_factory=list)
    cue_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "label": self.label,
            "cues": self.cues,
            "cue_counts": self.cue_counts,
        }

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

    @staticmethod
    def detect_cues(text: str) -> Dict[str, int]:
        if not text:
            return {}

        lowered = text.lower()
        cues: Dict[str, int] = {}

        def _add(cue: str, count: int) -> None:
            if count > 0:
                cues[cue] = count

        _add(IronySarcasmCue.QUOTATION, len(re.findall(r'["“”«»]', text)) // 2)
        _add(IronySarcasmCue.ELLIPSIS, len(re.findall(r"\.{2,}|…", text)))
        _add(IronySarcasmCue.EXCLAMATION, len(re.findall(r"!{2,}", text)))
        _add(IronySarcasmCue.QUESTION, len(re.findall(r"\?{2,}|!\?|\?!", text)))

        caps = len(re.findall(r"\b[A-ZÇĞİÖŞÜ]{3,}\b", text))
        repeated = len(re.findall(r"(.)\1{2,}", lowered))
        _add(IronySarcasmCue.EMPHASIS, caps + repeated)

        sarcastic_emojis = "🙃😏🙄😂🤣😒😑😬🤔"
        _add(IronySarcasmCue.EMOJI, sum(text.count(e) for e in sarcastic_emojis))

        return cues

    def annotate(self) -> List[IronySarcasmAnnotation]:
        annotations: List[IronySarcasmAnnotation] = []
        for ex in self.examples:
            cue_counts = self.detect_cues(ex.text)
            annotations.append(
                IronySarcasmAnnotation(
                    text=ex.text,
                    label=ex.label,
                    cues=list(cue_counts.keys()),
                    cue_counts=cue_counts,
                )
            )
        logger.info("Annotated %d examples.", len(annotations))
        return annotations

    def export_annotations_jsonl(self, output_path: str) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            for annotation in self.annotate():
                f.write(json.dumps(annotation.to_dict(), ensure_ascii=False) + "\n")

        logger.info("Exported annotations to %s", path)
        return str(path)