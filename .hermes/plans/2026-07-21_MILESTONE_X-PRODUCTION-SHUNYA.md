# MILESTONE X — Production SHUNYA

> **Goal:** Transform SHUNYA from a completed architecture into a production-grade Business Operating System.
>
> **Scope:** 12 deliverables across Identity, Auth, Authorization, Operations, Events, Observability, Security, Performance, Reliability, Deployment, QA, and final Readiness Report.
>
> **Constraint:** No new intelligence engines. No architectural expansion. No redesign of Human OS. Every change increases: reliability, security, scalability, observability, performance, operational resilience.
>
> **Tech Stack:** Python 3.12 · Flask · PostgreSQL 16 · SQLAlchemy 2.0 · Celery · Redis · Prometheus · Alembic

---

## Dependency Order

```
 D1 Identity/Orgs ───┐
 D2 Auth ─────────────┤
 D7 Security ─────────┤
                      ├──→ D3 Authorization ──┐
 D4 Operational Svcs ─┤                       │
 D5 Event Delivery ───┤                       │
 D6 Observability ────┤                       │
                      │                       ├──→ D8 Performance ──→ D9 Reliability ──→ D10 Deployment ──→ D11 QA ──→ D12 Report
                      └───────────────────────┘
```

---

## DELIVERABLE 1 — Identity & Organizations

**Existing state audit:**
- Identity Engine (`app/shunya/identity/`) — models, resolver, lifecycle, normalizer. Complete in-memory implementation.
- Organizational Intelligence (`app/organizational/`) — full models (OrgUnit, OrgRole, RoleAssignment, Responsibility, Ownership, Delegation, etc.) + engine (OrgModelStore, ResponsibilityGraph, OwnershipIntelligence, DelegationEngine, etc.). In-memory.
- Tenant model (`app/tenant.py`) — SQLAlchemy-backed with branding engine.
- TeamMember model (`app/auth.py`) — SQLAlchemy-backed with role-based access.
- `app/auth_routes.py` — basic login/logout + team CRUD routes.

**Gap:** No Organization CRUD API, no Workspace model, no Invitation system, no onboarding flow, no org switching.

### Task 1.1: Organization CRUD API

**Objective:** RESTful API for organizations (create, read, update, delete, list) with tenant scoping.

**Files:**
- Create: `app/production/identity/org_routes.py`
- Create: `app/production/identity/__init__.py`
- Create: `app/production/__init__.py`
- Create: `tests/production/identity/test_org_routes.py`

**Implementation:**
- Blueprint `org_bp` at `/api/v1/orgs`
- Endpoints: `GET /api/v1/orgs` (list), `POST /api/v1/orgs` (create), `GET /api/v1/orgs/<id>` (read), `PUT /api/v1/orgs/<id>` (update), `DELETE /api/v1/orgs/<id>` (delete)
- Validation: organization name required, slug auto-generated, tenant isolation enforced
- Responses: JSON with standard envelope `{success, data, error}`

### Task 1.2: Workspace CRUD API

**Objective:** Workspace model and API within organizations.

**Files:**
- Create: `app/production/identity/workspace_routes.py`
- Create: `tests/production/identity/test_workspace_routes.py`
- Modify: `app/models.py` — add Workspace model

**Implementation:**
- SQLAlchemy `Workspace` model: id, org_id (FK), name, slug, description, settings (JSON), is_active, created_at, updated_at
- Blueprint at `/api/v1/orgs/<org_id>/workspaces`
- Endpoints: list, create, read, update, delete
- Integration with Tenant isolation

### Task 1.3: User Management API

**Objective:** User CRUD, team management within organizations.

**Files:**
- Create: `app/production/identity/user_routes.py`
- Create: `tests/production/identity/test_user_routes.py`
- Modify: `app/auth.py` — add org_id to TeamMember

**Implementation:**
- Add `organization_id`, `workspace_id` FK columns to `TeamMember`
- Blueprint at `/api/v1/orgs/<org_id>/users`
- Endpoints: list, create, read, update, deactivate
- Role scoping for management

### Task 1.4: Invitation System

**Objective:** Email-based invitation workflow for adding users to organizations.

**Files:**
- Create: `app/production/identity/invitation_routes.py`
- Create: `app/production/identity/invitation_service.py`
- Create: `tests/production/identity/test_invitation.py`
- Modify: `app/models.py` — add Invitation model

**Implementation:**
- `Invitation` model: id, org_id, email, role, token, expires_at, accepted_at, created_at, invited_by
- Endpoint: `POST /api/v1/orgs/<id>/invitations` (create), `GET /api/v1/invitations/<token>` (verify), `POST /api/v1/invitations/<token>/accept` (accept)
- Token generation with expiry (48h default)

### Task 1.5: Organization Switching

**Objective:** API and middleware for switching between organizations.

