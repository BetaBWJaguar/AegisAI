from enum import Enum


class CustomRuleAction(str, Enum):
    BLOCK = "BLOCK"
    MASK = "MASK"
    WARN = "WARN"
    FLAG = "FLAG"
