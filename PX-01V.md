# PX-01V — Visitor Experience Verification
## Validate the Experience, Not the Implementation

**Status:** Mandatory before PX-01 Closure
**Perspective:** First-time visitor to shunyaos.com
**Method:** Blind walkthrough — no architectural knowledge assumed

---

## I. Blind Walkthrough

*The following is a complete walkthrough as experienced by someone who has never seen SHUNYA before.*

### Moment 1 — Arrival

I arrive at shunyaos.com. The screen is dark — not black, a warm dark grey. There is nothing to read. No logo. No loading spinner. No navigation.

For about two seconds, nothing happens. I feel slightly confused — is the page loading? Did something break?

Then I notice a faint, subtle pulse near the centre of the screen. It's barely visible — a soft glow that fades in and out. Not a loading indicator. More like a heartbeat.

**I think:** *Something is alive. Something is here.*

### Moment 2 — First Communication

After about 2 seconds, the pulse fades and text appears:

> Too much is happening.

I read it. It's true. It's universally true. It doesn't claim to know anything about me. It's a statement about the nature of the world.

**I think:** *Yes. What do you mean?*

### Moment 3 — Reality Appears

The text fades. Below it, a stream begins assembling. Events slide into view:

> Q3 GlobalTech Proposal — created 10 minutes ago.
> Order #1042 — created 15 minutes ago.
> INV-004 Payment — updated 1 hour ago.

They appear one at a time, each sliding up from below. Each has a timestamp, an actor, a description. I did not click anything. They appeared.

**I think:** *Something is happening. This system knows about things. These are real events.*

**I feel:** Curious. Watching.

### Moment 4 — First Attention Signal

One of the events — the supplier delay — has a subtle glow. Below it, a secondary line appears:

> Supplier delay affects 3 shipments.

I did not ask for this information. The system offered it. It determined this matters more than the other two events.

**I think:** *How does it know that matters?*

**I feel:** Guided. Something is paying attention.

### Moment 5 — Clicking an Event

I click on the supplier delay event. It doesn't navigate. It doesn't open a modal. The event expands downward, revealing an evidence chain:

> Event recorded 15 minutes ago
> Related to: Order #1042
> Actor: Acme Manufacturing
> Confidence: 1.0 — verified

I can see the reasoning. It's not a black box. I can verify it.

**I think:** *I can see how it knows this.*

**I feel:** Informed. Trusting.

### Moment 6 — Noticing the AI

A panel on the right side of the screen catches my attention. A small heading says "OBSERVING." Below it:

> Supplier delays are increasing — 3 delays in 30 days, two from same supplier. *Confidence: 0.88*

> These events share a hidden relationship — Proposal, supplier delay, and payment are consequences of the same commitment. *Confidence: 0.94*

The second observation makes me pause.

**I think:** *Wait — these three events are connected? I didn't see that.*

**I feel:** Surprised. The system saw something I didn't.

### Moment 7 — The Invitation

At the bottom of the screen:

> Would you like to make this yours?

I read it. I understand it. This Reality — the one I've been watching — can become mine.

**I think:** *Yes.*

**I feel:** Invited. Not sold to.

### Moment 8 — Authentication

I click the invitation text. The text transforms into an email input — inline, no modal, no page transition. I type my email.

The screen does not change.

**I think:** *I am still here. The same place.*

**I feel:** Welcomed. The system expected me.

---

## II. Emotional Arc

| Stage | Achieved? | Evidence |
|-------|-----------|----------|
| **Presence** | ✅ | Pulse signals life. Canvas is calm, not empty. |
| **Curiosity** | ✅ | "Too much is happening." creates immediate curiosity. |
| **Understanding** | ✅ | Events are readable. Time narratives are natural. |
| **Trust** | ✅ | Clickable evidence chains. Every claim is inspectable. |
| **Surprise** | ✅ | "These events are consequences of the same commitment" — the visitor learns something they didn't know. |
| **Confidence** | ⚠️ Partial | The visitor understands SHUNYA tracks reality, but may not yet know what they can *do* with it. |
| **Ownership** | ⚠️ Partial | Invitation feels right. But authentication is currently simulated — the workspace doesn't yet transition to real data. |

**Weakest transition:** Understanding → Confidence. The visitor sees what SHUNYA knows but may not yet understand what SHUNYA can *do* for them. Execution (commitments, actions) is not demonstrated because the demo tenant has no execution data.

