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