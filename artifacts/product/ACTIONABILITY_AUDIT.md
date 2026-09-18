# USER ACTIONABILITY AUDIT

For every major object/domain, can the user perform each action?
If an action intentionally does not apply, the reason is documented.

Last updated: 2026-09-18

Legend:
✅ = WORKS END TO END
🟡 = EXISTS BUT UNVERIFIED OR PARTIAL
🔴 = NOT IMPLEMENTED OR BROKEN
⚪ = DOES NOT APPLY (reason documented)

---

## 1. AUTHENTICATION

| Action | Status | Evidence | Notes |
|--------|--------|----------|-------|
| CREATE account | ✅ | Signup page, POST /api/v1/auth/signup | |
| SIGN IN (email) | ✅ | Login page, POST /api/v1/founder/signin | |
| SIGN IN (OAuth) | ✅ | OAuth buttons on login page | |
| RESET password | ✅ | Forgot/reset flow | |
| VERIFY email | ✅ | Verify endpoint | |
| ACCEPT invitation | ✅ | F-05 fixed, route exists | Not end-to-end journey tested |
| SIGN OUT | ✅ | | |

---

## 2. ONBOARDING

| Action | Status | Evidence | Notes |
|--------|--------|----------|-------|
| WELCOME screen | ✅ | step-welcome.tsx | |
| SET purpose | 🟡 | step-purpose.tsx | B-2 "Skip for now" unconfirmed |
| AUTO-CREATE objects | 🔴 | step-auto-objects.tsx | Orphaned step |
| IMPORT data during onboarding | 🔴 | step-import.tsx | Orphaned step |
| SET identity details | 🔴 | step-identity.tsx | Orphaned step |
| CREATE organization | ✅ | step-purpose or dedicated | |
| COMPLETE onboarding | ✅ | step-complete.tsx → localStorage flag | |
| CONTINUE after refresh | ✅ | B-3 fixed — URL says /onboarding | |
| RETURN after session restore | ✅ | Session check restores onboarding phase | |
| AUTHENTICATED REVISIT | ✅ | Cannot fall back to login | post-auth.ts |

---

## 3. GENERIC OBJECTS (sh_objects)

| Action | Status | Evidence | Notes |
|--------|--------|----------|-------|
| CREATE | 🟡 | POST /api/v1/objects | UI path exists? |
| VIEW | ✅ | GET /api/v1/objects/<type> | F-02 fixed |
| VIEW types | ✅ | GET /api/v1/objects/types | F-01 fixed |
| SEARCH | ✅ | GET /api/v1/objects?q= | F-03 fixed |
| LIST | ✅ | GET /api/v1/objects?limit= | |
| EDIT | 🟡 | PUT route exists | |
| RELATE | 🔴 | No UI for relationships | |
| ARCHIVE | 🟡 | Soft delete path | |
| RESTORE | 🔴 | | |
| TRASH | 🟡 | | |
| PERMANENT DELETE | 🔴 | | |
| RECOVER | 🔴 | | |
| SEE WHY IT EXISTS | 🔴 | No provenance UI | |
| SEE CURRENT STATE | 🟡 | Object display | |
| SEE WHAT CHANGED | 🔴 | No audit trail in UI | |
| CONTINUE AFTER REFRESH | ✅ | Object persists | |
| CONTINUE AFTER RESTART | ✅ | Object in DB survives | |

---

## 4. CRM LEADS

| Action | Status | Evidence | Notes |
|--------|--------|----------|-------|
| CREATE | 🟡 | CRM routes exist | Own table, not canonical |
| VIEW | 🟡 | | |
| EDIT | 🟡 | | |
| RELATE to other objects | 🔴 | | |
| ASK SHUNYA about | 🔴 | Not in AI context | |
| ARCHIVE | 🔴 | | |
| CONTINUE after refresh | 🟡 | | |

---

## 5. COMMITMENTS

| Action | Status | Evidence | Notes |
|--------|--------|----------|-------|
| CREATE | 🟡 | Commitment routes and UI | |
| VIEW | 🟡 | commitment-workspace.tsx | |
| EDIT | 🟡 | | |
| MARK COMPLETE | 🟡 | | |
| SEE OVERDUE | 🟡 | Warning in UI | |
| RELATE to objects | 🔴 | | |
| ASK SHUNYA about | 🔴 | | |
| CONTINUE after refresh | 🟡 | | |

---

## 6. DOCUMENTS / KNOWLEDGE

