from .contracts import AnomalySnapshot

def display_label(snapshot: AnomalySnapshot) -> str:
    return f"{snapshot.identifier} · {snapshot.status}"

def is_terminal(status: str) -> bool:
    return status.upper() in {"CLOSED", "FAILED", "QUARANTINED", "VERIFIED"}
