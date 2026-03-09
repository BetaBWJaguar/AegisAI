from typing import List, Dict, Tuple
from profanity.categories.profanity_categories import ProfanityCategories


class ProfanityLabelValidator:

    def __init__(self, categories: ProfanityCategories):
        self.categories = categories

    def validate_label(self, label: str) -> bool:
        category, subcategory = self.categories.parse_label(label)

        if category not in self.categories.get_main_categories():
            return False

        if subcategory:
            if subcategory not in self.categories.get_subcategories(category):
                return False

        return True

    def validate_entry(self, entry: Dict) -> bool:
        category = entry.get("label")
        subcategory = entry.get("sublabel")

        if not category:
            return False

        if category not in self.categories.get_main_categories():
            return False

        if subcategory:
            if subcategory not in self.categories.get_subcategories(category):
                return False

        return True

    def validate_dataset(self, dataset: List[Dict]) -> Tuple[bool, List[int]]:
        invalid_rows = []

        for i, entry in enumerate(dataset):
            if not self.validate_entry(entry):
                invalid_rows.append(i)

        return len(invalid_rows) == 0, invalid_rows