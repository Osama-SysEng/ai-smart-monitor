from dataclasses import dataclass


@dataclass
class DomainError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict | None = None

    def __str__(self) -> str:
        return self.message
