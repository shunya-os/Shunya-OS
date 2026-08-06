# EX-02-R1 — Constitutional Evidence Discipline

**Established by:** Founder directive, 2026-08-05 (CDR-006 review)
**Amends:** EX-02 (Constitutional Evidence Boundary), LX-06D-R3 (CDR mandatory sections)
**Status:** Locked — permanent addition to CDR methodology

---

## 1. The Discipline

The purpose of a Constitutional Discovery Report is to establish **constitutional truth**, not architectural preference.

From this point forward every CDR shall distinguish three independent layers:

### I. Repository Evidence (Observed)

This section shall contain only facts proven directly from the repository.

Every statement shall be traceable to code.

Examples:
- polling interval exists
- endpoint exists
- consumer exists
- producer exists
- event bus consumer exists
- runtime exists
- ownership exists

**No recommendation is permitted in this section.**

### II. Architectural Inference

This section shall contain conclusions derived from Repository Evidence.

Every inference shall explicitly reference the evidence that supports it.

Example:
> Repository Evidence:
> - Reality updates every 15 seconds.
> - Multiple consumers independently poll the same Reality endpoint.
>
> Inference:
> - Reality appears to represent a continuously changing business projection.

**An inference is not constitutional truth. It remains open to challenge.**

### III. Constitutional Recommendation

Only after Repository Evidence and Architectural Inference are complete may the CDR recommend a constitutional destination.

Every recommendation shall explicitly identify:
- Constitutional Article(s)
- Repository Evidence supporting it
- Architectural Inference supporting it
- Remaining assumptions
- Confidence level
- Alternative constitutional interpretations considered
- Why they were rejected

**A recommendation without supporting evidence is constitutionally invalid.**

---

## 2. Mandatory Constitutional Evidence Matrix

Every recommendation shall be accompanied by the following matrix:

| Recommendation | Repository Evidence | Architectural Inference | Constitutional Article | Remaining Assumptions | Confidence |
|---------------|-------------------|------------------------|----------------------|----------------------|------------|
| <recommendation> | <fact(s) from code> | <conclusion from facts> | <article/rule/law> | <what is still unknown> | HIGH/MEDIUM/LOW |

**No recommendation may omit this matrix.**

---

## 3. Constitutional Definition Requirement

Before CEP-006 may enter Implementation, Discovery shall answer:

**What is Reality inside SHUNYA?**

The answer shall be architectural, not philosophical. It shall identify:
- canonical owner
- canonical runtime
- lifecycle
- publication mechanism
- event ownership
- consumers
- persistence
- projection boundaries

If Reality is proven to be the canonical continuously changing business state, then Discovery shall evaluate whether SSE is merely a transport mechanism for the Reality Runtime rather than an objective in itself.

The constitutional objective is **not**:
> Replace polling with SSE.

The constitutional objective is:
> Reveal the canonical Reality Runtime and select the constitutionally correct transport for each class of Reality.

SSE, polling, or another mechanism shall emerge from constitutional truth — not be predetermined.

---

## 4. Expanded Discovery Exit Criteria

CDR-006 may proceed to Implementation only when:

1. **Repository Evidence is complete.**
2. **Architectural Inference is complete.**
3. **Constitutional Recommendation is fully justified.**
4. **Every recommendation has an Evidence Matrix.**
5. **Reality has a constitutional definition.**
6. **SSE is proven to be the constitutionally correct transport for Continuous Reality workloads** — rather than assumed.
7. **No recommendation depends upon unverified architectural assumptions.**

Until every condition is satisfied, Discovery continues. Implementation remains constitutionally prohibited.

---

*EX-02-R1 established by founder directive, 2026-08-05.*
*Amends EX-02 and LX-06D-R3. Conforms to CAS-01.*