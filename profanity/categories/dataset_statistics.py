from typing import List, Dict
from collections import defaultdict


class DatasetStatistics:

    def __init__(self, dataset: List[dict]):
        self.dataset = dataset

    def dataset_size(self) -> int:
        return len(self.dataset)

    def count_categories(self) -> Dict[str, int]:
        stats = defaultdict(int)

        for item in self.dataset:
            category = item.get("label")

            if category:
                stats[category] += 1

        return dict(stats)

    def count_subcategories(self) -> Dict[str, int]:
        stats = defaultdict(int)

        for item in self.dataset:
            category = item.get("label")
            subcategory = item.get("sublabel")

            if not category:
                continue

            if not subcategory or subcategory == "NONE":
                continue

            key = f"{category}_{subcategory}"
            stats[key] += 1

        return dict(stats)

    def summary(self) -> Dict:
        return {
            "dataset_size": self.dataset_size(),
            "category_distribution": self.count_categories(),
            "subcategory_distribution": self.count_subcategories()
        }