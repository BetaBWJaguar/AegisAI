# -*- coding: utf-8 -*-
from typing import Dict, Any
from trainer.service.trainer_service_impl import TrainerServiceImpl


class FineTuneTrainer:

    def __init__(self, config_file: str = "config.json"):
        self.trainer_service = TrainerServiceImpl(config_file)

    def fine_tune(self, model_path: str, dataset_id: str, output_dir: str, num_labels: int = 2) -> Dict[str, Any]:
        result = self.trainer_service.fine_tune_model(model_path, dataset_id, output_dir, num_labels)
        return {
            "task": "fine_tuning",
            **result
        }
