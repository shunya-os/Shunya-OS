# Department Capability & Marketing Intelligence Audit

**Directive:** Z-05 Article VII-VIII
**Purpose:** Audit every organizational function and demonstrate how it emerges from Universal Ontology.
**Status:** Design Artefact

---

## Article VII — Department Capability Audit

Every department's needs are expressed as a composition of universal capabilities, not as isolated modules.

### Marketing

| Need | Universal Ontology Representation | Capabilities Required |
|------|----------------------------------|----------------------|
| Campaign management | Commitment(campaign) + Events(launches) + Assets(creative) + Workflow(approval) | Identity, Commitment, Event, Asset, Workflow |
| Audience segmentation | Relationships + Knowledge(preferences) + Observations(behavior) | Identity, Relationship, Knowledge, Observation |
| Brand management | Asset(brand) + Document(guidelines) + Asset(creative) | Asset, Document, Identity |
| Content creation | Document + Asset(media) + Knowledge(topic) + Workflow(review) | Document, Asset, Knowledge, Workflow |
| Social publishing | Communication(channel=social) + Commitment(posts) + Workflow(calendar) | Communication, Commitment, Workflow |
| Analytics & attribution | Events(clicks, views) + Observations(conversions) + Decisions(budget allocation) | Event, Observation, Decision, Financial Record |

### Sales

| Need | Universal Ontology Representation | Capabilities Required |
|------|----------------------------------|----------------------|
| Lead management | Person + Relationship(prospect) + Workflow(pipeline) + Observations(engagement) | Identity, Relationship, Workflow, Observation |
| Deal tracking | Commitment(deal) + Events(meetings) + Communications(emails) + Documents(proposals) | Commitment, Event, Communication, Document |
| Territory management | Place(region) + Relationships(assigned) + Commitments(targets) | Place, Identity, Relationship, Commitment |
| Quota & targets | Commitment(quota) + Financial Records(revenue) + Observations(progress) | Commitment, Financial Record, Observation |
| Forecasting | Events(pipeline) + Knowledge(historical) + Decision(predictions) | Event, Knowledge, Decision, Memory |

### CRM

| Need | Universal Ontology Representation | Capabilities Required |
|------|----------------------------------|----------------------|
| Contact management | Person + Organization + Relationship | Identity |
| Interaction history | Events + Communications + Commitments | Event, Communication, Commitment, Memory |
| Customer segmentation | Relationships + Knowledge + Observations | Identity, Relationship, Knowledge, Observation |
| Support tickets | Commitment(ticket) + Workflow(resolution) + Communication | Commitment, Workflow, Communication |
| Customer health | Observations(satisfaction) + Events(engagement) + Memory(history) | Observation, Event, Memory |

### Finance

| Need | Universal Ontology Representation | Capabilities Required |
|------|----------------------------------|----------------------|
| Accounts payable | Commitment(bills) + Financial Records(payments) + Relationships(suppliers) | Commitment, Financial Record, Identity, Relationship |
| Accounts receivable | Commitment(invoices) + Financial Records(payments) + Relationships(customers) | Commitment, Financial Record, Identity, Relationship |
| Budgeting | Financial Record(budget) + Commitments(allocations) + Events(spend) | Financial Record, Commitment, Event |
| Expense management | Financial Record(expenses) + Events(purchases) + Asset(receipts) | Financial Record, Event, Asset, Document |
| Payroll | Commitment(employment) + Financial Record(salary) + Events(payments) | Commitment, Financial Record, Event, Identity |
| Reporting | Documents(reports) + Knowledge(financial) + Decisions(strategy) | Document, Knowledge, Decision |

### HR

