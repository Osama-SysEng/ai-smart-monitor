-- Apply once through a privileged migration job, then record the revision externally.
ALTER TABLE data_imports ADD COLUMN IF NOT EXISTS tenant_id varchar(64) NOT NULL DEFAULT 'default';
ALTER TABLE source_facts ADD COLUMN IF NOT EXISTS tenant_id varchar(64) NOT NULL DEFAULT 'default';
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS tenant_id varchar(64) NOT NULL DEFAULT 'default';
ALTER TABLE investigation_cases ADD COLUMN IF NOT EXISTS tenant_id varchar(64) NOT NULL DEFAULT 'default';
ALTER TABLE erp_outbox ADD COLUMN IF NOT EXISTS tenant_id varchar(64) NOT NULL DEFAULT 'default';
ALTER TABLE erp_outbox ADD COLUMN IF NOT EXISTS last_status_code integer;
ALTER TABLE erp_outbox ADD COLUMN IF NOT EXISTS locked_until timestamptz;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS tenant_id varchar(64) NOT NULL DEFAULT 'default';

CREATE TABLE IF NOT EXISTS service_accounts (
  id bigserial PRIMARY KEY, client_id varchar(120) UNIQUE NOT NULL, tenant_id varchar(64) NOT NULL,
  display_name varchar(200) NOT NULL, key_fingerprint varchar(64) UNIQUE NOT NULL,
  secret_hash varchar(255) NOT NULL, roles jsonb NOT NULL DEFAULT '[]'::jsonb,
  active boolean NOT NULL DEFAULT true, expires_at timestamptz, last_used_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS access_sessions (
  id bigserial PRIMARY KEY, service_account_id bigint NOT NULL, tenant_id varchar(64) NOT NULL,
  token_hash varchar(64) UNIQUE NOT NULL, expires_at timestamptz NOT NULL, revoked_at timestamptz,
  revoke_reason varchar(100), last_used_at timestamptz, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS delivery_attempts (
  id bigserial PRIMARY KEY, outbox_id bigint NOT NULL, tenant_id varchar(64) NOT NULL,
  attempt_number integer NOT NULL, outcome varchar(30) NOT NULL, status_code integer,
  error_category varchar(80), detail text, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS integration_circuits (
  id bigserial PRIMARY KEY, target varchar(100) NOT NULL, tenant_id varchar(64) NOT NULL,
  consecutive_failures integer NOT NULL DEFAULT 0, opened_until timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now(), UNIQUE(target, tenant_id)
);
CREATE INDEX IF NOT EXISTS ix_outbox_tenant_due ON erp_outbox(tenant_id, status, next_retry_at);
CREATE INDEX IF NOT EXISTS ix_delivery_attempt_tenant_outbox ON delivery_attempts(tenant_id, outbox_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_audit_tenant_timeline ON audit_logs(tenant_id, created_at DESC);
