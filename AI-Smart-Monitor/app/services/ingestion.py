import hashlib
import io
import re

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import append_audit_event
from app.core.config import settings
from app.core.errors import DomainError
from app.models import DataImport, SourceFact
from app.services.column_mapping import suggest_mapping
from app.services.validation import validate_row

SOURCE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{1,98}$", re.IGNORECASE)
SUPPORTED_EXTENSIONS = (".csv", ".xlsx", ".xls")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def record_hash(source: str, transaction_id: str, item_code: str) -> str:
    return sha256(f"{source}|{transaction_id}|{item_code}".encode("utf-8"))


def _read_frame(payload: bytes, filename: str) -> pd.DataFrame:
    if filename.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(payload))
    if filename.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(payload))
    raise DomainError("UNSUPPORTED_FILE", "Only CSV/XLS/XLSX imports are supported", 415)


def _safe_error(errors: list[dict]) -> list[dict]:
    return errors[: settings.max_error_details]


async def ingest(file, source_id: str, db: Session, correlation_id: str | None = None, tenant_id: str = "default", actor: str = "system"):
    normalized_source = source_id.strip().lower()
    if not SOURCE_ID.match(normalized_source):
        raise DomainError("INVALID_SOURCE_ID", "source_id must contain 2-99 letters, digits, hyphens, or underscores")

    filename = (file.filename or "upload").strip()
    if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
        raise DomainError("UNSUPPORTED_FILE", "Only CSV/XLS/XLSX imports are supported", 415)

    payload = await file.read(settings.max_upload_bytes + 1)
    if len(payload) > settings.max_upload_bytes:
        raise DomainError("UPLOAD_TOO_LARGE", "Import exceeds MAX_UPLOAD_BYTES", 413, {"max_bytes": settings.max_upload_bytes})
    if not payload:
        raise DomainError("EMPTY_FILE", "Import file is empty")

    file_hash = sha256(payload)
    existing_import = db.query(DataImport).filter_by(source_id=normalized_source, file_hash=file_hash, tenant_id=tenant_id).first()
    if existing_import:
        return {"status": "DUPLICATE_DETECTED", "import_id": existing_import.id, "facts_created": 0, "errors": []}

    try:
        frame = _read_frame(payload, filename)
    except DomainError:
        raise
    except Exception as exc:
        record = DataImport(source_id=normalized_source, filename=filename, file_hash=file_hash, status="FAILED", errors=[{"code": "PARSER_ERROR", "message": str(exc)[:300]}], correlation_id=correlation_id, tenant_id=tenant_id)
        db.add(record)
        append_audit_event(db, actor=actor, action="IMPORT_REJECTED", entity_type="DataImport", reason="PARSER_ERROR", correlation_id=correlation_id, tenant_id=tenant_id)
        db.commit()
        return {"status": "FAILED", "facts_created": 0, "errors": record.errors}

    if frame.empty:
        raise DomainError("EMPTY_DATASET", "Import contains no data rows")
    if len(frame) > settings.max_import_rows:
        raise DomainError("TOO_MANY_ROWS", "Import exceeds MAX_IMPORT_ROWS", 413, {"max_rows": settings.max_import_rows})

    mapping = suggest_mapping(list(frame.columns))
    reverse = {item["field"]: column for column, item in mapping.items() if item["field"]}
    missing_fields = [field for field in ("transaction_id", "item_code", "quantity") if field not in reverse]
    warnings = [f"Unknown column: {column}" for column, item in mapping.items() if not item["field"]]
    if missing_fields:
        raise DomainError("MAPPING_INCOMPLETE", "Required columns are not mapped", 422, {"missing_fields": missing_fields, "mapping": mapping})

    record = DataImport(source_id=normalized_source, filename=filename, file_hash=file_hash, status="PROCESSING", row_count=len(frame), column_count=len(frame.columns), warnings=warnings, correlation_id=correlation_id, tenant_id=tenant_id)
    db.add(record)
    db.flush()

    errors: list[dict] = []
    facts: list[SourceFact] = []
    seen_hashes: set[str] = set()
    existing_hashes = set(db.scalars(select(SourceFact.record_hash).where(SourceFact.source_id == normalized_source, SourceFact.tenant_id == tenant_id)).all())

    for row_index, raw_row in frame.iterrows():
        raw = {str(key): None if pd.isna(value) else str(value) for key, value in raw_row.to_dict().items()}
        row = {field: (None if pd.isna(raw_row[column]) else raw_row[column]) for field, column in reverse.items()}
        row["transaction_id"] = str(row.get("transaction_id") or "").strip()
        row["item_code"] = str(row.get("item_code") or "").strip()
        row["source_id"] = normalized_source
        row_errors, row_warnings = validate_row(row)
        if row_errors:
            errors.append({"row": int(row_index) + 2, "code": "ROW_INVALID", "errors": row_errors, "warnings": row_warnings})
            continue
        fingerprint = record_hash(normalized_source, row["transaction_id"], row["item_code"])
        if fingerprint in seen_hashes or fingerprint in existing_hashes:
            errors.append({"row": int(row_index) + 2, "code": "DUPLICATE_RECORD", "errors": ["duplicate_record"]})
            continue
        seen_hashes.add(fingerprint)
        facts.append(SourceFact(
            transaction_id=row["transaction_id"], item_code=row["item_code"], source_id=normalized_source,
            quantity=float(row["quantity"]), cost=float(row["cost"]) if row.get("cost") not in (None, "") else None,
            business_date=str(row.get("business_date")) if row.get("business_date") is not None else None,
            branch_code=str(row.get("branch_code")) if row.get("branch_code") is not None else None,
            warehouse_code=str(row.get("warehouse_code")) if row.get("warehouse_code") is not None else None,
            supplier_code=str(row.get("supplier_code")) if row.get("supplier_code") is not None else None,
            raw_payload=raw, record_hash=fingerprint, import_id=record.id, tenant_id=tenant_id,
        ))

    record.accepted_count = len(facts)
    record.rejected_count = len(errors)
    record.errors = _safe_error(errors)
    record.status = "COMPLETED" if not errors else "PARTIALLY_COMPLETED" if facts else "QUARANTINED"
    db.add_all(facts)
    append_audit_event(
        db,
        actor=actor,
        action="IMPORT_PROCESSED",
        entity_type="DataImport",
        entity_id=str(record.id),
        new_value={"source": normalized_source, "accepted": len(facts), "rejected": len(errors), "status": record.status},
        correlation_id=correlation_id, tenant_id=tenant_id,
    )
    db.commit()
    return {"import_id": record.id, "status": record.status, "rows": len(frame), "facts_created": len(facts), "rejected_count": len(errors), "errors": record.errors, "mapping": mapping}
