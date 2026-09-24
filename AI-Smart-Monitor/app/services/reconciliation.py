import hashlib
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.audit import append_audit_event
from app.core.config import settings
from app.models import Alert, Anomaly, ReconciliationResult, ReconciliationRun, SourceFact
from app.services.agents import AgentOrchestrator
from app.services.rules import load_rules
from app.services.severity import severity


def _rule_thresholds() -> dict[str, float]:
    rules = {rule["type"]: rule for rule in load_rules() if rule.get("enabled", True)}
    return {rule_type: float(rule.get("threshold", 0)) for rule_type, rule in rules.items()}


def reconcile(db: Session, correlation_id: str | None = None):
    run = ReconciliationRun(status="PROCESSING", correlation_id=correlation_id)
    db.add(run)
    db.flush()
    grouped: dict[tuple[str, str], dict[str, SourceFact]] = defaultdict(dict)
    fact_count = 0
    for fact in db.query(SourceFact).order_by(SourceFact.id).yield_per(1_000):
        grouped[(fact.transaction_id, fact.item_code)][fact.source_id.lower()] = fact
        fact_count += 1

    thresholds = _rule_thresholds()
    quantity_threshold = thresholds.get("quantity", 0.0)
    results = anomalies = alerts = 0
    orchestrator = AgentOrchestrator()

    for (transaction_id, item_code), sources in grouped.items():
        for source_a, source_b in settings.reconciliation_pair_list:
            expected, actual = sources.get(source_a), sources.get(source_b)
            if not expected or not actual:
                continue
            difference = actual.quantity - expected.quantity
            mismatch = abs(difference) > quantity_threshold
            impact = abs(difference) * (expected.cost or actual.cost or 0)
            calculated_severity = severity(difference, impact)
            db.add(ReconciliationResult(
                run_id=run.id, transaction_id=transaction_id, item_code=item_code, source_a=source_a, source_b=source_b,
                expected_value=expected.quantity, actual_value=actual.quantity, difference=difference,
                status="MISMATCH" if mismatch else "MATCH", severity=calculated_severity,
            ))
            results += 1
            if not mismatch:
                continue

            fingerprint = hashlib.sha256(f"{transaction_id}|{item_code}|{source_a}|{source_b}|quantity".encode()).hexdigest()
            evidence = [f"{source_a}={expected.quantity}", f"{source_b}={actual.quantity}", f"difference={difference}", f"threshold={quantity_threshold}"]
            anomaly = db.query(Anomaly).filter_by(fingerprint=fingerprint).first()
            if anomaly:
                anomaly.severity = calculated_severity
                anomaly.financial_impact = impact
                anomaly.evidence = evidence
                continue

            anomaly = Anomaly(
                type="MULTI_SOURCE_QUANTITY_MISMATCH", severity=calculated_severity, transaction_id=transaction_id,
                item_code=item_code, status="DETECTED", fingerprint=fingerprint, financial_impact=impact,
                facts={"source_a": source_a, "source_b": source_b, "expected": expected.quantity, "actual": actual.quantity, "difference": difference},
                evidence=evidence, confidence=0.99,
            )
            db.add(anomaly)
            db.flush()
            interpretation = orchestrator.run(db, anomaly)
            root_cause = interpretation["root_cause"].get("cause", "Insufficient evidence")
            message = f"Quantity mismatch\n{source_a}: {expected.quantity}\n{source_b}: {actual.quantity}\nDifference: {difference}\nFinancial impact: {impact}\nRoot cause hypothesis: {root_cause}"
            db.add(Alert(anomaly_id=anomaly.id, title=f"{calculated_severity} — {transaction_id} / {item_code}", message=message, severity=calculated_severity, status="PENDING_DISPATCH", channel="dashboard"))
            anomalies += 1
            alerts += 1

    run.status = "COMPLETED"
    run.finished_at = datetime.now(timezone.utc)
    run.summary = {"facts_analyzed": fact_count, "groups": len(grouped), "results": results, "anomalies": anomalies, "alerts": alerts, "quantity_threshold": quantity_threshold, "source_pairs": settings.reconciliation_pair_list}
    append_audit_event(db, actor="system", action="RECONCILIATION_COMPLETED", entity_type="ReconciliationRun", entity_id=str(run.id), new_value=run.summary, correlation_id=correlation_id)
    db.commit()
    return run
