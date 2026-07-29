# SHUNYA Product Completion Checklist

> **Canonical Document · Phase C1**
> **Status: CANONICAL — Executable Certification Checklist**
> **Version: 1.0**

---

## How to Use

This checklist is the executable certification suite for the Product Constitution (14). Each requirement is a pass/fail test. A requirement is **PASSED** when the specified test produces the correct result.

**Run frequency:** Every release candidate.
**Blocking:** Any FAILED requirement blocks release.

---

## §3 — Universal Intelligence Principle

| ID | Requirement | Test | Status |
|----|-------------|------|--------|
| UIP-1 | Single entry point for all requests | All requests route through a single input surface | ❌ |
| UIP-2 | No module/engine/pipeline specification required | Every request type resolves without user steering | ❌ |
| UIP-3 | Correct engine selection for every request type | Engine selection audit: every request type maps correctly | ❌ |
| UIP-4 | Correct output format for every request type | Format audit: every request type produces a sensible default | ❌ |

## §4 — Universal Knowledge Routing

| ID | Requirement | Test | Status |
|----|-------------|------|--------|
| UKR-1 | Multiple sources combined automatically | Integration test: memory + internet + computation resolves all three | ❌ |
| UKR-2 | No user source selection required | Every source is selected automatically, never via a picker | ❌ |
| UKR-3 | Source selection transparent on request | "Where did you get that?" reveals the source chain | ❌ |
| UKR-4 | Source selection invisible by default | Default response does not list sources unless asked | ❌ |
| UKR-5 | Each source is a live, queryable channel | Integration test: each source returns correct data | ❌ |

## §5 — Internet Intelligence

| ID | Requirement | Test | Status |
|----|-------------|------|--------|
| INT-1 | Automatic internet retrieval when internal knowledge insufficient | No internet command needed for external data | ❌ |
| INT-2 | No internet retrieval when internal knowledge sufficient | No network call for internally-answerable questions | ❌ |
| INT-3 | Trustworthy information (source attribution, freshness) | Every internet-sourced fact includes a verifiable source URL | ❌ |
| INT-4 | Source visible on request | "Where did you get that?" returns URL + timestamp | ❌ |
| INT-5 | Internet retrieval invisible by default | Default response does not say "I searched the internet" | ❌ |

## §6 — Internal Knowledge Priority

| ID | Requirement | Test | Status |
|----|-------------|------|--------|
| IKP-1 | Internal sources consulted before external | Source chain shows internal-first ordering | ❌ |
| IKP-2 | Only missing knowledge obtained externally | Partial internal coverage fetches only missing pieces | ❌ |
| IKP-3 | Internal knowledge preferred even when lower quality | Low-confidence internal data > high-confidence external | ❌ |
| IKP-4 | Founder can override source priority | "Use the internet for this" overrides internal-first | ❌ |

## §7 — Empty Organization Intelligence

| ID | Requirement | Test | Status |
|----|-------------|------|--------|
| EOI-1 | Empty organization produces useful output | Fresh signup → "Create a 6-day Bali itinerary" → complete itinerary | ❌ |
| EOI-2 | Output from public knowledge + reasoning, not templates | Verify output is not a hardcoded template | ❌ |
| EOI-3 | Output stored as organizational knowledge | Verify output saved to knowledge store | ❌ |
| EOI-4 | Storage requires Founder approval | Verify explicit consent before saving | ❌ |
| EOI-5 | Later refinements enrich proprietary knowledge | Same question after refinement uses refined data | ❌ |
| EOI-6 | "We don't have any data" never displayed | Every empty state produces a useful response | ❌ |

## §8 — Universal Output Generation

| ID | Requirement | Test | Status |
|----|-------------|------|--------|
| UOG-1 | Most appropriate format for every request | Format audit: each request type's default format is correct | ❌ |
| UOG-2 | Specific format produced if requested | "Create a PDF" produces a PDF | ❌ |
| UOG-3 | Correct format chosen when none specified | "Generate a proposal" produces a document, not conversation | ❌ |
| UOG-4 | Every supported format is producible | Integration test: every format in the supported list | ❌ |
| UOG-5 | Format selection transparent on request | "Why PDF?" reveals the reasoning | ❌ |
| UOG-6 | Unsupported format declined gracefully | "Create a video" is declined with helpful alternative | ❌ |

## §9 — Universal Action Principle

| ID | Requirement | Test | Status |
|----|-------------|------|--------|
| UAP-1 | Request type classified automatically | Every request classified into one of six types | ❌ |
| UAP-2 | Response matches request type | Execution requests trigger execution workflows | ❌ |
| UAP-3 | When execution impossible, system guides | "Book my honeymoon" without integration offers guidance | ❌ |
| UAP-4 | Classification transparent on request | "What kind of request is this?" reveals classification | ❌ |
| UAP-5 | Never claims actions it cannot execute | Every execution claim backed by real integration | ❌ |

## §10 — Universal AI Presence

| ID | Requirement | Test | Status |
|----|-------------|------|--------|
| UAP-1 | AI accessible from every surface | From any screen, AI can be summoned | ❌ |
| UAP-2 | AI always object-contextual | "What do you know about this?" refers to current object | ❌ |
| UAP-3 | AI present but not intrusive | Not automatically triggered on every page load | ❌ |
| UAP-4 | All 10 capabilities implemented | Integration test: each capability produces a correct result | ❌ |
| UAP-5 | AI discoverable within 2 clicks | New Founder can find AI within 2 clicks | ❌ |

## §11 — Product Discoverability

