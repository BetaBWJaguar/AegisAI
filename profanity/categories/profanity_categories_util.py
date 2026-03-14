from typing import Dict, List, Tuple
from collections import defaultdict


def build_category_tree(dataset: List[dict]) -> Dict[str, List[str]]:
    category_tree: Dict[str, List[str]] = defaultdict(list)

    for item in dataset:
        category = item.get("label")
        subcategory = item.get("sublabel")

        if not category:
            continue

        if subcategory and subcategory != "NONE":
            if subcategory not in category_tree[category]:
                category_tree[category].append(subcategory)

    return dict(category_tree)


def get_main_categories(category_tree: Dict[str, List[str]]) -> List[str]:
    return list(category_tree.keys())


def get_subcategories(category_tree: Dict[str, List[str]], category: str) -> List[str]:
    return category_tree.get(category, [])


def build_label(category: str, subcategory: str) -> str:
    if not subcategory or subcategory == "NONE":
        return category

    return f"{category}_{subcategory}"


def parse_label(label: str) -> Tuple[str, str]:
    parts = label.split("_", 1)

    if len(parts) == 1:
        return parts[0], "NONE"

    return parts[0], parts[1]