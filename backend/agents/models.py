from __future__ import annotations

from pydantic import BaseModel, Field


class DebateTopic(BaseModel):
    topic: str = Field(min_length=1, max_length=2000)
    rounds: int = Field(default=3, ge=1, le=10)


class AgentMessage(BaseModel):
    role: str
    content: str
    round: int


class DebateTranscript(BaseModel):
    topic: str
    messages: list[AgentMessage]
    judgment: dict | None = None
