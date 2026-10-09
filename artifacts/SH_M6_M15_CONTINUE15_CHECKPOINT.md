# SH-M6→M15 CONTINUE-15 CHECKPOINT — STAGE E4: the chat executes real business actions

Build at closure: 1a21eee (CI-25, SUCCESS — deployed; /health verified).

## What was found

The tool handlers registered at app startup (create_customer, create_supplier,
search_objects — validate → service → Outcome → canonical event) were
UNREACHABLE from the chat: the planner emitted only ANSWER/CLARIFY, and the
registered keys could not be produced by ActionType. Worse, the customer
handler wrote to the legacy ``customer`` table — ZERO rows in production, read
by no product surface — so a "created" customer would have been invisible in
the product. The canonical customer store is ``rel_relationships``
(CanonicalRelationship, organization-scoped; the import pipeline and the
Relationships UI both use it).

## What was implemented (E4)

1. ActionType gains CREATE_CUSTOMER / CREATE_SUPPLIER / SEARCH_OBJECTS
   (values match the registered handler keys → dispatchable).
2. Planner.detect_business_action: detects explicit create-requests from the
   raw message, extracts the name, records whether the SAME message carries an
   explicit confirmation word (single-turn confirmation; no hidden state).
3. Runtime confirmation gate: create-steps receive the authenticated
   organization + identity scope; WITHOUT confirmation the reply is a truthful
   preview ("Nothing has been created yet…") the create-step is REPLACED by a
   no-op answer (never executes) and reasoning-planned actions are stripped so
   the governed execution chain does not claim a completed action. WITH
   confirmation the handler runs and the reply reports exactly what happened
   (id, outcome id, event) — including truthful duplicates.
4. Handlers retargeted to the canonical stores: customer →
   CanonicalRelationship (dup-name check scoped to the org, truthful
   "already exists"); supplier → suppliers (org-scoped, dup-name check).
5. GJ-12 journey updated to pin the canonical contract (REST check via the
   authenticated /relationships/api/v1/relationships surface the UI consumes;
   org-scoping asserted on the canonical row).

## Honest observations (recorded, not hidden)

- Two Outcome rows arise per confirmed chat action: one from the tool handler
  (action outcome) and one from the governed execution chain's completion
  (create_outcome on success). Layered bookkeeping, both traceable; the reply
  cites the handler's outcome id, and the E4 test verifies THAT id exists in
  the ledger (traceability, not counts). Consolidating the two ledgers is a
  future increment, deliberately not done inside E4.
- For an unconfirmed preview the execution chain completes "failed" (the
  requested action did not execute) — truthful, if terse.
- The legacy /api/v1/customers/ API + Customer model remain (archive, not
  deleted); nothing in the product journey now depends on them for customers.

## Realtime test hardening — corrected root cause (important)

The intermittent CI failures of test_worker_a_to_worker_b_delivery were NOT a
client-side idle reconnect (redis-py 8 listen() blocks indefinitely; an
accelerated before/after probe came back INCONCLUSIVE and the mechanism claim
was retracted). TRUE root cause, found by reading the failure in the full-suite
context: earlier suite boots leak GLOBAL event-bus relays — SSEStreamManager
.start() starts a relay on the get_event_bus() singleton and stop() never
stops it — so PUBSUB NUMSUB reached 3 with only 2 FRESH relays subscribed.
The readiness gate (count >= 3) passed while the third fresh relay was still
connecting; the test published; Pub/Sub has no replay; the event was lost
forever. Fix (1a21eee): measure the subscriber-count BASELINE before starting
the fixture's relays and gate on the DELTA (baseline + WORKER_COUNT). Verified
locally with a simulated leaked subscriber held open (and the production app's
own relays subscribed): 24/24, three consecutive runs. The relay loop now also
polls get_message(timeout=...) instead of listen() (idle-live subscription,
prompt stop()), and a new idle-delivery invariant test publishes after 11s of
silence. The relay "leak" itself is left in place deliberately: the relay
belongs to the BUS (cross-worker delivery is wanted in production even without
SSE); the test-side gate is the correct fix.

## Evidence

### Live demo on the deployed build (1a21eee) — verified, not inferred

1. Chat: "create customer E4 Live Demo Co" → reply is the truthful preview
   ("I can create this customer: “E4 Live Demo Co”. Nothing has been created
   yet…"); production DB: zero rows for the name. Screenshot:
   STAGE_E4_LIVE_CONFIRM.png (preview + confirmed reply in the conversation).
2. Chat: "confirmed: create customer E4 Live Demo Co" → "Created customer
   “E4 Live Demo Co” (id 240). Recorded as outcome 3F116010101D and emitted to
   your event history."
3. Relationships workspace lists "E4 Live Demo Co / customer / active" —
   the created record is visible in the product (the exact gap E4 closes).
   Screenshot: STAGE_E4_LIVE_RELATIONSHIP.png.
4. Repeat of the confirmed message → "A customer named “E4 Live Demo Co”
   already exists (id 240) — nothing new was created." Screenshot:
   STAGE_E4_LIVE_DUPLICATE.png.
5. Production DB (read-only probe): exactly ONE rel_relationships row —
   id 240, type customer, organization_id 7, source ai_chat, created_by the
   authenticated identity; the cited outcome 3F116010101D exists in
   sh_outcomes with state.customer_id 240. The duplicate attempt wrote
   nothing.

### Supplier leg — live on the same build (6291795)

- Chat: "confirm: add supplier E4 Live Supply Co" → "Created supplier
  “E4 Live Supply Co” (id 14). Recorded as outcome 488E2EB6595A…"
- Duplicate retry → "A supplier named “E4 Live Supply Co” already exists
  (id 14) — nothing new was created."
- Production DB probe: exactly ONE suppliers row (id 14, tenant_id 7 — the
  organization, active) and outcome 488E2EB6595A exists with
  state.supplier_id 14. Screenshot: STAGE_E4_LIVE_SUPPLIER.png.

- tests/test_e4_chat_business_actions.py — 10 tests: detection (confirm/name
  trimming/negative/supplier), preview writes nothing, confirmed create lands
  in rel_relationships scoped to the org, reported outcome id exists, duplicate
  refused truthfully, supplier path.
- Journeys/ubme/fda regression: 160 passed (journey gj12 + e4 + ubme set).
- Live demo (post-deploy): preview → confirm → Relationships shows the row →
  duplicate refused. Screenshots to artifacts.
