from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ScoreThresholds:
    enabled: bool = False
    low_threshold: float = 30.0
    medium_threshold: float = 60.0
    high_threshold: float = 80.0
    critical_threshold: float = 90.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScoreThresholds":
        return cls(
            enabled=data.get("enabled", False),
            low_threshold=data.get("low_threshold", 30.0),
            medium_threshold=data.get("medium_threshold", 60.0),
            high_threshold=data.get("high_threshold", 80.0),
            critical_threshold=data.get("critical_threshold", 90.0)
        )


@dataclass
class SpamSettings:
    enabled: bool = True
    rate_limit_count: int = 5
    rate_limit_window_seconds: int = 10
    duplicate_check: bool = True
    duplicate_reset_seconds: int = 30
    burst_limit: int = 20
    burst_window_seconds: int = 60
    cooldown_seconds: int = 60
    exempt_roles: List[str] = field(default_factory=list)
    max_message_length: int = 1000
    max_emojis: int = 20
    max_repeated_char: int = 10
    blocked_domains: List[str] = field(default_factory=list)
    allowed_domains: List[str] = field(default_factory=list)
    suspicious_tlds: List[str] = field(default_factory=lambda: [
        ".xyz", ".click", ".top", ".gq", ".tk"
    ])

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpamSettings":
        return cls(
            enabled=data.get("enabled", True),
            rate_limit_count=data.get("rate_limit_count", 5),
            rate_limit_window_seconds=data.get("rate_limit_window_seconds", 10),
            duplicate_check=data.get("duplicate_check", True),
            duplicate_reset_seconds=data.get("duplicate_reset_seconds", 30),
            burst_limit=data.get("burst_limit", 20),
            burst_window_seconds=data.get("burst_window_seconds", 60),
            cooldown_seconds=data.get("cooldown_seconds", 60),
            exempt_roles=data.get("exempt_roles", []),
            max_message_length=data.get("max_message_length", 1000),
            max_emojis=data.get("max_emojis", 20),
            max_repeated_char=data.get("max_repeated_char", 10),
            blocked_domains=data.get("blocked_domains", []),
            allowed_domains=data.get("allowed_domains", []),
            suspicious_tlds=data.get("suspicious_tlds", [".xyz", ".click", ".top", ".gq", ".tk"])
        )


@dataclass
class ContentControlSettings:
    enabled: bool = True
    spam: SpamSettings = field(default_factory=SpamSettings)
    score_thresholds: ScoreThresholds = field(default_factory=ScoreThresholds)
    use_score_based_decision: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentControlSettings":
        spam_data = data.get("spam", {})
        score_data = data.get("score_thresholds", {})
        return cls(
            enabled=data.get("enabled", True),
            use_score_based_decision=data.get("use_score_based_decision", False),
            spam=SpamSettings.from_dict(spam_data),
            score_thresholds=ScoreThresholds.from_dict(score_data)
        )