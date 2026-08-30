# M2C.5 — LIVE RESIDUAL-GAP REGISTER
## Date: 2026-08-29 | SHA: d97cc6e | Deployed: d97cc6e
## Authority: Consolidated Residual-Gap & Certification Directive (§1)

### Status Legend
| Status | Definition |
|--------|-----------|
| VERIFIED COMPLETE | Independently proven end-to-end, works, tested |
| PARTIAL | Functionality exists but incomplete chain |
| BACKEND_ONLY | API/database exists but no UI or broken UI |
| UI_ONLY | UI renders but no backend data flow |
| DISCONNECTED | Data exists in one place but not connected to workflow |
| DUPLICATED | Multiple implementations of same concept |
| BROKEN | Exists but fails under normal use |
| GENUINELY MISSING | Not implemented at any layer |
| ENVIRONMENT BLOCKED | Cannot verify without external credentials/sudo |
| NOT PROVEN | Insufficient evidence to classify |
| RESOLVED | Previously broken, now fixed and verified |

---

## 1. IDENTITY — DUAL SYSTEMS, SEVERE ARCHITECTURAL RISK (§2)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Two identity systems (TeamMember + SHUNYAIdentity) | Signup creates both; no convergence path | RESOLVED | Sha efda28e. All 10 team_members now have identity_id FK to shunya_identities. Login resolves through canonical identity. | — | LAUNCH BLOCKER |
| Signup creates TeamMember AND identity but no link | auth_routes.py + shunya_public.py both create separate records | RESOLVED | api_create_identity stores identity_id on TeamMember at creation. Login auto-creates identity for members missing one. | — | LAUNCH BLOCKER |
| Password reset uses TeamMember only | /forgot-password → TeamMember email | PARTIAL | Tests pass (31/31 auth) but password reset still uses TeamMember email (valid since identity_id is now linked) | Wire password reset to use canonical identity lookup | HIGH |
| Invitation acceptance resolves to TeamMember, not canonical identity | org_invitations=0 — never tested | GENUINELY MISSING | No invitation flow exists | Build invitation→identity path | HIGH |
| No OAuth identity resolution | /auth/google, /auth/github routes missing | GENUINELY MISSING | No OAuth backend routes | Implement OAuth flow | HIGH |
| No identity merge/conflict semantics | No merge endpoints, no duplicate detection | GENUINELY MISSING | persons=10, person_identities=0 | Build merge/conflict resolution | HIGH |
| Persons table finally seeded but identity graph absent | Phase B seeded 10 persons | PARTIAL | persons=10, person_identities=0. Person→TeamMember links exist via person_id | Wire Person→TeamMember→SHUNYAIdentity links | HIGH |
| _resolve_identity_session overwrites identity_id with email | Middleware sets session["identity_id"] = tm.email when no org membership | RESOLVED | Middleware now prioritizes TeamMember.identity_id over email. Resolution order: identity_id → OrgMember → email fallback | — | LAUNCH BLOCKER |

## 2. ORGANIZATION / TENANT CONVERGENCE (§3)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Tenant + Organization coexist | tenants=32 rows, organizations=1 row | RESOLVED | e0216b2: org_routes now use Organization model. Tenant exists as legacy read-only, all new writes go to Organization. | — | HIGH |
| Org membership flow not tested | org_members=2, org_invitations=0, membership_requests=0 | RUNTIME_VERIFIED | e0216b2: Invitation routes create OrgInvitation + OrgMember. Org CRUD creates owner membership. 181/181 tests pass. | — | HIGH |
| Personal workspace not proven first-class | founder_spaces=3, workspaces=1, sh_workspaces=3 | IMPLEMENTED | e0216b2: _ensure_personal_workspace_for_user() auto-creates FounderSpace on login. | Full verification of data/memory/AI context/tasks ownership | HIGH |
| Workspace switching not tested | workspace_switch endpoint exists | IMPLEMENTED | e0216b2: Personal workspace switching wired via for2/switch/personal endpoint. | E2E browser verification | MEDIUM |

## 3. OBJECT DUPLICATION (§4 / §27)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| 5 competing object systems | objects=41, founder_objects=44, sh_objects=4, canonical_objects=0, sh_uop_objects=0 | PARTIAL | e82e7c2+: Migration wrote 85 objects to canonical UOPObject. Canonical access layer created (app/objects/canonical.py). Dual-write not yet wired to all creation paths. | Wire all creation paths (upload, AI, onboard) through canonical layer | HIGH |
| FounderObject still used by Executive Home | Executive Home queries founder_objects | PARTIAL | e82e7c2+: Migration done (44 FO → UOP). Executive Home still reads founder_objects. Canonical read helper created. | Update Executive Home to query UOPObject | HIGH |

