# SHUNYA Founder Journey Specification

> **Phase L · Canonical Document**
> **Status: CANONICAL — Every screen, runtime, automation, and workflow supports this journey.**

---

## 1. The Canonical Founder Journey

```
① Sign In
    ↓
② Founder Home (workspace)
    ↓
③ Create / Enter Space
    ↓
④ Create Object
    ↓
⑤ Open Object
    ↓
⑥ Converse with Object
    ↓
⑦ Search / Reopen Objects
    ↓
⑧ Execute Actions on Objects
    ↓
⑨ Learn from Outcomes
    ↓
⑩ Return to ②
```

## 2. Journey Detail

### Step ① — Sign In

| Aspect | Detail |
|--------|--------|
| **User action** | Email + password (or OAuth) |
| **OS pipeline** | Intent `sign_in` → Identity Resolution → Authentication |
| **Runtimes** | Identity Runtime |
| **Data** | Session created, identity resolved |
| **Route** | `POST /api/v1/founder/signin` or `POST /auth/login` |
| **UI** | Login page → redirect to workspace |
| **Status** | ✅ Implemented |

### Step ② — Founder Home (Workspace)

| Aspect | Detail |
|--------|--------|
| **User action** | Arrive at workspace after login |
| **OS pipeline** | Intent `enter_workspace` → Identity → Object → Graph → Memory → Projection → Workspace |
| **Runtimes** | Projection Runtime → Workspace Runtime |
| **Data** | Workspace projection assembled: spaces, recent objects, notifications |
| **Route** | `GET /founder/workspace` or `GET /workspace/` |
| **UI** | Three-zone layout: left panel (spaces), center (active object), right (intelligence) |
| **Status** | ⚠️ Partially implemented — Flask template exists, core runtimes not wired |

### Step ③ — Create / Enter Space

| Aspect | Detail |
|--------|--------|
| **User action** | Create a new space or click existing space |
| **OS pipeline** | Intent `create_space` or `enter_space` → Identity → Object → Graph → Memory → Projection |
| **Runtimes** | Kernel (SpaceStore), Knowledge Graph, Memory, Projection |
| **Data** | Space created in kernel SpaceStore + DB, relationship edge added, graph updated |
| **Route** | `POST /api/v1/founder/spaces` or `GET /founder/space/<id>` |
| **UI** | Space creation form → workspace view with objects |
| **Status** | ✅ Implemented |

### Step ④ — Create Object

| Aspect | Detail |
|--------|--------|
| **User action** | Create a new object in the current space |
| **OS pipeline** | Intent `create_object` → Identity → Object (registry) → Graph → Memory → Projection |
| **Runtimes** | Kernel (ObjectRegistry), Knowledge Graph, Memory, Projection |
| **Data** | Object created in registry + DB, graph node created, memory updated, projection assembled |
| **Route** | `POST /api/v1/founder/objects` |
| **UI** | Object creation form → workspace redirect to object view |
| **Status** | ✅ Implemented |

### Step ⑤ — Open Object

| Aspect | Detail |
|--------|--------|
| **User action** | Click on an object to open it |
| **OS pipeline** | Intent `view_object` → Identity → Object → Graph → Memory → Projection → Workspace |
| **Runtimes** | Kernel, Knowledge Graph, Memory, Projection, Workspace |
| **Data** | Object loaded, graph context resolved, memory retrieved, projection assembled |
| **Route** | `GET /founder/object/<id>` |
| **UI** | Object detail view with conversation, timeline, evidence, relationships |
| **Status** | ✅ Implemented (Flask), ⚠️ Not wired through OS pipeline |

### Step ⑥ — Converse with Object

| Aspect | Detail |
|--------|--------|
| **User action** | Send a message about the current object |
| **OS pipeline** | Intent `talk_to_customer` | `understand_opportunity` | `ask_question` |
| **Runtimes** | Identity → Object → Graph → Memory → Reasoning → Projection |
| **Data** | Message saved, graph updated, memory updated, reasoning output stored, projection updated |
| **Route** | `POST /api/v1/founder/converse` |
| **UI** | Chat interface in object view |
| **Status** | ⚠️ Partially implemented — messages work, AI response is scenario-based |

### Step ⑦ — Search / Reopen Objects

| Aspect | Detail |
|--------|--------|
| **User action** | Search for objects or reopen recent ones |
| **OS pipeline** | Intent `search_objects` → Identity → Object (search) → Projection |
| **Runtimes** | Memory (search), Knowledge Graph (traversal), Projection |
| **Data** | Search results assembled as SearchProjection |
| **Route** | (via workspace navigation) |
| **UI** | Command palette (Cmd+K) or object list in left panel |
| **Status** | ⚠️ Partially implemented — left panel lists objects, no search API |

### Step ⑧ — Execute Actions on Objects

| Aspect | Detail |
|--------|--------|
| **User action** | Update status, assign, approve, commit |
| **OS pipeline** | Intent `commit_to_follow_up` | `approve_proposal` | `execute_work` |
| **Runtimes** | Identity → Object → Graph → Memory → Plan → Reason → Execute → Automate → Project |
| **Data** | Object updated, execution trace created, automation triggers evaluated, projection updated |
| **Route** | `PUT /api/v1/founder/objects/<id>` |
| **UI** | Action buttons in object view |
| **Status** | ❌ Not implemented through OS pipeline — CRUD only |

### Step ⑨ — Learn from Outcomes

| Aspect | Detail |
|--------|--------|
| **User action** | Observe outcome of executed action |
| **OS pipeline** | Intent `learn_from_outcome` → Object → Graph → Memory → Reason → Project |
| **Runtimes** | Knowledge Graph, Memory, Reasoning, Projection |
| **Data** | Knowledge graph updated with outcome, memory consolidated, patterns detected |
| **Route** | (automatic, triggered by execution completion) |
| **UI** | Intelligence panel shows insights |
| **Status** | ❌ Not implemented — no learning loop integration |

## 3. Journey Invariants

1. Every journey step flows through the canonical pipeline.
2. Every step is traceable via PipelineContext.
3. Every step produces a projection that the workspace renders.
4. No step bypasses the runtime pipeline.
5. The workspace is the single UI surface for all steps.