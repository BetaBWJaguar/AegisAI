# -*- coding: utf-8 -*-
import json
from datetime import datetime
from pathlib import Path
from typing import Dict


class ScrapeLogger:
    def __init__(self, log_file: str = "scrape_logs.jsonl"):
        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = logs_dir / log_file

    def log(self, meta: Dict):
        meta["timestamp"] = datetime.utcnow().isoformat()
        print(f"[ScrapeLogger] {meta}")

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")

    def log_success(self, query: str, platform: str, count: int, duration: float):
        self.log({
            "status": "success",
            "platform": platform,
            "query": query,
            "result_count": count,
            "duration_sec": duration
        })

    def log_error(self, query: str, platform: str, error: str):
        self.log({
            "status": "error",
            "platform": platform,
            "query": query,
            "error": error
        })
