from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ActionDecision:
    action: str
    notify_user: bool = False
    notify_admin: bool = False
    mask_content: bool = False
    log_event: bool = True
    reason: Optional[str] = None
