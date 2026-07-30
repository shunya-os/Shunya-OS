# SHUNYA PLP Cycle 3.1 — Founder Acceptance Checklist
## XYZ Company — Complete Organizational Validation
## 100+ Tasks Covering Every Role, Capability, and Workflow

**Date:** 2026-07-30
**Organization:** XYZ Company (id=12)
**Members:** 19 | **Departments:** 7 | **Roles:** 5 (owner, admin, manager, member, viewer)

---

## SECTION 1: ORGANIZATION CREATION & SETUP (Tasks 1-10)

| # | Role | Objective | Expected Behaviour | Status |
|---|------|-----------|-------------------|--------|
| 1 | Founder | Sign up for SHUNYA | Email registration creates identity, org, and space | |
| 2 | Founder | Create organization profile | Org name, slug, business_type, email, phone, website saved | |
| 3 | Founder | Configure brand settings | Logo, brand colors, tagline, description persisted | |
| 4 | Founder | Set business information | Tax ID, registration, address, city, country saved | |
| 5 | Founder | Configure timezone & currency | UTC, USD settings applied to org | |
| 6 | Founder | Enable AI features | ai_enabled=true, default config applied | |
| 7 | Founder | Set max members | 50 member limit enforced | |
| 8 | Founder | View organization dashboard | Day-one dashboard shows empty state with guidance | |
| 9 | Founder | Begin onboarding flow | Progressive questions appear (company, industry, team size) | |
| 10 | Founder | Complete onboarding | All 3 stages answerable, org gets updated | |

---

## SECTION 2: DEPARTMENT MANAGEMENT (Tasks 11-20)

| # | Role | Objective | Expected Behaviour | Status |
|---|------|-----------|-------------------|--------|
| 11 | Founder | Create Sales department | Department created with name, description | |
| 12 | Founder | Create Operations department | Department created with name, description | |
| 13 | Founder | Create Finance department | Department created with name, description | |
| 14 | Founder | Create HR department | Department created with name, description | |
| 15 | Founder | Create Marketing department | Department created with name, description | |
| 16 | Founder | Create Support department | Department created with name, description | |
| 17 | Founder | Set department head for Sales | David Director assigned as head | |
| 18 | Founder | Set department hierarchy | Parent-child relationships defined | |
| 19 | Founder | Edit department description | Description updated successfully | |
| 20 | Founder | Deactivate department | is_active=false, members reassigned | |

---

## SECTION 3: MEMBER MANAGEMENT (Tasks 21-35)

| # | Role | Objective | Expected Behaviour | Status |
|---|------|-----------|-------------------|--------|
| 21 | Founder | Invite David Director | Email invitation sent, token generated | |
| 22 | Founder | Invite Olivia Director | Operations director invited with admin role | |
| 23 | Founder | Invite Felicia Director | Finance director invited with admin role | |
| 24 | Founder | Invite Henry Director | HR director invited with admin role | |
| 25 | Founder | Invite 5 managers | Sales, Ops, Finance, HR, Marketing managers invited | |
| 26 | Founder | Invite 6 staff members | Sales exec, Ops associate, Finance associate, etc. | |
| 27 | Founder | Set member roles | owner, admin, manager, member, viewer assigned correctly | |
| 28 | Founder | Assign members to department | Each member linked to correct department | |
| 29 | David Director | Accept invitation | Invitation accepted, joins org as admin | |
| 30 | Maya Manager | Accept invitation | Invitation accepted, joins org as manager | |
| 31 | Sarah Sales | Accept invitation | Invitation accepted, joins org as member | |
| 32 | Founder | Rescind invitation | Invitation cancelled, token invalidated | |
| 33 | Founder | Deactivate member | Member is_active=false, cannot login | |
| 34 | Founder | Reactivate member | Member is_active=true, can login again | |
| 35 | Founder | Remove member from org | Member record deleted or soft-deleted | |

---

## SECTION 4: IDENTITY & AUTHENTICATION (Tasks 36-50)

| # | Role | Objective | Expected Behaviour | Status |
|---|------|-----------|-------------------|--------|
| 36 | Founder | Login with email & password | Authenticated, session created | |
| 37 | Founder | Verify session persists after refresh | Still logged in, session cookie valid | |
| 38 | Founder | Logout | Session cleared, redirected to login | |
| 39 | Founder | Re-login after logout | Fresh session created, org context restored | |
| 40 | Founder | Wrong password attempt | 401 error, "Invalid email or password" | |
| 41 | Founder | Empty email field | Validation error, form not submitted | |
| 42 | Founder | Empty password field | Validation error, form not submitted | |
| 43 | Founder | Access profile | Name, email, role, identity_id returned | |
| 44 | David Director | Login | Director authenticated with admin role | |
| 45 | Maya Manager | Login | Manager authenticated with manager role | |
| 46 | Sarah Sales | Login | Staff authenticated with member role | |
| 47 | Founder | View team list | All 19 members visible to founder | |
| 48 | David Director | View team list | All members visible to director (admin) | |
| 49 | Maya Manager | View team list | Only department members visible to manager | |
| 50 | Sarah Sales | View team list | Only own profile visible to member | |

