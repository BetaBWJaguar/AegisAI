import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

@dataclass
class Device:
    id: uuid.UUID
    device_name: str
    ip_address: str
    user_agent: str
    login_time: datetime
    last_active: datetime
    is_active: bool = True
    logout_time: Optional[datetime] = None

    @staticmethod
    def create(device_name: str, ip_address: str, user_agent: str) -> "Device":
        now = datetime.utcnow()
        return Device(
            id=uuid.uuid4(),
            device_name=device_name or "Unknown Device",
            ip_address=ip_address or "0.0.0.0",
            user_agent=user_agent or "Unknown",
            login_time=now,
            last_active=now,
            is_active=True
        )

    def mark_logout(self):
        self.is_active = False
        self.logout_time = datetime.utcnow()

    def update_last_active(self):
        self.last_active = datetime.utcnow()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)
        return data
