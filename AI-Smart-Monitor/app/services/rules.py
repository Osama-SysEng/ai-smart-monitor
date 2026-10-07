from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2]
_FALLBACK = [{"rule_id": "R-QTY-001", "type": "quantity", "enabled": True, "threshold": 0}]

def load_rules():
    try:
        data = yaml.safe_load((ROOT/"config/rules/reconciliation.yml").read_text(encoding="utf-8")) or {}
    except (OSError, ValueError, yaml.YAMLError):
        return list(_FALLBACK)
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        return list(_FALLBACK)
    return rules
