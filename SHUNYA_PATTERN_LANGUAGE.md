# SHUNYA Pattern Language — Constitutional Behavioural Vocabulary

**Constitutional Layer:** Design Constitution → Pattern Language
**Status:** Frozen. Governs experience consistency across all SHUNYA surfaces.
**Conforms to:** SHUNYA Constitutional Architecture V1.0 (CANONICAL_ARCHITECTURE.md)

---

## Constitution of Patterns

Every recurring interaction pattern shall have exactly one canonical definition.

A pattern is valid only if it satisfies all of the following:

1. It serves a **constitutional purpose** (improves Understanding, Execution, Trust, or Adaptation)
2. It maps to **at least one** Founder Journey
3. It involves **at least one** Living Object
4. It visualizes **Reality** (never displays data without a reality anchor)
5. It exposes **AI cognition** where the founder is making a decision
6. It surfaces a **next action** (never leaves the founder stranded)
7. It has defined **failure** and **recovery** behaviour
8. It may never adopt a **forbidden behaviour**

No duplicate patterns may exist. If two surfaces need the same behaviour, they use the same pattern.

---

## Pattern Specification Template

Each pattern is defined by:

| Field | Meaning |
|-------|---------|
| **Purpose** | Why this pattern exists |
| **Experience Objective** | Which Experience question it answers |
| **Living Objects** | Which objects are involved |
| **Founder Journey** | Which journey(s) it serves |
| **Reality Visualized** | What real-world truth is shown |
| **AI Cognition Behaviour** | What SHUNYA is thinking/explaining |
| **Required CTA** | The next action surfaced |
| **Animation Behaviour** | Movement/transition rules |
| **Trust Behaviour** | How trust is built or maintained |
| **Failure Behaviour** | What happens on error |
| **Recovery Behaviour** | How it returns to normal |
| **Never Allowed** | Forbidden behaviours |
| **Constitutional Articles** | Which articles are satisfied |

---

## PATTERN 01 — Workspace

- **Purpose:** Manifest Reality relevant to the current human as a continuous, focused surface.
- **Experience Objective:** What does the founder now understand immediately? What became continuous?
- **Living Objects:** Workspace, all visible objects.
- **Founder Journey:** Every journey (workspace is the container).
- **Reality Visualized:** The current state of the founder's world.
- **AI Cognition Behaviour:** AI Presence stream shows current cognition relevant to this workspace.
- **Required CTA:** The next best action for the active object.
- **Animation Behaviour:** Spatial transitions; continuous, never page-load jumps.
- **Trust Behaviour:** Preserves exact context; founder never mentally restarts.
- **Failure Behaviour:** Workspace fails to load → show cached last-known-good state.
- **Recovery Behaviour:** Restore prior context and memory; no data loss.
- **Never Allowed:** Owning business logic, persistence, workflow, AI reasoning, or domain computation (Workspace Purity Law).
- **Constitutional Articles:** Workspace Constitution, Frontend Constitution, Navigation Constitution.

## PATTERN 02 — Workspace Transition

- **Purpose:** Move between workspaces or objects while preserving cognition and context.
- **Experience Objective:** What uncertainty disappeared? What became continuous?
- **Living Objects:** Workspace, destination object.
- **Founder Journey:** All journeys.
- **Reality Visualized:** The destination reality.
- **AI Cognition Behaviour:** Cognition state carries over; founder sees what was being thought.
- **Required CTA:** Continue the prior thread or start the new context.
- **Animation Behaviour:** Spatial slide/zoom; never hard `window.location.href` reload.
- **Trust Behaviour:** History preserves cognition; objects remain continuous.
- **Failure Behaviour:** Transition fails → remain on current workspace, no context loss.
- **Recovery Behaviour:** Return to prior workspace with full restored context.
- **Never Allowed:** Hard page navigation; context reset; mental restart for founder.
- **Constitutional Articles:** Navigation Constitution, Frontend Constitution.

## PATTERN 03 — Living Object Card

- **Purpose:** Present a Living Object as a compact, actionable, living representation.
- **Experience Objective:** What does the founder understand immediately?
- **Living Objects:** Any canonical object (Customer, Proposal, Invoice, etc.).
- **Founder Journey:** All object-bearing journeys.
- **Reality Visualized:** The object's current state and lifecycle stage.
- **AI Cognition Behaviour:** A small cognition line shows what SHUNYA understands about this object.
- **Required CTA:** Open object, or primary action on the object.
- **Animation Behaviour:** Subtle; card lifts on hover; state changes animate.
- **Trust Behaviour:** Shows source of truth and last-updated; never presents stale data as fresh.
- **Failure Behaviour:** Object fails to load → show known state + retry.
- **Recovery Behaviour:** Re-fetch object; preserve card position.
- **Never Allowed:** Displaying a datapoint without a reality anchor or next action.
- **Constitutional Articles:** Living Objects Constitution, Frontend Constitution.

## PATTERN 04 — Object Creation

