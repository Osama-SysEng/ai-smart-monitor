from .contracts import ReconciliationSnapshot

def display_label(snapshot: ReconciliationSnapshot) -> str:
    return f"{snapshot.identifier} · {snapshot.status}"

def is_terminal(status: str) -> bool:
    return status.upper() in {"CLOSED", "FAILED", "QUARANTINED", "VERIFIED"}
