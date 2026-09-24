# Staging Smoke Test

Create one tenant, issue a short-lived service token, upload a quarantined import, approve one anomaly, and verify that audit evidence includes the actor and correlation ID. Trigger a controlled ERP failure and confirm the outbox moves to retry or operator review without duplicate delivery.
