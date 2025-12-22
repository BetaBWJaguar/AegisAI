import math
import re
from collections import Counter

import unicodedata
from multilangsetup.constants.english import EN_CONTRACTIONS, EN_STOPWORDS

class EnglishNormalizer:
    @staticmethod
    def normalize_characters(text: str) -> str:
        if not isinstance(text, str):
            return ""

        text = unicodedata.normalize("NFC", text)

        replacements = {
            "–": "-",
            "—": "-",
            "…": "...",
            "“": '"', "”": '"',
            "‘": "'", "’": "'",
            "´": "'",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)

        return text

    @staticmethod
    def normalize_spacing(text: str) -> str:
        text = re.sub(r"\s+", " ", text)

        text = re.sub(r"\s+([,.!?;:])", r"\1", text)

        text = re.sub(r"([,.!?;:])([^\s])", r"\1 \2", text)

        return text.strip()

    @staticmethod
    def normalize_quotes(text: str) -> str:
        text = text.replace("“", '"').replace("”", '"')
        text = text.replace("‘", "'").replace("’", "'")
        return text

    @staticmethod
    def clean_unnecessary_punctuation(text: str) -> str:
        if not isinstance(text, str):
            return ""

        text = re.sub(r'([!?.,;:])\1{2,}', r'\1\1', text)

        text = re.sub(r'\b([!?.,;:]+)([a-zA-Z])', r'\2', text)

        text = re.sub(r'\(\s*([.,;:!?]+)\s*\)', '(', text)
        text = re.sub(r'\[\s*([.,;:!?]+)\s*\]', '[', text)

        text = re.sub(r'([.,;:!?])\s*"', r'"\1', text)
        text = re.sub(r'"\s*([.,;:!?])', r'\1"', text)
        
        return text

    @staticmethod
    def normalize_repeated_letters(text: str) -> str:
        if not isinstance(text, str):
            return ""

        text = re.sub(r'([a-zA-Z])\1{2,}', r'\1\1', text)
        
        return text

    @staticmethod
    def expand_contractions(text: str) -> str:
        if not isinstance(text, str):
            return ""

        contraction_pattern = re.compile('(%s)' % '|'.join(map(re.escape, EN_CONTRACTIONS.keys())),
                                       flags=re.IGNORECASE)
        
        def expand_match(contraction):
            match = contraction.group(0)
            expanded_contraction = EN_CONTRACTIONS.get(match.lower(), match)
            return expanded_contraction
        
        expanded_text = contraction_pattern.sub(expand_match, text)
        return expanded_text

    @staticmethod
    def remove_stopwords(text: str) -> str:
        if not isinstance(text, str):
            return ""
        
        words = text.split()
        filtered_words = [word for word in words if word.lower() not in EN_STOPWORDS]
        return ' '.join(filtered_words)

    @staticmethod
    def to_lower(text: str) -> str:
        if not isinstance(text, str):
            return ""
        return text.lower()

    @staticmethod
    def calculate_entropy(text: str) -> float:
        if not isinstance(text, str) or not text:
            return 0.0

        counts = Counter(text)
        total = len(text)

        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)

        return round(entropy, 4)


    @classmethod
    def normalize_all(cls, text: str, to_lower=True, expand_contractions=True, remove_stopwords=False) -> str:
        text = cls.normalize_characters(text)
        text = cls.clean_unnecessary_punctuation(text)
        text = cls.normalize_quotes(text)
        text = cls.normalize_repeated_letters(text)
        
        if expand_contractions:
            text = cls.expand_contractions(text)
            
        if to_lower:
            text = cls.to_lower(text)
            
        text = cls.normalize_spacing(text)
        
        if remove_stopwords:
            text = cls.remove_stopwords(text)
            
        return text.strip()

    @classmethod
    def preprocess_for_analysis(cls, text: str) -> str:
        text = cls.normalize_all(text, to_lower=True, expand_contractions=True, remove_stopwords=False)
        text = re.sub(r'[^\w\s]', '', text)
        text = cls.normalize_spacing(text)
        return text

    @classmethod
    def preprocess_for_keywords(cls, text: str) -> str:
        text = cls.normalize_all(text, to_lower=True, expand_contractions=True, remove_stopwords=True)
        text = re.sub(r'\d+', '', text)
        text = cls.normalize_spacing(text)
        return text

    @staticmethod
    def _count_syllables(word: str) -> int:
        if not isinstance(word, str) or not word:
            return 0
        
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        prev_char_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_char_was_vowel:
                syllable_count += 1
            prev_char_was_vowel = is_vowel

        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1

        return max(1, syllable_count)
