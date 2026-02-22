import random
from typing import Dict, List, Optional


class SynonymReplacer:

    def __init__(
        self,
        synonym_dict: Optional[Dict[str, List[str]]] = None,
        prob: float = 0.2,
        seed: int = None
    ):
        self.synonym_dict = synonym_dict or {}
        self.prob = prob

        if seed is not None:
            random.seed(seed)

    def replace_word(self, word: str) -> str:
        key = word.lower()

        if key in self.synonym_dict and random.random() < self.prob:
            replacement = random.choice(self.synonym_dict[key])

            if word[0].isupper():
                return replacement.capitalize()

            return replacement

        return word

    def replace(self, text: str) -> str:
        words = text.split()
        new_words = [self.replace_word(w) for w in words]
        return " ".join(new_words)