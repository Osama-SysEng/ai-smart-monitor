from dataclasses import dataclass

@dataclass(frozen=True)
class CreateCase:
    actor: str
    correlation_id: str
    reason: str | None = None

@dataclass(frozen=True)
class UpdateCaseStatus:
    identifier: str
    target_status: str
    actor: str
    reason: str | None = None
