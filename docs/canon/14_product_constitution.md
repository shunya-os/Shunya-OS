# Product Constitution — Universal Founder Experience & Intelligence Specification

> **Canonical Document · Phase C1**
> **Status: CANONICAL — Binding, Measurable, Testable**
> **Version: 1.0**
> **Supersedes: None (new document)**

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Binding Authority](#2-binding-authority)
3. [The Universal Intelligence Principle](#3-the-universal-intelligence-principle)
4. [Universal Knowledge Routing](#4-universal-knowledge-routing)
5. [Internet Intelligence](#5-internet-intelligence)
6. [Internal Knowledge Priority](#6-internal-knowledge-priority)
7. [Empty Organization Intelligence](#7-empty-organization-intelligence)
8. [Universal Output Generation](#8-universal-output-generation)
9. [Universal Action Principle](#9-universal-action-principle)
10. [Universal AI Presence](#10-universal-ai-presence)
11. [Product Discoverability](#11-product-discoverability)
12. [Universal Organization Adaptation](#12-universal-organization-adaptation)
13. [Founder Experience Certification](#13-founder-experience-certification)
14. [Product Completion Definition](#14-product-completion-definition)
15. [Measurability & Testability](#15-measurability--testability)
16. [Relationship to Other Canonical Documents](#16-relationship-to-other-canonical-documents)

---

## 1. Purpose

This document defines the **Product Constitution** — the binding specification for how SHUNYA presents itself to the human Founder as a **single intelligence operating system** that requires no knowledge of internal architecture.

The central directive is:

> **Every capability that exists within SHUNYA's architecture must be accessible through a single natural-language interface, automatically orchestrated, and visibly available to the Founder without requiring knowledge of the underlying implementation.**

This is a measurable, implementable requirement. It is not aspirational.

### 1.1 What This Document Is Not

This document does not claim that SHUNYA can produce "anything" or perform every action. That would be an untestable promise. Instead, it requires that:

- Every **implemented** capability is discoverable through natural language
- Every **implemented** orchestration path is automatic
- Every **implemented** output format is reachable without configuration
- The set of capabilities is enumerated, measurable, and bounded

### 1.2 The Prohibited Knowledge

The Founder shall never need to understand:

- Modules
- Engines
- Pipelines
- APIs
- Databases
- Internet search mechanics
- LLM selection
- Output generators
- Connectors
- Workflows
- Internal architecture of any kind

SHUNYA shall determine these automatically.

---

## 2. Binding Authority

### 2.1 Hierarchy

```
SHUNYA Constitution (02)
    │
    ▼
Product Constitution (this document)
    │
    ▼
Experience Canon (08) — UX principles
AI Canon (07) — AI behaviour principles
Runtime Canon (05) — engine architecture
    │
    ▼
All implementation specifications, ADRs, and code
```

This document is derived from and subordinate to the SHUNYA Constitution (02). It is binding on all experience, AI, and runtime implementations. No downstream document may contradict it.

### 2.2 Scope

This document applies to:

- All user-facing surfaces of SHUNYA
- All AI interaction behaviours
- All knowledge retrieval and routing logic
- All output generation pathways
- All action execution paths
- All onboarding, empty states, and discovery mechanisms
- All certification and completion criteria

---

## 3. The Universal Intelligence Principle

### 3.1 Statement

Every request from the Founder enters a **single intelligence runtime**. The runtime shall automatically decide:

| Dimension | Automatic Decision |
|-----------|-------------------|
| **Information needed** | What knowledge is required to fulfil the request |
| **Source location** | Where that knowledge exists (memory, knowledge, internet, etc.) |
| **External information need** | Whether internet access is required |
| **Reasoning need** | Whether reasoning, planning, or computation is required |
| **Engine selection** | Which engine(s) should execute |
| **Output format** | What format is most appropriate for the result |

### 3.2 Measurable Requirement

| ID | Requirement | Test |
|----|-------------|------|
| UIP-1 | The Founder's request enters a single entry point (one text input, one voice input) | All requests route through a single input surface |
| UIP-2 | No request requires the Founder to specify a module, engine, or pipeline | Automated routing test: every request type resolves without user steering |
| UIP-3 | The runtime selects the correct engine for every request type | Engine selection audit: every request type maps to a correct engine without user hint |
| UIP-4 | The runtime selects the correct output format for every request type | Format audit: every request type produces a sensible default format |

### 3.3 The Founder Simply Asks

The Founder shall interact only through natural goals and natural language. Examples:

- "Help me."
- "Find this."
- "Explain this."
- "Create this."
- "Compare these."
- "Summarize this."
- "Generate a proposal."
- "Prepare an itinerary."
- "Draft an email."
- "Analyse my business."
- "What's happening near me?"
- "Which hotel should I recommend?"
- "Create an Excel."
- "Generate a PDF."
- "Make a presentation."
- "Research this topic."
- "Schedule this."
- "Remind me."
- "Monitor this."
- "Prepare tomorrow."

All of the above must resolve to the correct engine, sources, and format without the Founder specifying any of them.

---

## 4. Universal Knowledge Routing

### 4.1 Statement

For every request, SHUNYA shall automatically determine whether information should come from one or more of:

| Source | Description |
|--------|-------------|
| **Founder Memory** | Personal memories, preferences, history |
| **Personal Workspace** | The Founder's private objects, documents, notes |
| **Organization Knowledge** | Shared organizational data, templates, pricing, suppliers |
| **Relationships** | Graph of connections between objects, people, entities |
| **Commitments** | Promises, tasks, decisions, deadlines |
| **Documents** | Uploaded or created documents |
| **Connected Applications** | Third-party integrations |
| **Uploaded Files** | Files the Founder has uploaded |
| **Historical Conversations** | Past conversations and their outcomes |
| **Internet** | External public information |
| **Foundation Model Reasoning** | LLM-based reasoning and synthesis |
| **Deterministic Computation** | Calculations, aggregations, lookup tables |

### 4.2 Measurable Requirements

| ID | Requirement | Test |
|----|-------------|------|
| UKR-1 | Multiple sources are combined automatically for a single request | Integration test: request needing memory + internet + computation resolves all three |
| UKR-2 | No user selection of source is required | Test: every knowledge source is selected automatically, never via a picker |
| UKR-3 | Source selection is transparent on request | Test: "Where did you get that?" reveals the source chain |
| UKR-4 | Source selection is invisible by default | Test: default response does not list sources unless asked |
| UKR-5 | Each source is a live, queryable channel | Integration test: each source returns correct data for its domain |

### 4.3 Source Priority Chain

When multiple sources contain relevant information, the priority is:

```
Founder data
    ↓
Organization knowledge
    ↓
Connected systems
    ↓
Documents
    ↓
Internet
    ↓
Reasoning
```

Higher-priority sources are preferred. Lower-priority sources are consulted only when higher-priority sources lack the required information.

**Example:** "Prepare Bali itinerary."

If Panchi Club (the organization) already has:
- Hotels
- Suppliers
- Templates
- Pricing
- Experiences

Those shall be used first. Only missing knowledge shall be obtained externally.

---

## 5. Internet Intelligence

### 5.1 Statement

When internal knowledge is insufficient, SHUNYA shall automatically retrieve trustworthy external information. The Founder shall not explicitly request "Search the internet." SHUNYA shall decide when internet access is appropriate.

### 5.2 Automatic Internet Retrieval

Internet retrieval is appropriate for, but not limited to:

| Category | Examples |
|----------|----------|
| **Travel** | Hotel prices, flight information, travel requirements, restaurant recommendations |
| **Entertainment** | Movie listings, event schedules, local attractions |
| **Weather** | Current conditions, forecasts, alerts |
| **Regulations** | Laws, policies, compliance requirements |
| **News** | Current events, industry news, market updates |
| **Finance** | Stock information, exchange rates, economic indicators |
| **Maps** | Directions, locations, geospatial data |
| **Public Information** | Government portals, scientific facts, public documents |
| **Business** | Company information, business listings, supplier data |
| **Education** | Educational material, research, reference works |

### 5.3 Measurable Requirements

| ID | Requirement | Test |
|----|-------------|------|
| INT-1 | Internet retrieval is triggered automatically when internal knowledge is insufficient | Test: ask a question requiring current external data — no internet command is needed |
| INT-2 | Internet retrieval is NOT triggered when internal knowledge is sufficient | Test: ask a question fully answerable from internal sources — no network call is made |
| INT-3 | Retrieved information is trustworthy (source attribution, freshness check) | Audit: every internet-sourced fact includes a verifiable source URL |
| INT-4 | The Founder can see the source of internet-sourced information on request | Test: "Where did you get that?" returns the URL and retrieval timestamp |
| INT-5 | Internet retrieval is invisible by default | Test: default response does not say "I searched the internet" |

### 5.4 When Internet is Unnecessary

If the answer is available from internal sources (memory, organization knowledge, documents, etc.), the internet must not be used. This is a performance and trust requirement — unnecessary network calls slow responses and introduce untrusted data.

---

## 6. Internal Knowledge Priority

### 6.1 Statement

Whenever possible, SHUNYA shall prioritize internal knowledge sources over external ones. The priority chain defined in §4.3 governs source selection.

### 6.2 Measurable Requirements

| ID | Requirement | Test |
|----|-------------|------|
| IKP-1 | Internal sources are consulted before external sources | Audit: every request's source chain shows internal-first ordering |
| IKP-2 | Only missing knowledge is obtained externally | Test: request with partial internal coverage fetches only the missing pieces |
| IKP-3 | Internal knowledge is preferred even when lower quality | Test: low-confidence internal data is used over high-confidence external data (trust boundary) |
| IKP-4 | The Founder can override source priority | Test: "Use the internet for this" overrides internal-first |

---

## 7. Empty Organization Intelligence

### 7.1 Statement

A newly created organization with no data shall still be immediately useful. The Founder shall never encounter:

> "We don't have any data."

### 7.2 Day One Scenario

**Example:** Panchi Club signs up. Database contains nothing.

**Founder asks:** "Create a 6-day Bali honeymoon itinerary."

SHUNYA shall:

1. Understand the request (itinerary generation)
2. Obtain destination knowledge (Bali geography, attractions, culture)
3. Retrieve relevant public information (travel requirements, weather, prices)
4. Reason about itinerary quality (logical flow, pacing, variety)
5. Generate a professional itinerary
6. Store it as organizational knowledge (subject to Founder approval)
7. Allow later refinement as proprietary knowledge grows

### 7.3 Measurable Requirements

| ID | Requirement | Test |
|----|-------------|------|
| EOI-1 | An empty organization can produce useful output for any common request | Test: sign up fresh, ask "Create a 6-day Bali itinerary" — get a complete, useful itinerary |
| EOI-2 | Output is generated from public knowledge + reasoning, not from templates | Test: verify output is not a hardcoded template |
| EOI-3 | Generated output is stored as organizational knowledge | Test: verify the output is saved to the organization's knowledge store |
| EOI-4 | Storage requires Founder approval | Test: verify explicit consent before saving |
| EOI-5 | Later refinements enrich the proprietary knowledge base | Test: ask the same question again after refinement — output uses the refined knowledge |
| EOI-6 | "We don't have any data" is never displayed | Test: every empty state produces a useful response, not an error |

---

## 8. Universal Output Generation

### 8.1 Statement

SHUNYA shall automatically generate the most appropriate output format for every request. If the Founder requests a specific format, that format shall be produced whenever supported. If no format is requested, SHUNYA shall choose the most appropriate one.

### 8.2 Supported Output Formats

| Format | Category | When Appropriate |
|--------|----------|------------------|
| **Conversational response** | Text | Default for Q&A, explanations, discussions |
| **Rich document** | Document | Proposals, reports, analyses |
| **PDF** | Document | Formal documents, contracts, proposals |
| **DOCX** | Document | Editable documents for collaboration |
| **Markdown** | Document | Technical documentation, notes |
| **TXT** | Document | Plain text output |
| **HTML** | Document | Web-viewable content |
| **Email draft** | Communication | Messages to be sent |
| **Excel spreadsheet** | Data | Tables, budgets, schedules, data analysis |
| **CSV** | Data | Raw data export |
| **PowerPoint** | Presentation | Decks, pitches, summaries |
| **Report** | Document | Structured analysis with findings |
| **Dashboard** | Visual | Real-time data, metrics, monitoring |
| **Quotation** | Business | Pricing, estimates |
| **Invoice** | Business | Billing, payment requests |
| **Proposal** | Business | Structured offers, bids |
| **Contract** | Legal | Binding agreements |
| **Itinerary** | Travel | Trip plans, schedules |
| **Checklist** | Productivity | Action items, verification |
| **Project plan** | Management | Timelines, milestones, dependencies |
| **Meeting notes** | Collaboration | Summaries, action items, decisions |
| **Timeline** | Visual | Chronological sequences |
| **Summary** | Text | Condensed information |
| **Comparison** | Text/Table | Side-by-side evaluation |
| **Table** | Data | Structured information |
| **Form** | Data | Structured input |

### 8.3 Measurable Requirements

| ID | Requirement | Test |
|----|-------------|------|
| UOG-1 | Every request produces output in the most appropriate format | Format audit: for each request type, the default format is correct |
| UOG-2 | If a specific format is requested, it is produced (if supported) | Test: "Create a PDF" produces a PDF |
| UOG-3 | If no format is requested, SHUNYA chooses correctly | Test: "Generate a proposal" produces a document, not a conversation |
| UOG-4 | Each supported format is actually producible | Integration test: every format in the supported list can be generated |
| UOG-5 | Format selection is transparent on request | Test: "Why did you choose PDF?" reveals the reasoning |
| UOG-6 | Unsupported format requests are declined gracefully | Test: "Create a video" is declined with a helpful alternative |

---

## 9. Universal Action Principle

### 9.1 Statement

SHUNYA shall distinguish between different types of requests and respond appropriately:

| Request Type | SHUNYA Response |
|--------------|-----------------|
| **Answering** | Provide information |
| **Planning** | Develop a plan, present for approval |
| **Creating** | Generate the requested artifact |
| **Executing** | Guide or perform the supported workflow |
| **Monitoring** | Set up ongoing observation and alerting |
| **Following up** | Track commitments and progress |

### 9.2 Example

"Book my honeymoon."

The Founder is requesting **execution**, not merely information. SHUNYA shall identify this distinction and guide or perform the supported workflow rather than simply replying with text.

### 9.3 Measurable Requirements

| ID | Requirement | Test |
|----|-------------|------|
| UAP-1 | Request type is classified automatically | Audit: every request is classified into one of the six types |
| UAP-2 | The response matches the request type | Test: execution requests trigger execution workflows, not information responses |
| UAP-3 | When execution is impossible, the system guides the Founder | Test: "Book my honeymoon" without a booking integration offers to guide the process |
| UAP-4 | Action type classification is transparent on request | Test: "What kind of request is this?" reveals the classification |
| UAP-5 | The system never claims to execute actions it cannot | Test: every execution claim is backed by a real integration |

---

## 10. Universal AI Presence

### 10.1 Statement

AI shall remain continuously available throughout the operating system. It shall:

| Capability | Description |
|------------|-------------|
| **Explain** | Clarify any system behaviour, decision, or output |
| **Guide** | Walk the Founder through any workflow step by step |
| **Recommend** | Suggest objects, actions, or decisions based on context |
| **Anticipate** | Proactively surface relevant information and actions |
| **Summarize** | Condense any object, conversation, or document |
| **Search** | Find any object, information, or relationship |
| **Generate** | Produce any supported output format |
| **Execute** | Perform supported actions through the object protocol |
| **Remember** | Maintain context across sessions and interactions |
| **Improve** | Continuously refine context, knowledge, and recommendations |

### 10.2 Measurable Requirements

| ID | Requirement | Test |
|----|-------------|------|
| UAP-1 | AI is accessible from every surface of the system | Test: from any screen, the AI can be summoned |
| UAP-2 | AI is always object-contextual | Test: "What do you know about this?" refers to the current object |
| UAP-3 | AI is present but not intrusive | Test: the AI is not automatically triggered on every page load |
| UAP-4 | Each of the 10 capabilities is implemented | Integration test: each capability produces a correct result |
| UAP-5 | AI presence is discoverable — not hidden in a menu | Test: a new Founder can find the AI within 2 clicks |

---

## 11. Product Discoverability

### 11.1 Statement

No capability shall remain hidden because the Founder does not know where it lives. Every capability implemented in SHUNYA shall be naturally discoverable through:

| Discovery Mechanism | Description |
|---------------------|-------------|
| **Conversation** | The Founder can ask about any capability in natural language |
| **Contextual suggestions** | The AI suggests relevant capabilities based on current context |
| **Search** | Typing a capability name in search finds it |
| **Recommendations** | The AI proactively recommends useful capabilities |
| **Onboarding** | New Founders are introduced to key capabilities |
| **Empty states** | Empty spaces show what capabilities are available |
| **Proactive AI guidance** | The AI offers help when the Founder seems stuck |

### 11.2 Measurable Requirements

| ID | Requirement | Test |
|----|-------------|------|
| PD-1 | Every implemented capability can be discovered through conversation | Test: "How do I create a PDF?" leads to the PDF generation capability |
| PD-2 | Every implemented capability can be found by searching its name | Test: search "proposal" finds the proposal generation capability |
| PD-3 | Empty states show available capabilities, not blank pages | Test: every empty state has a helpful suggestion |
| PD-4 | A capability that cannot be discovered is considered incomplete | This is a design rule, not a test: no capability ships without a discovery path |
| PD-5 | Onboarding covers all major capability categories | Test: completion of onboarding reveals awareness of all format types |

---

## 12. Universal Organization Adaptation

### 12.1 Statement

The same operating system shall naturally adapt to:

| Type | Example Needs |
|------|---------------|
| **Companies** | Projects, teams, revenue, clients, products |
| **Individuals** | Personal tasks, notes, decisions, finances |
| **Governments** | Public services, compliance, records, transparency |
| **Hospitals** | Patient records, schedules, compliance, referrals |
| **Educational institutions** | Students, courses, grades, curriculum |
| **NGOs** | Grants, beneficiaries, impact tracking, reporting |
| **Startups** | Funding, milestones, product, team |
| **Freelancers** | Clients, invoices, projects, portfolio |
| **Families** | Events, tasks, budgets, shared notes |

### 12.2 Measurable Requirement

| ID | Requirement | Test |
|----|-------------|------|
| UOA-1 | The system works for any organization type without separate products | Test: create an organization of each type — no code changes needed |
| UOA-2 | Adaptation is through configuration, not separate codebases | Audit: organization types are data-driven, not hardcoded |
| UOA-3 | Object types are universal — not tailored per organization type | Test: every organization type uses the same 18 object types |
| UOA-4 | Domain-specific behaviour is additive, not subtractive | Test: domain-specific features exist without removing universal ones |

---

## 13. Founder Experience Certification

### 13.1 Certification Gates

Every Founder journey shall successfully demonstrate the following certification gates. A gate is **passed** when the required action produces the correct result without the Founder specifying internal architecture.

| # | Gate | Description | Acceptance Criteria |
|---|------|-------------|---------------------|
| 1 | **Onboarding** | New Founder signs up and can perform a useful action immediately | Empty organization produces useful output (see §7) |
| 2 | **Understanding** | Founder can ask any question about the system and receive a clear answer | "How do I create a proposal?" produces a correct, actionable response |
| 3 | **Navigation** | Founder can find any object in the system through natural language | "Find the Q3 budget proposal" locates the correct object |
| 4 | **Creation** | Founder can create any supported object type through natural language | "Create a new task for the marketing campaign" creates the correct object |
| 5 | **Collaboration** | Founder can share objects and collaborate with others | "Share this proposal with Alice" sets up correct sharing |
| 6 | **AI Interaction** | Founder can interact with AI naturally in any context | "Summarize this document" produces a correct summary of the current object |
| 7 | **Document Generation** | Founder can generate any supported output format | "Create a PDF of this itinerary" produces a PDF |
| 8 | **Internet Intelligence** | Founder can ask questions requiring external data without specifying internet | "What's the weather in Bali next week?" retrieves current data |
| 9 | **Internal Intelligence** | Founder can ask questions that use internal knowledge preferentially | "What's our best hotel rate in Ubud?" uses organizational pricing data |
| 10 | **Execution** | Founder can trigger execution workflows through natural language | "Book the honeymoon package" triggers the booking workflow |
| 11 | **Returning** | Founder can return later and resume naturally | Context from previous session is available without re-explaining |
| 12 | **Continuation** | Founder can continue interrupted work naturally | "Continue where I left off" resumes the previous context |

### 13.2 Certification Requirements

| ID | Requirement | Test |
|----|-------------|------|
| FEC-1 | All 12 certification gates are passable | Full certification suite: every gate passes with a real Founder workflow |
| FEC-2 | Each gate passes without specifying internal architecture | Test: every gate triggers only through natural language |
| FEC-3 | Failed gates produce clear error messages | Test: "I can't book a honeymoon because no booking integration is connected" |
| FEC-4 | The certification suite is runnable as an automated test | E2E test: every gate is automated and verifiable |
| FEC-5 | Certification results are documented and traceable | Each gate produces evidence (screenshot, output, log) |

---

## 14. Product Completion Definition

### 14.1 Statement

SHUNYA is complete only when a Founder can naturally say the following — and SHUNYA automatically decides where to obtain information, how to reason, which capabilities to invoke, what format to produce, and how to present or execute the result — **for every capability that exists in the architecture**.

### 14.2 Completion Test Cases

The following are the canonical completion test cases. Each must be demonstrable:

| Request | Expected Behaviour |
|---------|-------------------|
| "Help me." | AI assesses context and offers relevant assistance |
| "Find this." | System locates the referenced object or information |
| "Explain this." | AI explains the current object or concept |
| "Create this." | System generates the requested artifact |
| "Compare these." | System produces a comparison of the referenced items |
| "Summarize this." | System summarizes the current object or content |
| "Generate a proposal." | System produces a proposal document |
| "Prepare an itinerary." | System generates a travel itinerary |
| "Draft an email." | System produces an email draft |
| "Analyse my business." | System analyzes organizational data and produces insights |
| "What's happening near me?" | System retrieves location-based information |
| "Which hotel should I recommend?" | System reasons about the best recommendation |
| "Create an Excel." | System produces a spreadsheet |
| "Generate a PDF." | System produces a PDF document |
| "Make a presentation." | System produces a PowerPoint deck |
| "Research this topic." | System retrieves and synthesizes information |
| "Schedule this." | System creates a calendar event or timeline |
| "Remind me." | System sets a reminder |
| "Monitor this." | System sets up ongoing observation |
| "Prepare tomorrow." | System prepares a daily briefing |

### 14.3 Measurable Requirement

| ID | Requirement | Test |
|----|-------------|------|
| PCD-1 | Every canonical completion test case is demonstrable | E2E test: each test case produces the correct result through natural language only |
| PCD-2 | No test case requires the Founder to specify internal architecture | Audit: each test case's trigger is a single natural language request |
| PCD-3 | New capabilities are added to this list when they ship | Process rule: every new capability must define its completion test case |

---

## 15. Measurability & Testability

### 15.1 Design Principle

This document avoids untestable promises. Every requirement is accompanied by a specific test that can be:

1. **Automated** — run as part of CI/CD
2. **Observed** — demonstrated to a human evaluator
3. **Measured** — pass/fail with clear criteria
4. **Traced** — linked to a specific implementation

### 15.2 Requirement Categories

| Category | Count | Testable | Verification Method |
|----------|-------|----------|---------------------|
| Universal Intelligence Principle | 4 | ✓ | Automated routing test |
| Universal Knowledge Routing | 5 | ✓ | Integration test |
| Internet Intelligence | 5 | ✓ | Network call audit |
| Internal Knowledge Priority | 4 | ✓ | Source chain audit |
| Empty Organization Intelligence | 6 | ✓ | E2E scenario test |
| Universal Output Generation | 6 | ✓ | Format generation test |
| Universal Action Principle | 5 | ✓ | Request classification audit |
| Universal AI Presence | 5 | ✓ | Integration test |
| Product Discoverability | 5 | ✓ | Discovery audit |
| Universal Organization Adaptation | 4 | ✓ | Multi-tenant scenario test |
| Founder Experience Certification | 5 | ✓ | Certification suite |
| Product Completion Definition | 3 | ✓ | E2E completion test |
| **Total** | **57** | **All** | — |

### 15.3 Certification Suite

A certification suite SHALL exist that:

1. Runs all 57 requirements as automated tests
2. Produces a pass/fail report for each requirement
3. Tracks pass rate over time
4. Blocks releases that fail any requirement
5. Is runnable by non-technical evaluators

---

## 16. Relationship to Other Canonical Documents

| Document | Relationship |
|----------|-------------|
| **00_universal_ontology.md** | The Intelligence Runtime operates on ontological primitives (Entity, Knowledge, Memory, Context) |
| **01_shunya_vision.md** | This document operationalizes the vision: "compounding intelligence" becomes automatic routing |
| **02_shunya_constitution.md** | This document is subordinate to the Constitution; all capabilities must respect Constitutional articles |
| **03_business_canon.md** | All business objects are accessible through natural language per this document |
| **04_universal_object_protocol.md** | The AI uses the Object Protocol to execute actions on behalf of the Founder |
| **05_runtime_canon.md** | The Intelligence Runtime (§3) is realized by the engine architecture in 05 |
| **06_data_canon.md** | Knowledge routing (§4) uses the data classification from 06 |
| **07_ai_canon.md** | AI behaviour must implement the Universal AI Presence (§10) requirements |
| **08_experience_canon.md** | The experience design must implement Product Discoverability (§11) |
| **09_repository_canon.md** | Repository structure must support multi-organization adaptation (§12) |
| **10_migration_canon.md** | Migration must preserve all certification gates (§13) |
| **11_engineering_canon.md** | Engineering standards must include the certification suite (§15) |
| **13_SHUNYA_FOUNDER_EXPERIENCE_ROADMAP_v1.0.md** | The roadmap milestones sequence the implementation of this document's requirements |
| **FOUNDER_JOURNEY.md** | The Founder Journey (§13) is a subset of the certification gates |

---

> **Next: [15_product_completion_checklist.md](15_product_completion_checklist.md) — The executable certification checklist**