from pydantic import BaseModel, Field
from typing import Optional


class LogMessageRequest(BaseModel):
    actor_key: str = Field(..., description="Unique identifier for the actor (user ID, IP address, etc.)")
    workspace_id: Optional[str] = Field(None, description="Workspace ID to check if bot detection is enabled")


class CheckActorRequest(BaseModel):
    actor_key: str = Field(..., description="Unique identifier for the actor")
    workspace_id: Optional[str] = Field(None, description="Workspace ID to check if bot detection is enabled")


class GetActorEventsRequest(BaseModel):
    actor_key: str = Field(..., description="Unique identifier for the actor")


class ClearActorDataRequest(BaseModel):
    actor_key: str = Field(..., description="Unique identifier for the actor")