- **Purpose:** Create a new Living Object through the universal lifecycle.
- **Experience Objective:** What work disappeared?
- **Living Objects:** The object being created (Customer, Proposal, etc.).
- **Founder Journey:** All journeys that begin an object.
- **Reality Visualized:** The new object anchored to reality.
- **AI Cognition Behaviour:** AI suggests fields/completes context; shows confidence.
- **Required CTA:** Commit creation.
- **Animation Behaviour:** Creation animates into the object graph.
- **Trust Behaviour:** Identity assigned immediately; object appears in graph.
- **Failure Behaviour:** Creation fails → preserve draft, show error with cause.
- **Recovery Behaviour:** Retry creation; never duplicate.
- **Never Allowed:** Skipping Identity Assignment or Reality Attachment.
- **Constitutional Articles:** Universal Object Lifecycle, Object Interaction Law.

## PATTERN 05 — Object Detail

- **Purpose:** Show the full reality of one Living Object with its relationships and history.
- **Experience Objective:** What became continuous? What does the founder understand?
- **Living Objects:** One canonical object.
- **Founder Journey:** All journeys that require deep object understanding.
- **Reality Visualized:** The object's full state, lifecycle stage, and related objects.
- **AI Cognition Behaviour:** Cognition panel explains the object's significance and options.
- **Required CTA:** Next action on the object.
- **Animation Behaviour:** Detail expands spatially; relationships animate.
- **Trust Behaviour:** Shows evidence, timeline, and rollback history (Object Interaction Law).
- **Failure Behaviour:** Detail fails → show summary + partial.
- **Recovery Behaviour:** Incremental load; never blank.
- **Never Allowed:** Hiding causation, evidence, or rollback history.
- **Constitutional Articles:** Object Interaction Law, Universal Object Lifecycle.

## PATTERN 06 — AI Thought

- **Purpose:** Expose a single unit of SHUNYA's current thinking.
- **Experience Objective:** What uncertainty disappeared? What does the founder understand?
- **Living Objects:** The object(s) the thought concerns.
- **Founder Journey:** Any journey where AI reasoning is needed.
- **Reality Visualized:** An observation/reasoning about reality.
- **AI Cognition Behaviour:** Shows observation, reasoning, confidence, alternatives, unknowns, remaining uncertainty.
- **Required CTA:** Acknowledge, act, or ask for more.
- **Animation Behaviour:** Thought streams in; confidence animates.
- **Trust Behaviour:** Confidence is stated; unknowns are explicit; never presented as certainty.
- **Failure Behaviour:** AI unavailable → show "thinking paused" not silence.
- **Recovery Behaviour:** Resume cognition; continue from last thought.
- **Never Allowed:** Presenting an AI thought as infallible; hiding confidence or unknowns.
- **Constitutional Articles:** Continuous Cognition, Experience Constitution.

## PATTERN 07 — AI Presence

- **Purpose:** Continuously show that SHUNYA is thinking alongside the founder.
- **Experience Objective:** What became continuous? What became calmer?
- **Living Objects:** All objects in the current workspace.
- **Founder Journey:** All journeys.
- **Reality Visualized:** Live cognition stream relevant to the workspace.
- **AI Cognition Behaviour:** Continuous publication of observations and reasoning.
- **Required CTA:** Engage with a thought or dismiss.
- **Animation Behaviour:** Calm, continuous presence; never intrusive.
- **Trust Behaviour:** Transparency; the founder always knows what SHUNYA is attending to.
- **Failure Behaviour:** Cognition stream pauses gracefully.
- **Recovery Behaviour:** Stream resumes with context preserved.
- **Never Allowed:** Random unsolicited interruptions with no relevance.
- **Constitutional Articles:** Continuous Cognition, Experience Constitution.

## PATTERN 08 — Reality Feed

- **Purpose:** Show the continuous stream of what is happening in reality.
- **Experience Objective:** What became continuous? What became calmer?
- **Living Objects:** All observed objects.
- **Founder Journey:** All journeys.
- **Reality Visualized:** The delta stream of Reality (events, changes, observations).
- **AI Cognition Behaviour:** Each feed item may carry an AI interpretation.
- **Required CTA:** Investigate a feed item or act on it.
- **Animation Behaviour:** Items stream in; new items animate without displacement.
- **Trust Behaviour:** Each item shows source, timestamp, causality, confidence, reversibility (Universal Event Law).
- **Failure Behaviour:** Feed stalls → show last event + reconnecting state.
- **Recovery Behaviour:** Reconnect; never lose events (queue for replay).
- **Never Allowed:** Anonymous events (Universal Event Law).
- **Constitutional Articles:** Observation, Universal Event Law.

## PATTERN 09 — Command Surface

