# SHUNYA — Business-Agnostic Personal OS Architecture

## The Core Insight

SHUNYA does not care what kind of business you run.
SHUNYA does not care what job title you hold.
SHUNYA cares about the **patterns** of human work.

Every business, every profession, every human life follows the same fundamental patterns:

| Pattern | SHUNYA Abstraction | Example 1 (Agency) | Example 2 (Creator) | Example 3 (Solopreneur) |
|---------|-------------------|-------------------|--------------------|------------------------|
| You have people | **Identities + Relationships** | Clients, team, vendors | Audience, collaborators, sponsors | Customers, partners, leads |
| You do work for them | **Objects + Commitments** | Campaigns, invoices, proposals | Content pieces, brand deals, products | Projects, invoices, tasks |
| You talk to them | **Conversations** | Client calls, team standups | Community replies, interview calls | Sales calls, support chats |
| Money changes hands | **Transactions** | Invoices, expenses, payroll | Affiliate payouts, sponsorships | Sales, refunds, fees |
| Things have deadlines | **Calendar + Nudges** | Campaign launch dates | Content calendar | Payment due dates |
| You make decisions | **Priorities + AI** | Which client to prioritize | Which content to publish | Which product to build |
| You learn and grow | **Knowledge + Skills** | Industry research, team training | Trend research, skill development | Market research, course learning |

## What This Means for Code

**Backend: No business-specific logic in core models.**
- `Identities` → any human (client, team member, partner, friend)
- `Objects` → any work unit (project, campaign, product, content)
- `Commitments` → any obligation (invoice, contract, task, goal)
- The Nudge Engine works on **patterns** (overdue, stalled, at-risk) — not business rules

**Frontend: Workspaces are type-driven, not business-specific.**
- A "Customer" workspace and a "Fan" workspace render the **same LivingWorkspace** with different panels
- The Calendar workspace works for business deadlines AND personal appointments
- The Email workspace handles client emails AND family emails
- The Music workspace is for focus music, not business music — there's no distinction

## What This Enables

A carpenter and a coder both have:
- People (clients, suppliers, family)
- Work (projects, invoices, tasks)
- Conversations (calls, emails, chats)
- Calendar (deadlines, appointments, events)
- Learning (skills, courses, research)
- Health (steps, sleep, meals)
- Money (income, expenses, savings)
- Time (what needs attention right now)

SHUNYA serves all of them with the same code. The difference is **only in the data** — not in the architecture.

## The API Backing (from the v2 Map)

| Dimension | Free API | Works for Any Business |
|-----------|----------|----------------------|
| Auth | Supabase Auth | Any identity, any org |
| Email | Gmail API | Any inbox |
| Calendar | Google Calendar API | Any schedule |
| Docs | BlockNote | Any document |
| Money | Tesseract OCR + Custom | Any transaction |
| Maps | Leaflet + OSM | Any location |
| Media | YouTube IFrame | Any content |
| AI | OpenRouter | Any intelligence task |