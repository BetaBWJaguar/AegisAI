from pydantic import BaseModel, Field


class LogMessageRequest(BaseModel):
    actor_key: str = Field(..., description="Unique identifier for the actor (user ID, IP address, etc.)")


class CheckActorRequest(BaseModel):
    actor_key: str = Field(..., description="Unique identifier for the actor")


class GetActorEventsRequest(BaseModel):
    actor_key: str = Field(..., description="Unique identifier for the actor")


class ClearActorDataRequest(BaseModel):
    actor_key: str = Field(..., description="Unique identifier for the actor")