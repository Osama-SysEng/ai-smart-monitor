# AI-Smart-Monitor Security Report

Generated: 2026-08-23T10:22:34Z

| Control | Status | Evidence |
|---|---|---|
| Dependency audit | findings_or_failure | pip-audit.json |
| Python SAST | passed | bandit.json |
| OWASP SAST | passed | semgrep.json |
| Secret scan | passed_heuristic | secret-heuristic.json (fallback) |

A missing scanner or fallback secret heuristic is not a production approval. Review raw evidence and remediate dependency findings before a production cutover.
