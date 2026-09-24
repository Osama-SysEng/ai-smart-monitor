import math
import re

MANDATORY = ("transaction_id", "item_code", "quantity")
IDENTIFIER = re.compile(r"^[A-Za-z0-9._:/-]{1,150}$")


def _missing(value) -> bool:
    return value is None or str(value).strip().lower() in {"", "nan", "none", "null"}


def _finite_number(value) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("not finite")
    return number


def validate_row(row: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for field in MANDATORY:
        if _missing(row.get(field)):
            errors.append(f"{field}_missing")
    for field in ("transaction_id", "item_code"):
        value = str(row.get(field) or "").strip()
        if value and not IDENTIFIER.match(value):
            errors.append(f"{field}_invalid")
    if not _missing(row.get("quantity")):
        try:
            if _finite_number(row["quantity"]) < 0:
                warnings.append("negative_quantity")
        except (TypeError, ValueError):
            errors.append("quantity_invalid")
    if not _missing(row.get("cost")):
        try:
            if _finite_number(row["cost"]) < 0:
                warnings.append("negative_cost")
        except (TypeError, ValueError):
            errors.append("cost_invalid")
    return errors, warnings
