# -*- coding: utf-8 -*-
import json
import time
from pathlib import Path


class PredictionLogger:
    LOG_FILE = Path("prediction_logs.jsonl")

    @staticmethod
    def log(text: str, label: str, offensive_prob: float):
        record = {
            "time": time.time(),
            "text": text,
            "label": label,
            "offensive_prob": offensive_prob
        }

        with open(PredictionLogger.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
