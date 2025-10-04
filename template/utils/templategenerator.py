import itertools
from string import Formatter
from typing import List, Dict, Any

class TemplateGenerator:
    def __init__(self, pattern: str):
        self.pattern = pattern

    def extract_placeholders(self) -> List[str]:
        return [fname for _, fname, _, _ in Formatter().parse(self.pattern) if fname]

    def generate_from_dataset_values(self, dataset_values: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        if "values" in dataset_values:
            dataset_values = dataset_values["values"]

        placeholders = self.extract_placeholders()
        filtered_values = {k: dataset_values[k] for k in placeholders if k in dataset_values}
        keys, values_lists = zip(*filtered_values.items()) if filtered_values else ([], [])
        variations = []
        for combo in itertools.product(*values_lists):
            value_map = dict(zip(keys, combo))
            text = self.pattern.format(**value_map)
            variations.append({"text": text, "values": value_map})
        return variations

