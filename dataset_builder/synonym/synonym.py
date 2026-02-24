import random
import re
from typing import Dict, List, Optional, Set


class SynonymReplacer:

    def __init__(
            self,
            synonym_dict: Optional[Dict[str, List[str]]] = None,
            prob: float = 0.2,
            seed: Optional[int] = None,
            min_word_length: int = 3,
            stopwords: Optional[Set[str]] = None,
            max_replacements: Optional[int] = None,
            avoid_duplicate_replacements: bool = True
    ):
        self.synonym_dict = synonym_dict or {}
        self.prob = prob
        self.min_word_length = min_word_length
        self.stopwords = stopwords or set()
        self.max_replacements = max_replacements
        self.avoid_duplicate_replacements = avoid_duplicate_replacements

        if seed is not None:
            random.seed(seed)

    def _clean_word(self, word: str):
        match = re.match(r"^(\W*)(\w+)(\W*)$", word)
        if match:
            return match.groups()
        return "", word, ""

    def replace(self, text: str) -> List[str]:
        words = text.split()
        variants = set()

        for i, word in enumerate(words):

            prefix, core, suffix = self._clean_word(word)
            key = core.lower()

            if (
                    key in self.synonym_dict
                    and len(key) >= self.min_word_length
                    and key not in self.stopwords
            ):

                for synonym in self.synonym_dict[key]:

                    new_words = words.copy()

                    replacement = synonym
                    if core and core[0].isupper():
                        replacement = replacement.capitalize()

                    new_words[i] = prefix + replacement + suffix
                    variants.add(" ".join(new_words))

        return list(variants)