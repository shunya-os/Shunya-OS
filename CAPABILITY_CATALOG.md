# Capability Catalog

**Directive:** Z-05 Article XI
**Purpose:** Replace modules with capabilities. Every workspace is composed from capabilities, not from hardcoded features.
**Status:** Design Artefact

---

## The Capability Model

SHUNYA has capabilities, not modules. A capability is a primitive atomic unit of functionality that SHUNYA can exercise.

| Old Thinking | New Thinking |
|-------------|-------------|
| "CRM module" | Identity + Relationship + Commitment capabilities |
| "Invoicing module" | Financial Record + Commitment capabilities |
| "Marketing module" | Commitment(campaign) + Assets(creative) + Event capabilities |
| "HR module" | Identity + Relationship + Workflow capabilities |
| "Project management" | Commitment + Event + Document capabilities |

---

## Complete Capability Catalog

### 1. Identity
Manage persons and organizations — create, find, verify, link.

```
Primitives:
  create_person(name, attributes)
  create_organization(name, metadata)
  find_identity(query)
  link_identities(source, target, type)
  verify_identity(id, method)
  merge_identities(primary, duplicate)
```

**Used by:** Every workspace type.

### 2. Memory
Persistent understanding built from past interactions.

```
Primitives:
  recall(context) → relevant past events, communications, decisions
  consolidate(memory) → store as knowledge
  forget(memory_id) → age out
  pattern_match(query) → find similar past situations
```

**Used by:** AI, Workspace, Decisions, Knowledge.

### 3. Knowledge
Structured information storage and retrieval.

```
Primitives:
  store_knowledge(content, domain, source)
  retrieve_knowledge(query, domain)
  embed(text) → vector for semantic search
  semantic_search(query, limit) → ranked results
  categorize(document, taxonomy)
```

**Used by:** Search, AI, Learning, Documents.

### 4. Relationships
Manage connections between identities and records.

```
Primitives:
  create_relationship(source, target, type, properties)
  find_relationships(id, type, direction)
  relationship_graph(id, depth) → network view
  relationship_strength(id1, id2) → computed closeness
  suggest_relationships(id) → AI-proposed connections
```

**Used by:** CRM, Social, Collaboration, Networking.

### 5. Communication
Send, receive, and manage messages across channels.

```
Primitives:
  send(channel, to, subject, body, attachments)
  receive(channel, filter) → inbox
  thread(communication_id) → conversation view
  template(name, variables) → formatted message
  schedule_communication(when, communication)
```

**Used by:** Email, SMS, WhatsApp, Notifications, Campaigns.

### 6. Decisions
Record, evaluate, and learn from choices.

```
Primitives:
  record_decision(subject, options, outcome, rationale, authority)
  evaluate_decision(id) → quality score
  decision_context(id) → what informed this decision
  suggest_decision(context) → AI recommendation
  decision_log(filters) → audit trail
```

**Used by:** Approvals, AI recommendations, Strategy, Governance.

### 7. Commitments
Manage agreements, obligations, promises, and deadlines.

```
Primitives:
  create_commitment(type, parties, terms, value)
  fulfill_commitment(id, evidence)
  breach_commitment(id, reason)
  find_pending(identity, timeframe)
  escalate_overdue(threshold)
```

**Used by:** Tasks, Invoices, Contracts, Goals, Proposals, SLAs.

### 8. Finance
Track monetary movement, budgets, and financial positions.

```
Primitives:
  record_transaction(from, to, amount, category, linked_record)
  reconcile(records) → match transactions
  budget(period, categories, amounts)
  financial_statement(type, period) → P&L, balance sheet
  forecast(period, model) → predicted financial position
```

**Used by:** Accounting, Invoicing, Budgeting, Personal Finance, Payroll.

### 9. Search
Find anything across all record types.

```
Primitives:
  search(query, filters, limit)
  full_text(query) → all text fields
  semantic(text) → meaning-based results
  cross_reference(id, type) → find related records
  global() → across all workspaces
```

**Used by:** Every workspace, every capability.

### 10. Intelligence
AI capabilities — understand, generate, reason, recommend.

```
Primitives:
  understand(text, context) → structured intent
  generate(prompt, format) → text, document, email
  reason(premises, question) → conclusion
  recommend(context, options) → ranked suggestions
  summarize(records, style) → condensed brief
  translate(text, target_language)
  classify(text, categories)
  extract(text, schema) → structured data
```

**Used by:** Language Layer, AI Resident, Suggestions, Automation.

### 11. Automation
Trigger actions based on conditions, schedules, or events.

```
Primitives:
  define_rule(trigger, condition, action)
  schedule_rule(when, action)
  trigger_rule(event, context)
  evaluate_rules(context) → applicable actions
  automation_log() → what ran and when
```

**Used by:** Workflows, Notifications, Reminders, Escalations.

### 12. Collaboration
Enable multiple identities to work together.

```
Primitives:
  share(record_id, with_identity, permission)
  comment(record_id, text, author)
  assign(commitment_id, to_identity)
  notify(identity, message, importance)
  workspace_invite(email, role, workspace_id)
```

**Used by:** Teams, Projects, Family Workspace, Client Portals.