| ID | Requirement | Test | Status |
|----|-------------|------|--------|
| PD-1 | Capabilities discoverable through conversation | "How do I create a PDF?" leads to PDF generation | ❌ |
| PD-2 | Capabilities findable by name search | Search "proposal" finds proposal generation | ❌ |
| PD-3 | Empty states show capabilities | Every empty state has a helpful suggestion | ❌ |
| PD-4 | Undiscoverable capability = incomplete | Design rule: no capability ships without discovery path | ❌ |
| PD-5 | Onboarding covers all capability categories | Completion of onboarding reveals awareness of all format types | ❌ |

## §12 — Universal Organization Adaptation

| ID | Requirement | Test | Status |
|----|-------------|------|--------|
| UOA-1 | Works for any organization type | Create organization of each type — no code changes | ❌ |
| UOA-2 | Adaptation through configuration, not code | Organization types are data-driven, not hardcoded | ❌ |
| UOA-3 | Object types universal across types | Every type uses same 18 object types | ❌ |
| UOA-4 | Domain-specific behaviour additive | Domain features exist without removing universal ones | ❌ |

## §13 — Founder Experience Certification

| # | Gate | Acceptance Criteria | Status |
|---|------|--------------------|--------|
| 1 | **Onboarding** | Empty organization produces useful output immediately | ❌ |
| 2 | **Understanding** | "How do I create a proposal?" produces correct response | ❌ |
| 3 | **Navigation** | "Find the Q3 budget proposal" locates correct object | ❌ |
| 4 | **Creation** | "Create a new task for marketing" creates correct object | ❌ |
| 5 | **Collaboration** | "Share this proposal with Alice" sets up correct sharing | ❌ |
| 6 | **AI Interaction** | "Summarize this document" produces correct summary | ❌ |
| 7 | **Document Generation** | "Create a PDF of this itinerary" produces a PDF | ❌ |
| 8 | **Internet Intelligence** | "What's the weather in Bali?" retrieves current data | ❌ |
| 9 | **Internal Intelligence** | "What's our best hotel rate in Ubud?" uses org pricing | ❌ |
| 10 | **Execution** | "Book the honeymoon package" triggers booking workflow | ❌ |
| 11 | **Returning** | Context from previous session is available | ❌ |
| 12 | **Continuation** | "Continue where I left off" resumes previous context | ❌ |

## §14 — Product Completion Definition

| ID | Test Case | Expected Behaviour | Status |
|----|----------|-------------------|--------|
| PC-01 | "Help me." | AI assesses context, offers relevant assistance | ❌ |
| PC-02 | "Find this." | System locates referenced object or information | ❌ |
| PC-03 | "Explain this." | AI explains current object or concept | ❌ |
| PC-04 | "Create this." | System generates requested artifact | ❌ |
| PC-05 | "Compare these." | System produces comparison of referenced items | ❌ |
| PC-06 | "Summarize this." | System summarizes current object or content | ❌ |
| PC-07 | "Generate a proposal." | System produces proposal document | ❌ |
| PC-08 | "Prepare an itinerary." | System generates travel itinerary | ❌ |
| PC-09 | "Draft an email." | System produces email draft | ❌ |
| PC-10 | "Analyse my business." | System analyzes organizational data, produces insights | ❌ |
| PC-11 | "What's happening near me?" | System retrieves location-based information | ❌ |
| PC-12 | "Which hotel should I recommend?" | System reasons about best recommendation | ❌ |
| PC-13 | "Create an Excel." | System produces spreadsheet | ❌ |
| PC-14 | "Generate a PDF." | System produces PDF document | ❌ |
| PC-15 | "Make a presentation." | System produces PowerPoint deck | ❌ |
| PC-16 | "Research this topic." | System retrieves and synthesizes information | ❌ |
| PC-17 | "Schedule this." | System creates calendar event or timeline | ❌ |
| PC-18 | "Remind me." | System sets a reminder | ❌ |
| PC-19 | "Monitor this." | System sets up ongoing observation | ❌ |
| PC-20 | "Prepare tomorrow." | System prepares daily briefing | ❌ |

---

## Summary

| Section | Total | Passed | Failed | Status |
|---------|-------|--------|--------|--------|
| §3 — Universal Intelligence Principle | 4 | 0 | 4 | ❌ FAIL |
| §4 — Universal Knowledge Routing | 5 | 0 | 5 | ❌ FAIL |
| §5 — Internet Intelligence | 5 | 0 | 5 | ❌ FAIL |
| §6 — Internal Knowledge Priority | 4 | 0 | 4 | ❌ FAIL |
| §7 — Empty Organization Intelligence | 6 | 0 | 6 | ❌ FAIL |
| §8 — Universal Output Generation | 6 | 0 | 6 | ❌ FAIL |
| §9 — Universal Action Principle | 5 | 0 | 5 | ❌ FAIL |
| §10 — Universal AI Presence | 5 | 0 | 5 | ❌ FAIL |
| §11 — Product Discoverability | 5 | 0 | 5 | ❌ FAIL |
| §12 — Universal Organization Adaptation | 4 | 0 | 4 | ❌ FAIL |
| §13 — Founder Experience Certification | 12 | 0 | 12 | ❌ FAIL |
| §14 — Product Completion Definition | 20 | 0 | 20 | ❌ FAIL |
| **Total** | **81** | **0** | **81** | **❌ FAIL** |

> **Status: ALL 81 REQUIREMENTS FAILING — This is expected. The Product Constitution defines the target state. Each requirement becomes a development milestone.**
>
> **Next update: After each release, re-run this checklist and update the status column.**