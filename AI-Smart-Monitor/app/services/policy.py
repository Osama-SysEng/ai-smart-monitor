HIGH_RISK={"CRITICAL","HIGH"}
def action_policy(anomaly, action):
    # Autonomous low-risk operations only. Financial/source mutations always require approval.
    if action in {"ERP_WRITE","SOURCE_MUTATION","FINANCIAL_ADJUSTMENT"}: return "APPROVAL_REQUIRED"
    if anomaly.severity in HIGH_RISK: return "APPROVAL_REQUIRED"
    return "AUTONOMOUS_ALLOWED"
