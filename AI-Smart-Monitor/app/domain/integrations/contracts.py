from datetime import datetime
from pydantic import BaseModel, Field

class IntegrationSnapshot(BaseModel):
    identifier: str = Field(min_length=1, max_length=150)
    status: str = Field(min_length=1, max_length=40)
    correlation_id: str | None = Field(default=None, max_length=64)
    observed_at: datetime | None = None

class IntegrationPage(BaseModel):
    items: list[IntegrationSnapshot] = Field(default_factory=list)
    next_cursor: str | None = None