---

## SECTION 5: PERMISSION VALIDATION (Tasks 51-65)

| # | Role | Objective | Expected Behaviour | Status |
|---|------|-----------|-------------------|--------|
| 51 | Founder | Access all org settings | Org edit, delete, manage members, billing all accessible | |
| 52 | Founder | Manage roles | Create, edit, delete roles and permissions | |
| 53 | Founder | View audit logs | All org activity visible | |
| 54 | David Director | View org settings | Org settings visible, can edit org info | |
| 55 | David Director | Delete org | Denied (only owner can delete) | |
| 56 | David Director | Manage members | Can add/remove members (admin permission) | |
| 57 | Maya Manager | Create proposals | Manager can create, edit, send, approve proposals | |
| 58 | Maya Manager | Delete org | Denied (insufficient permissions) | |
| 59 | Maya Manager | View finance reports | Manager can view finance reports | |
| 60 | Maya Manager | Edit finance records | Denied (insufficient permissions) | |
| 61 | Sarah Sales | View own tasks | Can see tasks assigned to self | |
| 62 | Sarah Sales | Create tasks | Can create tasks | |
| 63 | Sarah Sales | Delete org | Denied | |
| 64 | Sarah Sales | View all proposals | Can view proposals (member permission) | |
| 65 | Eve Viewer | Read-only access | Can view but not create or edit any data | |

---

## SECTION 6: WORKSPACE VALIDATION (Tasks 66-78)

| # | Role | Objective | Expected Behaviour | Status |
|---|------|-----------|-------------------|--------|
| 66 | Founder | View founder workspace | All 19 experiences available (business + optional + restricted) | |
| 67 | Founder | Access Executive Intelligence | Executive dashboard shows org health, pipeline, insights | |
| 68 | Founder | Access Business Dashboard | Dashboard shows metrics, recent activity, recommendations | |
| 69 | David Director | View director workspace | Business experiences + optional experiences visible | |
| 70 | David Director | Access sales-related data | Sales metrics, team performance visible | |
| 71 | Maya Manager | View manager workspace | Business experiences visible, restricted experiences hidden | |
| 72 | Maya Manager | Switch to focus mode | Only business experiences shown | |
| 73 | Sarah Sales | View member workspace | Business experiences visible, no restricted experiences | |
| 74 | Sarah Sales | Switch to break mode | Optional experiences become available | |
| 75 | Founder | Configure workspace policies | Org-level policy set for specific experiences | |
| 76 | Founder | Set experience to "controlled" | Experience only available in appropriate context | |
| 77 | Founder | Set experience to "disabled" | Experience hidden from all users | |
| 78 | Founder | Verify policy inheritance | Org → department → team → individual hierarchy | |

---

## SECTION 7: AI CAPABILITY VALIDATION (Tasks 79-90)

| # | Role | Objective | Expected Behaviour | Status |
|---|------|-----------|-------------------|--------|
| 79 | Founder | Ask AI about company context | AI identifies XYZ Company, knows departments and members | |
| 80 | Founder | Ask AI about user identity | AI knows founder's name, role, permissions | |
| 81 | Founder | Ask AI about organizational hierarchy | AI describes reporting structure, department heads | |
| 82 | Founder | Ask AI about permissions | AI correctly states what founder can access | |
| 83 | Founder | Multi-turn conversation | AI remembers previous messages in the conversation | |
| 84 | Founder | Ask AI to explain business data | AI analyzes org data and provides insights | |
| 85 | Founder | Ask AI for recommendations | AI suggests actionable next steps | |
| 86 | Founder | Ask AI to summarize work | AI summarizes recent activity and pending items | |
| 87 | Founder | Ask AI to assist planning | AI helps create a plan for the week | |
| 88 | Founder | Ask AI to generate a document | AI produces a professional document | |
| 89 | Founder | Ask AI to create a proposal | AI generates a proposal with itinerary and pricing | |
| 90 | Founder | Ask AI about industry news | AI retrieves and summarizes relevant industry news | |

---

## SECTION 8: INTERNET INTELLIGENCE (Tasks 91-98)

