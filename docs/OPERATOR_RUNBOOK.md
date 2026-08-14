# SHUNYA OS — Operator Runbook (FDA29)

Operational guide for diagnosing and recovering SHUNYA production incidents
without SSH archaeology.

## 1. Endpoints

| Endpoint | Purpose | Auth |
|---|---|---|
| `GET /health` | Full runtime check: DB connectivity, uptime, version, environment | Public |
| `GET /ready` | Readiness probe: can the app serve traffic? | Public |
| `GET /live` | Liveness probe: process alive? | Public |
| `GET /system/health` | Component health: DB latency, event queue backlog, integration token validity, execution loop | Public |
| `GET /api/v1/platform/health` | Integration + webhook health visibility | Public |
| `GET /api/v1/platform/diagnostics` | Route inventory, API version, integration registry | X-Identity-Id |
| `GET /api/v1/platform/webhooks/<id>/deliveries` | Webhook delivery evidence log | Identity owner |
| `GET /api/v1/jobs` | Background job status | Session |

## 2. Answering the 8 operator questions

### WHAT FAILED?
Check `GET /api/v1/platform/health` → `integrations[].error` and `webhooks.failed_recent`.
Check gunicorn logs (JSON structured): filter `"levelname": "ERROR"`.

### WHERE?
Structured logs carry `request_id`, route, and module. Filter by request_id
to trace the full path.

### WHEN?
Every log line and health payload carries an ISO-8601 UTC timestamp.

### FOR WHICH TENANT/REQUEST?
Every response includes `request_id`. Logs include `request_id` and identity
context where available.

### WHAT WAS THE USER ACTION?
Correlate the request_id against the audit log
(`app.security.audit.AuditLog` / `sh_audit_logs` table).

### WAS DATA COMMITTED?
Check the evidence store (`evidence_records`) and webhook delivery log.
Webhook deliveries record `delivered_at`, `http_status`, `error`.

### WAS RETRY ATTEMPTED?
Webhook deliveries carry `attempt`, `max_attempts`, `next_retry_at`.
Failed deliveries retry at 1min / 5min / 15min, then become `exhausted`.

### WHAT SHOULD THE OPERATOR DO NEXT?
Follow the runbook sections below.

## 3. Common incident responses

### Database failure
Symptom: `/health` returns `status: degraded`, `database: error: ...`.
Action: check PostgreSQL status (`systemctl status postgresql`), verify
connection string, check disk space. SHUNYA returns 503 on health checks
while degraded.

### Provider outage (external API)
Symptom: `/system/health` shows `integration_token_valid: false` or
integration `status: error`.
Action: verify provider credentials, wait for provider recovery, or
disable the integration in the integration registry. The provider fabric
isolates failures — other capabilities continue.

### OAuth expiry
Symptom: integration `error` mentions token/expiry.
Action: re-run the OAuth consent flow (`/gmail/oauth/initiate` for Gmail).
Credentials are stored encrypted in the credential store.

### Webhook failure
Symptom: `/api/v1/platform/health` → `webhooks.failed_recent > 0`.
Action: open `/api/v1/platform/webhooks/<id>/deliveries` to inspect
attempts and errors. If the endpoint is permanently failing, disable the
webhook (`PUT /api/v1/platform/webhooks/<id>` with `is_active: false`)
or rotate the secret (`POST .../rotate-secret`).

### Background job failure
Symptom: `/api/v1/jobs` shows failed jobs.
Action: inspect job payload in the jobs table; retry via the jobs API.

## 4. Retry and degraded state

- Webhook delivery: 3 attempts with exponential backoff (1/5/15 min),
  then `exhausted`. Idempotency key prevents duplicate side effects.
- Degraded state: `/health` returns 503 while DB is down. `/live` stays 200
  while the process is alive (orchestrators keep the container running,
  load balancers remove it from rotation).

## 5. Security note

Operator endpoints that expose internal state (`/api/v1/platform/diagnostics`)
require authentication. Public health endpoints expose only aggregate
status — never credentials, tenant data, or internal IPs.
