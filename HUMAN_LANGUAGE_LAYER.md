# Human Language Layer Specification

**Directive:** Z-05 Article IV
**Purpose:** Define how user language maps to universal ontology. The founder shall never think in SHUNYA object names.
**Status:** Design Artefact

---

## Principle

> The ontology exists for SHUNYA. Not for the founder.

Users say natural things. SHUNYA internally determines the correct universal concepts, relationships, and composition. The mapping layer translates between human intent and ontology operations.

---

## Translation Architecture

```
User: "Add a traveller named Alice"

  ↓  Natural Language Understanding (AI)

Internal: {
  action: "create",
  concepts: [
    { type: "Identity", subtype: "Person", name: "Alice" },
    { type: "Relationship", source: Alice, target: CurrentOrg, type: "traveller-of" }
  ],
  workspace: "Travel",
  context: { domain: "Travel / Hospitality" }
}

  ↓  Ontology Operations

1. Create Record(type=person, name="Alice", ...)
2. Create Record(type=relationship, source=alice_id, target=org_id, type="traveller-of")
3. Activate workspace capabilities for Travel domain

  ↓  Response to User

"Alice has been added as a traveller. Would you like to book a trip or add their preferences?"
```

---

## Phrase → Ontology Mapping Catalog

### Identity & Person

| User Says | Ontology Operations |
|-----------|-------------------|
| "Add John as a customer" | Create Person + Create Relationship(customer-of) |
| "Add a new supplier" | Create Person/Organization + Create Relationship(supplier-of) |
| "Invite Sarah to join" | Create Person + Create Relationship(employee-of, pending) |
| "Register a new patient" | Create Person + Create Relationship(patient-of) |
| "John works for Acme Corp" | Create Organization(Acme Corp) + Create Relationship(employed-by, John→Acme) |
| "We have a new investor" | Create Person/Organization + Create Relationship(investor) |
| "This is our new partner" | Create Organization + Create Relationship(partner-of) |

### Commitments & Agreements

| User Says | Ontology Operations |
|-----------|-------------------|
| "Create an invoice for $5000" | Create Commitment(type=invoice) + Create Financial Record(amount=5000) + Link to Customer |
| "Send a proposal to Beta LLC" | Create Commitment(type=proposal) + Create Document(proposal) + Link to Person + Create Communication |
| "Follow up with Alice next week" | Create Commitment(type=follow-up, due=next_week) + Link to Person |
| "Book a flight to London" | Create Commitment(type=booking) + Create Event(trip) + Create Place(destination=London) |
| "Schedule a meeting for Tuesday" | Create Event(type=meeting, date=Tuesday) + Link participants |
| "Assign a task to review the budget" | Create Commitment(type=task, assignee=X) + Link to Document(budget) |
| "Draft a contract for the new client" | Create Commitment(type=contract, status=draft) + Create Document |
| "Send a quote for the consulting project" | Create Commitment(type=quote) + Create Document + Create Communication |

### Events & Activities

| User Says | Ontology Operations |
|-----------|-------------------|
| "Log a call with John" | Create Event(type=call) + Create Communication + Link to Person |
| "Record the meeting notes" | Create Event(type=meeting) + Create Document(notes) |
| "We closed the deal with Acme" | Update Commitment(deal, status=won) + Create Event(type=deal-closed) |
| "Ship order #451" | Create Event(type=shipment) + Update Commitment(order, status=shipped) |
| "Patient arrived for appointment" | Create Event(type=arrival) + Update Event(appointment, status=in-progress) |

### Assets & Resources

| User Says | Ontology Operations |
|-----------|-------------------|
| "Add a new product to the catalog" | Create Asset(type=product) + Link to Organization |
| "Receive 50 units of raw material" | Create Event(type=receipt) + Update Asset(inventory, quantity+=50) |
| "List a new property" | Create Asset(type=property) + Create Commitment(type=listing) + Create Place |
| "Upload the company logo" | Create Asset(type=image, brand) + Link to Organization |
| "Add this document to the knowledge base" | Create Knowledge + Create Document |

### Financial

| User Says | Ontology Operations |
|-----------|-------------------|
| "Record a payment of $3000 from Acme" | Create Financial Record(type=payment, amount=3000) + Link to Commitment(invoice) |
| "Log an expense of $50 for parking" | Create Financial Record(type=expense, amount=50) + Link to Event |
| "What's our monthly revenue?" | Query Financial Records grouped by month + Commitment(invoice) status |
| "Create a budget for Q4 marketing" | Create Financial Record(type=budget) + Create Commitment(goal) |

### Knowledge & Learning

| User Says | Ontology Operations |
|-----------|-------------------|
| "Save this article to read later" | Create Knowledge + Create Commitment(reading goal) |
| "Document the onboarding process" | Create Workflow + Create Document + Create Knowledge |
| "What do we know about this customer?" | Query Knowledge + Memory + Events + Communications for Person |
| "Summarize our Q2 results" | Query Financial Records + Events + Commitments → AI generates Document |

### Observing & Deciding

| User Says | Ontology Operations |
|-----------|-------------------|
| "Note that the server is running slow" | Create Observation(subject=server, predicate=performance, value=slow) |
| "Approve the budget proposal" | Create Decision + Update Commitment(budget, status=approved) |
| "Why did we choose this vendor?" | Query Decision + linked Observations for vendor Relationship |
| "Flag accounts that haven't paid in 60 days" | Query Commitments(invoice, overdue) + Create Observations |

