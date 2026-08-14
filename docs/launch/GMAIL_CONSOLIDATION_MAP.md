# Gmail Canonical Consolidation — Dependency Map

**Date:** 2026-08-14  
**Status:** Before consolidation

---

## GMAIL PATHS

### Path 1: Canonical — GmailAdapter (PRODUCTION)
- **File:** `app/integration/gmail_adapter.py`
- **Class:** `GmailAdapter(EmailProvider)` 
- **Registration:** `IntegrationRegistry.register("gmail", GmailAdapter())`
- **Methods:** connect, disconnect, fetch_emails, send_email, refresh_auth, normalize
- **Used by:** IntegrationRegistry (potential), OAuth flow
- **Status:** Canonical production path. Has basic MIME extraction. Missing full email→object pipeline.

### Path 2: Transitional — gmail_ingest (PARALLEL)
- **File:** `app/integration/gmail_ingest.py`
- **Functions:** get_gmail_service, fetch_emails, _extract_email_data, _extract_body, email_to_object, ingest_emails, link_threads
- **Used by:** `app/intelligence/awareness_api.py` (POST /ingest/gmail)
- **Status:** Parallel path. Has better MIME/body extraction. Has full email→object pipeline (identity→evidence→conversation). Should be absorbed into canonical.

### Path 3: Phase 3 — GmailAdapter (LEGACY)
- **File:** `app/adapters/gmail/__init__.py`, `app/adapters/gmail/client.py`
- **Class:** `GmailAdapter(CommunicationAdapter)`, `GmailClientInterface`, `RealGmailClient`, `FakeGmailClient`
- **Methods:** normalize, normalize_history, sync_initial, sync_incremental
- **Used by:** No production code references found
- **Status:** Orphaned legacy adapter. Not referenced from any production code path.

### Path 4: email_store.py (DEVELOPMENT-ONLY)
- **File:** `backend/core/email/email_store.py`
- **Storage:** JSON file at `data/email_store.json`
- **Functions:** save_email, get_all
- **Used by:** `backend/integrations/google/gmail_client.py`
- **Status:** Development-only JSON store. NOT production truth. Must be quarantined.

### Path 5: OAuth infrastructure (CANONICAL)
- **File:** `app/communication/oauth.py`
- **Class:** `GmailOAuthService`
- **Used by:** `app/auth_routes.py` (OAuth routes)
- **Status:** Canonical OAuth path. Works correctly.

### Path 6: SMTP Email (CANONICAL)
- **File:** `app/communication/email_core.py`, `app/communication/email.py`
- **Status:** Canonical SMTP path. Separate from Gmail API.

---

## CONSOLIDATION PLAN

1. Move MIME/body extraction from `gmail_ingest._extract_body` into canonical `GmailAdapter.normalize`
2. Move email→object pipeline (identity→evidence→conversation) into canonical adapter
3. Update `/ingest/gmail` endpoint to use canonical adapter
4. Add deprecation warning to `gmail_ingest.py`
5. Add deprecation warning to `email_store.py`
6. Verify Phase 3 adapter is orphaned
7. Test: fresh ingestion, duplicate, MIME parsing, identity resolution, evidence

---

## ARCHITECTURE: After Consolidation

```
Gmail API
    ↓
GmailOAuthService (OAuth)
    ↓
GmailAdapter (canonical)
    ↓
  normalize() — MIME/body extraction (from gmail_ingest)
  ingest() — identity→evidence→conversation (from gmail_ingest)
    ↓
IdentityService → Identity record
    ↓
EvidenceRecord → evidence_records table
    ↓
Conversation → communication records
    ↓
Memory/Intelligence → memory_records
```