- **Purpose:** Capture founder intent and route it to execution.
- **Experience Objective:** What work disappeared? What is the next action?
- **Living Objects:** The object the command targets.
- **Founder Journey:** All journeys (command is the accelerator).
- **Reality Visualized:** The action options relevant to current context.
- **AI Cognition Behaviour:** AI suggests the best next command with reasoning.
- **Required CTA:** Execute a command.
- **Animation Behaviour:** Command palette opens spatially; results animate.
- **Trust Behaviour:** Commands map to real actions; no dead paths.
- **Failure Behaviour:** Command fails → explain why, show cause.
- **Recovery Behaviour:** Offer alternative command or undo.
- **Never Allowed:** Interpreting intent independently of the object context; hard navigation.
- **Constitutional Articles:** Command Surface ownership, Navigation Constitution.

## PATTERN 10 — Execution Timeline

- **Purpose:** Show the progress of work through the execution lifecycle.
- **Experience Objective:** What became continuous? What became calmer?
- **Living Objects:** Execution, Commitment, Outcome.
- **Founder Journey:** Commitment Management, Customer Acquisition.
- **Reality Visualized:** Real progress of work toward outcome.
- **AI Cognition Behaviour:** AI flags risk, delays, next actions.
- **Required CTA:** Advance the execution or unblock it.
- **Animation Behaviour:** Steps complete with movement; timeline animates forward.
- **Trust Behaviour:** Shows evidence of completion; never claims done without evidence.
- **Failure Behaviour:** Execution blocked → show blocker + cause.
- **Recovery Behaviour:** Recovery path is explicit (retry, escalate, back off).
- **Never Allowed:** Showing completion without verified Outcome evidence.
- **Constitutional Articles:** Execution, Outcome, Execution Runtime contract.

## PATTERN 11 — Journey Progress

- **Purpose:** Show where the founder is within a complete journey.
- **Experience Objective:** What does the founder understand immediately?
- **Living Objects:** Journey, all journey objects.
- **Founder Journey:** The journey being displayed.
- **Reality Visualized:** Position along Reality→Understanding→Decision→Execution→Outcome→Learning.
- **AI Cognition Behaviour:** AI indicates the next journey stage and what's needed.
- **Required CTA:** Advance to next stage.
- **Animation Behaviour:** Journey progresses spatially through stages.
- **Trust Behaviour:** Stage completion is evidence-backed.
- **Failure Behaviour:** Journey stalls → show what's missing.
- **Recovery Behaviour:** Resume journey from last completed stage.
- **Never Allowed:** Suggesting a journey stage is complete without evidence.
- **Constitutional Articles:** Journey Constitution, Canonical Experience Pipeline.

## PATTERN 12 — Relationship Graph

- **Purpose:** Visualize the connections between Living Objects.
- **Experience Objective:** What does the founder understand immediately?
- **Living Objects:** All linked objects.
- **Founder Journey:** Knowledge Discovery, Customer Acquisition.
- **Reality Visualized:** The object graph as it exists in reality.
- **AI Cognition Behaviour:** AI highlights important or risky relationships.
- **Required CTA:** Navigate to a connected object.
- **Animation Behaviour:** Graph expands/collapses spatially; links animate.
- **Trust Behaviour:** Links show causality and evidence (Object Interaction Law).
- **Failure Behaviour:** Graph fails to load → show known nodes.
- **Recovery Behaviour:** Rebuild graph from object events.
- **Never Allowed:** Showing a relationship without causality/evidence.
- **Constitutional Articles:** Object Graph, Object Interaction Law.

## PATTERN 13 — Search

- **Purpose:** Find a specific object or knowledge across the system.
- **Experience Objective:** What work disappeared? What uncertainty disappeared?
- **Living Objects:** All searchable objects and knowledge.
- **Founder Journey:** Knowledge Discovery.
- **Reality Visualized:** Matching reality objects.
- **AI Cognition Behaviour:** AI interprets the query intent and ranks results with reasoning.
- **Required CTA:** Open a result.
- **Animation Behaviour:** Results stream in; query refines dynamically.
- **Trust Behaviour:** Results show source and confidence; no fabricated answers.
- **Failure Behaviour:** No results → show "not found in reality" + alternatives.
- **Recovery Behaviour:** Suggest broader or corrected query.
- **Never Allowed:** Presenting a guessed/unsourced answer as fact.
- **Constitutional Articles:** Search ownership, Memory, Understanding.

## PATTERN 14 — Notification

- **Purpose:** Alert the founder to something that needs attention.
- **Experience Objective:** What became continuous? What became calmer?
- **Living Objects:** The object the notification concerns.
- **Founder Journey:** All journeys.
- **Reality Visualized:** A real change or event requiring attention.
- **AI Cognition Behaviour:** AI explains why this matters and suggested action.
- **Required CTA:** Act on the notification or dismiss.
- **Animation Behaviour:** Notification appears calmly; unread state is clear.
- **Trust Behaviour:** Notification links to evidence and source.
- **Failure Behaviour:** Notification fails to deliver → requeue.
- **Recovery Behaviour:** Re-deliver; never lose important events.
- **Never Allowed:** Anonymous notifications (Universal Event Law); notification spam.
- **Constitutional Articles:** Notification ownership, Universal Event Law.

## PATTERN 15 — Trust Explanation

