import time
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict


class SpamType(str, Enum):
    RATE_LIMIT = "RATE_LIMIT"
    DUPLICATE = "DUPLICATE"
    BURST = "BURST"
    COOLDOWN = "COOLDOWN"
    CONTENT = "CONTENT"


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
    burst_window_seconds: int = 60
    cooldown_seconds: int = 60
    exempt_roles: List[str] = field(default_factory=list)
    max_message_length: int = 1000
    max_emojis: int = 20
    max_repeated_char: int = 10


@dataclass
class SpamResult:
    allowed: bool
    spam_type: Optional[SpamType] = None
    risk: Optional[SpamRisk] = None
    reason: Optional[str] = None
    score: float = 0.0


class SpamControl:

    def __init__(self, settings: SpamSettings):
        self.settings = settings
        self._timestamps: Dict[str, List[float]] = defaultdict(list)
        self._burst_timestamps: Dict[str, List[float]] = defaultdict(list)
        self._last_message: Dict[str, str] = {}
        self._last_message_time: Dict[str, float] = {}
        self._cooldowns: Dict[str, float] = {}

    def check(self, user_id: str, message: str, user_role: Optional[str] = None) -> SpamResult:

        if not self.settings.enabled:
            return SpamResult(True)

        if user_role and user_role.upper() in [r.upper() for r in self.settings.exempt_roles]:
            return SpamResult(True)

        now = time.time()
        message = self._normalize(message)


        if self._cooldowns.get(user_id, 0) > now:
            return SpamResult(False, SpamType.COOLDOWN, SpamRisk.HIGH, "User in cooldown", score=90.0)


        content_spam = self._content_spam(message)
        if content_spam:
            return content_spam


        if self._rate_limit(user_id, now):
            self._apply_cooldown(user_id, now)
            return SpamResult(False, SpamType.RATE_LIMIT, SpamRisk.MEDIUM, "Rate limit exceeded", score=65.0)

        if self.settings.duplicate_check and self._duplicate(user_id, message, now):
            return SpamResult(False, SpamType.DUPLICATE, SpamRisk.LOW, "Duplicate message", score=35.0)

        if self._burst(user_id, now):
            self._apply_cooldown(user_id, now)
            return SpamResult(False, SpamType.BURST, SpamRisk.HIGH, "Burst spam detected", score=85.0)

        return SpamResult(True)

    def _normalize(self, message: str) -> str:
        return message.strip().lower()

    def _rate_limit(self, user_id: str, now: float) -> bool:
        window = self.settings.rate_limit_window_seconds
        timestamps = self._timestamps[user_id]

        self._timestamps[user_id] = [t for t in timestamps if now - t <= window]

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

    def _burst(self, user_id: str, now: float) -> bool:
        window = self.settings.burst_window_seconds
        timestamps = self._burst_timestamps[user_id]

        self._burst_timestamps[user_id] = [t for t in timestamps if now - t <= window]

        if len(self._burst_timestamps[user_id]) >= self.settings.burst_limit:
            return True

        self._burst_timestamps[user_id].append(now)
        return False

    def _content_spam(self, message: str) -> Optional[SpamResult]:

        if len(message) > self.settings.max_message_length:
            score = 50.0 + min(50.0, (len(message) - self.settings.max_message_length) / 10.0)
            return SpamResult(False, SpamType.CONTENT, SpamRisk.MEDIUM, "Message too long", score=score)


        if "http://" in message or "https://" in message:
            return SpamResult(False, SpamType.CONTENT, SpamRisk.HIGH, "Link detected", score=75.0)


        emojis = re.findall(r'[^\w\s]', message)
        if len(emojis) > self.settings.max_emojis:
            score = 40.0 + min(40.0, (len(emojis) - self.settings.max_emojis) * 2.0)
            return SpamResult(False, SpamType.CONTENT, SpamRisk.MEDIUM, "Too many symbols/emojis", score=score)


        for char in set(message):
            if message.count(char) > self.settings.max_repeated_char:
                repeat_count = message.count(char)
                score = 45.0 + min(45.0, (repeat_count - self.settings.max_repeated_char) * 3.0)
                return SpamResult(False, SpamType.CONTENT, SpamRisk.MEDIUM, "Character flood", score=score)

        return None

    def _apply_cooldown(self, user_id: str, now: float):
        self._cooldowns[user_id] = now + self.settings.cooldown_seconds