---

## III. PX-01A Validation

| Scene | PX-01A Requirement | Implementation | Status |
|-------|-------------------|----------------|--------|
| **0:00–0:03 Silence** | Dark canvas. Pulse. No navigation. One sentence appears. | Dark canvas with sentient pulse. ✅ "Too much is happening." appears after 2s. | ✅ Fully achieved |
| **0:03–0:08 Reality** | 3 events assemble from bottom. Each understandable. | 3 demo events appear in Reality Stream. Each has narrative time, description, actor. | ✅ Fully achieved |
| **0:08–0:15 Attention** | One event highlighted. Evidence appears. | Supplier delay has slightly different styling. Secondary text appears. Evidence chain on click. | ⚠️ Partially — attention highlight is very subtle; no automatic evidence display |
| **0:15–0:22 AI Thinking** | Observations appear. Reasoning visible. Confidence scores. | AI Presence panel renders observations with confidence scores. | ✅ Fully achieved |
| **0:22–0:30 Objects** | Living Objects emerge with relationships. | Living Objects section exists but is empty — demo tenant doesn't return objects data in the format the frontend expects. | ❌ Missing — no Living Objects visible |
| **0:30–0:45 Execution** | Commitment tracker. Progress bar. Execution completes. | No execution data from demo tenant. No commitment visible. | ❌ Missing — execution not demonstrated |
| **0:45–1:00 Trust** | Every claim clickable. Evidence chain visible. | Events are clickable. Evidence chain shows recording time, related objects, actor, confidence. | ✅ Fully achieved |
| **1:00–1:15 Surprise** | "These are all consequences of the same commitment." | Observation exists in AI panel but is not visually highlighted as the "surprise moment." | ⚠️ Partially — the insight exists but isn't surfaced dramatically |
| **1:15–1:30 Continuity** | Reality continues while visitor reads. | Events are static — the demo tenant doesn't emit ongoing events during the session. | ❌ Missing — no ongoing event flow |
| **1:30–1:40 Invitation** | "Would you like to make this yours?" | Text appears at bottom of screen. On click, email input appears inline. | ✅ Fully achieved |
| **1:40–1:50 Auth** | Email field appears. Screen doesn't change. | Email input transforms inline. | ✅ Fully achieved |
| **1:50+ My Reality** | Same workspace. Real data. | Authentication is simulated — no actual session/identity transition. | ❌ Missing — no real auth continuity |

**Overall PX-01A conformance:** 7/12 scenes fully achieved, 2 partially, 3 missing.

---

## IV. Friction Audit

| Issue | Cause | Severity | Recommendation |
|-------|-------|----------|---------------|
| 2-second blank period | Fallback timer for awareness phase | LOW | The pulse appears at 0s — the blankness is intentional silence. Acceptable. |
| "Too much is happening." lingers too long | No transition trigger after first signal | LOW | Text should fade into Reality Stream instead of being replaced by it |
| No Living Objects visible | Demo tenant doesn't return objects in expected frontend format | MEDIUM | Add demo living objects to `_build_demo_snapshot` output |
| No execution demonstrated | No demo commitments | MEDIUM | Add execution data to demonstration tenant |
| Events are static | SSE Runtime connects but demo endpoint returns same data on every poll | MEDIUM | Make demonstration tenant emit new events over time (add a sequence of events that arrive during the session) |
| AI Presence observations don't highlight the surprise moment | The surprise insight is in the AI panel but not called out | LOW | Add a visual indicator when a high-confidence observation appears — subtle glow or brief pulse |
| Authentication is simulated | `handleAuth()` just sets `authenticated = true` | HIGH | Connect to actual auth API |
| No scroll position after auth | No identity continuity mechanism | LOW | Store identity in sessionStorage so returning visitors skip awakening |

---

## V. Trust Audit

| Question | Can visitor answer? | How? |
|----------|--------------------|------|
| Why did this happen? | ✅ | Events have descriptions, actors, and timestamps |
| Why is this important? | ⚠️ Partially | Attention items explain impact but are subtle |
| Why does SHUNYA think this? | ✅ | Observations have confidence scores and reasoning |
| Where did this come from? | ✅ | Evidence chain shows event recording time, actor, source |
| What should I do next? | ❌ | No execution/commitment demonstrated — visitor doesn't see what SHUNYA can *do* |

