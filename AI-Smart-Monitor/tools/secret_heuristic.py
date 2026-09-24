"""Minimal local secret heuristic used only when Gitleaks is unavailable."""
import argparse
import json
import re
from pathlib import Path

PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "quoted_secret_assignment": re.compile(r"(?:secret|password|token|api[_-]?key)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]", re.I),
}
IGNORED = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", "reports"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    findings = []
    for file in root.rglob("*"):
        if not file.is_file() or any(part in IGNORED for part in file.parts) or file.name.startswith(".env") or file.stat().st_size > 1_000_000:
            continue
        try:
            lines = file.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, start=1):
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append({"rule": name, "file": str(file.relative_to(root)), "line": number})
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"scanner": "local_secret_heuristic", "findings": findings}, indent=2), encoding="utf-8")
    print(json.dumps({"findings": len(findings)}))
    raise SystemExit(1 if findings else 0)


if __name__ == "__main__":
    main()
