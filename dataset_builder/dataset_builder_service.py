from abc import ABC, abstractmethod
from typing import List, Optional
from dataset_builder.dataset_builder import DatasetBuilder, DatasetEntry, DatasetType


class DatasetBuilderService(ABC):

    @abstractmethod
    def create_dataset(self, name: str, description: str, dataset_type: DatasetType) -> DatasetBuilder:
        pass

    @abstractmethod
    def add_entry(self, dataset_id: str, text: str, label: str) -> Optional[DatasetEntry]:
        pass

    @abstractmethod
    def remove_entry(self, dataset_id: str, index: int) -> bool:
        pass

    @abstractmethod
    def get_dataset(self, dataset_id: str) -> Optional[DatasetBuilder]:
        pass

    @abstractmethod
    def list_datasets(self) -> List[DatasetBuilder]:
        pass

    @abstractmethod
    def delete_dataset(self, dataset_id: str) -> bool:
        pass
