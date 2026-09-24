"""Privileged service-account and session controls."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import append_audit_event
from app.core.identity import Identity, issue_session, provision_service_account, request_identity, require_capability
from app.db.session import get_db
from app.models import AccessSession

router = APIRouter(prefix="/security", tags=["security"])


class ServiceAccountCreate(BaseModel):
    client_id: str = Field(min_length=3, max_length=120, pattern=r"^[a-zA-Z0-9_-]+$")
    display_name: str = Field(min_length=2, max_length=200)
    tenant_id: str = Field(default="default", min_length=1, max_length=64)
    roles: list[str] = Field(min_length=1, max_length=5)


@router.post("/service-accounts", status_code=status.HTTP_201_CREATED)
def create_service_account(
    payload: ServiceAccountCreate,
    request: Request,
    identity: Identity = Depends(require_capability("security:manage")),
    db: Session = Depends(get_db),
):
    if identity.tenant_id != payload.tenant_id and "admin" not in identity.roles:
        raise HTTPException(status_code=403, detail="Cannot provision another tenant")
    try:
        account, raw_key = provision_service_account(
            db,
            client_id=payload.client_id,
            tenant_id=payload.tenant_id,
            roles=payload.roles,
            display_name=payload.display_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    append_audit_event(
        db,
        actor=identity.actor,
        action="SERVICE_ACCOUNT_PROVISIONED",
        entity_type="ServiceAccount",
        entity_id=str(account.id),
        new_value={"client_id": account.client_id, "roles": account.roles},
        correlation_id=request.headers.get("X-Request-Id"),
        tenant_id=account.tenant_id,
    )
    db.commit()
    return {"id": account.id, "client_id": account.client_id, "tenant_id": account.tenant_id, "roles": account.roles, "api_key": raw_key}


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_session(
    request: Request,
    identity: Identity = Depends(request_identity),
    db: Session = Depends(get_db),
):
    try:
        token = issue_session(db, identity)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    append_audit_event(
        db,
        actor=identity.actor,
        action="SERVICE_SESSION_CREATED",
        entity_type="AccessSession",
        entity_id=str(identity.service_account_id),
        correlation_id=request.headers.get("X-Request-Id"),
        tenant_id=identity.tenant_id,
    )
    db.commit()
    return {"access_token": token, "token_type": "bearer"}


@router.post("/sessions/current/revoke", status_code=status.HTTP_204_NO_CONTENT)
def revoke_current_session(
    request: Request,
    identity: Identity = Depends(request_identity),
    db: Session = Depends(get_db),
):
    if identity.session_id is None:
        raise HTTPException(status_code=409, detail="Current authentication is not a revocable session")
    session = db.get(AccessSession, identity.session_id)
    if session and not session.revoked_at:
        session.revoked_at = datetime.now(timezone.utc)
        session.revoke_reason = "operator_requested"
        append_audit_event(
            db,
            actor=identity.actor,
            action="SERVICE_SESSION_REVOKED",
            entity_type="AccessSession",
            entity_id=str(session.id),
            correlation_id=request.headers.get("X-Request-Id"),
            tenant_id=identity.tenant_id,
        )
        db.commit()