- **Purpose:** Explain why SHUNYA believes or recommends something.
- **Experience Objective:** What uncertainty disappeared? What became calmer?
- **Living Objects:** The object the explanation concerns.
- **Founder Journey:** Any decision-bearing journey.
- **Reality Visualized:** The evidence and reasoning behind a belief.
- **AI Cognition Behaviour:** Full explainability: reasoning, confidence, alternatives, unknowns.
- **Required CTA:** Accept, challenge, or adjust.
- **Animation Behaviour:** Explanation unfolds; evidence links animate.
- **Trust Behaviour:** Complete transparency; nothing hidden.
- **Failure Behaviour:** Explanation unavailable → say so, don't fake it.
- **Recovery Behaviour:** Rebuild explanation when evidence available.
- **Never Allowed:** Hiding reasoning; presenting opaque AI decisions.
- **Constitutional Articles:** Continuous Cognition, Trust, Explainable Intelligence.

## PATTERN 16 — Decision Review

- **Purpose:** Present a decision for founder review before or after commitment.
- **Experience Objective:** What uncertainty disappeared? What became calmer?
- **Living Objects:** Decision, Commitment.
- **Founder Journey:** Commitment Management, Customer Acquisition.
- **Reality Visualized:** The decision, its options, and consequences.
- **AI Cognition Behaviour:** AI recommends with reasoning and confidence; never decides for founder.
- **Required CTA:** Approve, reject, or modify the decision.
- **Animation Behaviour:** Decision options animate; consequences preview.
- **Trust Behaviour:** Decision recorded with evidence (Decision Runtime contract).
- **Failure Behaviour:** Decision cannot be recorded → return to draft.
- **Recovery Behaviour:** Re-submit decision; no loss.
- **Never Allowed:** Decision Runtime executing its own decision.
- **Constitutional Articles:** Decision Runtime contract, Object Interaction Law.

## PATTERN 17 — Approval

- **Purpose:** Route a decision to an authorized approver.
- **Experience Objective:** What became calmer? What became clearer?
- **Living Objects:** Decision, Organization, Identity (approver).
- **Founder Journey:** Commitment Management, Customer Acquisition.
- **Reality Visualized:** The item awaiting approval and its context.
- **AI Cognition Behaviour:** AI summarizes the approval request with evidence.
- **Required CTA:** Approve, reject, or request changes.
- **Animation Behaviour:** Approval flow animates; status updates.
- **Trust Behaviour:** Shows who approved, when, and on what evidence.
- **Failure Behaviour:** Approval fails to submit → preserve request.
- **Recovery Behaviour:** Re-submit approval.
- **Never Allowed:** Bypassing permission resolution (Universal Object Lifecycle).
- **Constitutional Articles:** Permission Resolution, Organization.

## PATTERN 18 — Payment

- **Purpose:** Complete a financial transaction with full traceability.
- **Experience Objective:** What became calmer? What became continuous?
- **Living Objects:** Invoice, Payment, Customer.
- **Founder Journey:** Customer Acquisition.
- **Reality Visualized:** The payment status and amount in reality.
- **AI Cognition Behaviour:** AI flags payment risk or next steps.
- **Required CTA:** Confirm payment or view status.
- **Animation Behaviour:** Payment status animates (pending → paid → reconciled).
- **Trust Behaviour:** Full transaction evidence, timeline, reversibility.
- **Failure Behaviour:** Payment fails → show reason, no silent failure.
- **Recovery Behaviour:** Retry or refund path is explicit.
- **Never Allowed:** Silent payment failure; hiding fees or status.
- **Constitutional Articles:** Payment object, Execution, Object Interaction Law.

## PATTERN 19 — Undo

- **Purpose:** Reverse the last action safely.
- **Experience Objective:** What became calmer? What uncertainty disappeared?
- **Living Objects:** The object affected by the undone action.
- **Founder Journey:** All journeys.
- **Reality Visualized:** The pre-action state being restored.
- **AI Cognition Behaviour:** AI confirms the scope of the undo.
- **Required CTA:** Confirm the undo.
- **Animation Behaviour:** State visibly reverts.
- **Trust Behaviour:** Rollback history is preserved (Object Interaction Law).
- **Failure Behaviour:** Undo unavailable → state is irreversible, say so.
- **Recovery Behaviour:** Maintain rollback history for future undo.
- **Never Allowed:** Undoing a mutating action without rollback history.
- **Constitutional Articles:** Object Interaction Law, State Fabric.

## PATTERN 20 — Error Recovery

- **Purpose:** Recover gracefully from any failure without data loss.
- **Experience Objective:** What became calmer? What uncertainty disappeared?
- **Living Objects:** The object affected by the error.
- **Founder Journey:** All journeys.
- **Reality Visualized:** The failure and its cause relative to reality.
- **AI Cognition Behaviour:** AI explains the error and offers recovery options.
- **Required CTA:** Retry, escalate, or recover.
- **Animation Behaviour:** Error state is clear, calm, non-alarming.
- **Trust Behaviour:** Error is honest; no fabricated success.
- **Failure Behaviour:** System fails → show last-known-good + cause.
- **Recovery Behaviour:** Recovery path is explicit per runtime contract.
- **Never Allowed:** Pretending a failure was a success.
- **Constitutional Articles:** Runtime Failure/Recovery Behaviour contracts.

