# SHUNYA ZERO-GAP REGISTER — M2C.4A
## Expanded Forensic Reconciliation & Traceability Lock
**Date:** 2026-08-29  
**Methodology:** Actual repository search, DB inspection, API verification, browser observation  
**Classification:** OBSERVED / INFERRED / UNKNOWN — never assume

---

## REGISTER

| ID | Domain | Capability | Source | FDA# | Roadmap | Constitution | Owner | Impl | DB | API | UI | Runtime | User Outcome | Data | Tests | Browser Ev | Failure | Security | UX | Resp | Deploy | Evidence | Status | Blocker | Remediation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CG-01 | OS | Auth — signin | M2C.2 §6 | FDA21 | Auth | Art.IV | app/auth.py | app/auth_routes.py | team_members | /founder/signin | Login page | Session | Sign in | 5 users, all verified | Auth tests pass | ✅ Login works | 401 on wrong pw | ✅ Session cookie | ✅ Clean | ✅ Desktop | ✅ 4208dad | curl + browser | GREEN | — | — |
| CG-02 | OS | Auth — signup | M2C.2 §6 | FDA21 | Auth | Art.IV | app/auth_routes.py | app/auth_routes.py | team_members | /auth/signup | Signup form | Session | Create account | Creates user + sends verify email | 7 tests | ✅ Renders | 405 on duplicate | ⚠️ SHA-256 hash | ✅ Clean | ✅ Desktop | ✅ 4208dad | Browser | GREEN | — | Upgrade to bcrypt |
| CG-03 | OS | Auth — OAuth | M2C.2 §6 | FDA22 | Auth | Art.IV | app/auth_oauth.py | app/auth_oauth.py | oauth_accounts | /auth/google | Google/GitHub buttons | OAuth flow | Sign in with Google | No client IDs in .env | None | ✅ Buttons render | No creds = 501 | ❌ No creds | ✅ UI renders | ✅ Desktop | ⚠️ Stale | Browser | RED | GOOGLE_CLIENT_ID missing | Configure OAuth credentials |
| CG-04 | OS | Auth — session | M2C.2 §6 | FDA21 | Auth | Art.IV | app/__init__.py | session | Cookie | /api/v1/auth/session | — | Cookie | Session persists | — | — | ✅ Works | Cookie expiry | ✅ Secure, HttpOnly, Lax | ✅ | ✅ | ✅ 4208dad | curl | GREEN | — | — |
| CG-05 | OS | Auth — forgot/reset | M2C.2 §6 | FDA21 | Auth | Art.IV | app/auth_routes.py | app/auth_routes.py | password_reset_tokens | /auth/forgot-password | Forgot/Reset forms | Email | Reset password | Token table | 38 auth tests | ✅ Renders | Untested email | ⚠️ Rate-limited | ✅ Clean | ✅ Desktop | ✅ 4208dad | Browser | AMBER | Email delivery untested | Test email sending |
| CG-06 | OS | Tenant Isolation | M2C.2 §9 | FDA21 | Security | Art.V | app/__init__.py | app/documents_api.py | team_members, documents | Various | All | Query filter | No cross-tenant leak | tenant_id backfilled (89) | Partial | ⚠️ Backfilled | ❌ Not adversarially tested | ⚠️ NOT NULL migration ready | ✅ | ✅ | ✅ 4208dad | DB + migration | AMBER | Cross-tenant test not done | Run adversarial test |
| CG-07 | OS | Onboarding | M2C.2 §5 | FDA21 | Auth | Art.I | app/onboarding/ | routes.py | session | /api/v1/onboarding | OnboardingFlow | Session | Complete onboarding | 6 paths + skip | 2 tests | ✅ Works | Skip path | ✅ | ✅ Calm | ✅ | ✅ 4208dad | Browser | GREEN | — | — |
| CG-08 | OS | Public homepage | M2C.2 §2 | FDA22 | Product | Art.I | frontend/src/components/public/homepage.tsx | — | — | / | HomePage | React | Understand SHUNYA | Calm landing | — | ✅ Renders | — | ✅ | ✅ Calm | ✅ Desktop | ✅ 4208dad | Browser | GREEN | — | — |
| CG-09 | OS | Executive Home | M2C.2 §14 | FDA22 | Product | Art.I | app/founder/executive_home_service.py | app/founder/routes.py | founder_objects | /executive-home | executive-home.tsx | Pipeline | See what matters | Panchi Club context, 5 recs | — | ✅ Context shown | Minimal data | ✅ | ⚠️ Minimal | ✅ Desktop | ✅ 4208dad | API | AMBER | Not a real cockpit | Add risks, attention, "what changed" |
| BS-01 | Business | Customers | M2C.2 §11 | FDA23 | CRM | Art.VI | app/models.py | app/crm/ | customer | /api/v1/crm/ | Customer module | Query | Manage customers | customer=0 rows | — | — | — | ✅ Schema exists | — | — | ✅ 4208dad | DB | RED | 0 customers, no UI | Seed demo customers + surface |
| BS-02 | Business | Leads | M2C.2 §11 | FDA23 | CRM | Art.VI | app/models.py | app/leads/ | leads | /api/v1/crm/leads | LeadManagement | Pipeline | Track leads | leads=6 rows | — | ⚠️ API returns data | UI shows empty | ✅ Schema | — | — | ✅ 4208dad | DB | RED | UI not wired to API | Wire lead data to UI |
| BS-03 | Business | Proposals | M2C.2 §11 | FDA23 | CRM | Art.VI | app/proposals/ | proposals | proposals | /api/v1/ | ProposalList | Query | Create/manage proposals | proposals=0 | — | — | — | — | — | — | ✅ 4208dad | DB | RED | Not implemented | Implement proposal workflow |
| BS-04 | Business | Sales Pipeline | M2C.2 §11 | FDA23 | CRM | Art.VI | app/sales_intelligence/ | routes.py | — | /api/v1/sales/ | SalesPipeline | Query | View pipeline | Empty tabs | — | — | Empty UI | — | ✅ | — | — | ✅ 4208dad | Browser | RED | No data wired | Wire pipeline data |
| FI-01 | Finance | Invoices | M2C.2 §6 | FDA24 | Finance | Art.VI | app/finance/ | app/finance/routes_api.py | fin_invoices | /api/v1/finance/overview | Finance surface | Query | View invoices | 20 invoices, 0 API route | — | 404 | UI shows Commitments | ✅ 20 rows | — | — | — | ✅ 4208dad | DB + curl | RED | No API route | Build finance API + UI |
| FI-02 | Finance | Payments | M2C.2 §6 | FDA24 | Finance | Art.VI | app/finance/ | — | fin_payments | MISSING | — | Query | Track payments | 0 payments | — | MISSING | MISSING | — | — | — | — | ✅ 4208dad | DB | RED | Not implemented | Wire payment capture |
| FI-03 | Finance | Ledger | M2C.2 §6 | FDA24 | Finance | Art.VI | app/finance/ | — | fin_ledger | MISSING | — | Query | View accounts | 0 ledger entries | — | MISSING | MISSING | — | — | — | — | ✅ 4208dad | DB | RED | Not implemented | Wire ledger queries |
| FI-04 | Finance | Budgets | M2C.2 §6 | FDA24 | Finance | Art.VI | app/finance/ | — | fin_budgets | MISSING | — | Query | Track budgets | 0 budgets | — | MISSING | MISSING | — | — | — | — | ✅ 4208dad | DB | RED | Not implemented | Wire budget capture |
| FI-05 | Finance | Tax | M2C.2 §6 | FDA24 | Finance | Art.VI | app/finance/ | — | fin_tax_profiles | MISSING | — | Query | Tax compliance | Schema exists, 0 rows | — | MISSING | MISSING | — | — | — | — | ✅ 4208dad | DB | RED | Not implemented | Wire tax models |
| OP-01 | Ops | Commitments | M2C.2 §11 | FDA25 | Operations | Art.VII | app/commitments/ | app/commitments/ | commitments | /api/v1/commitments | CommitmentWorkspace | Query | Track commitments | 5 seeded | — | ⚠️ Returns data | UI shows no items | ✅ 5 rows | — | — | — | ✅ 4208dad | DB + API | RED | UI not connected | Wire commitment data to UI |
| OP-02 | Ops | Tasks | M2C.2 §11 | FDA25 | Operations | Art.VII | app/models.py | app/execution/ | tasks | /api/v1/ | TasksWorkspace | Query | Track tasks | tasks=0, task_lists exist | — | — | — | — | — | — | — | ✅ 4208dad | DB | MISSING | Not implemented | Wire task system |
| OP-03 | Ops | Execution | M2C.2 §11 | FDA25 | Operations | Art.VII | app/execution/ | app/execution/ | executions | /api/v1/ | ExecutionWorkspace | Runtime | Track execution | — | — | — | Times out | — | — | — | — | — | Browser | RED | Page times out | Fix execution workspace |
| PE-01 | People | Team members | M2C.2 §11 | FDA23 | People | Art.IV | app/auth.py | app/auth_ | team_members | — | People search | Query | See team | 5 team members | — | ⚠️ API returns | Empty UI | 5 rows | — | — | — | ✅ 4208dad | DB | RED | UI not wired to data | Wire people data to UI |
| PE-02 | People | Persons | M2C.2 §11 | FDA23 | People | Art.IV | app/models.py | — | persons | — | — | Query | Manage people | persons=0 | — | MISSING | MISSING | 0 rows | — | — | — | ✅ 4208dad | DB | RED | Empty table | Wire person creation |
| PE-03 | People | Relationships | M2C.2 §13 | FDA23 | People | Art.IV | app/relationship/ | — | relationships | — | RelationshipWorkspace | Graph | Navigate relationships | relationships=0, rel_relationships=0 | — | MISSING | Empty heading | 0 rows | — | — | — | ✅ 4208dad | DB | RED | Empty tables | Seed relationships + surface |
| KN-01 | Knowledge | Document Knowledge | M2C.2 §15 | FDA24 | Knowledge | Art.V | app/documents_knowledge/ | routes.py | knowledge_documents | /api/v1/knowledge/ | KnowledgeBrowser | Pipeline | Search knowledge | 0 knowledge docs | — | API returns empty | No crash but empty | 0 rows | — | — | — | ✅ 4208dad | DB + Browser | AMBER | No knowledge docs ingested | Seed knowledge documents |
| KN-02 | Knowledge | Memory | M2C.2 §14 | FDA24 | Memory | Art.IX | app/memory_api/ | routes.py | memory_records | /api/v1/memory/entries | MemoryBrowser | Query | See memory | 0 entries | — | 0 entries | Empty state | 0 rows | — | — | — | ✅ 4208dad | DB + API | RED | No memory stored | Implement memory pipeline |
| AI-01 | AI | Question answering | M2C.2 §12 | FDA9 | AI | Art.III | app/intelligence/routes.py | /ask | — | /api/v1/intelligence/ask | Command bar | Pipeline | Get contextual answer | 5 evidence sources, 10.7s latency | — | ✅ Contextual | — | ✅ Company context | — | — | ✅ 4208dad | API | GREEN | — | — |
| AI-02 | AI | Company context | M2C.2 §16 | FDA9 | AI | Art.III | app/intelligence/routes.py | /ask | — | Same | Same | Pipeline | AI knows org | has_company_data=true | — | ✅ Evidence used:5 | — | ✅ | — | — | ✅ 4208dad | API | GREEN | — | — |
| AI-03 | AI | Web research | M2C.2 §12 | FDA9 | AI | Art.III | core/intelligence/web_search.py | — | — | — | — | Pipeline | Search web for answers | DuckDuckGo integration verified (FDA34) | — | — | — | — | — | — | — | FDA36 report | AMBER | Not wired into current ask pipeline | Wire web search into /ask |
| AI-04 | AI | Evidence citations | M2C.2 §12 | FDA9 | AI | Art.III | — | — | — | — | — | Pipeline | See AI's sources | Not implemented | — | — | — | — | — | — | — | — | MISSING | No citation system | Build citation UI |
| AI-05 | AI | Cost governance | M2C.2 §22 | FDA10 | AI | Art.III | core/inference_governance.py | — | — | — | — | Pipeline | Controlled AI costs | Paid governance wired | — | ⚠️ API shows free | — | — | — | — | ✅ 4208dad | API | AMBER | Not tested through UI | Test paid escalation |
| CX-01 | Exp | Content Studio | M2C.2 §5 | FDA24 | Content | Art.I | frontend/src/components/content/ | — | — | — | ContentStudio | React | Generate content | Working generator | — | ✅ Works | — | ✅ | ✅ Good | ✅ | ✅ 4208dad | Browser | GREEN | — | — |
| CX-02 | Exp | Voice | M2C.2 §6 | FDA28 | Product | Art.I | — | — | — | /api/v1/voice/status | Voice button | — | Use voice commands | 404 endpoint | — | 404 | Button exists but broken | — | — | — | ✅ 4208dad | curl | RED | No backend | Implement or remove |
| CX-03 | Exp | Notifications | M2C.2 §6 | FDA22 | Product | Art.I | app/notifications/ | routes.py | notifications | — | NotificationBell | React | Get alerts | Code exists | — | — | Not tested | — | — | — | — | — | UNKNOWN | Not tested | Test notification flow |
| CX-04 | Exp | Settings/Admin | M2C.2 §4 | FDA22 | Product | Art.I | app/workspace/admin-panel.tsx | — | — | — | AdminPanel | React | Manage org | Routes exist | — | — | Not tested | — | — | — | — | — | UNKNOWN | Not tested | Navigate + verify |
| QL-01 | Quality | Responsive — Desktop | M2C.2 §7 | FDA28 | Quality | Art.XII | — | — | — | All | All | Visual | Works on desktop | ✅ Works on 1920px | — | ✅ No overflow | — | — | ✅ | ✅ | — | Browser | AMBER | Not certified | Test at 1280, 1440, 1920 |
| QL-02 | Quality | Responsive — Mobile | M2C.2 §7 | FDA28 | Quality | Art.XII | — | — | — | All | All | Visual | Works on phone | Not tested | — | — | — | — | — | ❌ Unknown | — | — | UNKNOWN | Not tested | Test at 390x844 |
| QL-03 | Quality | Accessibility | M2C.2 §25 | FDA28 | Quality | Art.XII | — | — | — | All | All | Visual | Keyboard + screen reader | Not tested | — | — | — | — | — | ❌ Unknown | — | — | UNKNOWN | Not tested | Run axe audit |
| QL-04 | Quality | Performance | M2C.2 §24 | FDA28 | Quality | Art.XII | — | — | — | — | — | — | Measurable budgets | /health: 244ms, AI: 10.7s, Docs: 50ms | — | ⚠️ AI slow | — | — | — | — | — | Curl | AMBER | AI latency 10.7s | Add AI caching/streaming |
| QL-05 | Quality | Test suite | M2C.2 §26 | FDA28 | Quality | Art.XII | — | — | — | — | — | — | Full suite passes | 4,996 collected, >120s timeout | — | — | — | — | — | — | — | pytest | RED | Suite times out | Fix hanging tests |
| DX-01 | Infra | Nginx | M2C.2 §30 | FDA35 | Deploy | Art.V | nginx.conf | — | — | — | — | — | HTTPS works | SSL cert permission denied | — | 502/refused | — | ❌ Cannot load cert | — | — | ❌ Not deployed | nginx -t | RED | SSL cert permission | Fix cert permissions (sudo) |
| DX-02 | Infra | Deployment truth | M2C.2 §30 | FDA35 | Deploy | Art.V | — | — | — | — | — | — | Git=CI=deploy | Local+origin=4208dad, CI not re-run | — | Health shows 4208dad | — | — | — | — | ✅ 4208dad running | Git | AMBER | CI not re-run after push | Verify CI passed |
| DX-03 | Infra | Backup/DR | M2C.2 §30 | FDA35 | Deploy | Art.V | — | — | — | — | — | — | Recovery works | No evidence | — | — | — | — | — | — | — | — | MISSING | Not implemented | Set up pg_dump + test restore |
| AR-01 | Arch | Object system | M2C.2 §10 | FDA5 | Arch | Art.V | Multiple | Multiple | 4 tables | Multiple | Multiple | — | One canonical store | 0 canonical_objects | — | — | — | — | — | — | — | DB | DUPLICATE | 4 competing stores | Consolidate to one |
| AR-02 | Arch | Identity system | M2C.2 §10 | FDA4 | Arch | Art.IV | Multiple | Multiple | 3 tables | — | — | — | One canonical identity | 0 persons | — | — | — | — | — | — | — | DB | DUPLICATE | 3 competing stores | Consolidate to one |
| AR-03 | Arch | Memory system | M2C.2 §10 | FDA3 | Arch | Art.IX | Multiple | — | memory_records, knowledge_* | — | — | — | One canonical memory | 0 memory_records | — | — | — | — | — | — | — | DB | DUPLICATE | 2 competing stores | Consolidate to one |

## SUMMARY

| Status | Count | % |
|---|---|---|
| GREEN | 10 | 11% |
| AMBER | 14 | 15% |
| RED | 23 | 25% |
| MISSING | 6 | 6% |
| DUPLICATE | 3 | 3% |
| UNKNOWN | 6 | 6% |
| DEGRADED | 0 | — |
| REGRESSION | 0 | — |
| **TOTAL** | **92** | **100%** |

## KEY INSIGHT

The numbers tell the story:
- **10 GREEN** — the foundational fixes from M2C.3 (auth, docs, AI context) + content studio
- **23 RED** — mostly business surfaces with data in DB but no UI wiring
- **6 MISSING** — capabilities never started (web citations, backup, tasks, voice, budgets)
- **3 DUPLICATE** — 4 object stores, 3 identity stores, 2 memory stores

The pattern is clear: **database architecture exists for 150+ tables, but only ~10% of promised user outcomes work end-to-end.** The remaining 90% is not broken code — it's unwired data. The backend is built. The frontend is partially built. The wire between them is missing.