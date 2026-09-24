from dataclasses import dataclass

@dataclass(frozen=True)
class CreateImport:
    actor: str
    correlation_id: str
    reason: str | None = None

@dataclass(frozen=True)
class UpdateImportStatus:
    identifier: str
    target_status: str
    actor: str
    reason: str | None = None
