# SHUNYA — Current Truth Matrix

**Date:** 2026-08-14T16:48  
**Revision:** b1545c9 + working tree  
**Source:** Forensic audit

---

## STATUS LEGEND

| Status | Definition |
|--------|------------|
| PROVEN | Real runtime/user evidence exists |
| IMPLEMENTED_UNPROVEN | Code exists but promised user outcome not proven |
| PARTIAL | Some of the promised capability works |
| BROKEN | Expected behavior fails |
| DISCONNECTED | Backend/data/API exists but user-facing flow not connected |
| MOCK | Fake/demo behavior presented as product functionality |
| MISSING | Capability required by public promise does not exist |
| BLOCKED | Cannot be verified due to infrastructure/dependency limitation |
| OUT_OF_SCOPE | Explicitly not required for launch |
| MAINTENANCE | Not launch-blocking, belongs after foundational completion |

---

## 1. PUBLIC SURFACE — shunyaos.com

| Capability | Status | Evidence |
|------------|--------|----------|
| Homepage loads | PROVEN | HTTP 200, SPA renders (शून्य / SHUNYA / Get Started) |
| Title/meta | PROVEN | `<title>SHUNYA — AI Operating System</title>`, OG tags present |
| Responsive rendering | PROVEN | 21/21 browser QA: desktop/tablet/mobile, no overflow |
| Viewport meta | PROVEN | `<meta name="viewport" content="width=device-width">` |
| No dead content | PROVEN | No "coming soon", "lorem ipsum", "under construction" |
| No console errors | PROVEN | 0 console errors (browser QA) |
| No horizontal overflow | PROVEN | All viewports clean |
| No broken links | PROVEN | 0 broken in 10-link sample |
| Login flow | PROVEN | Tap to continue → email+password → Sign In |
| Login inputs | PROVEN | email, password fields verified |
| No login 500 | PROVEN | GET /login → 302 (no 500) |
| PWA manifest | PROVEN | /manifest.json → 200 |
| Service worker | PROVEN | /sw.js → 200 |
| PWA icons | MISSING | icon-192.png, icon-512.png, favicon.ico → 404 (files absent from dist after rebuild) |
| Semantic headings | PROVEN | H1 शून्य, H2 SHUNYA, H3 tagline |
| Accessibility (alt, labels) | PROVEN | 0 images missing alt, 0 buttons unlabeled |
| Semantic heading structure | PROVEN | h1-h3 present |

## 2. AUTHENTICATED APPLICATION — app.shunyaos.com

| Capability | Status | Evidence |
|------------|--------|----------|
| SSL/TLS | PROVEN | All 3 domains, valid LE certs, HSTS configured |
| HTTP→HTTPS redirect | PROVEN | All domains redirect to HTTPS |
| Login POST | PROVEN | demo@shunyaos.com / Demo2024! → 200, session cookie |
| Invalid credentials | PROVEN | Returns 401 |
| Logout | PROVEN | Session cleared, redirect |
| Session persistence | PROVEN | Cookie-based, survives requests |
| Session cookie security | PROVEN | Secure, HttpOnly, SameSite=Lax |
| CSRF protection | PROVEN | CSRF tokens returned on login |
| Rate limiting | PROVEN | flask-limiter (200/day, 50/hour) |
| Workspace API | PROVEN | SPA renders workspace shell |
| Workspace data | PARTIAL | Objects visible: 508 founder_objects, 600 sh_objects. Workspace renders correctly. |
| Signup flow | DISCONNECTED | `Signup` component exists in code. POST /api/v1/auth/signup works. But no signup link/button in login UI. |
| OAuth (Google/GitHub) | BLOCKED | Routes exist, no client IDs configured in .env |
| Email verification | IMPLEMENTED_UNPROVEN | Routes exist, dev mode auto-verifies |
| Password reset | IMPLEMENTED_UNPROVEN | Routes exist, not tested end-to-end |

## 3. ONBOARDING

| Capability | Status | Evidence |
|------------|--------|----------|
| First-use flow | PARTIAL | Tap to continue → email/password → Sign In → First Object screen |
| Object creation API | PROVEN | POST /api/v1/objects/ → creates in sh_objects (production store) |
| Object type descriptions | PROVEN | Descriptions added for Document, Task, Note, Lead, Invoice |
| Step navigation | PROVEN | Back, Continue, Create Object buttons work |
| Error handling | PROVEN | Error message shown on failure, Retry button |
| Business creation | PROVEN | POST /api/orgs creates organization |
| Welcome screen | PROVEN | Step-welcome component renders |
| AI intro | IMPLEMENTED_UNPROVEN | Step-ai-intro exists |
| Import step | IMPLEMENTED_UNPROVEN | Step-import exists |
| Complete step | IMPLEMENTED_UNPROVEN | Step-complete exists |
| End-to-end flow | UNVERIFIED | Full onboarding from register→workspace not tested as new user |

## 4. AI