## 4. UPLOAD → KNOWLEDGE → IDENTITY → AI PIPELINE (§5)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Document extraction works | 15 documents visible | VERIFIED COMPLETE | documents=15 with extracted text | — | — |
| Knowledge facts seeded | 51 facts from 3 documents | VERIFIED COMPLETE | knowledge_facts=51 | — | — |
| Entity extraction pipeline exists | extraction_pipeline.py | PARTIAL | Pipeline exists but entity→identity→relationship chain broken | Wire entity extraction to Person/Relationship creation | HIGH |
| No identity resolution from documents | extracted entities don't resolve to persons | BROKEN | persons=10 but no link from knowledge_facts to persons | Connect extraction→identity resolution | HIGH |
| No relationship creation from documents | no relationships despite 15 docs | BROKEN | relationships=0, rel_relationships=0 | Create relationships from extracted entities | HIGH |
| Malicious/prompt-injection document safety | Not tested | GENUINELY MISSING | No safety gate for document content | Add prompt-injection isolation | HIGH |

## 5. MEMORY / KNOWLEDGE DURABILITY (§6)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Memory records exist | memory_records=3 | PARTIAL | 3 records exist but provenance=0, candidates=0 | Wire provenance tracking | HIGH |
| Knowledge entries empty | knowledge_entries=0 | BROKEN | 51 knowledge_facts but 0 knowledge_entries | Connect knowledge_facts→knowledge_entries | HIGH |
| Knowledge documents empty | knowledge_documents=0 | BROKEN | 15 documents but 0 extracted knowledge documents | Wire document→knowledge pipeline | HIGH |
| No memory correction/deletion | No correction API | GENUINELY MISSING | No correction/delete endpoints | Build memory lifecycle | HIGH |
| No tenant isolation in memory | memory_records have no tenant_id column | NOT PROVEN | Not verified | Add tenant scoping to memory | LAUNCH BLOCKER |

## 6. AI / CONTEXT ASSEMBLY (§7)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| AI question answering works | /api/v1/intelligence/ask returns answers | VERIFIED COMPLETE | Works with company context | — | — |
| Context assembly not multi-source | Only uses evidence_records(1) | PARTIAL | 1 evidence record only | Wire identity+workspace+relationships+memory+knowledge+tasks | HIGH |
| No web research wired | No web search in AI pipeline | GENUINELY MISSING | No real search integration | Build web intelligence with citations | HIGH |
| No citation/provenance in answers | AI returns text without source citations | GENUINELY MISSING | No citation system | Add evidence citations to AI answers | HIGH |
| Company-first scenario not proven | No Amit/Bali-style test | NOT PROVEN | Not verified | Build company-first then web-fallback flow | HIGH |

## 7. AI → OUTPUT → EXECUTION (§8)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| AI can't generate persistent artifacts | No artifact creation from AI | GENUINELY MISSING | No artifact_records populated | Build AI→artifact→output→download pipeline | HIGH |
| No governed execution from AI | AI can't trigger governed actions | GENUINELY MISSING | No tool execution path | Wire AI→authorization→execution | HIGH |
| No audit trail for AI actions | No AI action audit trail | GENUINELY MISSING | No AI-specific audit records | Add AI action auditing | HIGH |

## 8. DURABLE EXECUTION (§9)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| BusinessExecutionInstance table missing | Relation does not exist | GENUINELY MISSING | No table for durable execution | Create BusinessExecutionInstance | HIGH |
| Tasks exist but not wired | tasks=14 | DISCONNECTED | 14 tasks but no execution context | Wire tasks→commitment→execution | HIGH |
| Commitments exist but not actionable | commitments=5 | DISCONNECTED | 5 commitments, 0 linked to execution | Wire commitments→plan→task→execution | HIGH |
| No retry/idempotency | execution_idempotency table exists but empty | NOT PROVEN | Table exists, 0 rows | Test idempotency | MEDIUM |
| Thread-based not durable | Current implementation uses threads | NOT PROVEN | Not verified under failure | Test worker crash recovery | HIGH |