| Need | Universal Ontology Representation | Capabilities Required |
|------|----------------------------------|----------------------|
| Employee records | Person + Relationship(employed-by) + Documents | Identity, Relationship, Document |
| Recruitment | Person(candidate) + Workflow(hiring) + Events(interviews) + Decisions(hires) | Identity, Workflow, Event, Decision |
| Onboarding | Workflow(onboarding) + Events(training) + Commitments(probation) | Workflow, Event, Commitment, Document |
| Performance | Observations(reviews) + Commitments(goals) + Events(1:1s) + Documents(feedback) | Observation, Commitment, Event, Document |
| Leave management | Commitment(leave) + Events(absence) + Workflow(approval) | Commitment, Event, Workflow |
| Learning & development | Knowledge(courses) + Events(training) + Commitments(certification) | Knowledge, Event, Commitment |

### Operations

| Need | Universal Ontology Representation | Capabilities Required |
|------|----------------------------------|----------------------|
| Project management | Commitment(project) + Events(milestones) + Persons(team) + Documents(plans) | Commitment, Event, Identity, Document, Workflow |
| Procurement | Commitment(purchase orders) + Assets(goods) + Relationships(suppliers) | Commitment, Asset, Identity, Relationship |
| Inventory | Assets(stock) + Events(receipts/shipments) + Observations(levels) | Asset, Event, Observation |
| Quality | Observations(inspections) + Events(checks) + Decisions(approvals) | Observation, Event, Decision |
| Facilities | Place(offices) + Assets(equipment) + Events(maintenance) | Place, Asset, Event |

### Legal

| Need | Universal Ontology Representation | Capabilities Required |
|------|----------------------------------|----------------------|
| Contract management | Commitment(contracts) + Documents + Events(renewals) + Relationships(parties) | Commitment, Document, Event, Identity |
| Case management | Commitment(cases) + Events(hearings) + Documents(filings) + Decisions(rulings) | Commitment, Event, Document, Decision |
| Compliance | Knowledge(regulations) + Observations(audits) + Commitments(requirements) | Knowledge, Observation, Commitment |
| IP management | Asset(IP) + Documents(patents) + Relationships(owners) | Asset, Document, Identity, Relationship |

### Customer Success

| Need | Universal Ontology Representation | Capabilities Required |
|------|----------------------------------|----------------------|
| Health scoring | Observations(product usage, satisfaction) + Memory(history) | Observation, Memory, Knowledge |
| Renewal management | Commitment(contracts) + Events(expiry) + Communications(renewal) | Commitment, Event, Communication |
| Upsell/cross-sell | Knowledge(needs) + Relationships + Events(engagement) + Decisions(recommendations) | Knowledge, Identity, Event, Decision |
| NPS & feedback | Observations(feedback) + Events(surveys) + Knowledge(insights) | Observation, Event, Knowledge |

### IT

| Need | Universal Ontology Representation | Capabilities Required |
|------|----------------------------------|----------------------|
| Asset management | Assets(hardware, software, licenses) + Events(lifecycle) | Asset, Event |
| Access control | Identity + Capabilities + Relationships(permissions) | Identity, Capability, Relationship |
| Incident management | Commitment(tickets) + Workflow(resolution) + Events(outages) | Commitment, Workflow, Event |
| Monitoring | Observations(metrics, uptime) + Events(alerts) + Knowledge(playbooks) | Observation, Event, Knowledge |

---

## Key Insight: Only 18 Concepts Needed

Every department above uses only the 18 universal concepts. No department requires a custom object type.

| Department | Concepts Used (of 18) | Unique Concepts |
|-----------|----------------------|-----------------|
| Marketing | 14 | Asset (campaign assets) |
| Sales | 13 | Place (territories) |
| CRM | 12 | — |
| Finance | 11 | — |
| HR | 12 | Workflow (recruitment) |
| Operations | 11 | Place (facilities) |
| Legal | 11 | — |
| Customer Success | 9 | — |
| IT | 10 | — |

No department uses more than 14 of the 18 concepts. Most use 10-12. The same concepts are reused across departments with different relationship patterns.

---

## Article VIII — Marketing Intelligence Specification

Marketing does not exist merely as "Leads." Complete marketing capabilities emerge from ontology composition.

