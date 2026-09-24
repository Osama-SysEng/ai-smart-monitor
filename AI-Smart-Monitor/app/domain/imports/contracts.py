from datetime import datetime
from pydantic import BaseModel, Field

class ImportSnapshot(BaseModel):
    identifier: str = Field(min_length=1, max_length=150)
    status: str = Field(min_length=1, max_length=40)
    correlation_id: str | None = Field(default=None, max_length=64)
    observed_at: datetime | None = None

class ImportPage(BaseModel):
    items: list[ImportSnapshot] = Field(default_factory=list)
    next_cursor: str | None = None
