from typing import Dict, List, Optional
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
            subcategories = self.categories.get_subcategories(category)

            if not subcategories:
                labels.append(category)
            else:
                for sub in subcategories:
                    labels.append(f"{category}_{sub}")

        labels = sorted(labels)

        self.label_to_index = {label: i for i, label in enumerate(labels)}
        self.index_to_label = {i: label for label, i in self.label_to_index.items()}
        self._is_fitted = True

    def encode(self, label: str) -> int:
        if not self._is_fitted:
            raise RuntimeError("Encoder has not been fitted. Call fit() first.")

        if label not in self.label_to_index:
            raise ValueError(f"Unknown label: {label}")
        return self.label_to_index[label]

    def decode(self, index: int) -> str:
        if not self._is_fitted:
            raise RuntimeError("Encoder has not been fitted. Call fit() first.")

        if index not in self.index_to_label:
            raise ValueError(f"Unknown index: {index}")
        return self.index_to_label[index]

    def encode_entry(self, entry: Dict) -> int:
        category = entry.get("label")
        subcategory = entry.get("sublabel")

        label = self.categories.build_label(category, subcategory)
        return self.encode(label)

    def encode_dataset(self, dataset: List[Dict]) -> List[int]:
        return [self.encode_entry(entry) for entry in dataset]

    def encode_batch(self, labels: List[str]) -> List[int]:
        return [self.encode(label) for label in labels]

    def decode_batch(self, indices: List[int]) -> List[str]:
        return [self.decode(index) for index in indices]

    def get_mapping(self) -> Dict[str, int]:
        return self.label_to_index

    def get_reverse_mapping(self) -> Dict[int, str]:
        return self.index_to_label

    def get_all_labels(self) -> List[str]:
        return sorted(self.label_to_index.keys())

    def get_num_classes(self) -> int:
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