| Capability | Status | Evidence |
|------------|--------|----------|
| Chat completion | PROVEN | Groq, llama-3.3-70b-versatile, <200ms |
| Provider chain | PROVEN | groq → gemini → openrouter → cloudflare → ... → local |
| Web search integration | PROVEN | DuckDuckGo, 8 results, sources injected into context |
| Company+Internet+AI | PROVEN | /api/v1/ai/analyze: 5 web sources + company context |
| Evidence logging | PROVEN | evidence_records table populated (6 rows) |
| Provider fallback | PROVEN | Chain tested: groq→gemini→openrouter→local on failure |
| Structured output | IMPLEMENTED_UNPROVEN | LLMRuntimeService.invoke_structured exists |
| AI governance | PARTIAL | Inference governance module exists. Age/safety policy NOT implemented. |
| OpenAI provider | BLOCKED | No API key in .env |
| Anthropic provider | BLOCKED | No API key in .env |
| Telemetry (model_runs) | DISCONNECTED | model_runs table empty (0 rows). AI chat uses own logging. |

## 5. SEARCH

| Capability | Status | Evidence |
|------------|--------|----------|
| DuckDuckGo web search | PROVEN | 8 results, deduplication |
| API endpoint | PROVEN | GET /api/v1/search?q= |
| Auth protection | PROVEN | Returns 401 without session |
| Proactive insights | IMPLEMENTED_UNPROVEN | Engine in app/search/routes.py exists |

## 6. CRM

| Capability | Status | Evidence |
|------------|--------|----------|
| Lead create | PROVEN | POST /api/v1/crm/leads creates lead |
| Lead qualify | PROVEN | GET /api/v1/crm/leads/{id}/qualify |
| Lead assign | PROVEN | POST /api/v1/crm/leads/{id}/assign |
| Lead SLA | PROVEN | GET /api/v1/crm/leads/{id}/sla |
| Follow-up task | PROVEN | POST /api/v1/crm/leads/{id}/follow-up |
| Create opportunity | PROVEN | POST /api/v1/crm/leads/{id}/opportunity |
| Convert to customer | PROVEN | POST /api/v1/crm/leads/{id}/won → creates customer record |
| Mark lost | PROVEN | POST /api/v1/crm/leads/{id}/lost |
| Reassign | PROVEN | POST /api/v1/crm/leads/reassign |
| UI CRM components | PROVEN | Workspace has people-panel, timeline-view, commitment-panel |
| Customer store | PARTIAL | CRM writes to `customer` table (4 rows). `customers` table is orphan (no model maps to it). |
| Lead→customer linkage | PARTIAL | Via entity_id system. No direct FK. 3 leads marked "converted" without corresponding customers. |

## 7. DOCUMENTS / KNOWLEDGE

| Capability | Status | Evidence |
|------------|--------|----------|
| Document model | PROVEN | DocumentRecord model exists |
| Document API | PROVEN | /api/v1/documents routes exist |
| Document ingestion | IMPLEMENTED_UNPROVEN | Code writes DocumentRecord + EvidenceRecord |
| Knowledge entries | PROVEN | 43 rows in knowledge_entries |
| Memory records | PROVEN | 35 rows in memory_records |
| Document uploads | PARTIAL | Upload route at /documents_knowledge/routes.py exists. No documents ingested (0 rows). |
| Knowledge facts | IMPLEMENTED_UNPROVEN | KnowledgeFact model (0 rows). Search queries it. |
| Document runtime | PROVEN | DocumentRuntime blueprint registered |

## 8. EXECUTION

| Capability | Status | Evidence |
|------------|--------|----------|
| Execution model | PROVEN | Execution, ExecutionTask models |
| Execution API | PROVEN | execution_bp registered |
| Auto execution loop | PROVEN | runtime/loop.py processes commitments |
| Execution log | PROVEN | act_execution_logs: 1769 rows (ENTITY_SEEN, NOOP, DECISION, ACTION, etc.) |
| Execution without evidence gate | PROVEN | execution_engine hard-blocks execution without EvidenceRecord |
| Evidence enforcement | PROVEN | require_evidence() raises RuntimeError if evidence missing |
| Commitments | IMPLEMENTED_UNPROVEN | API routes exist, model exists. 0 commitments created. |
| Outcomes | PARTIAL | 5 outcomes + 3 sh_outcomes. Split across 2 stores. |
| Decision traces | MISSING | 0 rows in decision_traces |
| Evidence records | PROVEN | 6 rows (AI + CRM). Previously 0, now populated. |

## 9. FINANCE

| Capability | Status | Evidence |
|------------|--------|----------|
| Invoice model | PROVEN | 16 finance tables |
| Invoice API | PROVEN | finance routes registered |
| Payment model | PROVEN | Payments, ledgers |
| Tax model | PROVEN | TaxProfile model |
| Budget model | PROVEN | Budget model |
| UI finance components | IMPLEMENTED_UNPROVEN | Exists in code, not UI-tested |

## 10. INTEGRATIONS