## PATTERN 21 — Loading

- **Purpose:** Show progress toward a complete state without blocking understanding.
- **Experience Objective:** What became calmer?
- **Living Objects:** The object being loaded.
- **Founder Journey:** All journeys.
- **Reality Visualized:** Partial reality with a clear path to full.
- **AI Cognition Behaviour:** AI may show partial cognition during load.
- **Required CTA:** None while loading (or a useful action on partial data).
- **Animation Behaviour:** Skeleton/continuous; never a blank flash.
- **Trust Behaviour:** Honest loading; never shows fake data.
- **Failure Behaviour:** Load times out → error recovery pattern.
- **Recovery Behaviour:** Retry with backoff.
- **Never Allowed:** Blank screen; fake "loaded" data.
- **Constitutional Articles:** Frontend Constitution, Loading state.

## PATTERN 22 — Empty State

- **Purpose:** Guide the founder when no objects exist yet.
- **Experience Objective:** What work disappeared? What is the next action?
- **Living Objects:** The absent object type.
- **Founder Journey:** The journey that would create these objects.
- **Reality Visualized:** Honest "nothing here yet."
- **AI Cognition Behaviour:** AI suggests the first action to create reality.
- **Required CTA:** Create the first object.
- **Animation Behaviour:** Calm, inviting; never a dead blank.
- **Trust Behaviour:** Honest emptiness + clear path forward.
- **Failure Behaviour:** n/a (empty state is complete).
- **Recovery Behaviour:** n/a.
- **Never Allowed:** A blank screen with no next action.
- **Constitutional Articles:** Frontend Constitution, CTA requirement.

## PATTERN 23 — Background Execution

- **Purpose:** Run long tasks while the founder continues working.
- **Experience Objective:** What became continuous? What waiting disappeared?
- **Living Objects:** Execution, the object being processed.
- **Founder Journey:** All journeys with heavy work.
- **Reality Visualized:** The background task's real progress.
- **AI Cognition Behaviour:** AI reports progress and flags issues.
- **Required CTA:** Monitor, or continue other work.
- **Animation Behaviour:** Task progresses in background; completion notifies.
- **Trust Behaviour:** Progress is real and honest.
- **Failure Behaviour:** Background task fails → notify with cause.
- **Recovery Behaviour:** Retry or resume from checkpoint.
- **Never Allowed:** Pretending a background task succeeded.
- **Constitutional Articles:** Execution Runtime, Background Execution.

## PATTERN 24 — Memory Review

- **Purpose:** Review what SHUNYA remembers about the founder and their world.
- **Experience Objective:** What became continuous? What uncertainty disappeared?
- **Living Objects:** Memory object.
- **Founder Journey:** All journeys.
- **Reality Visualized:** Accumulated observations and knowledge.
- **AI Cognition Behaviour:** AI explains what it remembers and why.
- **Required CTA:** Correct, confirm, or clear a memory.
- **Animation Behaviour:** Memories surface calmly.
- **Trust Behaviour:** Full transparency; founder controls memory.
- **Failure Behaviour:** Memory retrieval fails → show known subset.
- **Recovery Behaviour:** Restore memory from store.
- **Never Allowed:** Hiding what SHUNYA remembers; using memory without consent context.
- **Constitutional Articles:** Memory, Learning, Trust.

## PATTERN 25 — Continuous Presence

- **Purpose:** Maintain a calm, always-with-you companion feel.
- **Experience Objective:** What became continuous? What became calmer?
- **Living Objects:** All workspace objects.
- **Founder Journey:** All journeys.
- **Reality Visualized:** That SHUNYA is actively attending to reality.
- **AI Cognition Behaviour:** Continuous low-key cognition visible.
- **Required CTA:** Engage when the founder wishes.
- **Animation Behaviour:** Calm ambient indicators; never intrusive.
- **Trust Behaviour:** Presence is honest and non-alarming.
- **Failure Behaviour:** Presence drops → graceful pause.
- **Recovery Behaviour:** Presence resumes.
- **Never Allowed:** Intrusive, irrelevant, or alarming presence.
- **Constitutional Articles:** AI Presence, Experience Constitution.

## PATTERN 26 — Outcome Summary

- **Purpose:** Show the verified result of an execution.
- **Experience Objective:** What became clear? What uncertainty disappeared?
- **Living Objects:** Outcome, Execution.
- **Founder Journey:** Commitment Management, Customer Acquisition.
- **Reality Visualized:** The completed outcome and its evidence.
- **AI Cognition Behaviour:** AI summarizes outcome and draws lessons.
- **Required CTA:** Acknowledge, act, or learn.
- **Animation Behaviour:** Outcome completes with verified movement.
- **Trust Behaviour:** Outcome shown only with evidence (no fabrication).
- **Failure Behaviour:** Outcome incomplete → show as incomplete.
- **Recovery Behaviour:** Continue execution toward verified outcome.
- **Never Allowed:** Declaring an outcome complete without verification.
- **Constitutional Articles:** Outcome Engine, Learning.

