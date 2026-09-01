"""Security contracts for service accounts, tenant isolation, and revocable sessions."""
import asyncio

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.core.identity import authenticate_service_key, authenticate_session, issue_session, provision_service_account
from app.models import AccessSession
from app.services.ingestion import ingest
from tests.test_hardening import Upload


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


def test_service_account_key_is_hashed_and_session_is_revocable(db):
    account, raw_key = provision_service_account(
        db,
        client_id="integration-a",
        tenant_id="tenant-a",
        roles=["integration"],
        display_name="Integration A",
    )
    assert raw_key.startswith("sma_")
    assert raw_key not in account.secret_hash
    identity = authenticate_service_key(db, raw_key)
    assert identity is not None
    assert identity.tenant_id == "tenant-a"
    assert identity.allows("erp:write")
    assert not identity.allows("audit:read")

    token = issue_session(db, identity)
    session_identity = authenticate_session(db, token)
    assert session_identity is not None
    session = db.get(AccessSession, session_identity.session_id)
    session.revoked_at = session.created_at
    db.commit()
    assert authenticate_session(db, token) is None


def test_same_import_hash_is_isolated_by_tenant(db):
    content = b"transaction_id,item_code,quantity\nTX-1,SKU-1,5\n"
    tenant_a = asyncio.run(ingest(Upload("source.csv", content), "warehouse", db, tenant_id="tenant-a"))
    tenant_b = asyncio.run(ingest(Upload("source.csv", content), "warehouse", db, tenant_id="tenant-b"))
    assert tenant_a["status"] == "COMPLETED"
    assert tenant_b["status"] == "COMPLETED"
