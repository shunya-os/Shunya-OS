# Chat isolation repair — not full assistant certification

Authority: existing SHUNYA Constitution human agency/privacy/explainability;
Execution Doctrine fail-closed persistence and canonical ownership. No new runtime.

## Reproduced and repaired

Isolated authenticated HTTP regression tests reproduced cross-identity conversation
reads, appends and output attachment; shared conversation object identifiers;
missing-workspace acceptance; inference continuing after persistence failure.

The existing chat route now checks the authorized identity and organization,
verifies the canonical object's workspace, creates distinct objects via
ObjectService, persists messages before inference, and reports storage failure.
Canonical ObjectService inserts explicitly mark is_deleted=false: omitting it
caused a new conversation to disappear on continuation under SQLite.
Conversation outputs use portable JSON predicates and identity filtering.

Targeted suite: 16 passed at implementation checkpoint, including existing
conversation tests and new continuation/output readback tests. New tests replace
only inference with a unit-test responder; they exercise actual Flask decorators,
routes, ObjectService and isolated database persistence. This is NOT live AI quality
or browser acceptance evidence. Full regression and CI are separate gates.

## Preserved limits

- Existing legacy histories lacking canonical objects remain owner-readable for
  compatibility; they cannot continue through chat without valid canonical context.
  Full historical data reconciliation remains open.
- Authorization currently requires an organization; true organization-independent
  personal chat requires a canonical personal authorization path, not org_id=0.
- ObjectService commits its object before the conversation transaction. A later
  failure is reported, but atomic creation/idempotent recovery needs completion.
- Kernel/fallback budget enforcement, retrieval isolation, learning consent,
  full restart continuity and all other AI surfaces remain separate review items.
- This does not backfill the 167 NULL organization IDs or the 288 observed
  object/workspace organization mismatches from the restored snapshot.
- No paid inference, production fixture creation, or founding-data rewrite is
  used as verification. Authenticated founder browser validation remains open.

Project status: IN PROGRESS, not zero-error or complete.
