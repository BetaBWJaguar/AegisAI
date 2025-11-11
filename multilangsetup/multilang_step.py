from enum import Enum

class Step(str, Enum):
    NORMALIZE = "normalize"
    DETECT_LANGUAGE = "detect_language"
    LANG_NORMALIZE = "lang_normalize"
    ANALYZE = "analyze"
    LINGUISTICS = "linguistics"
    KEYWORDS = "keywords"
