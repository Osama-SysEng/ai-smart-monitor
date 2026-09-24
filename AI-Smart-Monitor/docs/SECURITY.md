# Security

- Secrets belong in `.env`/secret manager, never source control.
- AI receives structured evidence only.
- AI cannot write source facts or financial values.
- Financial impact is calculated deterministically.
- Sensitive workflow changes must be audited.
- Production deployment should add RBAC, TLS, rate limiting, secret manager and immutable audit retention.