### Ontology-Based Marketing Model

```
Person (site visitor, customer, influencer)
  ↓ Relationships
  ├── Campaign (Commitment)
  │   ├── Asset (creative, content, ads)
  │   ├── Event (launch, review, end)
  │   └── Communication (email, social, SMS)
  ├── Audience (Knowledge + Relationships)
  │   ├── Persona (Knowledge + Observations)
  │   ├── Segment (Relationship filter)
  │   └── Attribution (Events + Decisions)
  ├── Brand (Asset + Document)
  │   ├── Guidelines (Document)
  │   ├── Assets (logos, colors, fonts)
  │   └── Voice (Knowledge)
  ├── Funnel (Workflow)
  │   ├── Stages (Workflow states)
  │   └── Conversion (Events between stages)
  ├── Analytics (Events + Observations + Knowledge)
  │   ├── Attribution (Decision — which touchpoint influenced)
  │   ├── ROI (Financial Record)
  │   └── Forecasting (Knowledge + Memory)
  └── Budget (Financial Record + Commitments)
```

### Complete Marketing Capability Map

| Capability | Internal Ontology | How It Emerges |
|-----------|------------------|----------------|
| Campaigns | Commitment + Events + Assets + Workflow | A campaign IS a commitment with start/end dates, creative assets, and an approval workflow |
| Audiences | Knowledge + Relationships | An audience IS a set of relationship filters applied to Persons |
| Personas | Knowledge + Observations | A persona IS a cluster of observations about a group of Persons |
| Content | Asset + Document | Content IS an asset with format=document |
| Creative Assets | Asset | Creative IS an asset with type=creative |
| Social Publishing | Communication + Commitment + Workflow | A social post IS a communication with a publishing schedule |
| SEO | Knowledge + Observations | SEO IS knowledge about keywords + observations of ranking |
| Analytics | Events + Observations | Analytics ARE events (clicks, views, conversions) + observations (trends) |
| Attribution | Decisions + Events | Attribution IS decisions about which events influenced a conversion |
| Funnels | Workflow | A funnel IS a workflow with stages as states |
| Events (marketing) | Event + Place + Commitment | A marketing event IS an event at a place with a commitment to attend |
| Brand | Asset + Document + Knowledge | Brand IS asset + document + knowledge |
| PR | Communication + Relationships | PR IS communication with media relationships |
| Influencers | Person + Relationships + Commitments | An influencer IS a person with a relationship and possibly a sponsorship commitment |
| Budgets | Financial Record + Commitments | A budget IS a financial record with spending commitments |

### Marketing Dashboard Generation

```
Marketing Workspace (generated from capabilities):

┌──────────────────────────────────────────┐
│ MARKETING WORKSPACE                      │
│                                          │
│ Active Campaigns: 4  │  Budget: $45k     │
│ Leads this month: 87 │  Conv. rate: 3.2% │
│──────────────────────────────────────────│
│ Campaign: "Summer Launch"                │
│  Status: Active  │  Budget: $15k/$20k    │
│  Impressions: 45k│  CTR: 2.1%            │
│  Next: Review creatives (Wed)            │
│──────────────────────────────────────────│
│ AI Suggestion: "Top-performing content   │
│ this week is the blog post on pricing.   │
│ Consider promoting it on LinkedIn."      │
└──────────────────────────────────────────┘
```

### Key Difference From Current Approach

| Current (CRM-oriented) | Marketing Intelligence (Ontology-based) |
|----------------------|----------------------------------------|
| Marketing = Leads module | Marketing = Person + Relationships + Commitments + Events + Assets |
| Campaign = separate table | Campaign = Commitment with linked Assets + Events |
| Content = upload to "Documents" | Content = Asset with type=content, format knowledge |
| Attribution = custom code | Attribution = Events(conversions) + Decisions(touchpoints) |
| New marketing need → new table | New marketing need → new composition of existing concepts |

---

*Next: Article IX — Personal Workspace Specification*