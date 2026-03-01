from dataclasses import dataclass, field
from typing import List


@dataclass
class SpamSettings:
    enabled: bool = True
    rate_limit_count: int = 5
    rate_limit_window_seconds: int = 10
    duplicate_check: bool = True
    duplicate_reset_seconds: int = 30
    burst_limit: int = 20
    cooldown_seconds: int = 60


@dataclass
class ContentControlSettings:
    enabled: bool = True
    spam: SpamSettings = field(default_factory=SpamSettings)