from enum import Enum

class VisibilityMode(str, Enum):
    PUBLIC = "public"
    RECEIVER_ONLY = "receiver_only"
    SENDER_ONLY = "sender_only"
    HIDDEN = "hidden"