**Files:**
- Create: `app/production/identity/switch_routes.py`
- Create: `tests/production/identity/test_switch.py`
- Modify: `app/auth_routes.py` — add current_org_id to session

**Implementation:**
- Endpoint: `POST /api/v1/orgs/<id>/switch`
- Middleware: `g.current_org` set from session
- Auto-filter queries by current org

### Task 1.6: User Onboarding Flow

**Objective:** Guided onboarding workflow for new users.

**Files:**
- Create: `app/production/identity/onboarding_routes.py`
- Create: `app/production/identity/onboarding_service.py`
- Create: `tests/production/identity/test_onboarding.py`

**Implementation:**
- Onboarding state machine: `pending` → `profile` → `org_setup` → `invite_team` → `complete`
- Endpoints: `GET /api/v1/onboarding/status`, `PUT /api/v1/onboarding/step/<step>`
- Track progress per user

### Task 1.7: Organization Lifecycle

**Objective:** Activation, deactivation, archival, deletion of organizations.

**Files:**
- Create: `app/production/identity/lifecycle_routes.py`
- Create: `tests/production/identity/test_lifecycle.py`

**Implementation:**
- Endpoints: `POST /api/v1/orgs/<id>/activate`, `POST /api/v1/orgs/<id>/deactivate`, `POST /api/v1/orgs/<id>/archive`
- Soft-delete patterns — no hard deletes on production data
- Audit logging on lifecycle transitions

---

## DELIVERABLE 2 — Authentication

**Existing state audit:**
- `app/auth.py` — TeamMember model with SHA256 password hashing, basic AuthLayer for token verification and permission checking.
- `app/auth_routes.py` — login/logout, session management, team CRUD, login_required/admin_required/permission_required decorators.
- Password hashing uses SHA256 (weak — should be bcrypt/argon2).

**Gap:** No password reset, no email verification, no MFA, no device management, no session revocation. Password hashing needs upgrade.

### Task 2.1: Upgrade Password Hashing

**Objective:** Replace SHA256-based hashing with bcrypt.

**Files:**
- Modify: `app/auth.py` — replace set_password/check_password with bcrypt
- Create: `tests/production/auth/test_password_hashing.py`
- Add: `bcrypt` to `requirements.txt`

**Implementation:**
- `set_password(password)`: `return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()`
- `check_password(password)`: `return bcrypt.checkpw(password.encode(), self.password_hash.encode())`
- Migration script for existing hashes (detect SHA256 format, rehash on next login)

### Task 2.2: Password Reset Flow

**Objective:** Email-based password reset with secure tokens.

**Files:**
- Create: `app/production/auth/password_reset_routes.py`
- Create: `app/production/auth/password_reset_service.py`
- Create: `tests/production/auth/test_password_reset.py`
- Modify: `app/models.py` — add PasswordResetToken model
- Modify: `app/auth_routes.py` — add reset endpoints

**Implementation:**
- `PasswordResetToken` model: id, user_id, token, expires_at, used_at, created_at
- Endpoint: `POST /api/v1/auth/forgot-password` (sends email)
- Endpoint: `GET /api/v1/auth/reset-password/<token>` (verify token)
- Endpoint: `POST /api/v1/auth/reset-password/<token>` (set new password)
- Token expiry: 1 hour

### Task 2.3: Email Verification

**Objective:** Verify user email addresses on registration.

**Files:**
- Create: `app/production/auth/email_verification_routes.py`
- Create: `tests/production/auth/test_email_verification.py`
- Modify: `app/auth.py` — add email_verified_at to TeamMember
- Modify: `app/models.py` — add EmailVerificationToken model

**Implementation:**
- `EmailVerificationToken`: id, user_id, email, token, expires_at, verified_at, created_at
- Endpoint: `POST /api/v1/auth/request-verification` (sends email)
- Endpoint: `GET /api/v1/auth/verify-email/<token>` (verify)
- Mark `email_verified_at` on success
- Require verified email for sensitive operations

### Task 2.4: MFA Hooks

**Objective:** Pluggable MFA infrastructure with TOTP support.

**Files:**
- Create: `app/production/auth/mfa_routes.py`
- Create: `app/production/auth/mfa_service.py`
- Create: `tests/production/auth/test_mfa.py`

**Implementation:**
- TOTP implementation using `pyotp`
- Endpoint: `POST /api/v1/auth/mfa/setup` (generate secret + QR URI)
- Endpoint: `POST /api/v1/auth/mfa/verify` (validate TOTP code)
- Endpoint: `POST /api/v1/auth/mfa/disable` (remove MFA)
- MFA challenge on login when enabled
- Support for recovery codes (10 one-time codes)

### Task 2.5: Device Management

**Objective:** Track and manage authenticated devices/sessions.

**Files:**
- Create: `app/production/auth/device_routes.py`
- Create: `app/production/auth/device_service.py`
- Create: `tests/production/auth/test_device_management.py`