## 9. FINANCE (§10)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Invoices seeded but no API | 20 fin_invoices, 0 API route | BACKEND_ONLY | fin_invoices=20, no /api/v1/finance/* routes | Build finance API | LAUNCH BLOCKER |
| No payments, ledger, accounts, budgets | fin_payments=0, fin_ledger=0, fin_accounts=0, fin_budgets=0 | GENUINELY MISSING | All financial tracking tables empty | Build complete finance chain | LAUNCH BLOCKER |
| Finance UI shows wrong content | Workspace shows Commitments instead of Finance | BROKEN | UI renders incorrect data | Wire Finance UI to fin_* tables | LAUNCH BLOCKER |
| Legacy invoices table empty | invoices=0 | RESOLVED | Empty table — deprecation in progress | Drop legacy table | LOW |

## 10. SALES / CRM (§11)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Leads exist but no pipeline | leads=6 | DISCONNECTED | 6 leads in DB, pipeline UI empty | Wire leads→pipeline→opportunity→quote→conversion | HIGH |
| Opportunities empty | opportunities=0 | GENUINELY MISSING | No opportunities table populated | Build opportunity pipeline | HIGH |
| Proposals empty | proposals=0 | GENUINELY MISSING | No proposals | Build proposal→quote workflow | HIGH |
| Customers table missing | customers table does not exist | GENUINELY MISSING | No customer table | Create customer table and workflow | HIGH |
| CRM SLA route exists | /api/v1/crm/leads/<id>/sla | BACKEND_ONLY | Route exists but not proven end-to-end | Test SLA workflow | MEDIUM |

## 11. MARKETING (§12)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Campaigns seeded | campaigns=5 | DISCONNECTED | 5 campaigns but no campaign→lead→revenue chain | Wire campaign attribution | HIGH |
| Campaign contents empty | campaign_contents=0 | GENUINELY MISSING | No content pipeline | Build content→campaign→execution | HIGH |
| No attribution | g5_attributions, g5_campaign_events exist | PARTIAL | G5 tables exist but untested | Test UTM/source attribution | MEDIUM |

## 12. OPERATIONS (§11)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Operations surface timed out | ZERO-GAP register: Operations RED | BROKEN | Not verified — likely still broken | Debug Operations timeout | HIGH |
| No supplier tracking | suppliers=0 | GENUINELY MISSING | Suppliers table empty | Build procurement workflow | HIGH |
| No procurement chain | purchase_orders, quotes tables missing | GENUINELY MISSING | No procurement tables | Build procurement workflow | MEDIUM |

## 13. PEOPLE / ADMIN (§11)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Persons seeded but no identity graph | persons=10, person_identities=0 | PARTIAL | Persons exist but no identity links | Wire Person→TeamMember→SHUNYAIdentity | HIGH |
| No people permissions | people.view permission not wired | PARTIAL | People API exists but no authz | Wire role-based access to people | HIGH |
| No people UI wiring | People workspace shows empty | BROKEN | People surface exists but no data shown | Wire persons→People UI | HIGH |

## 14. NOTIFICATIONS (§13)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Notifications table empty | notifications=0 | GENUINELY MISSING | Table exists but no notification system | Build notification framework | HIGH |
| No alert classes/severity | Not implemented | GENUINELY MISSING | No notification architecture | Design alert taxonomy | MEDIUM |
| No push notifications wired | shunya_push_subscriptions exists | NOT PROVEN | Subscription table exists but untested | Wire push notification delivery | MEDIUM |

## 15. COMMUNICATIONS / EMAIL (§14)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Gmail adapter registered | Integration registry shows Gmail | PARTIAL | Adapter registered but no OAuth credentials | Add OAuth credentials | ENVIRONMENT BLOCKED |
| No outbound email | No outbound email capability | GENUINELY MISSING | SMTP configured but untested | Test outbound email | HIGH |
| Messages empty | messages=0 | GENUINELY MISSING | No messages in system | Wire communications pipeline | HIGH |
| Conversation table missing | conversations table does not exist | GENUINELY MISSING | No conversation model | Build conversation model | HIGH |

## 16. OAUTH / PROVIDER ADAPTERS (§15)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| OAuth credentials absent | No OAuth tokens configured | ENVIRONMENT BLOCKED | No credentials available | Add credentials | ENVIRONMENT BLOCKED |
| Google/GitHub OAuth routes missing | No /auth/google or /auth/github | GENUINELY MISSING | Backend OAuth routes don't exist | Implement OAuth routes | MEDIUM |
| Integration health untested | Integration registry exists | NOT PROVEN | Not verified with real providers | Test provider health/retry/failure | MEDIUM |