---

## Language Context Resolution

The same phrase means different things in different domains:

| Phrase | Travel Domain | Healthcare Domain | Consulting Domain |
|--------|--------------|-------------------|-------------------|
| "Add a traveller" | Person + Relationship(traveller-of) | N/A (not used) | N/A |
| "Register a patient" | N/A | Person + Relationship(patient-of) | N/A |
| "Onboard a client" | N/A | N/A | Person + Relationship(client-of) + Workflow(onboarding) |
| "Start a new case" | N/A | Observation(diagnosis) + Commitment(treatment) | Commitment(engagement) + Document(proposal) |
| "Book a room" | Commitment(reservation) + Place(hotel) | Commitment(appointment) + Place(clinic) | Commitment(meeting) + Place(conference) |
| "Schedule a review" | Event(performance) | Event(checkup) | Event(quarterly) |

**Resolution mechanism:** Active workspace domain + user's role + recent context determine which ontology mapping wins.

---

## Grammar of the Language Layer

### Verbs (Actions)

| Verb | Ontology Operation | Example |
|------|-------------------|---------|
| add, create, new, register | Create Record | "Add a customer" |
| edit, update, change | Update Record | "Update the invoice amount" |
| delete, remove, archive | Archive Record | "Remove this task" |
| find, search, show | Query Records | "Show me all leads" |
| send, share, notify | Create Communication | "Send the proposal" |
| link, connect, relate | Create Relationship | "Link this document to the customer" |
| schedule, book | Create Event | "Schedule a meeting" |
| approve, reject, confirm | Create Decision | "Approve the budget" |
| assign, delegate | Update Commitment(assignee) | "Assign this task to John" |
| upload, import | Create Document/Asset | "Upload the contract" |
| generate, draft | AI creates Record | "Generate a proposal" |
| summarize, analyze | AI queries + synthesizes | "Summarize customer history" |
| track, monitor | Create Observation | "Track inventory levels" |

### Nouns (Concepts)

Never shown to the user. Internal only. The Language Layer maps the user's noun to ontology.

| User Noun | Internal Concept(s) |
|-----------|-------------------|
| customer, client, contact | Person + Relationship |
| supplier, vendor, partner | Person/Organization + Relationship |
| employee, team member, staff | Person + Relationship |
| patient | Person + Relationship(patient-of) |
| student, trainee | Person + Relationship(student-of) |
| traveller, guest | Person + Relationship |
| invoice, bill | Commitment + Financial Record |
| proposal, quote | Commitment(proposed) + Document |
| order, purchase | Commitment + Assets + Financial Record |
| task, todo, follow-up | Commitment(promise to act) |
| project, engagement | Commitment(deliverable) + Events + Persons |
| campaign | Commitment + Assets(creative) + Events |
| meeting, appointment | Event |
| call, email, message | Communication |
| document, file, report | Document |
| product, item | Asset |
| property, venue | Place + Asset |
| budget, payment, expense | Financial Record |
| contract, agreement | Commitment + Document |
| goal, target | Commitment(promise about future state) |
| habit, routine | Commitment(recurring) + Events |
| note, journal | Document + Knowledge |
| knowledge, research | Knowledge + Documents |
| feedback, review | Communication + Observation |
| policy, procedure | Knowledge + Workflow |

---

## Conversational Patterns

### Pattern 1: Quick Create
```
User: "Add a customer: Acme Corp, contact John, john@acme.com"
AI: Creates Person(John) + Organization(Acme Corp) + Relationship + Workspace card
```

### Pattern 2: Contextual Query
```
User: "What's happening with Acme?"
AI: Queries all Records linked to Acme Corp or John → summarizes Events, Commitments, Communications
```

### Pattern 3: Multi-step Intent
```
User: "Invoice Acme for the March consulting work"
AI: 1. Queries Events(March, consulting, Acme) for billable hours
    2. Creates Commitment(invoice) with computed amount
    3. Creates Financial Record
    4. Creates Communication(send invoice to Acme)
```

### Pattern 4: Compound Creation
```
User: "Create a project for the new client engagement with a $50k budget"
AI: 1. Creates Person(client)
    2. Creates Commitment(engagement)
    3. Creates Commitment(project, deliverables)
    4. Creates Financial Record(budget=$50k)
    5. Creates Document(project plan)
    6. Links everything via Relationships
```

### Pattern 5: State Transition
```
User: "Mark the proposal as sent"
AI: Updates Commitment(proposal, status=sent) + Creates Event(proposal-sent)
```

### Pattern 6: Memory Recall
```
User: "What did Acme say about the pricing?"
AI: Queries Memory + Communications linked to Acme Corp → finds relevant messages
```

---

## Implementation Notes

1. **No hardcoded NLP pipeline.** The Language Layer is AI-native. SHUNYA's AI models interpret user phrases directly against the ontology schema.
2. **Feedback loop.** When the AI maps incorrectly, the user corrects ("No, that's a supplier, not a customer"). SHUNYA learns the correction for future.
3. **Domain priming.** The active workspace domain provides context that disambiguates phrases.
4. **Progressive disclosure.** As SHUNYA learns the user's language patterns, suggestions improve. Initial experience is more explicit; mature experience is conversational.
5. **Fallback.** When confidence is low, SHUNYA asks: "Did you mean to add a customer or a supplier?" — turning ambiguity into clarification.

---

*Next: Article V-VI — Workspace Philosophy + Onboarding Redesign*