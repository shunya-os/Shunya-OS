FDA5-G1 INVENTORY REPORT
============================================================

1. EXISTING HTTP/API ROUTES
============================================================

Total blueprints: 51 registered in create_app()
Total route files: 38
Estimated total routes: ~400+

/api/v1/ routes (canonical prefix):
  activation, ai, automation, cloudinary, commitments, communication,
  creative, documents, enterprise, execution, genesis, intake,
  integration, intelligence, intention, jobs, leads, objects, observations,
  onboarding, pdf, reality, search, space, travel, upload, webhook, authz

/api/v2/ routes:
  activation (activation/__init__.py)

Non-/api/ routes:
  /system/health, /system/unused-intelligence (health)
  /debug/* (debug)
  /operator/* (operator)
  /workspace/* (workspace)
  /relationships/* (relationship)
  /proposals/* (proposal_routes)
  /orgs/* (identity)
  /api/intelligence (intelligence_routes — non-v1)
  /api/ubme (ubme)

2. INTERNAL SERVICE INTERFACES
============================================================

Canonical (FDA-defined):
  IdentityService (app/identity/service.py) — IdentityResolutionInterface
  MemoryService (app/memory/__init__.py) — Memory context
  KnowledgeInterface (core/knowledge_interface.py) — Knowledge governance

Legacy services (still in production use):
  app/shunya/identity/engine.py — IdentityEngine (KnowledgeStore-backed)
  app/shunya/identity/resolver.py — IdentityResolver
  app/intelligence/context_assembly/engine.py — ContextAssemblyEngine
  app/integration/service.py — IntegrationService
  app/integration/providers/email_integration.py — EmailIntegration

3. AUTHENTICATION MECHANISMS
============================================================

  app/auth.py — TeamMember model, password hashing, verify token
  app/auth_routes.py — Login/logout, team management, email verification
  app/auth_oauth.py — Google OAuth, GitHub OAuth, Gmail OAuth
  app/production/auth/ — Session-based auth middleware
  app/authz/ — RBAC (roles, permissions, check)
  app/intake/session.py — Session management

4. AUTHORIZATION MECHANISMS
============================================================

  app/authz/routes.py — /api/v1/authz/permissions|roles|check|members
  app/production/auth/authorization_middleware.py — Request-level authz
  app/authz/models.py — Role, Permission, MemberRole models

5. OAUTH INTEGRATIONS
============================================================

  Google login: /google/login, /google/callback
  GitHub login: /github/login, /github/callback
  Gmail: /gmail/connect, /gmail/oauth/initiate, /gmail/oauth/callback
  app/communication/oauth.py — Token storage, refresh, lifecycle

6. GMAIL INTEGRATION
============================================================

  app/integration/gmail_ingest.py — Gmail fetch + normalization
  app/adapters/gmail/ — Gmail API client
  app/communication/email.py — Email service
  app/communication/email_core.py — Core email processing
  app/communication/providers/email_provider.py — Email provider abstraction
  app/integration/providers/email_integration.py — Email integration model

7. EXTERNAL PROVIDERS
============================================================

  Razorpay — /api/v1/razorpay/* (payments)
  Cloudinary — /api/v1/cloudinary/* (media)
  Google — OAuth, Gmail, Calendar
  GitHub — OAuth login
  WhatsApp — app/adapters/whatsapp_* (free + official)
  app/models.py — Lead, Supplier, Customer, Organization models

8. WEBHOOKS
============================================================

  app/api/webhook_routes.py — /api/v1/webhook/* (canonical)
  app/automation/models.py — AutomationRule with webhook triggers
  app/communication/inbound.py — Inbound webhook processing
  app/integration/service.py — Webhook delivery

9. BACKGROUND JOBS
============================================================

  app/automation/routes.py — /api/v1/automation/* (10 routes)
  app/jobs/routes.py — /api/v1/jobs/* (6 routes)
  app/events/routes.py — /api/v1/events/* (2 routes)

10. IMPORT/EXPORT MECHANISMS
============================================================

  app/upload/routes.py — /api/v1/upload (file upload)
  app/objects/upload.py — Object upload
  app/document_runtime/routes.py — Document management (14 routes)
  app/search/routes.py — Search functionality

11. HEALTH/STATUS ENDPOINTS
============================================================

  /system/health — DB connectivity, latency, integration status
  /system/unused-intelligence — Dormant module report

12. FRONTEND → BACKEND COMMUNICATION
============================================================

  app/ui/routes.py — /ui/* (3 routes, template rendering)
  app/workspace_routes.py — /workspace/* (6 routes)
  app/space/routes.py — /api/v1/space/* (42 routes)

13. BACKEND → PROVIDER COMMUNICATION
============================================================

  app/adapters/gmail/ — Gmail API
  app/communication/adapters.py — Communication adapters
  app/integration/providers/ — Provider integrations

14. INVENTORY ASSESSMENT
============================================================

| Category | Status | Authority |
|----------|--------|-----------|
| /api/v1/ routes | EXISTING, no canonical contract | TRANSITIONAL |
| /api/v2/ routes | BROKEN (only activation, incomplete) | INCOMPLETE |
| IdentityService | CANONICAL | FDA4 |
| MemoryService | CANONICAL | FDA3 |
| KnowledgeInterface | CANONICAL (contract only) | FDA3 |
| Legacy IdentityEngine | DUPLICATE | LEGACY |
| OAuth lifecycle | EXISTING | TRANSITIONAL |
| Gmail integration | EXISTING, multiple files | TRANSITIONAL |
| Webhook fabric | EXISTING | TRANSITIONAL |
| Health endpoints | EXISTING (minimal) | EXISTING |
| Authn/authz RBAC | EXISTING | TRANSITIONAL |
| Background jobs | EXISTING | TRANSITIONAL |
| Import/export | INCOMPLETE | MISSING |
| API contract | MISSING | MISSING |
| OpenAPI docs | MISSING | MISSING |
| Provider-neutral interface | MISSING | MISSING |

15. GATE VERDICT
============================================================

FDA5-G1: PASS

No architectural contradictions found. The inventory reveals a codebase with
established route/blueprint structure, working auth/authz, and several
integration paths that need canonical contracts. G2 will address the missing
API contract.