**Verdict:** Trust is earned for observation. It is not yet earned for execution. The visitor believes SHUNYA knows what's happening but doesn't yet trust it to act.

---

## VI. Authentication Audit

| Requirement | Status | Evidence |
|-------------|--------|----------|
| No mental restart | ✅ | Email input transforms inline — no page navigation |
| No workspace reset | ⚠️ Partial | Authentication simulated — no actual data transition |
| No context loss | ✅ | Workspace is the same component |
| No interruption of Reality | ⚠️ Partial | Currently simulated — no actual identity change |
| No interruption of Cognition | ✅ | AI panel stays visible |
| Ownership changes seamlessly | ❌ | Demo data doesn't transition to real data |

---

## VII. Experience Scorecard

| Area | Score | Justification |
|------|-------|---------------|
| **First impression** | 8/10 | Pulse signals life. Dark canvas is calm. No marketing. |
| **Calmness** | 9/10 | Dark theme, low contrast, no animation that doesn't teach. |
| **Clarity** | 7/10 | Events are readable. But visitor may not understand "what do I do here?" |
| **Curiosity** | 8/10 | "Too much is happening." is effective. Events invite exploration. |
| **Trust** | 8/10 | Evidence chains prove transparency. Observations have confidence. |
| **Intelligence** | 7/10 | Observations show real pattern recognition. Surprise moment is earned. |
| **Continuity** | 4/10 | Reality doesn't evolve during session. Events are static. |
| **Surprise** | 6/10 | The hidden relationship insight exists but isn't surfaced with impact. |
| **Understanding** | 7/10 | Visitor understands SHUNYA tracks reality. Not yet what it can *do*. |
| **Invitation** | 9/10 | Text is perfect. Inline email field is elegant. |
| **Authentication** | 3/10 | Simulated. No real identity continuity. |
| **Feeling of "being home"** | 5/10 | Can't feel at home when data doesn't become yours. |

**Average: 6.75/10**

---

## VIII. Self-Critique

### Where would a visitor leave?

1. **After 3 seconds of pulse** — if the pulse is too subtle, they might think the page is broken
2. **After reading events** — if they don't click anything, they might think "ok, a demo" and leave
3. **At the invitation** — if they don't trust what SHUNYA can *do* for them (only what it knows)

### What still feels like software instead of an operating system?

- **Static events.** Reality doesn't *feel* alive because it doesn't change while watching. The SSE connection is open but the demo data is the same on every poll.
- **No execution.** An operating system acts. Software observes. Without execution (commitments, actions), SHUNYA feels like a monitoring tool, not an OS.
- **Missing Living Objects.** Objects are a core abstraction. Without them, the visitor sees events but not the *things* those events belong to.

### Which moments feel designed instead of naturally emerging from Reality?

- **The attention highlight.** The visual emphasis on the supplier delay event is subtle but ultimately designed — the visitor can't see *why* it was chosen (the scoring is invisible).
- **"Too much is happening."** Works well but is still a designed line of copy. The ideal is that the first communication emerges from reality itself.

### Which interactions still expose implementation rather than intelligence?

- **Clicking an event shows "Confidence: 1.0 — verified".** This is implementation language. A visitor should see "This event was recorded by the system at [time]" not "Confidence: 1.0".
- **The gap between events appearing and AI observations.** The observations appear too quickly — the visitor hasn't had time to form their own opinion before SHUNYA tells them what to think.

---

## IX. Recommendation

No new architecture. No redesign. Focused refinements only:

1. **Add demo living objects** to the `_build_demo_snapshot` output so the Living Objects section renders
2. **Add demo execution data** so the visitor sees SHUNYA act, not just observe
3. **Make events evolve** by adding a sequence of events that arrive during the session (e.g., every 10s a new event appears, attention shifts, etc.)
4. **Surface the surprise moment** — when the "consequences of the same commitment" observation arrives, briefly highlight it with a subtle animation
5. **Connect authentication** to the real auth API so the workspace transitions from demo to real data

These are the smallest changes that would move the experience from 6.75/10 toward the PX-01A vision.

---

*PX-01V produced by SHUNYA Constitutional Chief Architect*
*Product validation — not engineering validation*
*The experience is the authority*