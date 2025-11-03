# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class TrainerService(ABC):


    @abstractmethod
    def train_language_model(self, corpus_files: List[str], output_dir: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def fine_tune_model(self, model_path: str, dataset_name: str, output_dir: str, num_labels: int) -> Dict[str, Any]:
        pass
