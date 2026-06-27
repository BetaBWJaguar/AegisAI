import logging
import statistics
from typing import Dict, List, Optional

from .irony_sarcasm import IronySarcasmDataset, IronySarcasmLabel

logger = logging.getLogger(__name__)


class IronySarcasmClassifier:

    def __init__(
        self,
        dataset: Optional[IronySarcasmDataset] = None,
        irony_threshold: float = 3.0,
        sarcasm_threshold: float = 6.0,
    ) -> None:
        if sarcasm_threshold <= irony_threshold:
            raise ValueError(
                "sarcasm_threshold must be greater than irony_threshold."
            )
        self.dataset = dataset if dataset is not None else IronySarcasmDataset()
        self.irony_threshold = irony_threshold
        self.sarcasm_threshold = sarcasm_threshold

    def _confidence(self, score: float, label: str) -> float:
        if label == IronySarcasmLabel.SARCASM:
            span = max(self.sarcasm_threshold, 1.0)
            return min(1.0, 0.5 + (score - self.sarcasm_threshold) / span)
        if label == IronySarcasmLabel.IRONY:
            span = max(self.sarcasm_threshold - self.irony_threshold, 1.0)
            return min(1.0, 0.5 + (score - self.irony_threshold) / span)
        span = max(self.irony_threshold, 1.0)
        return min(1.0, max(0.0, 1.0 - score / span))

    def classify(self, text: str) -> dict:
        if not text:
            return {
                "text": text,
                "predicted_label": IronySarcasmLabel.LITERAL,
                "score": 0.0,
                "cues": [],
                "cue_counts": {},
                "confidence": 1.0,
            }

        cue_counts = self.dataset.detect_cues(text)
        score = self.dataset.irony_score(text)

        if score >= self.sarcasm_threshold:
            predicted_label = IronySarcasmLabel.SARCASM
        elif score >= self.irony_threshold:
            predicted_label = IronySarcasmLabel.IRONY
        else:
            predicted_label = IronySarcasmLabel.LITERAL

        confidence = self._confidence(score, predicted_label)

        logger.debug(
            "Classified text (score=%.2f) as %s (confidence=%.2f)",
            score,
            predicted_label,
            confidence,
        )

        return {
            "text": text,
            "predicted_label": predicted_label,
            "score": round(score, 4),
            "cues": list(cue_counts.keys()),
            "cue_counts": cue_counts,
            "confidence": round(confidence, 4),
        }

    def predict_batch(self, texts: List[str]) -> List[dict]:
        return [self.classify(text) for text in texts]

    def evaluate(self) -> dict:
        if not self.dataset.examples:
            return {"accuracy": 0.0, "support": 0, "per_label": {}}

        total = 0
        correct = 0
        per_label_correct: Dict[str, int] = {}
        per_label_total: Dict[str, int] = {}

        for ex in self.dataset.examples:
            prediction = self.classify(ex.text)
            predicted_label = prediction["predicted_label"]

            total += 1
            per_label_total[ex.label] = per_label_total.get(ex.label, 0) + 1
            if predicted_label == ex.label:
                correct += 1
                per_label_correct[ex.label] = (
                    per_label_correct.get(ex.label, 0) + 1
                )

        per_label = {
            label: per_label_correct.get(label, 0) / per_label_total[label]
            for label in per_label_total
        }

        logger.info(
            "Evaluation complete: accuracy=%.2f over %d examples",
            correct / total if total else 0.0,
            total,
        )

        return {
            "accuracy": correct / total if total else 0.0,
            "support": total,
            "per_label": per_label,
        }

    def fit_thresholds(self) -> None:
        labeled_scores: Dict[str, List[float]] = {}
        for ex in self.dataset.examples:
            score = self.dataset.irony_score(ex.text)
            labeled_scores.setdefault(ex.label, []).append(score)

        literal_scores = labeled_scores.get(IronySarcasmLabel.LITERAL, [0.0])
        irony_scores = labeled_scores.get(IronySarcasmLabel.IRONY, [])
        sarcasm_scores = labeled_scores.get(IronySarcasmLabel.SARCASM, [])

        literal_max = max(literal_scores)
        irony_median = statistics.median(irony_scores) if irony_scores else literal_max
        sarcasm_median = (
            statistics.median(sarcasm_scores) if sarcasm_scores else irony_median
        )

        self.irony_threshold = max(literal_max, irony_median)
        self.sarcasm_threshold = max(self.irony_threshold + 1.0, sarcasm_median)

        logger.info(
            "Calibrated thresholds: irony=%.2f, sarcasm=%.2f",
            self.irony_threshold,
            self.sarcasm_threshold,
        )
