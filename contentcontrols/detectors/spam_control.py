import time
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
from collections import defaultdict


class SpamType(str, Enum):
    RATE_LIMIT = "RATE_LIMIT"
    DUPLICATE = "DUPLICATE"
    BURST = "BURST"
    COOLDOWN = "COOLDOWN"


class SpamRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class SpamSettings:
    enabled: bool = True

    rate_limit_count: int = 5
    rate_limit_window_seconds: int = 10

    duplicate_check: bool = True
    duplicate_reset_seconds: int = 30

    burst_limit: int = 20

    cooldown_seconds: int = 60
    exempt_roles: List[str] = None


@dataclass
class SpamResult:
    allowed: bool
    spam_type: Optional[SpamType] = None
    risk: Optional[SpamRisk] = None
    reason: Optional[str] = None


class SpamControl:

    def __init__(self, settings: SpamSettings):
        self.settings = settings
        self._timestamps: Dict[str, List[float]] = defaultdict(list)
        self._last_message: Dict[str, str] = {}
        self._last_message_time: Dict[str, float] = {}
        self._burst_counter: Dict[str, int] = defaultdict(int)
        self._cooldowns: Dict[str, float] = {}

    def check(self, user_id: str, message: str, user_role: Optional[str] = None) -> SpamResult:

        if not self.settings.enabled:
            return SpamResult(True)

        if user_role and self.settings.exempt_roles:
            if user_role.upper() in [r.upper() for r in self.settings.exempt_roles]:
                return SpamResult(True)

        now = time.time()


        if self._cooldowns.get(user_id, 0) > now:
            return SpamResult(
                False,
                SpamType.COOLDOWN,
                SpamRisk.HIGH,
                "User in cooldown period"
            )

        if self._rate_limit(user_id, now):
            self._apply_cooldown(user_id, now)
            return SpamResult(
                False,
                SpamType.RATE_LIMIT,
                SpamRisk.MEDIUM,
                "Rate limit exceeded"
            )

        if self.settings.duplicate_check and self._duplicate(user_id, message, now):
            return SpamResult(
                False,
                SpamType.DUPLICATE,
                SpamRisk.LOW,
                "Duplicate message"
            )

        if self._burst(user_id):
            self._apply_cooldown(user_id, now)
            return SpamResult(
                False,
                SpamType.BURST,
                SpamRisk.HIGH,
                "Burst spam detected"
            )

        return SpamResult(True)


    def _rate_limit(self, user_id: str, now: float) -> bool:
        window = self.settings.rate_limit_window_seconds

        self._timestamps[user_id] = [
            t for t in self._timestamps[user_id]
            if now - t <= window
        ]

        if len(self._timestamps[user_id]) >= self.settings.rate_limit_count:
            return True

        self._timestamps[user_id].append(now)
        return False

    def _duplicate(self, user_id: str, message: str, now: float) -> bool:
        last_msg = self._last_message.get(user_id)
        last_time = self._last_message_time.get(user_id, 0)

        if last_msg == message and (now - last_time) <= self.settings.duplicate_reset_seconds:
            return True

        self._last_message[user_id] = message
        self._last_message_time[user_id] = now
        return False

    def _burst(self, user_id: str) -> bool:
        self._burst_counter[user_id] += 1
        return self._burst_counter[user_id] > self.settings.burst_limit

    def _apply_cooldown(self, user_id: str, now: float):
        self._cooldowns[user_id] = now + self.settings.cooldown_seconds