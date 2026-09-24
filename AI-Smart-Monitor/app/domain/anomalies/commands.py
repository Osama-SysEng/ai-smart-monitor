from dataclasses import dataclass

@dataclass(frozen=True)
class CreateAnomaly:
    actor: str
    correlation_id: str
    reason: str | None = None

@dataclass(frozen=True)
class UpdateAnomalyStatus:
    identifier: str
    target_status: str
    actor: str
    reason: str | None = None
