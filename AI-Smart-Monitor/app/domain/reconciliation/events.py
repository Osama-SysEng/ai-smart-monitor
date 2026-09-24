from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class ReconciliationEvent:
    event_type: str
    identifier: str
    correlation_id: str
    occurred_at: datetime

    @classmethod
    def now(cls, event_type: str, identifier: str, correlation_id: str):
        return cls(event_type, identifier, correlation_id, datetime.now(timezone.utc))