## PATTERN 27 — Conversation

- **Purpose:** Sustain a business dialogue with full context.
- **Experience Objective:** What became continuous? What work disappeared?
- **Living Objects:** Conversation, participants.
- **Founder Journey:** Customer Acquisition.
- **Reality Visualized:** The dialogue and its real-world stakes.
- **AI Cognition Behaviour:** AI summarizes, suggests, and tracks intent.
- **Required CTA:** Reply, or advance the conversation.
- **Animation Behaviour:** Messages stream; context persists.
- **Trust Behaviour:** Conversation history preserved; no context loss.
- **Failure Behaviour:** Send fails → preserve draft.
- **Recovery Behaviour:** Re-send; no duplicates.
- **Never Allowed:** Losing conversation context.
- **Constitutional Articles:** Conversation object, Navigation Constitution.

## PATTERN 28 — Knowledge Card

- **Purpose:** Present a stored fact or insight cleanly.
- **Experience Objective:** What does the founder understand immediately?
- **Living Objects:** Knowledge object.
- **Founder Journey:** Knowledge Discovery.
- **Reality Visualized:** A fact anchored to reality and source.
- **AI Cognition Behaviour:** AI relates the knowledge to current context.
- **Required CTA:** Apply, save, or explore.
- **Animation Behaviour:** Card reveals smoothly.
- **Trust Behaviour:** Knowledge shows source and confidence.
- **Failure Behaviour:** Knowledge unavailable → say so.
- **Recovery Behaviour:** Re-fetch from knowledge store.
- **Never Allowed:** Presenting unverified knowledge as fact.
- **Constitutional Articles:** Knowledge Store, Understanding.

## PATTERN 29 — Calendar Event

- **Purpose:** Show time-bound reality and commitments.
- **Experience Objective:** What became continuous? What became calmer?
- **Living Objects:** Commitment, Execution, Journey.
- **Founder Journey:** All scheduling-bearing journeys.
- **Reality Visualized:** Real scheduled events.
- **AI Cognition Behaviour:** AI flags conflicts and suggests times.
- **Required CTA:** Confirm, reschedule, or act.
- **Animation Behaviour:** Calendar updates smoothly.
- **Trust Behaviour:** Events link to real objects.
- **Failure Behaviour:** Sync fails → show last-known schedule.
- **Recovery Behaviour:** Re-sync.
- **Never Allowed:** Showing a schedule disconnected from its objects.
- **Constitutional Articles:** Commitment, Execution.

## PATTERN 30 — Document

- **Purpose:** Present or edit a persisted artifact.
- **Experience Objective:** What work disappeared?
- **Living Objects:** Document object.
- **Founder Journey:** All document-bearing journeys.
- **Reality Visualized:** The document's content and version.
- **AI Cognition Behaviour:** AI assists drafting, summarising, editing.
- **Required CTA:** Save, share, or act on the document.
- **Animation Behaviour:** Editing is fluid; autosave is calm.
- **Trust Behaviour:** Version history and rollback preserved.
- **Failure Behaviour:** Save fails → keep draft, no loss.
- **Recovery Behaviour:** Re-save; never lose work.
- **Never Allowed:** Silent save failure; losing authored content.
- **Constitutional Articles:** Document object, Lifecycle (Historical Preservation).

## PATTERN 31 — Media

- **Purpose:** Present rich media (images, video, audio) with context.
- **Experience Objective:** What does the founder understand immediately?
- **Living Objects:** Document/Media object.
- **Founder Journey:** All journeys.
- **Reality Visualized:** The media as it relates to reality.
- **AI Cognition Behaviour:** AI describes/references the media.
- **Required CTA:** View, share, or act.
- **Animation Behaviour:** Media loads smoothly.
- **Trust Behaviour:** Media is honest and sourced.
- **Failure Behaviour:** Media fails → show placeholder + retry.
- **Recovery Behaviour:** Re-fetch from CDN.
- **Never Allowed:** Misrepresenting media.
- **Constitutional Articles:** Object Runtime, Media.

## PATTERN 32 — Reports

- **Purpose:** Present aggregated reality insight.
- **Experience Objective:** What does the founder understand immediately?
- **Living Objects:** Multiple objects aggregated.
- **Founder Journey:** Knowledge Discovery.
- **Reality Visualized:** Aggregated truth, not fabricated numbers.
- **AI Cognition Behaviour:** AI explains trends and anomalies.
- **Required CTA:** Drill in, export, or act.
- **Animation Behaviour:** Data animates; drill-down is spatial.
- **Trust Behaviour:** Numbers trace to underlying objects.
- **Failure Behaviour:** Report fails → show available subset.
- **Recovery Behaviour:** Recompute report.
- **Never Allowed:** Fabricating or rounding away reality.
- **Constitutional Articles:** Reports, Understanding.

