def _coerce_number(value, default=0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number or number in (float("inf"), float("-inf")):
        return default
    return number


def severity(difference, financial, recurrence=0):
    difference = _coerce_number(difference)
    financial = _coerce_number(financial)
    recurrence = _coerce_number(recurrence)
    score=min(abs(difference)*3,35)+min(financial/100,35)+min(recurrence*5,30)
    if score>=70:return "CRITICAL"
    if score>=45:return "HIGH"
    if score>=20:return "MEDIUM"
    if score>0:return "LOW"
    return "INFO"
