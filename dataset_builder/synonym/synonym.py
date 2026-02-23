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

    def replace(self, text: str) -> str:
        words = text.split()
        replaced_words = []
        replaced_count = 0
        used_words = set()

        for word in words:

            prefix, core, suffix = self._clean_word(word)
            key = core.lower()

            if (
                    key in self.synonym_dict
                    and len(key) >= self.min_word_length
                    and key not in self.stopwords
                    and random.random() < self.prob
            ):

                if self.avoid_duplicate_replacements and key in used_words:
                    replaced_words.append(word)
                    continue

                if self.max_replacements and replaced_count >= self.max_replacements:
                    replaced_words.append(word)
                    continue

                replacement = random.choice(self.synonym_dict[key])

                if core[0].isupper():
                    replacement = replacement.capitalize()

                replaced_word = prefix + replacement + suffix
                replaced_words.append(replaced_word)

                used_words.add(key)
                replaced_count += 1
            else:
                replaced_words.append(word)

        return " ".join(replaced_words)