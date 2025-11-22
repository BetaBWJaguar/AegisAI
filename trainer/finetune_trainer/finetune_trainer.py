# -*- coding: utf-8 -*-
from typing import Dict, Any
from trainer.modelregistry import ModelRegistry
from trainer.service.trainer_service_impl import TrainerServiceImpl


class FineTuneTrainer:

    def __init__(self, config_file: str = "config.json"):
        self.trainer_service = TrainerServiceImpl(config_file)
        self.registry = ModelRegistry()

    def fine_tune(
            self,
            model_path: str,
            dataset_id: str,
            output_dir: str,
            training_args: Dict[str, Any]
    ) -> Dict[str, Any]:

        result = self.trainer_service.fine_tune_model(
            model_path=model_path,
            dataset_id=dataset_id,
            output_dir=output_dir,
            training_args=training_args
        )

        saved_path = result.get("saved_path", output_dir)

        metrics = result.get("metrics", {})

        model_info = self.registry.save_model_info(
            name=result.get("model_name", "fine-tuned-model"),
            version=result.get("version", "v1"),
            model_path=saved_path,
            dataset_id=dataset_id,
            parameters=training_args,
            metrics=metrics
        )

        return {
            "task": "fine_tuning",
            "model_info": model_info,
            "saved_path": saved_path,
            "metrics": metrics,
            "details": result
        }
