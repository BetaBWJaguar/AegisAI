from enum import Enum


class CustomRuleType(str, Enum):
    KEYWORD = "KEYWORD"
    REGEX = "REGEX"
    DYNAMIC = "DYNAMIC"