## PATTERN 33 — Dashboard

- **Purpose:** Give an at-a-glance continuous view of the founder's world.
- **Experience Objective:** What does the founder understand immediately?
- **Living Objects:** All workspace objects.
- **Founder Journey:** All journeys.
- **Reality Visualized:** Current state of many objects at once.
- **AI Cognition Behaviour:** AI surfaces what needs attention.
- **Required CTA:** Act on the most important item.
- **Animation Behaviour:** Live updates flow calmly.
- **Trust Behaviour:** Data is live and sourced.
- **Failure Behaviour:** Widget fails → isolated; others continue.
- **Recovery Behaviour:** Widget recovers independently.
- **Never Allowed:** A dashboard that hides what needs attention.
- **Constitutional Articles:** Frontend Constitution, Attention.

## PATTERN 34 — Approval Queue

- **Purpose:** Manage a list of items awaiting founder approval.
- **Experience Objective:** What became calmer? What is the next action?
- **Living Objects:** Decisions, Approvals.
- **Founder Journey:** Commitment Management.
- **Reality Visualized:** Real pending decisions.
- **AI Cognition Behaviour:** AI prioritizes the queue by importance.
- **Required CTA:** Approve, reject, or defer each item.
- **Animation Behaviour:** Queue items animate; status updates.
- **Trust Behaviour:** Each item links to evidence.
- **Failure Behaviour:** Queue fails → show cached items.
- **Recovery Behaviour:** Re-fetch queue.
- **Never Allowed:** Hiding items behind a dead queue.
- **Constitutional Articles:** Approval, Decision.

## PATTERN 35 — Quick Action

- **Purpose:** Execute a common action with minimal effort.
- **Experience Objective:** What work disappeared?
- **Living Objects:** The object the action targets.
- **Founder Journey:** All journeys.
- **Reality Visualized:** The action and its effect on reality.
- **AI Cognition Behaviour:** AI confirms the right action for context.
- **Required CTA:** Execute.
- **Animation Behaviour:** Action is fast and immediate.
- **Trust Behaviour:** Action effects are visible and reversible.
- **Failure Behaviour:** Action fails → explain, no side effect.
- **Recovery Behaviour:** Undo or retry.
- **Never Allowed:** A quick action that hides its consequences.
- **Constitutional Articles:** Command Surface, Execution.

## PATTERN 36 — Onboarding

- **Purpose:** Guide a new identity into their first workspace.
- **Experience Objective:** What uncertainty disappeared?
- **Living Objects:** Identity, Organization, Workspace.
- **Founder Journey:** Identity Onboarding.
- **Reality Visualized:** The founder's real context being established.
- **AI Cognition Behaviour:** AI learns and adapts to the founder.
- **Required CTA:** Complete each onboarding step.
- **Animation Behaviour:** Progressive, guided, calm.
- **Trust Behaviour:** Nothing is lost; identity is permanent.
- **Failure Behaviour:** Step fails → guide recovery.
- **Recovery Behaviour:** Resume onboarding from last step.
- **Never Allowed:** Creating an identity without Identity Assignment.
- **Constitutional Articles:** Identity Onboarding journey, Universal Object Lifecycle.

## PATTERN 37 — Permission Gate

- **Purpose:** Enforce authorization before sensitive actions.
- **Experience Objective:** What became calmer? What became trustworthy?
- **Living Objects:** Identity, Organization, the object being protected.
- **Founder Journey:** All journeys with protected actions.
- **Reality Visualized:** Who may act and why.
- **AI Cognition Behaviour:** AI explains the permission context.
- **Required CTA:** Request access or authenticate.
- **Animation Behaviour:** Gate appears calmly.
- **Trust Behaviour:** Permission resolution is explicit (Lifecycle).
- **Failure Behaviour:** Access denied → explain why.
- **Recovery Behaviour:** Guide to the correct permission path.
- **Never Allowed:** Silently bypassing permissions.
- **Constitutional Articles:** Permission Resolution, Authorization.

## PATTERN 38 — Retry

- **Purpose:** Safely retry a failed operation.
- **Experience Objective:** What became calmer?
- **Living Objects:** The object of the failed operation.
- **Founder Journey:** All journeys.
- **Reality Visualized:** The persistent goal and progress.
- **AI Cognition Behaviour:** AI suggests the best retry strategy.
- **Required CTA:** Retry.
- **Animation Behaviour:** Retry is calm, with backoff.
- **Trust Behaviour:** No duplicate side effects.
- **Failure Behaviour:** Retry fails → escalate.
- **Recovery Behaviour:** Backoff and escalate per runtime contract.
- **Never Allowed:** Duplicate side effects on retry.
- **Constitutional Articles:** Runtime Failure/Recovery Behaviour.

## PATTERN 39 — Notification Preference

