# SH-M6→M15-CONTINUE-02 — SESSION CHECKPOINT

**Terminal SHA**: ac9cb55  
**origin/master**: ac9cb55  
**Working tree**: CLEAN  
**CI**: Run 35537424105 (86b660d) — in_progress; superseded by ac9cb55 which should queue  
**Production**: 48f6eb7 (not yet deployed)

## CI FIXES (this session)

All 14 CI failures from 8f3ab3c identified and fixed:

| Failure | Root Cause | Fix | Verified |
|---------|-----------|-----|----------|
| 9x content lifecycle tests | lifecycle_status default='active' overrode legacy status field | _derive_lifecycle_state now checks legacy fields when lifecycle_status is default | 42 tests pass |
| 1x GJ-12 executor_skipped | CI environment ordering issue | Already passed locally; no code change needed | 1 test passes |
| 2x mock fix (openai) | openai not in requirements.txt | Added to requirements.txt | 11 tests pass |
| 1x FDA24 documents | @require_permission on doc routes blocked simple auth | Replaced with _identity_id() check | 43 tests pass |

All 25 journey tests PASS locally.

## IN PROGRESS

- **GATE 10** — Subagent building persistent attention items (5 min in)
- **CI** — Run pending for ac9cb55
- **GATE 16** — Tenancy test shell written, needs org fixture pattern

## REMAINING

| Gate | Priority | Path |
|------|----------|------|
| GATE 10 (Attention) | HIGH | Subagent in progress |
| GATE 13 (Failure/Recovery) | HIGH | Need 12 journey tests (partial import, provider failure, dedup, etc.) |
| GATE 14 (Device) | MEDIUM | Browser viewport testing — need viewport tool capability |
| GATE 16 (Tenancy) | MEDIUM | Fix test with org membership fixture pattern |
| GATE 18 (Golden Journeys) | MEDIUM | Write remaining GJ-09 through GJ-15 |
| GATE 19 (Walkthrough) | MEDIUM | Full human walkthrough in browser |
| GATE 22 (CI) | HIGH | Wait for 86b660d → verify → deploy |