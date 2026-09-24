import asyncio
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.errors import DomainError
from app.db.session import Base
from app.models import Anomaly, DataImport
from app.services.ingestion import ingest
from app.services.workflow import create_case, queue_erp, transition


class Upload:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content

    async def read(self, _limit=None):
        return self._content


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def test_import_quarantines_invalid_rows_and_deduplicates_across_imports(db):
    content = b"transaction_id,item_code,quantity,cost\nTX-1,SKU-1,5,10\nTX 2,SKU-2,3,12\n"
    first = asyncio.run(ingest(Upload("source.csv", content), "warehouse", db, "req-import"))
    assert first["status"] == "PARTIALLY_COMPLETED"
    assert first["facts_created"] == 1
    assert first["rejected_count"] == 1
    record = db.get(DataImport, first["import_id"])
    assert record.accepted_count == 1
    assert record.rejected_count == 1

    duplicate = asyncio.run(ingest(Upload("source.csv", content), "warehouse", db))
    assert duplicate["status"] == "DUPLICATE_DETECTED"


def test_case_and_erp_controls_are_idempotent_and_auditable(db):
    anomaly = Anomaly(type="MISMATCH", severity="CRITICAL", transaction_id="TX-1", item_code="SKU-1", fingerprint="a" * 64)
    db.add(anomaly)
    db.commit()

    case, created = create_case(db, anomaly, assigned_to="operator@example.test", correlation_id="req-case")
    duplicate_case, duplicate_created = create_case(db, anomaly)
    assert created is True
    assert duplicate_created is False
    assert case.id == duplicate_case.id
    assert case.case_key == f"CASE-{anomaly.id}"

    with pytest.raises(DomainError) as missing_approval:
        queue_erp(db, "ERP_WRITE", {"severity": "CRITICAL", "entity": anomaly.id})
    assert missing_approval.value.code == "APPROVAL_REQUIRED"

    event, created_event = queue_erp(db, "ERP_WRITE", {"severity": "CRITICAL", "entity": anomaly.id}, approval_reference="APR-001")
    duplicate_event, duplicate_created = queue_erp(db, "ERP_WRITE", {"severity": "CRITICAL", "entity": anomaly.id}, approval_reference="APR-001")
    assert created_event is True
    assert duplicate_created is False
    assert event.id == duplicate_event.id


def test_terminal_transition_requires_reason(db):
    anomaly = Anomaly(type="MISMATCH", severity="HIGH", transaction_id="TX-2", item_code="SKU-2", fingerprint="b" * 64, status="ACKNOWLEDGED")
    db.add(anomaly)
    db.commit()
    with pytest.raises(DomainError) as missing_reason:
        transition(db, anomaly, "RESOLVED")
    assert missing_reason.value.code == "RESOLUTION_REASON_REQUIRED"
    assert transition(db, anomaly, "RESOLVED", reason="Verified supplier correction").status == "RESOLVED"
