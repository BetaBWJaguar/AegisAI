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

    @abstractmethod
    def export_format(self, dataset_id: str, export_type: str) -> Optional[bytes]:
        pass

    @abstractmethod
    def add_entries_bulk(self, dataset_id: str, entries: List[dict]) -> List[DatasetEntry]:
        pass

    @abstractmethod
    def search_entries(self, dataset_id: str, query: Optional[str] = None,
                       label: Optional[str] = None) -> List[DatasetEntry]:
        pass

    @abstractmethod
    def merge_datasets(self, primary_id: str, secondary_id: str, remove_dupes: bool,new_dataset: bool) -> Optional[DatasetBuilder]:
        pass
