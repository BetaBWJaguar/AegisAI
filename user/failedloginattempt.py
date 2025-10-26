from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class FailedLoginAttempt:
    timestamp: datetime
    ip_address: str
    user_agent: str
    reason: str

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "reason": self.reason
        }
