# Learning Engine — Engineering Summary

**Engine:** Learning Engine (ES-007)
**Layer:** Learning
**Phase:** Phase 2 (Learning Layer)
**Status:** Draft specification

---

## One-Page Summary

### What It Is

The Learning Engine transforms verified observations into long-term improvement. It is the engine that closes the Compounding Intelligence Loop. It analyzes observations, discovers patterns, correlates outcomes with context, calibrates confidence scores, and produces governance-validated proposals for knowledge updates, policy improvements, and confidence calibration.

### Position in the Pipeline

```
Observer → [Learning Engine] → Governance → Knowledge / Policy Update → (next cycle)
```

### How It Works

The Learning Engine follows a 9-stage pipeline:

1. **Learning Intake** — Receive and validate observations and learning signals
2. **Pattern Discovery** — Identify recurring patterns across observations
3. **Correlation Analysis** — Correlate with context, action types, channels
4. **Outcome Evaluation** — Evaluate outcome quality against objectives
5. **Confidence Calibration** — Adjust confidence scores based on accuracy
6. **Improvement Recommendation** — Generate actionable recommendations
7. **Knowledge Proposal** — Package as concrete knowledge update proposals
8. **Governance Review Package** — Package for validation
9. **Continuous Learning Archive** — Archive for longitudinal analysis

### Learning Types

8 learning types: Supervised, Reinforcement-inspired, Rule refinement, Pattern learning, Statistical, Temporal, Comparative, Human-guided.

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Governance gate | Every learning proposal goes through governance | Learning cannot bypass the same rules as any other change |
| Immutable history | Knowledge proposals create new versions, never overwrite | Preserves complete audit trail |
| Pattern library | Catalogued, confidence-scored, with scope and recurrence | Enables cross-cycle pattern detection |
| Confidence calibration | Adjustment formula based on outcome accuracy | Simple, interpretable, auditable |
| Knowledge proposal lifecycle | 8 states from Proposed to Superseded | Full traceability of every learning-driven change |

### Current Implementation vs Specification

| Aspect | Current (`observer_learning.py`) | Specification Target |
|--------|----------------------------------|---------------------|
| Patterns | 5 hardcoded patterns | Full pattern discovery with frequency, confidence, scope |
| Learning types | Rule-based only | 8 learning types composable |
| Confidence calibration | Hardcoded (0.3 or 0.6) | Formula-based calibration from outcome accuracy |
| Knowledge proposals | Simple store() call | Full lifecycle: Proposed → Review → Approved → Applied → Verified |
| Policy proposals | None | Structured policy improvement proposals |
| Outcome evaluation | None | Per-dimension outcome quality scoring |

---

## Open Architectural Questions

1. **How does the Learning Engine handle the cold start problem?** With zero observations, no patterns can be discovered and no recommendations generated. Initial patterns must be seeded or the engine must operate in "observation collection mode" for a minimum period before learning begins.

2. **How are learning recommendations prioritized?** Multiple recommendations may conflict or compete for governance attention. A prioritization scheme (impact × confidence / implementation cost) is needed but the authority for the prioritization formula is a product decision.

3. **How does the Learning Engine detect concept drift?** When previously valid patterns stop predicting outcomes accurately. This requires a pattern staleness model that is not yet specified.

---

## Assumptions and Risks

| Assumption / Risk | Detail |
|-------------------|--------|
| Sufficient observation volume for meaningful patterns | Minimum 100 observations per pattern discovery cycle |
| Governance validates learning proposals in reasonable time | Proposals held until governance is available; backlog possible |
| Confidence calibration does not create oscillation | Learning rate must prevent over-correction |
| Pattern library does not grow unbounded | 10,000 active pattern limit; stale patterns archived after 90 days |

See full document for 7 failure modes, 5 critical dependencies, and 12 cross-referenced specifications.

---

**End of Engineering Summary**