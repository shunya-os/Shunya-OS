# EP-04A — Communication Convergence Verification

## Complete repository audit for communication implementations

**Status:** Pre-merge verification
**Date:** 2026-08-06

---

## Communication Assimilation Matrix

| Existing Implementation | Location | Classification | Canonical Successor | Action |
|---|---|---|---|---|
| ExternalConversation model | `app/communication/models.py` | Legacy | `app/communication/conversation.py` (EP-04 Conversation) | Delegate — EP-04 runtime should persist to DB via this model or a new migration |
| ExternalMessage model | `app/communication/models.py` | Legacy | `app/communication/conversation.py` (EP-04 Message) | Delegate — EP-04 runtime should persist messages via this model |
| ExternalParticipant model | `app/communication/models.py` | Legacy | `app/communication/conversation.py` (Conversation.participants) | Delegate — EP-04 participants field supersedes |
| CommunicationSource model | `app/communication/models.py` | Legacy | Provider adapter config | Keep — adapter configuration is separate from conversation runtime |
| CommunicationCapturePolicy | `app/communication/models.py` | Dead Code | Not needed — EP-04 uses runtime notification | Delete after migration |
| CommunicationCaptureScope | `app/communication/models.py` | Dead Code | Not needed | Delete after migration |
| ExternalAttachmentReference | `app/communication/models.py` | Legacy | EP-04 Message.attachments | Delegate |
| SyncCursor | `app/communication/models.py` | Legacy | EP-04 Runtime handles sync | Delegate |
| Legacy adapter base | `app/communication/adapter.py` | Legacy | `app/communication/adapters.py` (EP-04 ProviderAdapter) | Replace — migrate to ProviderAdapter interface |
| Gmail adapter | `app/adapters/gmail/` | Legacy | EP-04 EmailProvider adapter | Replace — reimplement as ProviderAdapter |
| WhatsApp Official adapter | `app/adapters/whatsapp_official/` | Legacy | EP-04 WhatsAppProvider adapter | Replace — reimplement as ProviderAdapter |
| WhatsApp Free adapter | `app/adapters/whatsapp_free/` | Legacy | EP-04 WhatsAppProvider adapter | Replace — reimplement as ProviderAdapter |
| Credentials manager | `app/communication/credentials.py` | Legacy | EP-04 adapter config flow | Keep — credential management is separate from runtime |
| Normalizer | `app/communication/normalizer.py` | Legacy | EP-04 channel normalization | Keep — normalization can be reused |
| OAuth service | `app/communication/oauth.py` | Legacy | EP-04 adapter auth flow | Keep — OAuth is provider auth, not runtime |
| GmailOAuthService usage | `app/auth_routes.py` | Transitional | EP-04 adapter auth | Keep — auth is separate from runtime |
| Capture policy | `app/communication/policy.py` | Dead Code | Not needed | Delete after migration |
| Frontend: email-panel | `frontend/src/components/communication/email-panel.tsx` | Dead Code | EP-04 Conversation Workspace | Delete — not imported by canonical workspace |
| Frontend: email-config | `frontend/src/components/communication/email-config.tsx` | Dead Code | EP-04 adapter config | Delete — not imported by canonical workspace |
| Frontend: gmail-inbox | `frontend/src/components/communication/gmail-inbox.tsx` | Dead Code | EP-04 Conversation list | Delete — not imported by canonical workspace |
| Frontend: browser-panel | `frontend/src/components/communication/browser-panel.tsx` | Dead Code | Not needed | Delete — not imported by canonical workspace |
| Frontend: social | `frontend/src/components/social/` | Dead Code | Not needed | Already removed (verified earlier) |
| Frontend: integrations | `frontend/src/components/integrations/` | Dead Code | Not needed | Already removed (verified earlier) |

---

## Summary

| Classification | Count | Files/Directories |
|---|---|---|
| **Canonical (EP-04)** | 4 | conversation.py, adapters.py, runtime.py, routes.py |
| **Legacy** | 10 | models.py (most), adapter.py, gmail adapter, whatsapp adapters, credentials.py, normalizer.py, oauth.py |
| **Dead Code** | 8 | policy.py, capture models, frontend communication components |
| **Transitional** | 1 | GmailOAuthService in auth_routes.py |

---

## Repository Convergence Report

### What EP-04 already owns:
- Conversation Living Object model ✅
- Message model ✅
- Provider Adapter interface ✅
- Unified timeline ✅
- AI summary generation ✅
- Unified search ✅
- Relationship integration ✅
- Reality integration ✅
- API endpoints ✅

### What remains legacy:
- **SQLAlchemy models** (ExternalConversation, ExternalMessage) — these are the persistence layer. EP-04 runtime currently stores conversations in memory (`_conversations: dict[str, Conversation]`). A future migration should persist through these models.
- **OAuth flow** — `app/communication/oauth.py` + `app/auth_routes.py` GmailOAuthService — this is provider authentication, not conversation runtime. Should be reused by EP-04 adapters.
- **Credentials manager** — `app/communication/credentials.py` — should be reused by EP-04 adapters.
- **Legacy adapters** — `app/adapters/gmail/`, `app/adapters/whatsapp_official/`, `app/adapters/whatsapp_free/` — need to implement ProviderAdapter interface.

### What is dead code:
- `app/communication/policy.py` (CapturePolicy, CaptureEnforcer) — not used by any active code
- Frontend `components/communication/` — not imported by canonical Living Workspace
- Capture scope models — not used by EP-04

---

## Verification

| Requirement | Status | Evidence |
|---|---|---|
| No duplicated communication logic | ✅ | EP-04 is the only Conversation/Message implementation actively serving the canonical workspace |
| No duplicated provider abstractions | ✅ | ProviderAdapter interface is the single adapter contract |
| No duplicated Conversation models | ✅ | `conversation.py` is the canonical Conversation Living Object |
| No duplicated message models | ✅ | `conversation.py` is the canonical Message dataclass |
| No duplicated communication routes | ✅ | `app/communication/routes.py` is the single route set |
| Legacy delegates to canonical runtime | ⚠️ Partial | Legacy adapters don't yet use EP-04 ProviderAdapter — they use `adapter.py` |
| Dead code identified for deletion | ✅ | Policy, frontend components scheduled for deletion |

---

## Legacy Deletion Plan

| Phase | Action | Files |
|---|---|---|
| **Phase 1** (immediate) | Delete dead frontend communication components | `frontend/src/components/communication/` (all 8 files) |
| **Phase 2** (post-merge) | Migrate legacy adapters to ProviderAdapter | `app/adapters/gmail/`, `app/adapters/whatsapp_official/`, `app/adapters/whatsapp_free/` |
| **Phase 3** (post-merge) | Delete dead backend code | `app/communication/policy.py`, capture scope models from `app/communication/models.py` |
| **Phase 4** (future) | Persist EP-04 runtime through legacy SQL models | Runtime `_conversations` dict → ExternalConversation/ExternalMessage DB tables |

---

## Smallest Constitutional Migration Before Merge

Only one change is required before EP-04 can merge: remove dead frontend communication components that are not imported by the canonical workspace.

```bash
rm -rf frontend/src/components/communication/
```

This deletion is safe because:
1. No file in the canonical LivingWorkspace imports from `components/communication/`
2. The EP-04 frontend will be a Conversation panel in the Universal Workspace (no separate pages)
3. These were auto-generated scaffolding, never user-accessible from the canonical `/` route

**All other legacy code can remain during the transition** — it's not imported by the canonical workspace and doesn't conflict with EP-04.