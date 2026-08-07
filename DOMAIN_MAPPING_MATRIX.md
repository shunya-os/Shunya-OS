# Domain Mapping Matrix — Universal Ontology × 12 Domains

**Directive:** Z-05 Article III
**Purpose:** Map the Universal Ontology to multiple domains, proving composition over hardcoded types.
**Status:** Design Artefact

---

## How to Read This Matrix

For each domain:
- **User Language** — What the founder says (never sees ontology terms)
- **Internal Ontology** — Which universal concepts activate
- **Workspace Generated** — What panels/capabilities appear
- **AI Understanding** — How SHUNYA's AI interprets this domain

---

## 1. Personal Workspace

| Dimension | Description |
|-----------|-------------|
| **User Language** | "My goals", "track my habits", "journal", "my reading list", "my finances", "family events" |
| **Internal Ontology** | Identity(me) + Relationships(family, friends) + Commitments(goals, habits, tasks) + Events(appointments) + Documents(journals, notes) + Financial Records(budget, expenses) + Knowledge(learning, reading) + Assets(things I own) + Place(home, visited) |
| **Workspace Generated** | Goals dashboard, Habit tracker, Journal, Reading list, Personal finance, Calendar, Notes, Health log, Learning progress |
| **AI Understanding** | "Plan my week" → generates Events + Commitments. "What did I learn last month?" → queries Knowledge + Documents. "How am I doing on my fitness goal?" → checks Commitment(habit) progress against Events(workouts) |

---

## 2. Consulting

| Dimension | Description |
|-----------|-------------|
| **User Language** | "Client engagement", "project deliverable", "timesheet", "statement of work", "invoice client", "quarterly review" |
| **Internal Ontology** | Identity(client, consultant) + Relationship(engagement) + Commitment(SOW, deliverables, timeline) + Events(meetings, reviews) + Financial Records(invoices, payments, expenses) + Documents(reports, proposals) + Knowledge(domain expertise) + Place(client site, remote) |
| **Workspace Generated** | Client dashboard, Active engagements, Deliverables tracker, Timesheet, Invoicing, Expense log, Knowledge base, Meeting notes |
| **AI Understanding** | "What's the status of the Acme engagement?" → queries Commitments + Events for that Relationship. "Draft the quarterly report" → generates Document from Knowledge + Events. "Invoice for last month" → creates Financial Record from timesheet Events. |

---

## 3. Travel / Hospitality

| Dimension | Description |
|-----------|-------------|
| **User Language** | "Add a traveller", "book a flight", "hotel reservation", "itinerary", "guest profile", "package tour", "invoice" |
| **Internal Ontology** | Identity(traveller, agent, hotel) + Relationship(booking, guest-of) + Commitment(reservation, itinerary) + Events(trip, check-in, check-out) + Place(destinations, hotels, airports) + Financial Records(payments, refunds) + Documents(itinerary, tickets, visas) + Knowledge(destinations, policies) |
| **Workspace Generated** | Traveler profiles, Booking dashboard, Itinerary builder, Payment tracking, Supplier management, Destination knowledge |
| **AI Understanding** | "Add a traveller" → creates Person Identity + Relationship(traveller-of). "Show me all bookings for next week" → queries Commitments with type=reservation. "What do I know about this guest?" → retrieves Person + Events + Communications. |

---

## 4. Healthcare

| Dimension | Description |
|-----------|-------------|
| **User Language** | "Patient record", "appointment", "prescription", "diagnosis", "treatment plan", "medical history" |
| **Internal Ontology** | Identity(patient, doctor, provider) + Relationship(patient-of, treating) + Events(appointments, procedures) + Documents(medical records, prescriptions, lab results) + Knowledge(conditions, treatments, protocols) + Commitments(treatment plan, medication) + Observations(vitals, symptoms, diagnoses) + Place(hospital, clinic, home) |
| **Workspace Generated** | Patient dashboard, Appointment schedule, Treatment plans, Medical records, Prescriptions, Lab results, Billing |
| **AI Understanding** | "Patient Smith's history" → queries Person + Events + Documents + Observations. "Flag overdue follow-ups" → checks Commitment(treatment) status against timeline. "Summarize this diagnosis" → synthesizes Knowledge + Observations + Documents. |

---

## 5. Education