### 13. Governance
Enforce policies, rules, and compliance.

```
Primitives:
  define_policy(name, rules, scope)
  check_compliance(record_id, policy) → pass/fail
  audit_log(filters) → all changes with identities
  approve(record_id, decision_id)
  enforce_rule(rule, context) → allow/deny
```

**Used by:** Permissions, Compliance, Quality, Architecture Validation.

### 14. Documents
Create, store, manage, and transform documents.

```
Primitives:
  create_document(content, format, metadata)
  store_document(file, metadata)
  generate_document(template, variables) → PDF, DOCX
  sign_document(document_id, identity)
  version(document_id) → revision history
  convert(document_id, target_format)
```

**Used by:** Reports, Contracts, Invoices, Proposals, Knowledge.

### 15. Analytics
Measure, visualize, and understand data.

```
Primitives:
  aggregate(records, dimensions, measures)
  visualize(data, chart_type) → chart configuration
  trend(records, metric, period) → change over time
  compare(groups, metric) → difference analysis
  anomaly_detect(records, metric) → outliers
  export_analytics(data, format)
```

**Used by:** Dashboards, Reports, Insights, BI.

### 16. Events
Track and manage occurrences across time.

```
Primitives:
  record_event(type, participants, timestamp, place, outcome)
  find_events(filters, timeframe)
  schedule_event(type, participants, when, where)
  event_series(pattern, count, interval) → recurring events
  link_event_to(event_id, record_id, relationship)
```

**Used by:** Calendar, Timeline, Activity Log, Workflows.

### 17. Observations
Perceive and record facts about the world.

```
Primitives:
  observe(subject, predicate, value, source, confidence)
  validate_observation(observation_id, method)
  trend_observations(predicate, period) → changes
  alert_on_observation(rule, observation) → notify
  inference(observations) → derived conclusions
```

**Used by:** Monitoring, Health checks, IoT, Behavior tracking, Analytics.

### 18. Assets
Manage items of value — physical, digital, financial, intellectual.

```
Primitives:
  register_asset(type, value, owner, custodian, metadata)
  transfer_asset(asset_id, new_owner, reason)
  depreciate(asset_id, method, period)
  inventory(filters) → current stock/value
  asset_lifecycle(asset_id) → history
```

**Used by:** Inventory, Product catalog, Equipment, IP, Brand.

---

## Workspace Composition

A workspace is a set of activated capabilities, not a set of pages.

| Workspace Type | Activated Capabilities |
|---------------|----------------------|
| **Executive Home** | Identity, Memory, Intelligence, Commitments, Analytics, Search, Events |
| **CRM** | Identity, Relationships, Communications, Commitments, Events, Intelligence |
| **Finance** | Financial, Commitments, Documents, Analytics, Search |
| **Marketing** | Identity, Relationships, Communications, Assets, Commitments, Events, Intelligence, Analytics |
| **Operations** | Commitments, Events, Assets, Workflows, Observations, Analytics |
| **Personal** | Identity, Memory, Commitments, Events, Knowledge, Financial, Intelligence |
| **Project Management** | Commitments, Events, Documents, Collaboration, Workflows |
| **Legal** | Documents, Commitments, Decisions, Events, Knowledge, Identity |
| **Support** | Identity, Communications, Commitments, Workflows, Knowledge, Events |
| **Analytics** | Analytics, Intelligence, Search, Financial |

---

## Capability Activation Rules

1. **Capabilities are activated by domain, not purchased.**
   - Choosing "Consulting" activates Identity + Relationships + Commitments + Financial + Documents + Intelligence.
   - Choosing "Personal" activates Identity + Memory + Commitments + Events + Knowledge + Financial + Intelligence.

2. **Multiple capabilities can be active simultaneously.**
   - A consulting firm using Marketing = Identity + Relationships + Commitments + Financial + Communications + Assets + Intelligence.

3. **Capabilities share a unified data model.**
   - A Person created by Identity capability is the same Person used by Communications, Commitments, and Financial.
   - There is no "CRM contact" vs "Marketing lead" — there is only a Person with different relationship types.

4. **AI enables capabilities to compose dynamically.**
   - When the user says "Create an invoice for the Acme project", SHUNYA uses:
     - Intelligence (understand intent)
     - Identity (find Acme)
     - Commitments (find project, create invoice)
     - Financial (set amount)
     - Documents (generate PDF)
     - Communications (send to client)

5. **No capability requires another to function — but they amplify each other.**
   - Identity works alone. Identity + Intelligence = smart suggestions. Identity + Intelligence + Memory = proactive relationship management.

---

## What This Replaces

| Current SHUNYA Feature | Capability Composition |
|-----------------------|----------------------|
| "Executive Home" dashboard | Analytics + Intelligence + Memory + Commitments |
| "New Object" modal | Identity (for Person/Org), Commitments (for Tasks/Invoices), Assets (for Products) |
| "AI Resident" | Intelligence + Memory + Knowledge |
| "System Status" | Observations + Events |
| Context Panel | Memory + Relationships + Events + Commitments |
| Command Surface | Intelligence (all capabilities accessible via language) |

---

*Next: Article XII — Genesis Readiness*