**Implementation:**
- Device tracking: user_agent, ip_address, last_seen, device_name, trusted flag
- Endpoint: `GET /api/v1/auth/devices` (list)
- Endpoint: `DELETE /api/v1/auth/devices/<id>` (revoke)
- Auto-untrack stale devices (>90 days)

### Task 2.6: Session Revocation

**Objective:** Force-logout all sessions for a user.

**Files:**
- Create: `app/production/auth/session_routes.py`
- Create: `tests/production/auth/test_session_revocation.py`
- Modify: `app/auth.py` — add session_version to TeamMember

**Implementation:**
- `session_version` counter on TeamMember — incremented on revocation
- Store `session_version` in Flask session
- Middleware checks `session_version` matches — mismatch = force logout
- Endpoint: `POST /api/v1/auth/revoke-sessions`

---

## DELIVERABLE 3 — Authorization (Governance Enforcement)

**Existing state audit:**
- `app/auth.py` — AuthLayer with basic role checks (admin/manager/agent)
- `app/shunya/governance/` — legacy governance (empty `__init__.py`)
- `app/shunya/governance_engine/` — canonical Governance Engine with 6-stage pipeline (validation → enrichment → constitutional → policy → risk → verdict)

**Gap:** No integration between Governance Engine and API routing. No per-object permissions. No org-boundary enforcement at the API level.

### Task 3.1: API Authorization Middleware

**Objective:** Enforce Governance Engine across all `/api/v1/` routes.

**Files:**
- Create: `app/production/auth/authorization_middleware.py`
- Create: `tests/production/auth/test_authorization_middleware.py`

**Implementation:**
- `@require_permission(resource, action)` decorator
- Calls GovernanceEngine for each request
- Caches policy decisions per session (60s TTL)
- Returns 403 with structured error on denial

### Task 3.2: Role-Permission Mapping

**Objective:** Define and enforce role → permission mappings.

**Files:**
- Create: `app/production/auth/permissions.py`
- Create: `tests/production/auth/test_permissions.py`

**Implementation:**
- Permission registry: `{role: {resource: [actions]}}`
- Default roles: owner, admin, manager, editor, viewer, guest
- Permission check: user has role → resource has action → allowed
- Granularity: create, read, update, delete, approve, admin

### Task 3.3: Object Permissions

**Objective:** Per-object ACL support (who can access what).

**Files:**
- Create: `app/production/auth/object_permissions.py`
- Create: `tests/production/auth/test_object_permissions.py`

**Implementation:**
- `ObjectACL` model: object_type, object_id, user_id, role, permissions (JSON)
- Endpoints for managing ACLs: `GET/POST/PUT/DELETE /api/v1/acls/<object_type>/<object_id>`
- Middleware checks ACLs before granting access
- Inherited permissions from org/workspace level

### Task 3.4: Organization Boundary Enforcement

**Objective:** Ensure no cross-org data access.

**Files:**
- Create: `app/production/auth/org_boundary.py`
- Create: `tests/production/auth/test_org_boundary.py`

**Implementation:**
- All queries auto-filtered by `g.current_org_id`
- Data integrity check: returned data's org_id must match current
- Admin override capability with audit logging

### Task 3.5: Governance Route Integration

**Objective:** Wire Governance Engine into API routing pipeline.

**Files:**
- Modify: `app/__init__.py` — register governance middleware
- Create: `tests/production/auth/test_governance_integration.py`

**Implementation:**
- `@before_request` hook that pre-checks governance policies
- Cached policy evaluation per endpoint per session
- Governance violations returned as structured 403 responses

---

## DELIVERABLE 4 — Operational Services

**Existing state audit:**
- Celery worker exists (`celery_worker.py`, `app/cache.py`)
- Event Bus (`app/shunya/infrastructure/event_bus.py`) — publish/subscribe, retry, dead-letter queue, health reporting
- NotificationManager (`app/notifications.py`) — in-app notifications
- `app/models.py` has Notification model

**Gap:** No background worker abstraction for non-Celery environments. No job queue management UI. No scheduled task system. No comprehensive notification delivery pipeline.

### Task 4.1: Background Worker Abstraction

**Objective:** Abstract worker interface supporting Celery and simple thread pool.

**Files:**
- Create: `app/production/ops/worker.py`
- Create: `app/production/ops/__init__.py`
- Create: `tests/production/ops/test_worker.py`

**Implementation:**
- `WorkerInterface` with `enqueue(task, args, kwargs)`, `get_result(task_id)` 
- CeleryWorker implementation (wraps existing Celery)
- ThreadPoolWorker implementation (simple ThreadPoolExecutor for dev/test)
- Environment-based selection via config

### Task 4.2: Job Queue Management

**Objective:** Job queue with status tracking, retry, and management.

**Files:**
- Create: `app/production/ops/job_queue.py`
- Create: `tests/production/ops/test_job_queue.py`

