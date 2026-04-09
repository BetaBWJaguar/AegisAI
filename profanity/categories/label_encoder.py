from typing import Dict, List
from profanity.categories.profanity_categories import ProfanityCategories


class LabelEncoder:

    def __init__(self, categories: ProfanityCategories):
        self.categories = categories
        self.label_to_index: Dict[str, int] = {}
        self.index_to_label: Dict[int, str] = {}
        self._is_fitted: bool = False

    def fit(self) -> None:
        labels = []
        for category in self.categories.get_main_categories():
            subs = self.categories.get_subcategories(category)
            labels.extend([category] if not subs else [f"{category}_{s}" for s in subs])
        
        labels = sorted(labels)
        self.label_to_index = {label: i for i, label in enumerate(labels)}
        self.index_to_label = {i: label for label, i in self.label_to_index.items()}
        self._is_fitted = True

    def _check_fitted(self) -> None:
        if not self._is_fitted:
            raise RuntimeError("Encoder has not been fitted. Call fit() first.")

    def encode(self, label: str) -> int:
        self._check_fitted()
        if label not in self.label_to_index:
            raise ValueError(f"Unknown label: {label}")
        return self.label_to_index[label]

    def decode(self, index: int) -> str:
        self._check_fitted()
        if index not in self.index_to_label:
            raise ValueError(f"Unknown index: {index}")
        return self.index_to_label[index]

    def encode_entry(self, entry: Dict) -> int:
        return self.encode(self.categories.build_label(entry.get("label"), entry.get("sublabel")))

    def encode_dataset(self, dataset: List[Dict]) -> List[int]:
        return [self.encode_entry(entry) for entry in dataset]

    def encode_batch(self, labels: List[str]) -> List[int]:
        return [self.encode(label) for label in labels]

    def decode_batch(self, indices: List[int]) -> List[str]:
        return [self.decode(index) for index in indices]

    @property
    def mapping(self) -> Dict[str, int]:
        return self.label_to_index

    @property
    def reverse_mapping(self) -> Dict[int, str]:
        return self.index_to_label

    @property
    def labels(self) -> List[str]:
        return sorted(self.label_to_index.keys())

    @property
    def num_classes(self) -> int:
        return len(self.label_to_index)

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    def __len__(self) -> int:
        return len(self.label_to_index)

    def __contains__(self, label: str) -> bool:
        return label in self.label_to_index

    def __repr__(self) -> str:
        return f"LabelEncoder(num_classes={len(self)}, is_fitted={self._is_fitted})"
