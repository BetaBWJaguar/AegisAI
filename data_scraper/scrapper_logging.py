from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional
import json


@dataclass(slots=True)
class ScrapeLogger:
    log_file: str = "scrape_logs.jsonl"
    logs_dir: Path = field(default_factory=lambda: Path("logs"))
    print_logs: bool = True
    log_path: Path = field(init=False)

    def __post_init__(self) -> None:
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.logs_dir / self.log_file

    @staticmethod
    def _utc_iso() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")

    def _write_line(self, payload: Mapping[str, Any]) -> None:
        line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        if self.print_logs:
            print(f"[ScrapeLogger] {line}")
        with self.log_path.open("a", encoding="utf-8", buffering=1) as f:
            f.write(line + "\n")

    def log(self, meta: Mapping[str, Any]) -> None:
        payload: Dict[str, Any] = dict(meta)
        payload.setdefault("timestamp", self._utc_iso())
        self._write_line(payload)

    def log_success(self, query: str, platform: str, count: int, duration: float) -> None:
        self.log({
            "status": "success",
            "platform": platform,
            "query": query,
            "result_count": int(count),
            "duration_sec": float(duration),
        })

    def log_error(self, query: str, platform: str, error: str, *, error_type: Optional[str] = None) -> None:
        payload: Dict[str, Any] = {
            "status": "error",
            "platform": platform,
            "query": query,
            "error": error,
        }
        if error_type:
            payload["error_type"] = error_type
        self.log(payload)
