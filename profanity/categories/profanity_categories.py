from typing import Dict, List, Tuple
from collections import defaultdict


class ProfanityCategories:

    def __init__(self):
        self.category_tree: Dict[str, List[str]] = defaultdict(list)

    def build_from_dataset(self, dataset: List[dict]) -> None:
        for item in dataset:
            category = item.get("label")
            subcategory = item.get("sublabel")

            if not category:
                continue

            if subcategory and subcategory not in self.category_tree[category]:
                self.category_tree[category].append(subcategory)

            if category not in self.category_tree:
                self.category_tree[category] = []

    def get_main_categories(self) -> List[str]:
        return list(self.category_tree.keys())

    def get_subcategories(self, category: str) -> List[str]:
        return self.category_tree.get(category, [])

    def build_label(self, category: str, subcategory: str) -> str:
        if not subcategory or subcategory == "NONE":
            return category

        return f"{category}_{subcategory}"

    def parse_label(self, label: str) -> Tuple[str, str]:
        parts = label.split("_", 1)

        if len(parts) == 1:
            return parts[0], "NONE"

        return parts[0], parts[1]