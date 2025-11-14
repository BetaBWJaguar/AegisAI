# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class TrainerService(ABC):

    @abstractmethod
    def train_language_model(self, corpus_files: List[str], output_dir: str, model_size: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def fine_tune_model(
            self,
            model_path: str,
            dataset_id: str,
            output_dir: str,
            training_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass
