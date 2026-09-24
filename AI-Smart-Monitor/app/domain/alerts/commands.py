from dataclasses import dataclass

@dataclass(frozen=True)
class CreateAlert:
    actor: str
    correlation_id: str
    reason: str | None = None

@dataclass(frozen=True)
class UpdateAlertStatus:
    identifier: str
    target_status: str
    actor: str
    reason: str | None = None
