from datetime import datetime
from pydantic import BaseModel, Field

class AnomalySnapshot(BaseModel):
    identifier: str = Field(min_length=1, max_length=150)
    status: str = Field(min_length=1, max_length=40)
    correlation_id: str | None = Field(default=None, max_length=64)
    observed_at: datetime | None = None

class AnomalyPage(BaseModel):
    items: list[AnomalySnapshot] = Field(default_factory=list)
    next_cursor: str | None = None
