from enum import Enum


class CustomRuleType(str, Enum):
    KEYWORD = "KEYWORD"
    REGEX = "REGEX"
    DYNAMIC = "DYNAMIC"
    WILDCARD = "WILDCARD"
    SEMANTIC = "SEMANTIC"
    PATTERN = "PATTERN"
    EXACT = "EXACT"
