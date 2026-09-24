#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
report_dir="${SECURITY_REPORT_DIR:-$root_dir/reports/security}"
mkdir -p "$report_dir"
declare -A state

run_check() {
  local name="$1"; shift
  if command -v "$1" >/dev/null 2>&1; then
    if "$@"; then state["$name"]="passed"; else state["$name"]="findings_or_failure"; fi
  else
    state["$name"]="tool_missing"
  fi
}

cd "$root_dir"
run_check dependency_audit pip-audit -r requirements.txt -f json -o "$report_dir/pip-audit.json"
run_check python_sast bandit -r app -f json -o "$report_dir/bandit.json"
run_check owasp_sast semgrep --config p/owasp-top-ten --json --output "$report_dir/semgrep.json" app
if command -v gitleaks >/dev/null 2>&1; then
  run_check secret_scan gitleaks detect --source . --report-format json --report-path "$report_dir/gitleaks.json" --no-banner
  secret_evidence="gitleaks.json"
else
  if python tools/secret_heuristic.py --root . --output "$report_dir/secret-heuristic.json"; then state[secret_scan]="passed_heuristic"; else state[secret_scan]="findings_or_failure"; fi
  secret_evidence="secret-heuristic.json (fallback)"
fi

{
  echo "# AI-Smart-Monitor Security Report"
  echo
  echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "| Control | Status | Evidence |"
  echo "|---|---|---|"
  echo "| Dependency audit | ${state[dependency_audit]} | pip-audit.json |"
  echo "| Python SAST | ${state[python_sast]} | bandit.json |"
  echo "| OWASP SAST | ${state[owasp_sast]} | semgrep.json |"
  echo "| Secret scan | ${state[secret_scan]} | ${secret_evidence} |"
  echo
  echo "A missing scanner or fallback secret heuristic is not a production approval. Review raw evidence and remediate dependency findings before a production cutover."
} > "$report_dir/summary.md"
cat "$report_dir/summary.md"
