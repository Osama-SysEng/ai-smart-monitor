DOMAIN_CATALOG = {
    "imports": "Data intake, validation, and quarantine",
    "reconciliation": "Deterministic comparison and evidence",
    "anomalies": "Detection, severity, and prioritisation",
    "cases": "Operator-owned investigation lifecycle",
    "alerts": "Controlled delivery and acknowledgement",
    "integrations": "Outbox delivery and external system boundaries",
}


def supported_domains() -> tuple[str, ...]:
    return tuple(DOMAIN_CATALOG)
