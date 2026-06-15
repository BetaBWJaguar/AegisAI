from enum import Enum
from typing import Iterable, Optional


class RuleSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EXTRA = "EXTRA"


    @classmethod
    def weight(cls, severity: "RuleSeverity") -> int:
        return {
            cls.LOW: 1,
            cls.MEDIUM: 2,
            cls.HIGH: 3,
            cls.CRITICAL: 4,
            cls.EXTRA: 5,
        }.get(severity, 0)


    @classmethod
    def from_value(
        cls, value, default: "Optional[RuleSeverity]" = None
    ) -> "Optional[RuleSeverity]":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            normalized = value.strip().upper()
            for member in cls:
                if member.value == normalized:
                    return member
        return default

    @classmethod
    def safe(cls, value) -> "RuleSeverity":
        return cls.from_value(value, cls.LOW)


    @classmethod
    def highest(
        cls, severities: "Iterable[Optional[RuleSeverity]]"
    ) -> "Optional[RuleSeverity]":
        best: Optional[RuleSeverity] = None
        for sev in severities:
            resolved = cls.from_value(sev)
            if resolved is None:
                continue
            if best is None or cls.weight(resolved) > cls.weight(best):
                best = resolved
        return best

    def is_at_least(self, other: "RuleSeverity") -> bool:
        return RuleSeverity.weight(self) >= RuleSeverity.weight(other)

    def is_high_or_above(self) -> bool:
        return self.is_at_least(RuleSeverity.HIGH)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, RuleSeverity):
            return NotImplemented
        return RuleSeverity.weight(self) < RuleSeverity.weight(other)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, RuleSeverity):
            return NotImplemented
        return RuleSeverity.weight(self) <= RuleSeverity.weight(other)

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, RuleSeverity):
            return NotImplemented
        return RuleSeverity.weight(self) > RuleSeverity.weight(other)

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, RuleSeverity):
            return NotImplemented
        return RuleSeverity.weight(self) >= RuleSeverity.weight(other)


    @property
    def color(self) -> str:
        return {
            RuleSeverity.LOW: "#28a745",
            RuleSeverity.MEDIUM: "#ffc107",
            RuleSeverity.HIGH: "#fd7e14",
            RuleSeverity.CRITICAL: "#dc3545",
            RuleSeverity.EXTRA: "#6f42c1",
        }.get(self, "#6c757d")
