# Business-Agnostic Proof — 20 Industries

**Directive:** Z-05 Article X
**Purpose:** Demonstrate that 20 industries can be supported through ontology composition + AI, without custom code per industry.
**Status:** Design Artefact

---

## Method

For each industry, the process is identical:

1. **Onboarding** — User selects industry → domain template activates
2. **Workspace generated** — Capability composition + tenant-specific terminology
3. **AI understanding** — Language Layer primed with industry vocabulary + ontology mapping
4. **Terminology** — User-facing labels use industry language, not ontology terms
5. **Starter dashboards** — Pre-built Analytics queries for common KPIs
6. **Starter capabilities** — Which capabilities activate by default

No custom code. No new object types. No new tables. The same 18 concepts + 18 capabilities serve every industry.

---

## Industry Matrix

### 1. Personal Productivity

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | "How would you like to use SHUNYA?" → Personal Workspace |
| **Generated Workspace** | Goals dashboard, Habit tracker, Journal, Notes, Reading list, Personal finance, Calendar |
| **AI Understanding** | "Plan my week", "Track my reading", "How am I doing on my fitness goal?" |
| **Terminology** | Goals, habits, notes, journal, tasks, reminders, budget, calendar |
| **Starter Dashboards** | Today's agenda, Habit streak, Weekly reflection, Monthly budget |
| **Active Capabilities** | Identity, Memory, Commitments, Events, Knowledge, Financial, Intelligence, Documents |
| **Custom Code Needed** | 0 lines |

### 2. Consulting

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | "How would you like to use SHUNYA?" → My Business → Consulting |
| **Generated Workspace** | Client dashboard, Engagements, Deliverables, Timesheet, Invoicing, Knowledge base |
| **AI Understanding** | "What's the status of the Acme engagement?", "Draft the quarterly report", "Invoice for last month" |
| **Terminology** | Client, engagement, deliverable, timesheet, invoice, SOW, proposal, project |
| **Starter Dashboards** | Active engagements, Utilization rate, Pipeline, Revenue by client, Overdue invoices |
| **Active Capabilities** | Identity, Relationships, Commitments, Events, Financial, Documents, Intelligence, Knowledge, Communications |
| **Custom Code Needed** | 0 lines |

### 3. Travel & Hospitality

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Travel Company |
| **Generated Workspace** | Traveller profiles, Bookings, Itineraries, Supplier management, Payment tracking, Destination knowledge |
| **AI Understanding** | "Add a traveller named Alice", "Book a flight to London", "Show me all bookings for next week" |
| **Terminology** | Traveller, guest, booking, reservation, itinerary, trip, destination, invoice, supplier |
| **Starter Dashboards** | Upcoming bookings, Revenue by destination, Supplier performance, Guest history |
| **Active Capabilities** | Identity, Relationships, Commitments, Events, Place, Financial, Documents, Intelligence, Knowledge |
| **Custom Code Needed** | 0 lines |

### 4. Healthcare

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Healthcare (Hospital, Clinic, Practice) |
| **Generated Workspace** | Patient dashboard, Appointment schedule, Treatment plans, Medical records, Prescriptions, Billing, Lab results |
| **AI Understanding** | "Patient Smith's history", "Flag overdue follow-ups", "Summarize this diagnosis" |
| **Terminology** | Patient, provider, appointment, prescription, diagnosis, treatment, record, billing |
| **Starter Dashboards** | Today's appointments, Patient wait times, Revenue by provider, Treatment outcomes, Overdue follow-ups |
| **Active Capabilities** | Identity, Relationships, Events, Documents, Knowledge, Financial, Observations, Intelligence, Commitments |
| **Custom Code Needed** | 0 lines |

### 5. Education

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Education (School, University, Training) |
| **Generated Workspace** | Student profiles, Course catalog, Schedule, Gradebook, Assignments, Attendance, Reports |
| **AI Understanding** | "Enroll student", "What assignments are due this week?", "Generate report card" |
| **Terminology** | Student, teacher, course, class, assignment, grade, attendance, report card |
| **Starter Dashboards** | Class performance, Attendance trends, Assignment completion, Grade distribution, Schedule |
| **Active Capabilities** | Identity, Relationships, Events, Commitments, Documents, Knowledge, Financial, Intelligence |
| **Custom Code Needed** | 0 lines |

### 6. Manufacturing

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Manufacturing |
| **Generated Workspace** | Production dashboard, Inventory, Orders, Quality control, Supply chain, Maintenance schedule |
| **AI Understanding** | "Production status for order #451", "Flag low inventory", "Schedule maintenance" |
| **Terminology** | Production order, BOM, inventory, work order, quality check, shipment, supplier, maintenance |
| **Starter Dashboards** | Production throughput, Inventory levels, Order fulfillment, Quality metrics, Machine uptime |
| **Active Capabilities** | Identity, Assets, Commitments, Events, Workflows, Observations, Financial, Place, Intelligence |
| **Custom Code Needed** | 0 lines |

### 7. Retail

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Retail |
| **Generated Workspace** | Sales dashboard, Inventory, Order management, Customer profiles, Supplier management, Reports |
| **AI Understanding** | "Customer Johnson's purchase history", "Reorder top-selling items", "Process a return" |
| **Terminology** | Customer, product, order, return, inventory, supplier, sales, report |
| **Starter Dashboards** | Daily sales, Top products, Low stock alerts, Customer lifetime value, Return rate |
| **Active Capabilities** | Identity, Assets, Commitments, Events, Financial, Place, Relationships, Intelligence, Analytics |
| **Custom Code Needed** | 0 lines |

### 8. Marketing Agency

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Agency |
| **Generated Workspace** | Campaign dashboard, Content calendar, Asset library, Client reporting, Budget tracker, Approval workflow |
| **AI Understanding** | "Launch a campaign", "Show me content performance", "Draft a social post for the campaign" |
| **Terminology** | Campaign, client, creative, content, analytics, media buy, budget, approval |
| **Starter Dashboards** | Active campaigns, Content performance, Budget vs actual, Client satisfaction, Pipeline |
| **Active Capabilities** | Identity, Relationships, Commitments, Assets, Events, Communications, Financial, Intelligence, Analytics, Workflows |
| **Custom Code Needed** | 0 lines |

### 9. Software Company

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Software / Technology |
| **Generated Workspace** | Sprint dashboard, Backlog, Releases, Customer tickets, Documentation, Roadmap, Code repository view |
| **AI Understanding** | "What's in the next sprint?", "Summarize customer feedback", "Generate release notes" |
| **Terminology** | Sprint, feature, bug, release, ticket, roadmap, documentation, task |
| **Starter Dashboards** | Sprint progress, Bug age, Release readiness, Customer ticket volume, Team velocity |
| **Active Capabilities** | Identity, Commitments, Events, Workflows, Knowledge, Documents, Observations, Communications, Intelligence |
| **Custom Code Needed** | 0 lines |

### 10. Law Firm

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Law Firm |
| **Generated Workspace** | Case dashboard, Deadline calendar, Document management, Time tracking, Billing, Legal research |
| **AI Understanding** | "What's the status of the Smith case?", "Find all documents mentioning clause 7", "Generate invoice for this month" |
| **Terminology** | Case, client, matter, filing, deadline, contract, discovery, billing, retainer |
| **Starter Dashboards** | Active cases, Upcoming deadlines, Billable hours, Revenue by practice area, Document discovery status |
| **Active Capabilities** | Identity, Relationships, Commitments, Documents, Events, Financial, Knowledge, Decisions, Intelligence |
| **Custom Code Needed** | 0 lines |

### 11. Real Estate

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Real Estate |
| **Generated Workspace** | Property dashboard, Listings, Client management, Deal pipeline, Commission tracking, Document vault |
| **AI Understanding** | "Show me available properties under $500k", "Schedule a viewing", "Generate purchase agreement" |
| **Terminology** | Property, listing, buyer, seller, agent, viewing, offer, closing, commission |
| **Starter Dashboards** | Active listings, Price trends, Days on market, Deal pipeline, Commission forecast |
| **Active Capabilities** | Identity, Assets, Commitments, Events, Place, Financial, Documents, Relationships, Intelligence |
| **Custom Code Needed** | 0 lines |

### 12. Non-Profit

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Non-Profit |
| **Generated Workspace** | Donor dashboard, Campaign tracking, Volunteer management, Grant calendar, Impact reports, Program budgets |
| **AI Understanding** | "Show me this quarter's donations", "Find major donors", "Generate impact report" |
| **Terminology** | Donor, campaign, volunteer, grant, program, impact, beneficiary, fundraising |
| **Starter Dashboards** | Donation trends, Campaign performance, Volunteer hours, Grant pipeline, Program impact metrics |
| **Active Capabilities** | Identity, Relationships, Commitments, Financial, Events, Documents, Knowledge, Observations, Intelligence |
| **Custom Code Needed** | 0 lines |

### 13. Restaurant

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Restaurant |
| **Generated Workspace** | Menu management, Reservations, Orders, Inventory, Staff scheduling, Sales reports, Supplier orders |
| **AI Understanding** | "What's the most popular dish this week?", "Schedule staff for Friday night", "Reorder ingredients" |
| **Terminology** | Menu, reservation, order, table, inventory, supplier, staff, shift, sales |
| **Starter Dashboards** | Daily covers, Popular items, Reservation volume, Inventory alerts, Labor cost vs sales |
| **Active Capabilities** | Identity, Assets, Commitments, Events, Place, Financial, Relationships, Observations, Intelligence |
| **Custom Code Needed** | 0 lines |

### 14. Construction

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Construction |
| **Generated Workspace** | Project dashboard, Site management, Subcontractor tracking, Material orders, Equipment, Safety inspections |
| **AI Understanding** | "What's the status of the Greenfield project?", "Order materials for next week", "Flag safety violations" |
| **Terminology** | Project, site, subcontractor, material, equipment, inspection, permit, change order |
| **Starter Dashboards** | Project timeline, Budget vs actual, Subcontractor performance, Safety incidents, Equipment utilization |
| **Active Capabilities** | Identity, Assets, Commitments, Events, Place, Financial, Workflows, Observations, Documents, Intelligence |
| **Custom Code Needed** | 0 lines |

### 15. Healthcare Practice (Dental, Physio, etc.)

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Healthcare → [Type] |
| **Generated Workspace** | Patient records, Appointment scheduling, Treatment plans, Insurance claims, Inventory supplies |
| **AI Understanding** | "Schedule Jane for a cleaning", "What treatments are due for Mr. Smith?", "Submit insurance claim" |
| **Terminology** | Patient, appointment, treatment, insurance, claim, supply, provider, record |
| **Starter Dashboards** | Daily schedule, Treatment completion, Insurance claims status, Revenue by procedure, Supply inventory |
| **Active Capabilities** | Identity, Events, Commitments, Documents, Financial, Knowledge, Assets, Observations, Intelligence |
| **Custom Code Needed** | 0 lines |

### 16. Coaching & Training

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Coaching / Training |
| **Generated Workspace** | Client profiles, Session schedule, Progress tracking, Program materials, Invoicing, Assessments |
| **AI Understanding** | "What progress has Sarah made?", "Schedule next session", "Generate progress report" |
| **Terminology** | Client, session, program, assessment, goal, progress, invoice, material |
| **Starter Dashboards** | Session calendar, Client progress, Program completion, Revenue, Goal achievement |
| **Active Capabilities** | Identity, Relationships, Commitments, Events, Documents, Knowledge, Observations, Financial, Intelligence |
| **Custom Code Needed** | 0 lines |

### 17. E-commerce

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Retail → E-commerce |
| **Generated Workspace** | Product catalog, Orders, Inventory, Customer profiles, Marketing, Analytics, Fulfillment |
| **AI Understanding** | "Show me this week's top sellers", "Process a refund for order #1234", "Recommend products for customer X" |
| **Terminology** | Product, order, customer, inventory, fulfillment, return, review, analytics |
| **Starter Dashboards** | Sales by product, Order fulfillment, Customer acquisition cost, Return rate, Inventory turnover |
| **Active Capabilities** | Identity, Assets, Commitments, Events, Financial, Place, Relationships, Communications, Intelligence, Analytics |
| **Custom Code Needed** | 0 lines |

