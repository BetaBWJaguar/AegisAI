from typing import Dict, List
from profanity.categories.profanity_categories_util import (
    build_category_tree,
    get_main_categories,
    get_subcategories,
    build_label,
    parse_label
)


class ProfanityCategories:

    def __init__(self):
        self.category_tree: Dict[str, List[str]] = {}

    def build_from_dataset(self, dataset: List[dict]) -> None:
        self.category_tree = build_category_tree(dataset)

    def get_main_categories(self) -> List[str]:
        return get_main_categories(self.category_tree)

    def get_subcategories(self, category: str) -> List[str]:
        return get_subcategories(self.category_tree, category)

    def build_label(self, category: str, subcategory: str) -> str:
        return build_label(category, subcategory)

    def parse_label(self, label: str) -> tuple[str, str]:
        return parse_label(label)