from datetime import date, datetime

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


class ClimateMemoryIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    note: str = Field(..., min_length=1, max_length=1200)
    memory_date: date
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    city: str = Field(default="", max_length=120)
    climate_tag: str = Field(default="", max_length=80)
    feeling: str = Field(default="", max_length=80)
    temp_c: float | None = Field(default=None, ge=-80, le=70)


class ClimateMemoryOut(ClimateMemoryIn):
    id: int
    created_at: datetime


class ClimateStatsOut(BaseModel):
    total_count: int
    avg_temp_c: float | None
    top_tags: list[dict]
    yearly_counts: list[dict]
