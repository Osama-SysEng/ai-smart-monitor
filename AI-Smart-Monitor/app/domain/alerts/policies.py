SENSITIVE_ACTIONS = {"ERP_WRITE", "SOURCE_MUTATION", "FINANCIAL_ADJUSTMENT"}

def approval_required(action: str, severity: str = "INFO") -> bool:
    return action.upper() in SENSITIVE_ACTIONS or severity.upper() in {"HIGH", "CRITICAL"}

def may_auto_dispatch(channel: str, severity: str) -> bool:
    return channel == "dashboard" and severity.upper() in {"INFO", "LOW"}
