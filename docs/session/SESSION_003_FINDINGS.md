| SHUNYA — MASTER GAP & PENDING REGISTER (SUPERSET, ALL SOURCES)

**Date:** 2026-10-14 (consolidated; session 003 — CI fix + FK migration)
**Repository:** shunya-os/Shunya-OS @ master **07a1fae** (CI RED — see H9)
**Sources merged:** Previous register + session 003 findings
**Rule:** this document is the single umbrella register. Child registers stay authoritative for their own detail; nothing here is closed without evidence.

---

## NEW SESSION FINDINGS (2026-10-14, Session 003)

**CI state:** master is RED. Run 38518470577 — 4 failures rooted in commit 07a1fae (taxation engine). Root cause: 07a1fae added FounderObject/FounderSpace construction blocks to 3 files as FK workaround. The canonical model (R6B-2) declares founder_conversations FK → sh_objects, but production DB has FK → founder_objects — the migration was never applied.

**Fixes in PR #22** (fix/founderobject-regression-ci):
- Removed FounderObject creation blocks from app/ai/routes.py, app/founder/routes.py
- Replaced _ensure_founder_object with canonical ObjectService path in conversation_bridge.py
- 26/26 guard tests pass locally. Full suite running.

**Migration created:** r6b2_conversation_fk.py — backfills 12 orphan conversations, re-points FK → sh_objects.

**Credits inspection:** ErrorClass.CREDITS_REQUIRED exists at catalog level. HuggingFace flagged outage="credits_required". Final platform-wide billing link (F-001/D11) remains DEFERRED per founder.

---

| ID | Item | Status |
|----|------|--------|
| H9 | **master CI red (07a1fae)** — 4 failures from FounderObject regression | **FIX IN PR #22** — code fix applied, 26 targeted tests pass, full suite running. CI runner stuck on GitHub Actions (3 attempts failed) |
| H10 | **production FK mismatch** — founder_conversations FK points to founder_objects, model says sh_objects | **MIGRATION CREATED** — r6b2_conversation_fk.py handles orphans + FK change. Apply after PR #22 deploy |
| H11 | **12 orphan conversations** with no matching sh_objects row | Migration backfills these; must verify post-migration |
| H12 | **CI runner issue** — 3 consecutive runs on fix/founderobject-regression-ci stuck at setup phase | Runs on other branches/targets succeed. Possibly runner image drift or resource contention. Workaround: local full-suite run in progress |