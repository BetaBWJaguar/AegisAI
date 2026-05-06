from enum import Enum


class CustomRuleAction(str, Enum):
    BLOCK = "BLOCK"
    MASK = "MASK"
    WARN = "WARN"
    FLAG = "FLAG"
    REPLACE = "REPLACE"
    REDACT = "REDACT"
    LOG = "LOG"
