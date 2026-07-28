# Homepage Narrative Flow Specification (DNA-01.8)

**Status:** Design — Not Yet Ratified  
**Dependency:** DNA-01 Device-Native Architecture, DNA-01.7 Motion & Transition Spec

---

## 1. Current Defects

The audit identified these specific defects in the current homepage (homepage.tsx):

1. **शून्य → Scene One transition is abrupt** — The intro sequence fades out, then Scene One appears. There is no continuity between "before" and "after."

2. **Scene Five (phases) is over-separated** — Relationship, Proposal, Finance, Intelligence, CALM each occupy their own full-viewport section. The user scrolls through five disconnected pages instead of one cohesive chapter.

3. **Vertical rhythm is inconsistent** — Scene padding varies between 2rem and 4rem with no narrative reason.

4. **The six-principle summary grid is disconnected** — It appears as an afterthought below the phases, with no visual or narrative relationship to them.

5. **Footer is disconnected** — It follows Scene Six with no transition. The user suddenly arrives at a footer.

## 2. Narrative Architecture (Redesigned)

The homepage is a single, continuous story with three acts:

```
ACT I:   Identity (Scenes 0–1)
ACT II:  The Question (Scenes 2–4)  
ACT III: The Answer (Scene 5)
CLOSING: Invitation (Scene 6 + Footer)
```

### Act I — Identity

**Scene 0 (शून्य):** 3.2s sequence
- 0.5s black (stillness, anticipation)
- 1.0s शून्य fade in (ease-out, opacity only)
- 1.5s hold (absorb)
- 0.8s शून्य fade out + **0.3s later** Scene One begins fade in
- 0.5s overlap where शून्य is departing and "One Operating System" is arriving
- **This overlap is the critical fix** — without it, the two scenes feel disconnected

**Scene One (Identity):** First scroll stop
- "One Operating System" — full visibility, fade complete
- Tagline + body text fade in sequentially with 200ms stagger between them
- No scroll snap — the scene is already partially faded in from the overlap

### Act II — The Question

**Scene Two (The Question):** Continuous from Scene One
- The question quote is visible at the bottom of Scene One's viewport
- Stats cards appear as the user scrolls further
- Transition: Scene One content fades out (0.6s) while Scene Two fades in (0.8s)
- Overlap: 0.3s

**Scene Three (Demonstration):** Particles + Question
- Particles are positioned at the boundary of Scene Two
- As Scene Two fades, particles have already started their float animation
- The question "What if your data never needed to be organised?" is the narrative pivot

**Scene Four (Invitation):** Company name input
- Full viewport, minimal
- The input appears centred, no other content visible
- CTA appears when company name is entered
- "Begin" scrolls to Act III

### Act III — The Answer

**Scene Five (The Answer — reworked):**

This is the section identified as defective. The current five separate phases must become ONE continuous chapter.

**Before (defective):**
```
[Full viewport] Relationship
[Full viewport] Proposal  
[Full viewport] Finance
[Full viewport] Intelligence
[Full viewport] CALM
[Full viewport] Summary grid
```

**After (corrected):**
```
[Section heading: "One Operating System"]
[Section subtitle: remains visible throughout the chapter]

=== Phase block: ===
[Relationship] -> 200px scrolling
[Proposal]    -> 200px scrolling  
[Finance]     -> 200px scrolling
[Intelligence]-> 200px scrolling
[CALM]        -> 200px scrolling

[Summary grid: inline, same scroll context]
```

Specifications:

1. **Section heading** "One Operating System" is pinned at the top of the viewport during the entire chapter. It only fades out when the user scrolls past the summary grid.

2. **Phase cards** are compact (200px height each) with tighter vertical rhythm (12px gap between phases, down from full viewports).

3. **Icon + text layout** is preserved but at a smaller scale — consistent with the device's typography matrix.

4. **Transition between phases** is a 300ms crossfade (faster than full scene transitions because these are sub-sections of one narrative beat).

5. **Summary grid** follows immediately after CALM with no full-viewport gap. It appears as the conclusion of the chapter, not a separate section.

6. **Total scroll distance** for the entire chapter: approximately 1,200px (down from 3,000px+), fitting within 1.5–2 viewport scrolls on desktop, 2–3 on mobile.

