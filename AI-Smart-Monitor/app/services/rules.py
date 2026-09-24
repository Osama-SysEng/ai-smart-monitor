from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2]
def load_rules():
    return yaml.safe_load((ROOT/"config/rules/reconciliation.yml").read_text())["rules"]
