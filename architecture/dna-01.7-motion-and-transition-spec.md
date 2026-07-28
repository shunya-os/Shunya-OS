# Motion & Transition Specification (DNA-01.7)

**Status:** Design — Not Yet Ratified  
**Version:** 2.0  
**Dependency:** DNA-01 Device-Native Architecture

---

## 1. Motion Philosophy

SHUNYA has one motion language. The opening "शून्य" sequence — a slow, cinematic fade — establishes the visual vocabulary. Every subsequent transition inherits it.

Motion communicates continuity. The user should never feel they have moved between disconnected pages. Every transition is a chapter turn in the same book.

**Behavioural guarantee:** The user experiences transitions as connected, not as page changes. The animation language is consistent across the entire application.

## 2. The Canonical Transition

The opening sequence establishes the pattern:

1. **Stillness** (hold for purpose) — the moment before content appears
2. **शून्य** appears via fade — opacity only, no movement, no scaling
3. **Pause** — the user absorbs the emblem
4. **शून्य** departs via fade — same curve, same opacity-only approach
5. **Content** appears via fade — inheriting the same rhythm

**Behavioural guarantee:** Every transition that follows must use a subset of this vocabulary. No new curves, no different timings, no competing animation styles. The opening sequence is the reference for all motion.

## 3. Transition Vocabulary

SHUNYA has exactly three transition types:

### Fade (Primary)

**Used for:** Scene transitions, page changes, modal open/close, element appears

**Behaviour:**
- The element goes from invisible to visible (or vice versa) by changing opacity
- The change decelerates into its final state — it does not snap or sudden-stop
- No movement, no scaling, no rotation during the transition
- Duration: deliberate but not slow — perceptible as a transition, not as waiting

**Exceptions (faster durations):**
- Modals: quick (the user expects instant feedback)
- Tooltips: near-instant
- Reduced motion: no opacity animation, instant visibility

### Slide Up (Secondary)

**Used for:** Bottom sheets, dialogs on phone, panels

**Behaviour:**
- The element appears from below, moving upward a short distance while fading in
- The movement is subtle — the element was already at the bottom edge, it slides into view
- The element never slides from the left, right, or top (except toasts from top)
- Duration: faster than fade — this is a reveal, not a narrative transition

### Crossfade (Narrative)

**Used for:** Between scenes on the homepage, between narrative chapters

**Behaviour:**
- The departing scene fades out as the arriving scene fades in
- There is no gap — no frame where nothing is visible
- The arriving scene's fade-in starts slightly before the departing scene's fade-out completes
- The viewer feels a continuous narrative, not a sequence of slides

## 4. Prohibited Transition Types

These animation patterns are forbidden in all SHUNYA interfaces:

- Slide left/right (page turn metaphor — rejected)
- Scale transforms (zoom in/out — too dramatic)
- Rotate (decorative — no purpose)
- Bounce/spring (too playful — not SHUNYA)
- Scroll snap to sections (creates separate pages — anti-narrative)
- Parallax (decorative motion — creates motion sickness)
- Staggered reveals (different elements appearing at different times on the same scene — creates visual noise)
- Typewriter effect (too slow)
- Flash/glitch (too aggressive)

## 5. Scene Transition Rules (Homepage)

The homepage is a continuous narrative, not separate pages. All scene transitions must obey:

**1. Fade only** — No scroll snap. No slide. Each scene fades into the next as the user scrolls.

**2. Overlap** — Scene N begins fading out as Scene N+1 begins fading in. There is no gap where nothing is visible.

**3. The शून्य → Scene One transition** — This specific transition has been identified as defective. The current implementation:
- शून्य fades out abruptly
- Scene One appears suddenly
- The connection is lost

Correct behaviour:
- शून्य begins fading out
- After a short overlap, Scene One begins fading in
- The two overlap for a perceptible moment — the user feels the continuation
- Scene One reaches full opacity as शून्य completes its fade

**4. The five phases (Scene Five)** — Relationship, Proposal, Finance, Intelligence, CALM must feel like one chapter. Transition between phases:
- Faster fade (they are sub-sections of one narrative beat)
- Use opacity crossfade between phase elements
- Do not trigger a full scene transition between them
- The section heading "One Operating System" remains visible throughout

## 6. Interaction Micro-transitions

| Action | Behaviour |
|--------|-----------|
| Button hover | Subtle opacity change — the element acknowledges the cursor |
| Button active | Quick opacity change — immediate feedback |
| Card hover | Border or background change — signals interactivity |
| Input focus | Border/outline change — visible focus state |
| Dropdown open | Brief fade with minimal movement |
| Toast appear | Brief movement from the edge with fade |
| Tab switch | Fast crossfade between content panes |

## 7. Reduced Motion

When the user has indicated a preference for reduced motion:

- All transition and animation durations collapse — no element takes time to animate
- Elements that depend on animation for visibility must be visible at rest (no fade-in delay)
- Content that reveals on scroll must be visible immediately
- Pulsing/breathing elements must become static
- Shimmer/skeleton loading must become static (no movement)

**Behavioural guarantee:** Reduced motion mode is not a degradation — it is a peer experience. Every piece of content reaches the user without animation-based delay.

## 8. Transition Consistency Checklist

Every new interface element must pass:

- [ ] Does this use the canonical fade vocabulary?
- [ ] Is the duration appropriate — perceptible but not waiting?
- [ ] Is opacity the primary transform?
- [ ] Does it avoid prohibited animation types?
- [ ] Does it respect reduced motion preferences?
- [ ] Does the animation convey continuity, not separation?
- [ ] Is there a spatial reason for any movement?
- [ ] Does it match the language established by the शून्य opening?