| Action | Status | Evidence | Notes |
|--------|--------|----------|-------|
| UPLOAD | 🟡 | /api/v1/upload | |
| VIEW | 🟡 | document-browser.tsx | |
| SEARCH by filename | 🟡 | | |
| SEARCH by meaning | 🔴 | No semantic classification | |
| CLASSIFY | 🔴 | No classification system | |
| RELATE to objects | 🔴 | | |
| ASK SHUNYA about | 🔴 | No document AI context | |
| DOWNLOAD | 🔴 | | |
| ARCHIVE | 🔴 | | |
| CONTINUE after refresh | 🟡 | | |

---

## 7. CONTENT GENERATION

| Action | Status | Evidence | Notes |
|--------|--------|----------|-------|
| CREATE (generate) | 🟡 | Content studio | |
| VIEW | 🟡 | | |
| EDIT | 🟡 | | |
| RENAME | 🔴 | | |
| DUPLICATE | 🔴 | | |
| DOWNLOAD | 🔴 | | |
| SEE DETAILS | 🟡 | | |
| RELATE to objects | 🔴 | | |
| ARCHIVE | 🟡 | | |
| RESTORE | 🔴 | | |
| TRASH / SOFT DELETE | 🟡 | | |
| PERMANENT DELETE | 🟡 | | |
| RECOVER | 🔴 | | |
| REGENERATE | 🟡 | | |
| SEE GENERATION METADATA | 🟡 | Provider, prompt saved | |
| CONTINUE after refresh | 🟡 | | |

---

## 8. AI / ASK SHUNYA

| Action | Status | Evidence | Notes |
|--------|--------|----------|-------|
| ASK a question | ✅ | AI panel works | Fixed F-04, F-06 |
| ASK about company data | 🔴 | Single-object context only | §7 missing |
| ASK using internet | ✅ | DuckDuckGo integration | |
| SEE answer provenance | 🟡 | Per-turn evidence exists | |
| SEE AI context | 🔴 | No context display | |
| EXECUTE an action | 🔴 | §8 not built | |
| CONTINUE after refresh | 🟡 | Conversation? | |
| CONTINUE after restart | 🟡 | | |

---

## 9. INGESTION

| Action | Status | Evidence | Notes |
|--------|--------|----------|-------|
| SELECT file | 🟡 | UI exists | |
| UPLOAD | 🟡 | /api/v1/upload | |
| ANALYZE | 🔴 | No analysis | |
| IDENTIFY content type | 🔴 | | |
| PREVIEW | 🔴 | | |
| CLASSIFY | 🔴 | | |
| CONFIRM/CORRECT | 🔴 | | |
| COMMIT to workspace | 🔴 | | |
| VERIFY it's in workspace | 🔴 | | |
| Partial ingestion recoverable | 🔴 | | |
| Duplicate handling | 🔴 | | |

---

## 10. ATTENTION (M9 — NOT BUILT)

| Action | Status | Notes |
|--------|--------|-------|
| SEE attention items | 🔴 | |
| UNDERSTAND why surfaced | 🔴 | |
| DISMISS | 🔴 | |
| DEFER | 🔴 | |
| CONTINUE after refresh | 🔴 | |

---

## 11. FAILURE / RECOVERY

| Action | Status | Notes |
|--------|--------|-------|
| RETRY on failure | 🔴 | |
| RESUME after interruption | 🔴 | |
| UNDO last action | 🔴 | |
| RESTORE from archive | 🔴 | |
| INSPECT failure details | 🔴 | |
| CORRECT a mistake | 🔴 | |
| DISMISS an error | 🔴 | |
| RECONNECT after disconnect | 🔴 | |

---

## 12. EMOTIONAL / HUMAN FEELING

| Action | Status | Notes |
|--------|--------|-------|
| EXPRESS feeling | 🔴 | Not built |
| HAVE SHUNYA UNDERSTAND | 🔴 | |
| CORRECT SHUNYA's interpretation | 🔴 | |
| HAVE feeling affect product | 🔴 | |
| DEFER without pressure | 🔴 | |

---

## 13. VISUAL / DEVICE

| Action | Status | Evidence |
|--------|--------|----------|
| USE on desktop | 🟡 | Not formally certified |
| USE on tablet | 🔴 | |
| USE on mobile | 🔴 | |
| USE with keyboard only | 🔴 | |
| USE with screen reader | 🔴 | |
| ZOOM browser | 🟡 | |
| REDUCE MOTION | 🟡 | data-reduced-motion attribute |

---

## 14. SECURITY BOUNDARIES

| Action | Status | Notes |
|--------|--------|-------|
| ACCESS my data only | 🟡 | Tenant isolation partially tested |
| ACCESS wrong org | 🟡 | Logic-level test, not DB isolation |
| ACCESS wrong workspace | 🟡 | |
| BYPASS frontend restrictions | 🟡 | Direct API calls gated |
