from dataclasses import dataclass

@dataclass(frozen=True)
class CreateIntegration:
    actor: str
    correlation_id: str
    reason: str | None = None

@dataclass(frozen=True)
class UpdateIntegrationStatus:
    identifier: str
    target_status: str
    actor: str
    reason: str | None = None
