from typing import List, Dict, Tuple
from profanity.categories.profanity_categories import ProfanityCategories


class ProfanityLabelValidator:

    def __init__(self, categories: ProfanityCategories):
        self.categories = categories

    def validate_label(self, label: str) -> bool:
        return self.categories.is_valid_label(label)

    def validate_entry(self, entry: Dict) -> bool:
        category = entry.get("label")
        subcategory = entry.get("sublabel")

        if not category:
            return False

        if subcategory and subcategory != "NONE":
            label = self.categories.build_label(category, subcategory)
        else:
            label = category

        return self.validate_label(label)

    def validate_dataset(self, dataset: List[Dict]) -> Tuple[bool, List[int]]:
        invalid_rows = [
            i for i, entry in enumerate(dataset)
            if not self.validate_entry(entry)
        ]

        return len(invalid_rows) == 0, invalid_rows

    def filter_valid_entries(self, dataset: List[Dict]) -> List[Dict]:
        return [entry for entry in dataset if self.validate_entry(entry)]