**Implementation:**
- `Job` model: id, type, status (pending/running/failed/completed), payload, retry_count, max_retries, error, created_at, started_at, completed_at
- `JobQueueService`: enqueue, dequeue, acknowledge, fail, retry
- Configurable retry: 3 attempts with exponential backoff (1s, 4s, 9s)

### Task 4.3: Scheduled Tasks

**Objective:** Cron-like scheduled task system.

**Files:**
- Create: `app/production/ops/scheduler.py`
- Create: `tests/production/ops/test_scheduler.py`

**Implementation:**
- `ScheduledTask` model: id, name, task_type, schedule (cron expression), payload, enabled, last_run, next_run
- Scheduler service: loads tasks, checks schedule, enqueues via JobQueue
- Health check: report missed runs

### Task 4.4: Notification Delivery Pipeline

**Objective:** Multi-channel notification delivery (in-app, email, webhook).

**Files:**
- Create: `app/production/ops/notification_delivery.py`
- Create: `tests/production/ops/test_notification_delivery.py`
- Modify: `app/notifications.py` — integrate with delivery pipeline

**Implementation:**
- `NotificationDeliveryService`: takes `Notification` + channel list, dispatches
- Channels: in_app (existing), email (SMTP), webhook (HTTP POST)
- Batched delivery, retry on failure, dead-letter after max retries

### Task 4.5: Dead-Letter Handling

**Objective:** Dead-letter queue with inspection and reprocess capability.

**Files:**
- Create: `app/production/ops/dead_letter.py`
- Create: `tests/production/ops/test_dead_letter.py`

**Implementation:**
- `DeadLetterEntry` model: original_job_id, type, payload, error, failed_at, retry_count
- Service: `reprocess(id)`, `list(limit, offset)`, `purge(older_than_days)`
- Integration with Event Bus existing dead-letter functionality

---

## DELIVERABLE 5 — Event Delivery (Live Runtime)

**Existing state audit:**
- Event Bus (`app/shunya/infrastructure/event_bus.py`) — in-process pub/sub with retry, DLQ, idempotency
- Collaboration Runtime (`app/collaboration/`) — PresenceRuntime, SessionManager, LiveCollaboration (in-memory)
- Workspace Runtime (`app/workspace_runtime.py`) — ObjectRegistry, object handlers, StreamingRuntime

**Gap:** No WebSocket/SSE transport for live events. No graceful reconnection. No structured event delivery for workspace/collaboration/executive/decision events.

### Task 5.1: SSE Endpoint Infrastructure

**Objective:** Server-Sent Events endpoint for live runtime delivery.

**Files:**
- Create: `app/production/events/sse_routes.py`
- Create: `app/production/events/__init__.py`
- Create: `app/production/events/event_delivery.py`
- Create: `tests/production/events/test_sse.py`

**Implementation:**
- SSE endpoint at `GET /api/v1/events/stream`
- Authenticated connection, auto-connects to relevant event channels
- Event types: workspace_updates, collaboration_events, executive_intel, decision_changes, execution_updates, presence, attention_changes
- JSON-formatted SSE events with `event`, `data`, `id`, `retry` fields

### Task 5.2: Event Type Registration & Routing

**Objective:** Register event types and route from Event Bus to SSE.

**Files:**
- Create: `app/production/events/event_registry.py`
- Create: `tests/production/events/test_event_registry.py`

**Implementation:**
- Central registry: `{event_type: [subscriber_channels]}`
- Wildcard subscription: `workspace:*` matches all workspace events
- Per-user channel filtering: user only gets events they're authorized for

### Task 5.3: Graceful Reconnection

**Objective:** Support `Last-Event-ID` for reconnection.

**Files:**
- Create: `app/production/events/reconnect.py`
- Create: `tests/production/events/test_reconnect.py`

**Implementation:**
- Track last 1000 events per user in ring buffer
- On reconnect with `Last-Event-ID`, replay missed events
- Idempotent event IDs (UUID-based)

### Task 5.4: Event Integration with Existing Runtimes

**Objective:** Wire CollaborationRuntime, WorkspaceRuntime, etc. to emit events.

**Files:**
- Modify: `app/collaboration/engine.py` — publish events on state changes
- Modify: `app/workspace_runtime.py` — publish events on object changes
- Create: `tests/production/events/test_integration.py`

**Implementation:**
- Each engine publishes `CanonicalEvent` through Event Bus when state changes
- SSE subscriber picks up events and delivers to connected clients

---

## DELIVERABLE 6 — Observability

**Existing state audit:**
- Structured logging (`app/shunya/infrastructure/logging.py`) — JSON logger, PII redaction, correlation_id
- Metrics framework (`app/shunya/infrastructure/metrics.py`) — Counter, Gauge, Histogram, Prometheus exposition
- Health framework (`app/shunya/infrastructure/health.py`) — HealthRegistry, HealthCheckFn
- `app/monitoring.py` — Sentry integration
- prometheus-flask-exporter in requirements
- `app/__init__.py` — request_id middleware, JSON logging setup, error handlers with structured responses

