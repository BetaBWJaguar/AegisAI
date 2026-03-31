from typing import Dict, List
from profanity.categories.profanity_categories import ProfanityCategories


class LabelEncoder:

    def __init__(self, categories: ProfanityCategories):
        self.categories = categories
        self.label_to_index: Dict[str, int] = {}
        self.index_to_label: Dict[int, str] = {}

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

    def encode(self, label: str) -> int:
        if label not in self.label_to_index:
            raise ValueError(f"Unknown label: {label}")
        return self.label_to_index[label]

    def decode(self, index: int) -> str:
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

    def get_mapping(self) -> Dict[str, int]:
        return self.label_to_index