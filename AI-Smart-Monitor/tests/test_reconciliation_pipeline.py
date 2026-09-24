from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models import Alert, ReconciliationResult, SourceFact
from app.services.reconciliation import reconcile


def test_reconciliation_uses_configured_pairs_and_queues_dashboard_alerts():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, autoflush=False)()
    try:
        db.add_all([
            SourceFact(transaction_id="TX-100", item_code="SKU-100", source_id="warehouse", quantity=10, cost=25, raw_payload={}, record_hash="w" * 64, import_id=1),
            SourceFact(transaction_id="TX-100", item_code="SKU-100", source_id="branch", quantity=14, cost=25, raw_payload={}, record_hash="b" * 64, import_id=2),
        ])
        db.commit()
        run = reconcile(db, correlation_id="req-reconcile-001")
        results = db.query(ReconciliationResult).filter_by(run_id=run.id).all()
        alerts = db.query(Alert).all()
        assert run.status == "COMPLETED"
        assert run.summary["facts_analyzed"] == 2
        assert any(result.status == "MISMATCH" for result in results)
        assert len(alerts) == 1
        assert alerts[0].channel == "dashboard"
        assert alerts[0].status == "PENDING_DISPATCH"
    finally:
        db.close()
        Base.metadata.drop_all(engine)