**Gap:** Prometheus endpoint not wired. No comprehensive tracing. No health endpoint aggregation. No operational dashboards.

### Task 6.1: Prometheus Metrics Endpoint

**Objective:** Wire `/metrics` endpoint for Prometheus scraping.

**Files:**
- Create: `app/production/observability/metrics_routes.py`
- Create: `app/production/observability/__init__.py`
- Create: `tests/production/observability/test_metrics.py`
- Modify: `app/__init__.py` — register metrics routes
- Modify: `config.yaml` — ensure metrics section is active

**Implementation:**
- `GET /metrics` endpoint returning Prometheus exposition format
- Built-in metrics: request count, latency (histogram), error count, active connections
- Integration with `prometheus-flask-exporter` for Flask request metrics
- Engine-level metrics published via MetricsRegistry

### Task 6.2: Health Endpoint Aggregation

**Objective:** Comprehensive `/health` endpoint with per-component status.

**Files:**
- Create: `app/production/observability/health_routes.py`
- Create: `tests/production/observability/test_health.py`
- Modify: `app/__init__.py` — register health routes

**Implementation:**
- `GET /health` returns aggregated status: `{status, components: [{name, status, detail, duration_ms}]}`
- Registered checkers: database, redis, event bus, governance, identity, collaboration, runtime
- HTTP status codes: 200 (all healthy), 200 (degraded), 503 (unhealthy)
- `GET /health/<component>` for per-component detail

### Task 6.3: Distributed Tracing

**Objective:** Correlation ID propagation and tracing infrastructure.

**Files:**
- Create: `app/production/observability/tracing.py`
- Create: `tests/production/observability/test_tracing.py`

**Implementation:**
- Trace ID generation on first request in chain
- Correlation ID propagation via `X-Correlation-Id` header (incoming), response header (outgoing)
- Span tracking: `trace_id`, `span_id`, `parent_span_id`, `start`, `end`, `operation`, `metadata`
- Export to console log with structured JSON format

### Task 6.4: Error Reporting Pipeline

**Objective:** Centralized error reporting with aggregation and alerting.

**Files:**
- Create: `app/production/observability/error_reporting.py`
- Create: `tests/production/observability/test_error_reporting.py`

**Implementation:**
- Capture all unhandled exceptions via `@app.errorhandler`
- Structured error envelope: `{error_id, timestamp, type, message, stack_trace, request_id, route, user_id}`
- Store in error log table (rotated, last 10000 entries)
- Integration with Sentry (existing `monitoring.py`)

### Task 6.5: Operational Dashboard Configuration

**Objective:** Pre-configured Prometheus + Grafana dashboard definitions.

**Files:**
- Create: `monitoring/prometheus.yml`
- Create: `monitoring/grafana_dashboard.json`

**Implementation:**
- Prometheus scrape config: scrape `/metrics` every 15s
- Grafana dashboard: request rate, latency p50/p95/p99, error rate, health status, memory, connections

---

## DELIVERABLE 7 — Security

**Existing state audit:**
- CORS setup (`app/__init__.py` — `_cors_setup`)
- Rate limiting (`app/__init__.py` — `_rate_limiter_setup` with flask-limiter)
- Security headers (`app/__init__.py` — `_security_headers_middleware`: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy)
- `flask-talisman` in requirements (not yet wired)
- PII redaction in logging (`app/shunya/infrastructure/logging.py`)

**Gap:** CSRF not configured. Flask-Talisman not wired. No input validation pipeline. No secrets management. Encryption not applied. No audit logging infra.

### Task 7.1: CSRF Protection

**Objective:** Enable CSRF protection on all mutating endpoints.

**Files:**
- Modify: `app/__init__.py` — enable `WTF_CSRF_ENABLED`
- Create: `tests/production/security/test_csrf.py`

**Implementation:**
- Use Flask-WTF CSRF protection, exempt API endpoints that use token/CORS auth
- All HTML form-based mutations require CSRF token
- API requests authenticated via `Authorization: Bearer <token>` are exempt

### Task 7.2: Wire Flask-Talisman

**Objective:** Apply comprehensive security headers via Flask-Talisman.

**Files:**
- Modify: `app/__init__.py` — init Flask-Talisman
- Create: `tests/production/security/test_talisman.py`

**Implementation:**
- Enable HSTS (max-age=31536000, includeSubDomains)
- Strict Content-Security-Policy
- Disable Flask-Talisman in test mode
- Override existing `_security_headers_middleware`

### Task 7.3: Input Validation Pipeline

**Objective:** Centralized request input validation.

**Files:**
- Create: `app/production/security/validation.py`
- Create: `tests/production/security/test_validation.py`

