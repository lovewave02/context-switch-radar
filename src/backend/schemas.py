from datetime import datetime

from pydantic import BaseModel, Field


class EventIn(BaseModel):
    source: str = Field(..., examples=["vscode", "chrome"])
    title: str = Field(..., examples=["Fix login bug"])
    task_key: str | None = Field(default=None, examples=["bugfix-login"])
    occurred_at: datetime


class EventOut(BaseModel):
    id: int
    source: str
    title: str
    task_key: str
    occurred_at: datetime


class FragmentationOut(BaseModel):
    event_count: int
    switch_count: int
    rapid_switch_count: int
    fragmentation_score: float
