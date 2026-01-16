# -*- coding: utf-8 -*-

import json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class TrainingConfig:
    training_hours: float
    gpu_hour_price: float
    cpu_hour_price: float
    dataset_size_gb: float
    storage_price_per_gb: float
    tokens_used: int
    token_price_per_million: float
    energy_source: str


@dataclass
class ReportConfig:
    currency: str
    title: str


class ReportConfigLoader:

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)

    def load(self) -> tuple[TrainingConfig, ReportConfig]:
        with self.config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        training = data.get("training", {})
        report = data.get("report", {})

        training_config = TrainingConfig(
            training_hours=training.get("training_hours", 0.0),
            gpu_hour_price=training.get("gpu_hour_price", 0.0),
            cpu_hour_price=training.get("cpu_hour_price", 0.0),
            dataset_size_gb=training.get("dataset_size_gb", 0.0),
            storage_price_per_gb=training.get("storage_price_per_gb", 0.0),
            tokens_used=training.get("tokens_used", 0),
            token_price_per_million=training.get("token_price_per_million", 0.0),
            energy_source=training.get("energy_source", "EXTERNAL")
        )

        report_config = ReportConfig(
            currency=report.get("currency"),
            title=report.get("title")
        )

        return training_config, report_config