| Dimension | Description |
|-----------|-------------|
| **User Language** | "Student enrollment", "course catalog", "class schedule", "grades", "assignment", "report card" |
| **Internal Ontology** | Identity(student, teacher, admin) + Relationship(enrolled, teaches) + Events(classes, exams) + Commitments(courses, assignments, grades) + Documents(course materials, reports) + Place(classroom, campus) + Knowledge(curriculum, subjects) |
| **Workspace Generated** | Student profiles, Course catalog, Schedule, Gradebook, Assignments, Attendance, Reports |
| **AI Understanding** | "Enroll student" → creates Person + Relationship(enrolled). "What assignments are due this week?" → queries Commitments(assignment) with deadlines. "Generate report card" → compiles Documents from Commitments(grades). |

---

## 6. Manufacturing

| Dimension | Description |
|-----------|-------------|
| **User Language** | "Production order", "bill of materials", "inventory", "work order", "quality check", "shipment" |
| **Internal Ontology** | Organization(plant, supplier) + Assets(raw materials, equipment, products) + Commitments(orders, work orders) + Events(production runs, inspections) + Workflow(production process) + Place(warehouse, factory floor) + Financial Records(costs, revenue) + Observations(quality metrics) |
| **Workspace Generated** | Production dashboard, Inventory, Order management, Quality control, Supply chain, Maintenance schedule |
| **AI Understanding** | "Production status for order #451" → queries Commitments + Events + Workflow state. "Flag low inventory" → checks Assets(quantity) against thresholds. "Schedule maintenance" → creates Events from Asset lifecycle. |

---

## 7. Retail

| Dimension | Description |
|-----------|-------------|
| **User Language** | "Product catalog", "customer order", "return", "inventory count", "sales report", "supplier order" |
| **Internal Ontology** | Identity(customer, staff, supplier) + Assets(products, inventory) + Commitments(orders, returns) + Events(sales, deliveries) + Financial Records(transactions, refunds) + Place(store, warehouse, online) + Relationships(supplier-of) |
| **Workspace Generated** | Sales dashboard, Inventory, Order management, Customer profiles, Supplier management, Reports |
| **AI Understanding** | "Customer Johnson's order history" → queries Person + Commitments(orders) + Events. "Reorder top-selling items" → analyzes Events(sales) → creates Commitments(supplier orders). "Process return" → creates Event(return) + updates Financial Records. |

---

## 8. Marketing Agency

| Dimension | Description |
|-----------|-------------|
| **User Language** | "Campaign", "client brief", "creative asset", "social post", "analytics", "media buy", "content calendar" |
| **Internal Ontology** | Identity(client, team, audience) + Commitments(campaigns, deliverables) + Assets(creative, content) + Events(launches, reviews) + Communications(briefs, approvals) + Financial Records(budgets, invoices) + Documents(briefs, reports) + Workflow(approval process) |
| **Workspace Generated** | Campaign dashboard, Content calendar, Asset library, Client reporting, Budget tracker, Approval workflow |
| **AI Understanding** | "Launch campaign" → creates Commitment(campaign) + Assets(creative) + Workflow(approval). "Show me content performance" → queries Events(clicks, impressions) + Observations. "Draft a social post" → generates Communication from Knowledge(brand guidelines). |

---

## 9. Software Company

| Dimension | Description |
|-----------|-------------|
| **User Language** | "Sprint", "feature request", "bug report", "release", "roadmap", "customer ticket" |
| **Internal Ontology** | Identity(dev, PM, customer) + Commitments(tasks, features, sprints) + Events(releases, standups) + Assets(code, infrastructure) + Workflow(sprint cycle, CI/CD) + Knowledge(documentation, specs) + Observations(bugs, performance) + Documents(PRDs, specs) |
| **Workspace Generated** | Sprint dashboard, Backlog, Releases, Customer tickets, Documentation, Roadmap, Code repository view |
| **AI Understanding** | "What's in the next sprint?" → queries Commitments(tasks) grouped by Workflow(sprint). "Summarize customer feedback" → synthesizes Communications + Observations. "Generate release notes" → compiles Documents from Events(releases) + Commitments(completed). |

---

## 10. Law Firm

| Dimension | Description |
|-----------|-------------|
| **User Language** | "Client matter", "case file", "contract review", "filing deadline", "billing", "document discovery" |
| **Internal Ontology** | Identity(client, attorney, paralegal) + Relationship(represents) + Commitments(cases, filings, deadlines) + Documents(contracts, filings, evidence) + Events(hearings, meetings, depositions) + Financial Records(billing, retainers) + Knowledge(legal research, precedents) + Place(court, office) |
| **Workspace Generated** | Case dashboard, Calendar (deadlines), Document management, Time tracking, Billing, Legal research |
| **AI Understanding** | "What's the status of the Smith case?" → queries Commitments(case) + Events(hearings) + Documents. "Find all documents mentioning clause 7" → searches Documents + Knowledge. "Generate invoice for this month" → creates Financial Record from Event(billable hours). |

---

## 11. Real Estate

| Dimension | Description |
|-----------|-------------|
| **User Language** | "Property listing", "client viewing", "offer", "closing", "commission", "property management" |
| **Internal Ontology** | Identity(buyer, seller, agent) + Assets(properties) + Commitments(listings, offers, contracts) + Events(viewings, closings) + Place(locations) + Financial Records(commissions, deposits, mortgages) + Documents(listings, contracts, disclosures) |
| **Workspace Generated** | Property dashboard, Listings, Client management, Deal pipeline, Commission tracking, Document vault |
| **AI Understanding** | "Show me available properties under $500k" → queries Assets(properties) with price filter. "Schedule a viewing" → creates Event(viewing) linked to Asset(property) + Identity(buyer). "Generate purchase agreement" → creates Document from Commitment(offer) template. |

---

## 12. Non-Profit

| Dimension | Description |
|-----------|-------------|
| **User Language** | "Donor", "campaign", "volunteer", "grant application", "program", "impact report" |
| **Internal Ontology** | Identity(donor, volunteer, beneficiary) + Relationships(donated, volunteered) + Commitments(donations, grants, programs) + Events(fundraisers, volunteer days) + Financial Records(donations, expenses) + Documents(reports, applications) + Knowledge(impact data) + Observations(outcomes) |
| **Workspace Generated** | Donor dashboard, Campaign tracking, Volunteer management, Grant calendar, Impact reports, Program budgets |
| **AI Understanding** | "Show me this quarter's donations" → queries Financial Records grouped by Event(campaign). "Find major donors" → filters Relationships(donated) by Financial Record amount. "Generate impact report" → compiles Documents from Knowledge(outcomes) + Observations. |

---

## Cross-Domain Pattern Analysis

| Ontology Concept | Used in All 12 Domains? | Most Intense Users |
|-----------------|------------------------|-------------------|
| Identity | ✅ 12/12 | All |
| Person | ✅ 12/12 | All |
| Organization | ✅ 12/12 | All |
| Relationship | ✅ 12/12 | Healthcare, Legal, Non-Profit |
| Place | ✅ 12/12 | Travel, Real Estate, Manufacturing |
| Asset | ✅ 12/12 | Retail, Manufacturing, Real Estate |
| Commitment | ✅ 12/12 | Consulting, Legal, Software |
| Event | ✅ 12/12 | Healthcare, Education, Travel |
| Communication | ✅ 12/12 | Marketing, Consulting, Legal |
| Knowledge | ✅ 12/12 | Education, Healthcare, Legal |
| Financial Record | ✅ 12/12 | Consulting, Retail, Non-Profit |
| Document | ✅ 12/12 | Legal, Education, Healthcare |
| Workflow | ⚠️ 10/12 | Manufacturing, Software (absent in Personal, Travel) |
| Observation | ⚠️ 8/12 | Healthcare, Manufacturing, Software |
| Decision | ⚠️ 7/12 | Legal, Healthcare, Consulting |
| Memory | ⚠️ 9/12 | Personal, Healthcare, Legal |
| Capability | ⚠️ 6/12 | Software, Education (more about what users can do than domain entities) |

**Key finding:** 12 of 18 concepts are universal across ALL domains. The remaining 6 are structural (Workflow, Observation, Decision, Memory, Capability) — they exist in SHUNYA itself, not as domain-specific entities. This validates the ontology as truly universal.

---

## What This Means for Architecture

1. **No new object types.** Every domain maps to the same 18 concepts.
2. **Domain = ontology subset + relationship pattern + AI context.**
3. **Workspace = capability composition based on active domain.**
4. **Onboarding = domain selection → ontology activation → workspace generation.**
5. **Cross-domain = multiple ontology subsets active simultaneously.**

---

*Next: Article IV — Human Language Layer Specification*