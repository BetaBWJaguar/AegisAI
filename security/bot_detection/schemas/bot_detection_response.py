from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class BotDetectionResponse(BaseModel):
    actor_key: str = Field(..., description="Unique identifier for the actor")
    verdict: str = Field(..., description="Bot detection verdict (BOT, HUMAN, SUSPICIOUS, UNKNOWN)")
    confidence: float = Field(..., description="Confidence score of the verdict (0.0 to 1.0)")
    action: str = Field(..., description="Recommended action (BLOCK, ALLOW, MONITOR)")
    timestamp: str = Field(..., description="Timestamp of the analysis")
    reason: Optional[str] = Field(None, description="Reason for the verdict when applicable")


class LogMessageResponse(BaseModel):
    success: bool = Field(..., description="Whether the message was logged successfully")
    actor_key: str = Field(..., description="Unique identifier for the actor")
    message: str = Field(..., description="Status message")


class ActorEventsResponse(BaseModel):
    actor_key: str = Field(..., description="Unique identifier for the actor")
    event_count: int = Field(..., description="Number of events recorded")
    events: List[float] = Field(..., description="List of event timestamps")
    statistics: Dict[str, Any] = Field(..., description="Statistical analysis of the events")
    window_sec: float = Field(..., description="Time window used for analysis")


class ClearActorDataResponse(BaseModel):
    success: bool = Field(..., description="Whether the data was cleared successfully")
    actor_key: str = Field(..., description="Unique identifier for the actor")
    message: str = Field(..., description="Status message")