| # | Role | Objective | Expected Behaviour | Status |
|---|------|-----------|-------------------|--------|
| 91 | Founder | Ask about competitor information | AI retrieves competitor data with sources | |
| 92 | Founder | Ask about public regulations | AI cites relevant regulations with references | |
| 93 | Founder | Ask for travel advice | AI provides practical travel guidance | |
| 94 | Founder | Ask general knowledge question | AI answers accurately from knowledge base | |
| 95 | Founder | Ask AI to perform reasoning | AI demonstrates logical reasoning | |
| 96 | Founder | Ask AI to brainstorm | AI generates creative ideas | |
| 97 | Founder | Ask AI for educational assistance | AI explains concepts clearly | |
| 98 | Founder | Verify knowledge source distinction | AI clearly labels org knowledge vs internet knowledge vs assumptions | |

---

## SECTION 9: FREE LLM ROUTING (Tasks 99-105)

| # | Role | Objective | Expected Behaviour | Status |
|---|------|-----------|-------------------|--------|
| 99 | System | Verify free model selection | Default model is free provider (not paid) | |
| 100 | System | Verify model failover | When primary model fails, secondary model takes over | |
| 101 | System | Verify provider outage handling | Conversation continues through provider outage | |
| 102 | System | Verify conversation continuity | Context preserved across model/provider switches | |
| 103 | System | Verify paid model avoidance | Paid models only used when explicitly configured | |
| 104 | System | Verify model routing logic | Correct model selected based on task type | |
| 105 | System | Document current model configuration | Models, providers, selection criteria, failover chain documented | |

---

## SECTION 10: ORGANIZATIONAL OPERATIONS (Tasks 106-120)

| # | Role | Objective | Expected Behaviour | Status |
|---|------|-----------|-------------------|--------|
| 106 | Sarah Sales | Create a lead | New lead created with customer info, source, status | |
| 107 | Sarah Sales | Update lead status | Lead status changes from new to in_progress | |
| 108 | Maya Manager | Assign lead to team member | Lead assigned to Sarah Sales | |
| 109 | Maya Manager | View sales pipeline | Pipeline view shows leads by stage | |
| 110 | Uma Finance | Create an invoice | Invoice created with items, tax, total | |
| 111 | Felicia Director | Approve invoice | Invoice approved through approval chain | |
| 112 | Uma Finance | Record payment | Payment recorded against invoice | |
| 113 | Fiona Manager | View financial report | Report shows revenue, expenses, profit | |
| 114 | Nathan Manager | Create a project | Project created with timeline, team, budget | |
| 115 | Tom Ops | Create a task | Task created and assigned to team member | |
| 116 | Nathan Manager | Track task completion | Task status updated to completed | |
| 117 | Rachel HR | Create a document | Document uploaded with title, category, tags | |
| 118 | Hannah Manager | Search knowledge base | Document found via search | |
| 119 | Founder | Generate business report | Report generated with org-wide metrics | |
| 120 | Founder | View analytics dashboard | Dashboard shows KPIs, trends, insights | |

---

## SECTION 11: CROSS-DEPARTMENT WORKFLOWS (Tasks 121-130)

| # | Role | Objective | Expected Behaviour | Status |
|---|------|-----------|-------------------|--------|
| 121 | Sarah Sales | Request finance approval | Approval request sent to Finance department | |
| 122 | Fiona Manager | Review and approve | Approval processed, requester notified | |
| 123 | Maya Manager | Request HR to hire | Cross-department task created for HR | |
| 124 | Hannah Manager | Process hiring request | HR review completed, status updated | |
| 125 | Tom Ops | Notify support about issue | Notification sent to Support team | |
| 126 | Sonia Support | Respond to issue | Issue resolved, Tom notified | |
| 127 | Mike Marketing | Request ops for campaign | Campaign resources requested from Operations | |
| 128 | Nathan Manager | Allocate resources | Resources allocated, campaign proceeds | |
| 129 | Founder | Review cross-dept activity | All cross-department workflows visible in dashboard | |
| 130 | Founder | Make executive decision | Decision recorded, affects all departments | |

---

## SECTION 12: END-OF-DAY & CONTINUITY (Tasks 131-135)

| # | Role | Objective | Expected Behaviour | Status |
|---|------|-----------|-------------------|--------|
| 131 | Founder | Logout at end of day | Session cleared, secure logout | |
| 132 | Founder | Re-login next day | Session restored, context preserved | |
| 133 | Founder | View unfinished work | Carry-over tasks visible from previous session | |
| 134 | Founder | Continue conversation | AI remembers previous day's context | |
| 135 | Founder | Complete daily summary | AI generates end-of-day summary | |

---

**TOTAL: 135 Tasks**
**PASS: 0 | FAIL: 0 | PENDING: 135**

*Progress will be updated as each task is executed and verified.*