import hashlib
import math
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
    try:
        loaded = load_rules()
    except Exception:
        loaded = []
    rules = {rule["type"]: rule for rule in loaded if isinstance(rule, dict) and rule.get("enabled", True) and rule.get("type")}
    thresholds: dict[str, float] = {}
    for rule_type, rule in rules.items():
        try:
            value = float(rule.get("threshold", 0))
        except (TypeError, ValueError):
            value = 0.0
        if value != value or value in (float("inf"), float("-inf")):
            value = 0.0
        thresholds[rule_type] = value
    return thresholds


def _finite(value, default=0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return number


def reconcile(db: Session, correlation_id: str | None = None, tenant_id: str | None = None):
    run = ReconciliationRun(status="PROCESSING", correlation_id=correlation_id)
    db.add(run)
    db.flush()
    try:
        return _reconcile_inner(db, run, correlation_id=correlation_id, tenant_id=tenant_id)
    except Exception as exc:
        db.rollback()
        run = db.get(ReconciliationRun, run.id)
        if run is None:
            raise
        run.status = "FAILED"
        run.finished_at = datetime.now(timezone.utc)
        run.summary = {"error": str(exc)[:300], "error_type": type(exc).__name__}
        db.commit()
        return run


def _reconcile_inner(db: Session, run: ReconciliationRun, correlation_id: str | None = None, tenant_id: str | None = None):
    grouped: dict[tuple[str, str, str], dict[str, SourceFact]] = defaultdict(dict)
    fact_count = 0
    query = db.query(SourceFact).order_by(SourceFact.id)
    if tenant_id:
        query = query.filter(SourceFact.tenant_id == tenant_id)
    skipped_facts = 0
    for fact in query.yield_per(1_000):
        if fact.quantity is None:
            skipped_facts += 1
            continue
        grouped[(fact.tenant_id, fact.transaction_id, fact.item_code)][fact.source_id.lower()] = fact
        fact_count += 1

    thresholds = _rule_thresholds()
    quantity_threshold = thresholds.get("quantity", 0.0)
    pairs = settings.reconciliation_pair_list
    results = anomalies = alerts = 0
    orchestrator = AgentOrchestrator()
    tenants = {key[0] for key in grouped.keys()}

    for (group_tenant, transaction_id, item_code), sources in grouped.items():
        for source_a, source_b in pairs:
            expected, actual = sources.get(source_a), sources.get(source_b)
            if not expected or not actual:
                continue
            expected_qty = _finite(expected.quantity)
            actual_qty = _finite(actual.quantity)
            difference = actual_qty - expected_qty
            if not math.isfinite(difference):
                continue
            mismatch = abs(difference) > quantity_threshold
            unit_cost = _finite(expected.cost, default=0.0) or _finite(actual.cost, default=0.0)
            impact = abs(difference) * unit_cost
            calculated_severity = severity(difference, impact)
            db.add(ReconciliationResult(
                run_id=run.id, transaction_id=transaction_id, item_code=item_code, source_a=source_a, source_b=source_b,
                expected_value=expected_qty, actual_value=actual_qty, difference=difference,
                status="MISMATCH" if mismatch else "MATCH", severity=calculated_severity,
            ))
            results += 1
            if not mismatch:
                continue

            fingerprint = hashlib.sha256(f"{group_tenant}|{transaction_id}|{item_code}|{source_a}|{source_b}|quantity".encode()).hexdigest()
            legacy_fingerprint = hashlib.sha256(f"{transaction_id}|{item_code}|{source_a}|{source_b}|quantity".encode()).hexdigest()
            evidence = [f"{source_a}={expected_qty}", f"{source_b}={actual_qty}", f"difference={difference}", f"threshold={quantity_threshold}"]
            anomaly = db.query(Anomaly).filter_by(fingerprint=fingerprint).first()
            if anomaly is None:
                anomaly = db.query(Anomaly).filter_by(fingerprint=legacy_fingerprint).first()
                if anomaly is not None:
                    anomaly.fingerprint = fingerprint
                    if not anomaly.tenant_id or anomaly.tenant_id == "default":
                        anomaly.tenant_id = group_tenant
            if anomaly:
                anomaly.severity = calculated_severity
                anomaly.financial_impact = impact
                anomaly.evidence = evidence
                continue

            anomaly = Anomaly(
                type="MULTI_SOURCE_QUANTITY_MISMATCH", severity=calculated_severity, transaction_id=transaction_id,
                item_code=item_code, status="DETECTED", fingerprint=fingerprint, financial_impact=impact,
                facts={"source_a": source_a, "source_b": source_b, "expected": expected_qty, "actual": actual_qty, "difference": difference},
                evidence=evidence, confidence=0.99, tenant_id=group_tenant,
            )
            db.add(anomaly)
            db.flush()
            interpretation = orchestrator.run(db, anomaly)
            root_cause = interpretation["root_cause"].get("cause", "Insufficient evidence")
            message = f"Quantity mismatch\n{source_a}: {expected_qty}\n{source_b}: {actual_qty}\nDifference: {difference}\nFinancial impact: {impact}\nRoot cause hypothesis: {root_cause}"
            db.add(Alert(anomaly_id=anomaly.id, title=f"{calculated_severity} — {transaction_id} / {item_code}", message=message, severity=calculated_severity, status="PENDING_DISPATCH", channel="dashboard"))
            anomalies += 1
            alerts += 1

    run.status = "COMPLETED"
    run.finished_at = datetime.now(timezone.utc)
    run.summary = {"facts_analyzed": fact_count, "groups": len(grouped), "results": results, "anomalies": anomalies, "alerts": alerts, "quantity_threshold": quantity_threshold, "source_pairs": pairs, "tenants": sorted(tenants), "skipped_facts": skipped_facts, "tenant_filter": tenant_id}
    append_audit_event(db, actor="system", action="RECONCILIATION_COMPLETED", entity_type="ReconciliationRun", entity_id=str(run.id), new_value=run.summary, correlation_id=correlation_id)
    db.commit()
    return run
