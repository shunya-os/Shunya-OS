# SHUNYA USER OUTCOME MATRIX — M2C.4
## What Can a Real Human Actually Accomplish?

**Rule:** GREEN = human can accomplish the outcome end-to-end through the browser without developer intervention. 
RED = the chain breaks before the human gets value.

---

| # | User Outcome | Domain | Path | Current Status | Break Point | Evidence |
|---|---|---|---|---|---|---|
| UO-01 | Visit SHUNYA and understand what it is | Public Site | Browser → shunyaos.com → landing page | GREEN | — | O — landing loads, calm, clear value prop |
| UO-02 | Create an account | Auth | Browser → / → Get Started → Signup | GREEN | — | O — signup form works, sends verification |
| UO-03 | Sign in with existing credentials | Auth | Browser → Login → credentials → workspace | GREEN | — | O — signin works, session persists |
| UO-04 | Complete onboarding | Onboarding | Signin → onboarding flow → workspace | GREEN | — | O — 6 paths → skip → workspace |
| UO-05 | Upload a document | Documents | Browser → Documents → Choose File → Add | GREEN | — | O — upload works, extracted text backfilled |
| UO-06 | View uploaded documents | Documents | Browser → Documents → list | GREEN | — | O — 15 docs visible with metadata |
| UO-07 | View document content | Documents | Click document → detail panel → extracted text | AMBER | Detail panel shows raw extracted text, not formatted | O — text appears but unformatted |
| UO-08 | Ask AI a question about the business | AI | Command bar → type question → get answer | GREEN | — | O — AI answers with Panchi Club context, 5 evidence sources |
| UO-09 | Get AI answer with company data | AI | "What do you know about my business?" → contextual answer | GREEN | — | O — AI knows org is Panchi Club, travel, has commitments |
| UO-10 | Create content with AI | Content | Content Studio → tone/topic → Generate | GREEN | — | O — Studio works end-to-end |
| UO-11 | View People in organization | People | Sidebar → People → see team | RED | persons table = 0 rows | O — empty surface with search only |
| UO-12 | Find a person's details | People | Search → person profile | RED | No persons exist | O — nothing to find |
| UO-13 | View Conversations | Conversations | Sidebar → Conversations | RED | Empty surface | O — empty, nothing to see |
| UO-14 | View Commitments/Work | Work | Sidebar → Work → see commitments | RED | API returns data, UI shows filters but no items | O — 5 commitments in DB, 0 shown |
| UO-15 | Create a Commitment | Work | Click "+ New Commitment" → form → submit | UNKNOWN | Not tested | U — button exists, form untested |
| UO-16 | View Finance | Finance | Sidebar → Finance | RED | Shows Commitments, not Finance | O — 20 invoices in DB, no finance UI |
| UO-17 | View Sales Pipeline | Sales | Sidebar → Sales → Pipeline tab | RED | Pipeline tab renders empty | O — 6 leads in DB, 0 in UI |
| UO-18 | View Commercial opportunities | Commercial | Sidebar → Commercial → Opportunities | RED | "Opportunities (0)" always | O — empty |
| UO-19 | View Marketing channels | Marketing | Sidebar → Marketing | AMBER | Connect buttons visible, campaigns in DB | O — not connected (expected for demo) |
| UO-20 | View Knowledge | Knowledge | Sidebar → Knowledge | AMBER | No longer crashes, but empty | O — empty state renders (no crash) |
| UO-21 | View Operations | Operations | Sidebar → Operations | RED | Times out | U — page does not load |
| UO-22 | View Outputs | Outputs | Sidebar → Outputs | RED | Times out | U — page does not load |
| UO-23 | View Memory | Memory | Sidebar → Memory | RED | Empty — "No memory entries yet" | O — memory_records=0 |
| UO-24 | View Relationships | Relationships | Sidebar → Relationships | RED | Title only, no content | O — just heading |
| UO-25 | View Entities | Entities | Sidebar → Entities | RED | Empty | O — no entities |
| UO-26 | Use Voice | Voice | Click voice button on command bar | RED | 404 endpoint | O — no backend |
| UO-27 | Use Notifications | Notifications | Any | MISSING | Not implemented | U — not tested |
| UO-28 | Access on mobile phone | Responsive | Mobile browser → SHUNYA | UNKNOWN | Not tested | U — no responsive testing done |
| UO-29 | Access Settings | Settings | Profile → Settings | UNKNOWN | Not tested | U — settings route exists |
| UO-30 | Use keyboard navigation | Accessibility | Tab through workspace | UNKNOWN | Not tested | U — not verified |
| UO-31 | Sign in with OAuth | Auth | Click "Sign in with Google" | RED | No OAuth credentials configured | O — button renders, flow incomplete |
| UO-32 | Reset password | Auth | Forgot password → email → reset | AMBER | Endpoint exists, email service untested | O — UI renders, backend untested |
| UO-33 | View Executive Home | Home | Authenticated → workspace | AMBER | Shows org context and "1 new item" | O — works but minimal |
| UO-34 | Complete end-to-end: Document → Person → Relationship | Journeys | Upload doc → SHUNYA extracts → identifies people | RED | extracted_text=✅, persons=0, relationships=0 | O — chain breaks at identity step |
| UO-35 | Complete end-to-end: Lead → Customer → Invoice → Payment | Journeys | Create lead → convert → invoice → payment | RED | leads=6, customer=0, invoices=20, payments=0 | O — chain breaks at customer/payment |
| UO-36 | Complete end-to-end: Commitment → Execution → Evidence → Outcome | Journeys | Create commitment → execute → evidence → outcome | RED | commitments=5, evidence_records=1, no outcomes | O — chain breaks at evidence+outcome |
| UO-37 | Return next day, find continuity | Journeys | Login → see what changed | AMBER | Session persists, home shows "new items" | O — basic continuity exists |
| UO-38 | Understand SHUNYA's AI confidence | AI | Ask question → evaluate confidence markers | AMBER | Pipeline shows evidence sources but no confidence UI | O — confidence available in API, not surfaced |
| UO-39 | Filter/export financial reports | Finance | Finance → reports → export | MISSING | No finance surface | O — not implemented |
| UO-40 | Manage organization settings | Admin | Settings → org → members/roles | UNKNOWN | Not tested | U — admin routes exist |

## SUMMARY

| Status | Count | % |
|---|---|---|
| GREEN (outcome works end-to-end) | 8 | 20% |
| AMBER (partial) | 6 | 15% |
| RED (breaks before value) | 17 | 42.5% |
| MISSING (not implemented) | 2 | 5% |
| UNKNOWN (not tested) | 7 | 17.5% |
| **Total** | **40** | **100%** |

**Only 8 of 40 promised user outcomes work end-to-end.** This confirms the founder's concern: the product is substantially less complete than the code suggests.