## 17. ROUTE DUPLICATION (§16)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Duplicate intelligence routes | Multiple /api/v1/intelligence/* endpoints | NOT PROVEN | Route table shows various intelligence paths | Audit and canonicalize | MEDIUM |
| Multiple /api/v1/identity/* routes | identity/create + founder/signin both create identities | DUPLICATED | Both create TeamMember records | Consolidate identity creation | HIGH |
| Multiple signup paths | /api/v1/auth/signup, /api/v1/founder/signin, /api/v1/identity/create | DUPLICATED | Three identity creation paths | Single canonical signup | HIGH |

## 18. ROLE / AUTHORIZATION (§17)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Auth roles table empty | auth_roles=0 | GENUINELY MISSING | Table exists but empty | Seed role definitions | LAUNCH BLOCKER |
| Auth permissions table missing | auth_permissions does not exist | GENUINELY MISSING | No permission table | Create permission model | LAUNCH BLOCKER |
| User roles table missing | user_roles does not exist | GENUINELY MISSING | No user-role assignments | Create user-role mapping | LAUNCH BLOCKER |
| No permission enforcement | No permission checks on API endpoints | GENUINELY MISSING | No authorization middleware | Wire role/permission enforcement | LAUNCH BLOCKER |
| Tenant isolation not proven | No cross-tenant test evidence | NOT PROVEN | Not verified | Test cross-tenant denial | LAUNCH BLOCKER |

## 19. SECURITY / AI SAFETY (§18)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Tenant isolation tests pass | 31/31 auth tests | PARTIAL | Auth tests pass but no cross-tenant tests | Add cross-tenant security tests | LAUNCH BLOCKER |
| No malicious document safety | Not tested | GENUINELY MISSING | No safety gate | Add document safety checks | HIGH |
| No prompt injection protection | Not tested | NOT PROVEN | Not verified | Test prompt injection resistance | LAUNCH BLOCKER |
| No data exfiltration prevention | Not tested | NOT PROVEN | Not verified | Add data exfiltration controls | LAUNCH BLOCKER |

## 20. WEB INTELLIGENCE (§19)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| No web research capability | No web search in AI | GENUINELY MISSING | Not implemented | Build web research with citations | HIGH |
| No citation/provenance | Answers have no source citations | GENUINELY MISSING | No citation system | Add citation tracking | HIGH |
| No source quality assessment | Not implemented | GENUINELY MISSING | No source quality | Build source quality scoring | MEDIUM |

## 21. UX/UI — PRODUCT EXPERIENCE (§21)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| 70/20/10 visual hierarchy | Constitution requirement | NOT PROVEN | Not verified against live UI | Audit visual hierarchy | MEDIUM |
| Living UI behavior | Real-time state, motion, pulse | NOT PROVEN | Not verified | Verify living UI behavior preserved | MEDIUM |
| Object-first interaction | Constitution requirement | NOT PROVEN | Not verified | Verify object-first UX | MEDIUM |
| Contextual AI vs chatbot | Constitution requirement | NOT PROVEN | Not verified | Verify AI is contextual, not generic | MEDIUM |

## 22. RESPONSIVE / MOBILE / ACCESSIBILITY (§22)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Desktop not certified | ZERO-GAP: AMBER | NOT PROVEN | Not verified | Viewport matrix testing | MEDIUM |
| Tablet/mobile not tested | ZERO-GAP: UNKNOWN | NOT PROVEN | Not verified | Mobile viewport testing | HIGH |
| Keyboard navigation not tested | ZERO-GAP: UNKNOWN | NOT PROVEN | Not verified | Keyboard navigation audit | HIGH |
| Screen reader not tested | ZERO-GAP: UNKNOWN | NOT PROVEN | Not verified | Screen reader audit | HIGH |
| Loading/error/empty states not verified | Not certified | NOT PROVEN | Not verified | State audit across all surfaces | MEDIUM |

## 23. OBSERVABILITY (§23)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Structured JSON logging | Configured | VERIFIED COMPLETE | JSON logging working | — | — |
| Correlation IDs | X-Request-Id header on every response | VERIFIED COMPLETE | Working | — | — |
| Health endpoint | 10+ fields | VERIFIED COMPLETE | /health returns comprehensive status | — | — |
| No alerting configured | Not implemented | GENUINELY MISSING | No alert system | Build alerting | HIGH |
| No runbooks | Not implemented | GENUINELY MISSING | No operational runbooks | Write incident runbooks | MEDIUM |
| No user-facing recovery state | Not implemented | GENUINELY MISSING | No recovery UI | Build user-facing recovery | MEDIUM |

## 24. PERFORMANCE / TIMEOUTS (§24)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Operations/Outputs timeout | ZERO-GAP: Operations timed out | BROKEN | Not re-verified | Debug Operations timeout | HIGH |
| AI latency ~10.7s | External model latency | DEGRADED | Measured but high | Optimize AI response time | MEDIUM |
| Full test suite timeout | 4996 tests hang | BROKEN | Not verified | Investigate test suite hang | HIGH |

## 25. BACKUPS / RESTORE (§25)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| No backup evidence | No backup configuration verified | GENUINELY MISSING | No evidence | Configure automated backups | LAUNCH BLOCKER |
| No restore demonstrated | Not tested | GENUINELY MISSING | No evidence | Perform restore demonstration | LAUNCH BLOCKER |
| No RPO/RTO defined | Not defined | GENUINELY MISSING | No target metrics | Define RPO/RTO | LAUNCH BLOCKER |

## 26. IMPORT / EXPORT (§26)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Import/Export UI exists | ImportExportPanel component | UI_ONLY | Component exists but untested | Test import/export workflows | MEDIUM |
| Document import works | 15 documents ingested | VERIFIED COMPLETE | Documents working | — | — |
| CSV import not tested | No CSV import verification | NOT PROVEN | Not verified | Test CSV import with validation | MEDIUM |
| No dry-run import | Not implemented | GENUINELY MISSING | No dry-run capability | Add dry-run import | LOW |

## 27. LEGACY / DUPLICATE SYSTEM CLEANUP (§27)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| Objects: 5 competing systems | objects, founder_objects, sh_objects, canonical_objects, sh_uop_objects | DUPLICATED | 3 active stores (89 rows total) | Consolidate to objects | HIGH |
| Identity: 3 systems | team_members, shunya_identities, persons | DUPLICATED | 10+10+2=22 records across 3 tables | Consolidate identity | LAUNCH BLOCKER |
| Organization: 2 systems | organizations, tenants | DUPLICATED | 1+32=33 records across 2 tables | Deprecate tenants | HIGH |
| Invoice: 2 systems | fin_invoices, invoices | DUPLICATED | 20+0=20 records across 2 tables | Drop invoices table | MEDIUM |
| Document: 3 systems | documents, knowledge_documents, document_records | DUPLICATED | 15+0+0=15 records across 3 tables | Consolidate document stores | MEDIUM |
| Relationship: 2+ systems | relationships, rel_relationships, rel_timeline, rel_ai_memory | DUPLICATED | All empty | Consolidate or remove | MEDIUM |
| Memory: 2+ systems | memory_records, knowledge_entries, memory_candidates | DUPLICATED | 3+0+0=3 records across 3 tables | Consolidate memory stores | HIGH |

## 28. TEST SUITE (§28)

| Finding | Original Evidence | Current Status | Current Evidence | Fix Required | Priority |
|---------|------------------|---------------|-----------------|-------------|----------|
| 3 TestIdentityAPI failures | Pre-existing — now fixed | RESOLVED | d97cc6e: all 12 pass, CI GREEN | — | — |
| Full suite times out | 4996 tests hang | BROKEN | Not re-verified | Investigate full suite hang | HIGH |
| No cross-tenant tests | Missing | GENUINELY MISSING | No tenant isolation tests | Add cross-tenant tests | LAUNCH BLOCKER |
| No failure injection tests | Missing | GENUINELY MISSING | No failure scenario tests | Add failure injection tests | HIGH |

---

## SUMMARY COUNTS

| Classification | Count |
|---------------|-------|
| VERIFIED COMPLETE | 8 |
| RESOLVED | 2 |
| PARTIAL | 10 |
| BACKEND_ONLY | 2 |
| UI_ONLY | 1 |
| DISCONNECTED | 4 |
| DUPLICATED | 8 |
| BROKEN | 5 |
| GENUINELY MISSING | 28 |
| NOT PROVEN | 14 |
| ENVIRONMENT BLOCKED | 2 |
| DEGRADED | 1 |
| **TOTAL FINDINGS** | **85** |

## LAUNCH BLOCKERS (12)

1. Identity — dual systems, no canonical authority
2. Signup — creates two unlinked records
3. Password reset — doesn't use canonical identity
4. Memory — no tenant isolation
5. Finance — no API, no payment chain, wrong UI
6. Auth roles — table empty
7. Auth permissions — table missing
8. User roles — table missing
9. No permission enforcement middleware
10. Tenant isolation not proven
11. No prompt injection protection
12. No backup/restore evidence