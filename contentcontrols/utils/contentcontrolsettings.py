from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ScoreThresholds:
    enabled: bool = False
    low_threshold: float = 30.0
    medium_threshold: float = 60.0
    high_threshold: float = 80.0
    critical_threshold: float = 90.0


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


@dataclass
class ContentControlSettings:
    enabled: bool = True
    spam: SpamSettings = field(default_factory=SpamSettings)
    score_thresholds: ScoreThresholds = field(default_factory=ScoreThresholds)
    use_score_based_decision: bool = False