**Implementation:**
- `validate_input(data, schema)` — validates against JSON Schema or Pydantic model
- Built-in validators: email, phone, UUID, URL, slug, datetime, numeric range
- Returns structured error: `{field, message, code}`
- Middleware option: `@validate(schema)` decorator on routes

### Task 7.4: Secrets Management

**Objective:** Secure secrets storage with encryption at rest.

**Files:**
- Create: `app/production/security/secrets.py`
- Create: `tests/production/security/test_secrets.py`
- Modify: `.env.example` — document secret management

**Implementation:**
- `SecretsManager` class wrapping environment variables + encrypted file store
- Supported backends: env vars (dev), encrypted JSON file (staging), HashiCorp Vault API (prod — hooks only)
- AES-256-GCM encryption for stored secrets
- No secrets in code, config, or logs

### Task 7.5: Field-Level Encryption

**Objective:** Encrypt sensitive fields at the database level.

**Files:**
- Create: `app/production/security/encryption.py`
- Create: `tests/production/security/test_encryption.py`

**Implementation:**
- `@encrypted_field` decorator for SQLAlchemy models
- AES-256-GCM deterministic encryption for searchable fields
- Key rotation support via key ID tagging

### Task 7.6: Comprehensive Security Headers

**Objective:** Ensure all security headers are set correctly.

**Files:**
- Modify: `app/__init__.py` — review + update security headers
- Create: `tests/production/security/test_security_headers.py`

### Task 7.7: Audit Logging

**Objective:** Immutable audit log for all security-relevant events.

**Files:**
- Create: `app/production/security/audit_log.py`
- Create: `tests/production/security/test_audit_log.py`

**Implementation:**
- `AuditLog` model: id, timestamp, actor_id, actor_type, action, resource_type, resource_id, details (JSON), ip_address, user_agent
- All authentication events logged (login, logout, failed_login, password_reset, mfa, session_revoke)
- All authorization decisions logged (permit, deny)
- All lifecycle operations logged (org create/delete, user invite/remove)
- Append-only (insert-only, no update/delete)

---

## DELIVERABLE 8 — Performance

**Existing state audit:**
- Cache layer (`app/cache.py`) — Redis + in-memory fallback, basic get/set/delete
- No dedicated performance optimization work

### Task 8.1: Database Query Optimization

**Objective:** Profile and optimize critical queries.

**Files:**
- Modify: `app/models.py` — add missing indexes
- Create: `app/production/performance/query_optimizer.py`
- Create: `app/production/performance/__init__.py`
- Create: `tests/production/performance/test_queries.py`

**Implementation:**
- Audit all query patterns for N+1 issues
- Add eager loading (`joinedload`, `subqueryload`) where needed
- Add composite indexes on frequent query patterns (org_id + status + created_at, etc.)
- Paginate all list endpoints (default 20, max 100)

### Task 8.2: Cache Layer Enhancement

**Objective:** Multi-level caching for workspace, object, and search operations.

**Files:**
- Create: `app/production/performance/cache_enhanced.py`
- Create: `tests/production/performance/test_cache.py`

**Implementation:**
- L1: in-memory dict (100ms TTL, 1000 entries max)
- L2: Redis (5min TTL)
- Cache-aside pattern: load → cache → return
- Cache invalidation on writes (event-driven from Event Bus)
- Cache stats: hit rate, miss rate, eviction count

### Task 8.3: Search Optimization

**Objective:** Optimize search queries with full-text search.

**Files:**
- Modify: `app/search.py` — add full-text search using PostgreSQL tsvector
- Create: `tests/production/performance/test_search.py`

**Implementation:**
- Add `tsvector` columns for Lead and Person tables
- Create PostgreSQL `GIN` indexes
- Use `ts_query` + `ts_rank` for relevance scoring

### Task 8.4: API Latency Profiling

**Objective:** Profile and optimize top 10 slowest API endpoints.

**Files:**
- Create: `app/production/performance/profiler.py`
- Create: `tests/production/performance/test_profiler.py`

**Implementation:**
- Per-endpoint latency tracking (automatically via middleware)
- P50/P95/P99 tracking per route
- Report: top 10 slowest endpoints
- Expected targets: P50 < 50ms, P95 < 200ms, P99 < 500ms

### Task 8.5: Streaming Efficiency

**Objective:** Optimize SSE/event delivery for maximum throughput.

**Files:**
- Create: `app/production/performance/streaming.py`
- Create: `tests/production/performance/test_streaming.py`

**Implementation:**
- Event batch compression (merge multiple events per SSE message)
- Connection pooling for Redis pub/sub
- Backpressure handling (slow consumer detection)

---

## DELIVERABLE 9 — Reliability

**Existing state audit:** No dedicated reliability infrastructure.

### Task 9.1: Graceful Degradation

**Objective:** System continues functioning when dependencies fail.

