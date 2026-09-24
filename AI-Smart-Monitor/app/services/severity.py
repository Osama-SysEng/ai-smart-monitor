def severity(difference, financial, recurrence=0):
    score=min(abs(difference)*3,35)+min(financial/100,35)+min(recurrence*5,30)
    if score>=70:return "CRITICAL"
    if score>=45:return "HIGH"
    if score>=20:return "MEDIUM"
    if score>0:return "LOW"
    return "INFO"
