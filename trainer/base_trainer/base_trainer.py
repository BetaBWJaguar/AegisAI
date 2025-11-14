# -*- coding: utf-8 -*-
from typing import List, Dict, Any
from trainer.service.trainer_service_impl import TrainerServiceImpl


class BaseTrainer:
    def __init__(self, config_file: str = "config.json"):
        self.trainer_service = TrainerServiceImpl(config_file)

    def train(self, corpus_files: List[str], output_dir: str,model_size: str) -> Dict[str, Any]:
        result = self.trainer_service.train_language_model(corpus_files, output_dir,model_size)
        return {
            "task": "base_language_model_training",
            **result
        }