### 18. Property Management

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Real Estate → Property Management |
| **Generated Workspace** | Property portfolio, Tenant management, Lease tracking, Maintenance requests, Rent collection, Inspections |
| **AI Understanding** | "Show me units with overdue rent", "Schedule maintenance for unit 4B", "Generate lease renewal" |
| **Terminology** | Property, unit, tenant, lease, maintenance, rent, inspection, vendor |
| **Starter Dashboards** | Occupancy rate, Rent collection, Maintenance backlog, Lease expirations, Property financials |
| **Active Capabilities** | Identity, Assets, Commitments, Events, Place, Financial, Documents, Relationships, Observations, Intelligence |
| **Custom Code Needed** | 0 lines |

### 19. Fitness & Wellness

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | My Business → Fitness / Wellness |
| **Generated Workspace** | Member profiles, Class schedule, Membership management, Trainer assignments, Billing, Progress tracking |
| **AI Understanding** | "What classes are available tomorrow?", "Show me member attendance trends", "Generate membership renewal" |
| **Terminology** | Member, class, trainer, membership, schedule, attendance, billing, progress |
| **Starter Dashboards** | Class attendance, Membership renewals, Trainer utilization, Revenue, Member retention |
| **Active Capabilities** | Identity, Relationships, Events, Commitments, Financial, Place, Observations, Documents, Intelligence |
| **Custom Code Needed** | 0 lines |

### 20. Freelancer / Creator

| Dimension | Specification |
|-----------|--------------|
| **Onboarding** | Personal Workspace → Freelancer / Creator |
| **Generated Workspace** | Client dashboard, Project tracker, Time tracking, Invoicing, Portfolio, Expense tracking, Tax prep |
| **AI Understanding** | "Send invoice to client X for this month's work", "Track my expenses for Q3", "What's my utilization rate?" |
| **Terminology** | Client, project, invoice, expense, portfolio, milestone, contract, rate |
| **Starter Dashboards** | Active projects, Income vs expenses, Invoicing status, Client pipeline, Tax estimates |
| **Active Capabilities** | Identity, Relationships, Commitments, Events, Financial, Documents, Knowledge, Assets, Intelligence |
| **Custom Code Needed** | 0 lines |

---

## Proof Summary

| Industry | Custom Object Types Needed | Custom Code Lines | New Ontology Concepts |
|----------|--------------------------|-------------------|----------------------|
| Personal Productivity | 0 | 0 | 0 (uses 10 of 18) |
| Consulting | 0 | 0 | 0 (uses 12 of 18) |
| Travel & Hospitality | 0 | 0 | 0 (uses 11 of 18) |
| Healthcare | 0 | 0 | 0 (uses 12 of 18) |
| Education | 0 | 0 | 0 (uses 11 of 18) |
| Manufacturing | 0 | 0 | 0 (uses 12 of 18) |
| Retail | 0 | 0 | 0 (uses 11 of 18) |
| Marketing Agency | 0 | 0 | 0 (uses 13 of 18) |
| Software Company | 0 | 0 | 0 (uses 12 of 18) |
| Law Firm | 0 | 0 | 0 (uses 12 of 18) |
| Real Estate | 0 | 0 | 0 (uses 11 of 18) |
| Non-Profit | 0 | 0 | 0 (uses 12 of 18) |
| Restaurant | 0 | 0 | 0 (uses 11 of 18) |
| Construction | 0 | 0 | 0 (uses 13 of 18) |
| Healthcare Practice | 0 | 0 | 0 (uses 12 of 18) |
| Coaching & Training | 0 | 0 | 0 (uses 11 of 18) |
| E-commerce | 0 | 0 | 0 (uses 12 of 18) |
| Property Management | 0 | 0 | 0 (uses 12 of 18) |
| Fitness & Wellness | 0 | 0 | 0 (uses 11 of 18) |
| Freelancer / Creator | 0 | 0 | 0 (uses 11 of 18) |

**Total custom code required: 0 lines.**
**Total new concepts needed: 0.**
**The same 18 universal concepts serve all 20 industries.**

---

*Next: Article XII — Genesis Readiness*