### Closing — Invitation + Footer

**Scene Six:** Full viewport CTA
- शून्य emblem (smaller than intro, referencing it)
- "The operating system your business deserves"
- CTA: "Begin" (same destination as Scene Four's button)
- "No credit card. No setup call."

**Footer:** Continuous fade from Scene Six
- As Scene Six scrolls up, the footer crossfades in
- No gap, no horizontal rule — just a gentle transition

## 3. Vertical Rhythm Specification

| Element | Top Margin | Bottom Margin | Notes |
|---------|-----------|--------------|-------|
| Scene One padding | 2rem | 2rem | Studio Experience; clamp to 1.5rem Compact |
| Scene Two padding | 3rem | 2rem | Slightly more breathing for quote |
| Scene Three padding | 2rem | 2rem | Particles need room |
| Scene Four padding | 3rem | 3rem | Input needs focus space |
| Scene Five heading | 2rem | 0.5rem | Tight — heading is pinned |
| Phase card gap | 0 | 12px | Compact, connected |
| Summary grid top | 1.5rem | 2rem | Conclusion spacing |
| Scene Six padding | 3rem | 3rem | CTA needs breathing |
| Footer padding | 2rem | 2rem | Match brand presence |

All values are desktop defaults. Scale per device typography matrix.

## 4. Motion Sequence for Each Scene

| Transition | Type | Duration | Overlap | Notes |
|-----------|------|----------|---------|-------|
| Black → शून्य | Fade in | 1.0s | — | Pure ease-out |
| शून्य → One OS | Crossfade | 0.8s out + 0.8s in | 0.3s overlap | **Key fix** |
| One OS → Question | Crossfade | 0.6s out + 0.8s in | 0.3s overlap | |
| Question → Demo | Crossfade | 0.6s out + 0.8s in | 0.3s overlap | Particles persist |
| Demo → Invitation | Crossfade | 0.6s out + 0.8s in | 0.3s overlap | |
| Invitation → Act III | Scroll-driven fade | 0.5s | 0.2s | Smooth transition |
| Phase transitions (within Scene Five) | Crossfade | 0.3s out + 0.3s in | 0.1s overlap | Fast — same chapter |
| Act III → Scene Six | Crossfade | 0.6s out + 0.8s in | 0.3s | |
| Scene Six → Footer | Crossfade | 0.6s out + 0.6s in | 0.2s | Subtle |

## 5. Responsive Scene Adjustments

| Scene | Studio | Shared | Compact |
|-------|---------|--------|--------|
| Scene zero | Full screen | Full screen | Full screen, smaller text |
| Scene one | 2rem padding, fluid-3xl | 1.5rem, fluid-2xl | 1rem, fluid-xl |
| Scene two | 2rem padding | 1.5rem | 1rem, 2-column stats |
| Scene three | Full screen particles | Full screen, fewer particles | Compact, 15 particles |
| Scene four | 300px input | 250px input | Full-width input |
| Scene five phases | 200px each | 180px each | 150px each |
| Summary grid | 3 columns | 2 columns | 1 column, stacked |
| Scene six | 60vh + CTA | 50vh | 40vh |
| Footer | Inline | Inline | Stacked |

## 6. Verifiability Criteria

Before ratification, the homepage must pass:

- [ ] Record the शून्य → Scene One transition at 30fps. Is there an overlapping crossfade for at least 300ms? [Y/N]
- [ ] Measure the scroll distance of Scene Five. Is it ≤ 1,500px on desktop? [Y/N]
- [ ] Record any scene transition at 30fps. Does it use the canonical ease-out curve? [Y/N]
- [ ] Check for scroll snap between scenes. Is it absent? [Y/N]
- [ ] Toggle `prefers-reduced-motion: reduce`. Do all animations stop? [Y/N]
- [ ] On mobile viewport (375×812), does any content clip or overflow? [Y/N] (must be N)
- [ ] On desktop viewport (1440×900), is there excessive whitespace? [Y/N] (must be N)
- [ ] Is the "One Operating System" heading pinned during the phase scroll? [Y/N]
- [ ] Can the user visually identify five phases? [Y/N]
- [ ] Does the footer feel connected to Scene Six? [Y/N]