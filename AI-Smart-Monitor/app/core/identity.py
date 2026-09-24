"""Service-account identity, revocable bearer sessions, and capability policy."""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request

from app.core.config import settings
from app.models import AccessSession, ServiceAccount


ROLE_CAPABILITIES = {
    "admin": {"*"},
    "operator": {"imports:read", "imports:write", "reconciliation:run", "cases:read", "cases:write", "erp:read", "anomalies:read", "anomalies:write", "operations:read"},
    "integration": {"imports:write", "erp:write", "erp:read"},
    "auditor": {"audit:read", "cases:read", "anomalies:read", "erp:read", "operations:read"},
    "viewer": {"imports:read", "cases:read", "anomalies:read", "erp:read"},
}


@dataclass(frozen=True)
class Identity:
    actor: str
    tenant_id: str
    roles: tuple[str, ...]
    service_account_id: int | None = None
    session_id: int | None = None

    def allows(self, capability: str) -> bool:
        grants = set().union(*(ROLE_CAPABILITIES.get(role, set()) for role in self.roles))
        return "*" in grants or capability in grants


def _hash_secret(secret: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(secret.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$" + base64.urlsafe_b64encode(salt).decode("ascii") + "$" + base64.urlsafe_b64encode(digest).decode("ascii")


def _verify_secret(secret: str, encoded: str) -> bool:
    try:
        algorithm, salt_text, expected_text = encoded.split("$", 2)
        if algorithm != "scrypt":
            return False
        expected = base64.urlsafe_b64decode(expected_text.encode("ascii"))
        candidate = hashlib.scrypt(secret.encode("utf-8"), salt=base64.urlsafe_b64decode(salt_text.encode("ascii")), n=2**14, r=8, p=1)
        return hmac.compare_digest(candidate, expected)
    except (ValueError, TypeError):
        return False


def provision_service_account(db, *, client_id: str, tenant_id: str, roles: list[str], display_name: str) -> tuple[ServiceAccount, str]:
    if any(role not in ROLE_CAPABILITIES for role in roles):
        raise ValueError("Unknown service-account role")
    if db.query(ServiceAccount).filter_by(client_id=client_id).first():
        raise ValueError("client_id already exists")
    raw_key = "sma_" + secrets.token_urlsafe(32)
    account = ServiceAccount(
        client_id=client_id,
        tenant_id=tenant_id,
        display_name=display_name,
        secret_hash=_hash_secret(raw_key),
        key_fingerprint=hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:20],
        roles=sorted(set(roles)),
        active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account, raw_key


def authenticate_service_key(db, raw_key: str) -> Identity | None:
    fingerprint = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:20]
    account = db.query(ServiceAccount).filter_by(key_fingerprint=fingerprint, active=True).first()
    if not account or not _verify_secret(raw_key, account.secret_hash):
        return None
    if account.expires_at and account.expires_at <= datetime.now(timezone.utc):
        return None
    account.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return Identity(actor=f"service:{account.client_id}", tenant_id=account.tenant_id, roles=tuple(account.roles or []), service_account_id=account.id)


def issue_session(db, identity: Identity) -> str:
    if identity.service_account_id is None:
        raise ValueError("Only service accounts can create revocable sessions")
    raw = secrets.token_urlsafe(36)
    session = AccessSession(
        service_account_id=identity.service_account_id,
        token_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        tenant_id=identity.tenant_id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.session_ttl_minutes),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return f"sms_{session.id}_{raw}"


def authenticate_session(db, token: str) -> Identity | None:
    try:
        prefix, session_id_text, raw = token.split("_", 2)
        if prefix != "sms":
            return None
        session_id = int(session_id_text)
    except (ValueError, AttributeError):
        return None
    session = db.get(AccessSession, session_id)
    expires_at = session.expires_at.replace(tzinfo=timezone.utc) if session and session.expires_at.tzinfo is None else (session.expires_at if session else None)
    if not session or session.revoked_at or (expires_at and expires_at <= datetime.now(timezone.utc)):
        return None
    if not hmac.compare_digest(session.token_hash, hashlib.sha256(raw.encode("utf-8")).hexdigest()):
        return None
    account = db.get(ServiceAccount, session.service_account_id)
    if not account or not account.active:
        return None
    session.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return Identity(actor=f"service:{account.client_id}", tenant_id=session.tenant_id, roles=tuple(account.roles or []), service_account_id=account.id, session_id=session.id)


def resolve_identity(request: Request, db) -> Identity:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        identity = authenticate_session(db, authorization[7:].strip())
        if identity:
            return identity
    api_key = request.headers.get("x-api-key")
    if settings.auth_mode == "service_accounts" and api_key:
        identity = authenticate_service_key(db, api_key)
        if identity:
            return identity
    if settings.auth_mode == "legacy_api_key" and api_key and hmac.compare_digest(api_key, settings.api_key):
        return Identity(actor="legacy_api-key", tenant_id="default", roles=("admin",))
    if settings.environment in {"development", "test"} and not settings.require_api_key:
        return Identity(actor="dev", tenant_id="default", roles=("admin",))
    raise HTTPException(status_code=401, detail="Valid service identity required")


def request_identity(request: Request) -> Identity:
    identity = getattr(request.state, "identity", None)
    if not identity:
        raise HTTPException(status_code=401, detail="Authenticated identity required")
    return identity


def require_capability(capability: str):
    def dependency(request: Request) -> Identity:
        identity = request_identity(request)
        if not identity.allows(capability):
            raise HTTPException(status_code=403, detail=f"Capability required: {capability}")
        return identity
    return dependency