**Files:**
- Create: `app/production/reliability/degradation.py`
- Create: `app/production/reliability/__init__.py`
- Create: `tests/production/reliability/test_degradation.py`

**Implementation:**
- Circuit breaker pattern for: Redis, Celery, Database
- Degradation modes: `full` (all OK), `degraded` (cache down → direct DB), `limited` (async jobs queued locally), `minimal` (read-only)
- Auto-detection and recovery

### Task 9.2: Automatic Recovery

**Objective:** Self-healing for common failure modes.

**Files:**
- Create: `app/production/reliability/recovery.py`
- Create: `tests/production/reliability/test_recovery.py`

**Implementation:**
- Database connection retry with backoff
- Redis reconnection
- Celery worker auto-restart
- Stuck job detection (timeout → retry → dead-letter)

### Task 9.3: Backup Strategy

**Objective:** Automated database backup.

**Files:**
- Create: `scripts/backup.sh`
- Create: `scripts/backup_verify.sh`
- Create: `app/production/reliability/backup.py`

**Implementation:**
- Daily PostgreSQL dump (`pg_dump`)
- Retention: 7 daily, 4 weekly, 12 monthly
- Encrypted backup files (AES-256-GCM)
- Backup verification script (restore to temp DB, run health check)
- S3/object-storage upload for off-site

### Task 9.4: Restore Procedures

**Objective:** Documented and tested restore procedures.

**Files:**
- Create: `scripts/restore.sh`
- Create: `docs/production/restore_procedure.md`

**Implementation:**
- Step-by-step restore script
- Point-in-time recovery support (WAL archiving)
- Verify procedure: restore + health check + data integrity check

### Task 9.5: Failure Isolation

**Objective:** One component failure should not cascade.

**Files:**
- Create: `app/production/reliability/isolation.py`
- Create: `tests/production/reliability/test_isolation.py`

**Implementation:**
- Timeout boundaries for all external calls (DB: 5s, Redis: 2s, external API: 10s)
- Per-tenant resource limits
- Graceful worker pool exhaustion handling

---

## DELIVERABLE 10 — Deployment

**Existing state audit:**
- `Dockerfile`, `docker-compose.yml`, `nginx.conf`, `Procfile`, `wsgi.py`, `runtime.txt`, `alembic.ini`
- `migrations/` directory with Alembic env and phase1 migration

### Task 10.1: Production Configuration

**Objective:** Production-optimized configuration.

**Files:**
- Create: `.env.production.example`
- Create: `config/production.yaml`
- Modify: `config.yaml` — add environment profiles

**Implementation:**
- Production database pool: 10 connections, 30s timeout
- Redis session store
- Gunicorn: 4 workers (2x CPU cores), preload, timeout 120s
- Log level: WARNING, JSON output to stdout

### Task 10.2: Environment Management

**Objective:** Structured environment profiles.

**Files:**
- Create: `config/development.yaml`
- Create: `config/staging.yaml`
- Create: `config/production.yaml`
- Modify: `app/shunya/config.py` — load profile-based config

**Implementation:**
- Environment profiles: development, staging, production
- Config overrides: `SHUNYA_APP__DEBUG=true`
- Sensible defaults for each profile

### Task 10.3: Database Migration Automation

**Objective:** Automated migration execution on deploy.

**Files:**
- Create: `scripts/migrate.sh`
- Create: `scripts/migrate_check.sh`
- Modify: `Procfile` — add release command

**Implementation:**
- Alembic auto-generated migrations
- Pre-deploy migration check (read-only, verify up-to-date)
- Release phase migration execution
- Rollback migration on deploy failure

### Task 10.4: Deployment Automation

**Objective:** CI/CD pipeline scripts.

**Files:**
- Create: `.github/workflows/deploy.yml`
- Create: `scripts/deploy.sh`
- Create: `scripts/deploy_rollback.sh`

**Implementation:**
- GitHub Actions: build → test → migrate → deploy → health check
- Blue-green deployment pattern
- Health check gate: 3 consecutive successful checks before routing traffic

### Task 10.5: Rollback Procedures

**Objective:** Fast rollback on deploy failure.

**Files:**
- Create: `docs/production/rollback_procedure.md`

**Implementation:**
- Application rollback: redeploy previous Docker image
- Database rollback: `alembic downgrade -1`
- Data integrity verification post-rollback

### Task 10.6: Versioning

**Objective:** Structured versioning for the platform.

**Files:**
- Create: `VERSION`
- Create: `app/version.py`

**Implementation:**
- Semantic versioning: `MAJOR.MINOR.PATCH`
- Version baked into Docker image tag
- `/api/v1/version` endpoint returning `{version, build, commit, built_at}`

---

## DELIVERABLE 11 — Quality Assurance

**Existing state audit:**
- 80+ test files covering Phases A–M, organizational, collaboration, prediction, decision, cognitive, awareness, etc.
- `conftest.py` with app/client/db fixtures (in-memory SQLite)
- Test characterization file

