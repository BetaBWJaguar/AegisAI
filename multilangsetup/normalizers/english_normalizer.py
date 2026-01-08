import math
import re
import unicodedata
from collections import Counter
from multilangsetup.constants.english import EN_CONTRACTIONS, EN_STOPWORDS

CHAR_TRANSLATION_TABLE = str.maketrans({
    "–": "-",
    "—": "-",
    "…": "...",
    "“": '"', "”": '"',
    "‘": "'", "’": "'",
    "´": "'",
})

RE_MULTI_SPACE = re.compile(r"\s+")
RE_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.!?;:])")
RE_SPACE_AFTER_PUNCT = re.compile(r"([,.!?;:])([^\s])")
RE_REPEAT_PUNCT = re.compile(r'([!?.,;:])\1{2,}')
RE_PUNCT_BEFORE_LETTER = re.compile(r'\b([!?.,;:]+)([a-zA-Z])')
RE_REPEAT_LETTER = re.compile(r'([a-zA-Z])\1{2,}')
RE_NON_WORD = re.compile(r'[^\w\s]')
RE_DIGITS = re.compile(r'\d+')
RE_URL = re.compile(r'https?://\S+|www\.\S+')
RE_EMAIL = re.compile(r'\b[\w\.-]+@[\w\.-]+\.\w+\b')
RE_MENTION = re.compile(r'@\w+')


CONTRACTION_PATTERN = re.compile(
    r'(%s)' % '|'.join(map(re.escape, EN_CONTRACTIONS)),
    flags=re.IGNORECASE
)
VOWELS = "aeiouy"

class EnglishNormalizer:
    @staticmethod
    def normalize_characters(text: str) -> str:
        if not text:
            return ""
        text = unicodedata.normalize("NFC", text)
        return text.translate(CHAR_TRANSLATION_TABLE)


    @staticmethod
    def normalize_spacing(text: str) -> str:
        text = RE_MULTI_SPACE.sub(" ", text)
        text = RE_SPACE_BEFORE_PUNCT.sub(r"\1", text)
        text = RE_SPACE_AFTER_PUNCT.sub(r"\1 \2", text)
        return text.strip()

    @staticmethod
    def remove_urls_emails_mentions(text: str) -> str:
        text = RE_URL.sub("", text)
        text = RE_EMAIL.sub("", text)
        text = RE_MENTION.sub("", text)
        return text



    @staticmethod
    def normalize_quotes(text: str) -> str:
        text = text.replace("“", '"').replace("”", '"')
        text = text.replace("‘", "'").replace("’", "'")
        return text

    @staticmethod
    def clean_unnecessary_punctuation(text: str) -> str:
        text = RE_REPEAT_PUNCT.sub(r'\1\1', text)
        text = RE_PUNCT_BEFORE_LETTER.sub(r'\2', text)
        return text

    @staticmethod
    def normalize_repeated_letters(text: str) -> str:
        return RE_REPEAT_LETTER.sub(r'\1\1', text)


    @staticmethod
    def expand_contractions(text: str) -> str:
        if not isinstance(text, str):
            return ""

        def expand(match):
            return EN_CONTRACTIONS.get(match.group(0).lower(), match.group(0))

        return CONTRACTION_PATTERN.sub(expand, text)

    @staticmethod
    def remove_stopwords(text: str) -> str:
        return ' '.join(
            word for word in text.split()
            if word.lower() not in EN_STOPWORDS
        )

    @staticmethod
    def to_lower(text: str) -> str:
        if not isinstance(text, str):
            return ""
        return text.lower()

    @staticmethod
    def calculate_entropy(text: str) -> float:
        if not text:
            return 0.0

        total = len(text)
        entropy = sum(
            -(count / total) * math.log2(count / total)
            for count in Counter(text).values()
        )
        return round(entropy, 4)


    @classmethod
    def normalize_all(cls, text: str,
                      to_lower: bool = True,
                      expand_contractions: bool = True,
                      remove_stopwords: bool = False) -> str:

        if not text:
            return ""

        text = cls.normalize_characters(text)
        text = cls.clean_unnecessary_punctuation(text)
        text = cls.normalize_repeated_letters(text)
        text = cls.remove_urls_emails_mentions(text)

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
        text = cls.normalize_all(text)
        text = RE_NON_WORD.sub("", text)
        return cls.normalize_spacing(text)

    @classmethod
    def preprocess_for_keywords(cls, text: str) -> str:
        text = cls.normalize_all(text, remove_stopwords=True)
        text = RE_DIGITS.sub("", text)
        return cls.normalize_spacing(text)

    @staticmethod
    def _count_syllables(word: str) -> int:
        if not word:
            return 0
        
        word = word.lower()
        count = 0
        prev_vowel = False

        for ch in word:
            is_vowel = ch in VOWELS
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel

        if word.endswith("e") and count > 1:
            count -= 1

        return max(1, count)