| Capability | Status | Evidence |
|------------|--------|----------|
| Integration registry | PROVEN | 1 integration registered (email/Gmail) |
| Webhook system | PROVEN | 1 webhook subscription, 1 delivery |
| OAuth framework | PROVEN | Google + GitHub flows fully implemented |
| Gmail OAuth | PARTIAL | Routes exist (initiate, callback, disconnect). No OAuth sources configured (0 in DB). |
| Social accounts | PARTIAL | 1 social account record |
| Cloudinary | IMPLEMENTED_UNPROVEN | Cloudinary routes exist |
| Razorpay | IMPLEMENTED_UNPROVEN | Razorpay routes exist |

## 11. SECURITY

| Capability | Status | Evidence |
|------------|--------|----------|
| HTTPS | PROVEN | All domains, valid certs |
| Security headers | PROVEN | X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, HSTS |
| CSRF | PROVEN | Flask-WTF tokens returned on login |
| Rate limiting | PROVEN | 200/day, 50/hour per IP |
| Session cookie | PROVEN | Secure, HttpOnly, SameSite=Lax |
| Tenant isolation | PARTIAL | Most tables have tenant_id. sh_objects and founder_objects lack tenant_id (use workspace_id/space_id). |
| Authorization | PARTIAL | AuthLayer works. But all 71 members are role=admin. AuthMemberRole table empty (0 rows). |
| Input validation | IMPLEMENTED_UNPROVEN | Not explicitly tested |
| Prompt injection | NOT ADDRESSED | No prompt injection mitigation found |
| Age/safety policy | MISSING | Not implemented |
| Secret handling | PARTIAL | API keys in .env on disk |
| DB encryption at rest | UNVERIFIED | Not verified |

## 12. PERFORMANCE

| Capability | Status | Evidence |
|------------|--------|----------|
| Homepage load | PROVEN | 25ms local, 34ms live TTFB |
| Health endpoint | PROVEN | 4.6ms |
| AI chat | PROVEN | ~200ms with Groq |
| Search | PARTIAL | ~1.39s baseline (FDA32). Not retested with production data. |
| Object listing | PARTIAL | ~1.16s for 508 objects (FDA32). Not retested. |
| Cache headers | MISSING | No Cache-Control headers on SPA responses |
| DB query optimization | UNVERIFIED | Not profiled |

## 13. BACKUP / RECOVERY

| Capability | Status | Evidence |
|------------|--------|----------|
| Backup exists | PROVEN | pg_dump custom format (Fc), 1968 entries, 384 tables |
| Backup integrity | PROVEN | pg_restore --list passes, 25MB compressed |
| Restore procedure | DOCUMENTED | Requires postgres superuser (shunya user lacks CREATEDB) |
| Restore tested | BLOCKED | Cannot test without postgres superuser credentials |
| Rollback procedure | UNVERIFIED | Git revert + deploy not documented |

## 14. DEPLOYMENT

| Capability | Status | Evidence |
|------------|--------|----------|
| Git HEAD | PROVEN | b1545c9 |
| origin/master match | PROVEN | 0 ahead, 0 behind |
| Deployed revision | PROVEN | HEAD + working tree |
| Working tree deviation | PARTIAL | 59 modified files, 34 untracked. Working tree deployed code differs from committed HEAD. |
| nginx config | PARTIAL | 4 server blocks (2 HTTP + 2 HTTPS). One duplicate HTTPS block with different cert. Consolidated config ready at /home/shunya-deploy/nginx_consolidated.conf. |
| Frontend bundle match | PROVEN | Live hash matches local dist |
| Environment = production | PROVEN | /health reports environment=production |
| Gunicorn service | PROVEN | systemd, Restart=always |
| Migration state | PARTIAL | alembic at 0006, 7 migrations on disk (0007 unapplied) |
| DB user restrictions | PROVEN | shunya user lacks CREATEDB, CREATEROLE |

## 15. ARCHITECTURE

| Capability | Status | Evidence |
|------------|--------|----------|
| Object stores | VIOLATION | 4 stores: sh_objects(600), founder_objects(508), objects(29), canonical_objects(2). 0 ID overlap between sh_objects and founder_objects. canonical_objects has no code references. |
| Customer stores | MISNAMED | `customers` table (0 rows) is orphan. `customer` table (4 rows) is what Customer model actually uses (__tablename__="customer"). |
| Identity stores | PARTIAL | team_members(71), shunya_identities(35), person_identities(0). PersonIdentity (canonical) empty. |
| Audit stores | FRAGMENTED | 6 audit tables: genesis_audit_log(0), sh_audit_logs(2), user_activity_logs(287), evidence_records(6), decision_traces(0), m9_audit_records(0) |
| Outcome stores | DUPLICATE | outcomes(5), sh_outcomes(3) |
| Knowledge stores | FRAGMENTED | document_records(0), knowledge_facts(0), knowledge_documents(0), knowledge_entries(43), memory_records(35) |

---

*End of Current Truth Matrix*