- **Purpose:** Let the founder control what reaches them.
- **Experience Objective:** What became calmer?
- **Living Objects:** Identity, Notification.
- **Founder Journey:** All journeys.
- **Reality Visualized:** What the founder will be notified about.
- **AI Cognition Behaviour:** AI recommends notification settings.
- **Required CTA:** Save preferences.
- **Animation Behaviour:** Preferences apply live.
- **Trust Behaviour:** Founder controls their attention.
- **Failure Behaviour:** Preference save fails → keep prior.
- **Recovery Behaviour:** Re-save.
- **Never Allowed:** Overriding founder notification preferences.
- **Constitutional Articles:** Notification, Experience Constitution.

## PATTERN 40 — Object Archival

- **Purpose:** Move an object to read-only archival state.
- **Experience Objective:** What became calmer?
- **Living Objects:** Any object being archived.
- **Founder Journey:** All journeys with object lifecycle.
- **Reality Visualized:** The object's archival status.
- **AI Cognition Behaviour:** AI confirms the archival and its effect.
- **Required CTA:** Confirm archival or recover.
- **Animation Behaviour:** Object moves to archived state.
- **Trust Behaviour:** Archival is reversible (Recovery).
- **Failure Behaviour:** Archival fails → object stays active.
- **Recovery Behaviour:** Restore from archival.
- **Never Allowed:** Permanent deletion without explicit Retirement.
- **Constitutional Articles:** Universal Object Lifecycle.

## PATTERN 41 — Collaboration

- **Purpose:** Enable multiple identities to work on shared reality.
- **Experience Objective:** What became continuous?
- **Living Objects:** Organization, shared objects.
- **Founder Journey:** All journeys.
- **Reality Visualized:** Shared reality and presence.
- **AI Cognition Behaviour:** AI coordinates shared understanding.
- **Required CTA:** Collaborate, comment, or act.
- **Animation Behaviour:** Presence indicators animate.
- **Trust Behaviour:** Changes are attributed and evidence-backed.
- **Failure Behaviour:** Collaboration fails → changes preserved.
- **Recovery Behaviour:** Re-sync shared state.
- **Never Allowed:** Unattributed changes (Universal Event Law).
- **Constitutional Articles:** Collaboration, Universal Event Law.

## PATTERN 42 — Feedback Loop

- **Purpose:** Let founder learning flow back into the system.
- **Experience Objective:** What became continuous?
- **Living Objects:** Memory, Outcome, Journey.
- **Founder Journey:** All journeys.
- **Reality Visualized:** The lesson learned.
- **AI Cognition Behaviour:** AI incorporates feedback into learning.
- **Required CTA:** Confirm the lesson.
- **Animation Behaviour:** Learning updates apply.
- **Trust Behaviour:** Feedback is transparent and reversible.
- **Failure Behaviour:** Feedback fails → preserve.
- **Recovery Behaviour:** Re-apply feedback.
- **Never Allowed:** Silently ignoring founder feedback.
- **Constitutional Articles:** Learning, Experience Constitution.

---

## Pattern → Journey → Object Traceability Matrix

| Pattern | Founder Journey | Primary Living Object |
|---------|----------------|----------------------|
| Workspace | All | Workspace |
| Workspace Transition | All | Workspace |
| Living Object Card | All | Any object |
| Object Creation | All | Created object |
| Object Detail | All | Any object |
| AI Thought | All | Any object |
| AI Presence | All | Workspace |
| Reality Feed | All | Observations |
| Command Surface | All | Any object |
| Execution Timeline | Commitment, Acquisition | Execution |
| Journey Progress | All | Journey |
| Relationship Graph | Discovery, Acquisition | Relationship |
| Search | Knowledge Discovery | Knowledge |
| Notification | All | Any object |
| Trust Explanation | All (decision-bearing) | Decision |
| Decision Review | Commitment, Acquisition | Decision |
| Approval | Commitment, Acquisition | Decision |
| Payment | Customer Acquisition | Payment |
| Undo | All | Any object |
| Error Recovery | All | Any object |
| Loading | All | Any object |
| Empty State | All | Absent object |
| Background Execution | All (heavy work) | Execution |
| Memory Review | All | Memory |
| Continuous Presence | All | Workspace |
| Outcome Summary | Commitment, Acquisition | Outcome |
| Conversation | Customer Acquisition | Conversation |
| Knowledge Card | Knowledge Discovery | Knowledge |
| Calendar Event | All (scheduling) | Commitment |
| Document | All (document work) | Document |
| Media | All | Media |
| Reports | Knowledge Discovery | Aggregated objects |
| Dashboard | All | All objects |
| Approval Queue | Commitment Management | Decision |
| Quick Action | All | Any object |
| Onboarding | Identity Onboarding | Identity |
| Permission Gate | All (protected) | Any object |
| Retry | All | Any object |
| Notification Preference | All | Notification |
| Object Archival | All | Any object |
| Collaboration | All | Organization |
| Feedback Loop | All | Memory |

Every pattern maps to at least one journey and one Living Object. No pattern is orphaned.

---

**END OF PATTERN LANGUAGE — 42 canonical patterns**

*This document standardizes behaviour only. It introduces no architecture, no runtime ownership, and no features. It conforms to CANONICAL_ARCHITECTURE.md.*