### Task 11.1: Full Regression Suite

**Objective:** Run all existing tests and ensure they pass.

**Files:**
- Create: `scripts/run_regression.sh`
- Create: `tests/production/regression/test_full_suite.py`

**Implementation:**
- `pytest tests/ -v --tb=short --cov=app --cov-report=html`
- Expected: all existing tests pass (80+ test files)
- Fix any pre-existing failures

### Task 11.2: Integration Testing

**Objective:** Test end-to-end across all deliverables.

**Files:**
- Create: `tests/production/integration/test_identity_flow.py`
- Create: `tests/production/integration/test_auth_flow.py`
- Create: `tests/production/integration/test_event_delivery.py`
- Create: `tests/production/integration/test_observability.py`

### Task 11.3: Load Testing

**Objective:** Verify performance under load.

**Files:**
- Create: `tests/load/locustfile.py`
- Create: `tests/load/README.md`

**Implementation:**
- Locust-based: 100 concurrent users, 10 req/s ramp-up
- Endpoint targets: `/health` (5/s), `/api/v1/orgs` (2/s), Event SSE (1/s), search (2/s)
- Success criteria: P95 < 200ms, error rate < 1%

### Task 11.4: Security Testing

**Objective:** Identify and fix security vulnerabilities.

**Files:**
- Create: `tests/production/security/test_security_scan.py`

**Implementation:**
- Check OWASP Top 10: injection, XSS, CSRF, auth bypass, insecure direct object reference
- Session hijacking: test token predictability
- Rate limiting: verify enforcement
- Permission escalation: cross-role access attempts

### Task 11.5: Accessibility Validation

**Objective:** Ensure web UI meets WCAG 2.1 AA standards.

**Files:**
- Create: `tests/production/accessibility/test_accessibility.py`

### Task 11.6: Performance Benchmarking

**Objective:** Establish baseline performance metrics.

**Files:**
- Create: `tests/production/benchmark/test_benchmarks.py`

**Implementation:**
- Benchmark endpoints: org create (1s), user list (200ms), search (500ms)
- Report: pass/fail per target

### Task 11.7: Operational Readiness Review Checklist

**Objective:** Verify all production readiness criteria.

**Files:**
- Create: `docs/production/readiness_checklist.md`

**Implementation checklist:**
- [ ] All 12 deliverables implemented
- [ ] Regression suite passes
- [ ] Integration tests pass
- [ ] Load tests meet targets
- [ ] Security scan clean
- [ ] Backup/restore verified
- [ ] Deployment automation tested
- [ ] Rollback procedure tested
- [ ] Monitoring endpoints responding
- [ ] Alerting configured
- [ ] Documentation updated

---

## DELIVERABLE 12 — Production Readiness Report

**Objective:** Comprehensive final report covering:

### Task 12.1: Architecture Status

- Summary of all SHUNYA subsystems (intelligence engines, runtimes, infrastructure)
- Completion status per system
- Architecture compliance verification

### Task 12.2: Operational Readiness

- Backup/restore verification results
- Deployment automation test results
- Rollback procedure test results
- Environment parity checks

### Task 12.3: Security Status

- Security scan results
- Penetration test summary
- CSRF, rate limiting, input validation verification
- Audit log implementation status

### Task 12.4: Performance Results

- Load test results (P50/P95/P99 per endpoint)
- Bottleneck analysis
- Cache hit rates
- Query optimization results

### Task 12.5: Known Limitations

- Unresolved issues
- Known trade-offs
- Future optimization opportunities

### Task 12.6: Deployment Guide

- Prerequisites (PostgreSQL 16, Redis 7, Python 3.12)
- Environment setup instructions
- Config reference
- First deploy walkthrough

### Task 12.7: Rollback Guide

- Application rollback steps
- Database migration rollback
- Data integrity verification post-rollback

### Task 12.8: Verification Evidence

- Test suite output (coverage report)
- Load test results (HTML report)
- Security scan results
- Health check endpoint responses

### Task 12.9: Recommendation

- Formal recommendation: GO / NO-GO for Founder deployment
- Conditions for GO
- Post-deployment monitoring period (7 days)
- SHUNYA OS onboarding checklist

---

## Verification Protocol

After each deliverable is completed:
1. Run all tests in that deliverable's test directory
2. Run the full regression suite
3. Verify no regressions introduced
4. Commit with message format: `feat(production): [Deliverable N] — [summary]`

## Execution Strategy

This plan will be executed deliverable-by-deliverable. Each deliverable will be dispatched as a subagent task with full context including:
- The specific tasks within the deliverable
- All relevant existing code paths
- Test expectations
- Verification criteria

No parallel execution across deliverables — sequential to ensure stability.
No cross-deliverable dependencies assumed until D3 (which waits for D1, D2, D7).