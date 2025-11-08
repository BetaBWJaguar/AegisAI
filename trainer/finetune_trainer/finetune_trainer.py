# -*- coding: utf-8 -*-
from typing import Dict, Any

from transformers import TrainingArguments

from trainer.service.trainer_service_impl import TrainerServiceImpl


class FineTuneTrainer:

    def __init__(self, config_file: str = "config.json"):
        self.trainer_service = TrainerServiceImpl(config_file)

    def fine_tune(
            self,
            model_path: str,
            dataset_id: str,
            output_dir: str,
            training_args: Dict[str, Any]
    ) -> Dict[str, Any]:

        args = TrainingArguments(**training_args)

        result = self.trainer_service.fine_tune_model(
            model_path=model_path,
            dataset_id=dataset_id,
            output_dir=output_dir,
            training_args=args
        )

        return {
            "task": "fine_tuning",
            **result
        }
