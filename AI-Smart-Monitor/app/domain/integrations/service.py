from .contracts import IntegrationSnapshot

def display_label(snapshot: IntegrationSnapshot) -> str:
    return f"{snapshot.identifier} · {snapshot.status}"

def is_terminal(status: str) -> bool:
    return status.upper() in {"CLOSED", "FAILED", "QUARANTINED", "VERIFIED"}
