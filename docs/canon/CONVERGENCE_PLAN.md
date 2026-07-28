# SHUNYA System Convergence Plan

> **Phase L · Convergent Architecture**
> **Status: ACTIVE — Migration in progress**

---

## 1. Duplication Audit

Every duplicated concept identified during the Phase L audit. Each entry lists the current representations and the target convergence path.

### 1.1 Business Objects

| Concept | Current representations | Convergence target | Migration path |
|---------|----------------------|-------------------|----------------|
| Objects | `app.founder.models.FounderObject` (SQLAlchemy), `core.kernel.object.UniversalObject` (dataclass), `core.memory_knowledge_runtime.models.MemoryObject` (dataclass) | `core.kernel.object.UniversalObject` | Phase L: Adaptor pattern. Phase L+1: Deprecate Flask model. |
| Identity | `core.kernel.identity.SHUNYAIdentity` (dataclass), `app.production.identity_repository.SHUNYAIdentityModel` (SQLAlchemy), `app.auth.TeamMember` (SQLAlchemy) | `core.kernel.identity.SHUNYAIdentity` | TeamMember remains for session. SHUNYAIdentityModel wraps kernel identity. |
| Spaces | `core.kernel.space.SpaceStore` (in-memory), `app.founder.models.FounderSpace` (SQLAlchemy) | `core.kernel.space.SpaceStore` with persistence | Keep Flask model for query; push writes to kernel. |
| Relationships | `core.kernel.relationship.RelationshipEngine` (in-memory), `app.kernel.relationship` (same) | `core.kernel.relationship` | Already unified — single source. |
| Workspace | `core/workspace_runtime/orchestrator.py` (dataclass workspace), `templates/workspace.html`, `templates/founder_workspace.html`, `templates/founder_workspace.html` (two copies), `frontend/` (Next.js) | One canonical workspace: `core.workspace_runtime` backend + Next.js frontend | Phase L: Identify canonical. Phase L+1: Remove duplicates. |

### 1.2 Execution Paths

| Path | Current location | Must converge to |
|------|-----------------|-----------------|
| Flask CRUD routes | `app/routes.py` | Intent → Pipeline |
| Founder API routes | `app/founder/routes.py` | Intent → Pipeline |
| Telegram webhook | `app/routes.py` | Intent → Pipeline |
| Direct model queries | `app/workspace_routes.py`, `app/founder/routes.py` | Through kernel OS |

### 1.3 State Models

| State machine | Location | Notes |
|--------------|----------|-------|
| ObjectStatus (6 states) | `core.kernel.object` | Canonical |
| ExecutionState (12 states) | `core/execution_runtime/models.py` | Correct — execution has its own lifecycle |
| PlanStatus | `core/planning_runtime/models.py` | Correct — planning has its own lifecycle |
| LeadStatus | `app/models.py` | Must be removed — migrate to ObjectStatus |

### 1.4 UI Representations

| UI | Location | Status |
|----|----------|--------|
| Flask Jinja2 templates | `templates/` | Legacy — phase out during convergence |
| Next.js SPA | `frontend/` | Canonical — needs API wiring |
| Founder workspace (Flask) | `templates/founder_workspace.html` | Stub — should call Next.js instead |

## 2. Migration Strategy

### Phase L (Current) — Foundation

| Action | Owner | Depends on |
|--------|-------|------------|
| Create canonical runtime pipeline | Done | — |
| Create OS kernel | Done | — |
| Write all specification documents | Done | — |
| Create convergence plan | Done | — |
| Create capability matrix | Done | — |

### Phase L+1 — Runtime Wired

| Action | Owner | Depends on |
|--------|-------|------------|
| Wire Flask founder routes to OS kernel | Kernel team | OS kernel |
| Replace MockRuntime "kernel" with real `core/kernel/` runtime | Kernel team | Phase L |
| Replace MockRuntime "identity" with real `core/identity/` runtime | Identity team | Phase L |
| Wire Next.js to Flask API that calls OS kernel | Frontend team | OS kernel |
| Remove duplicate `founder_workspace.html` | Frontend team | Canonical workspace identified |

### Phase L+2 — Full Pipeline

| Action | Owner | Depends on |
|--------|-------|------------|
| Replace MockRuntime "memory" with real `core/memory_knowledge_runtime/` | Memory team | Phase L+1 |
| Replace MockRuntime "planning" with real `core/planning_runtime/` | Planning team | Phase L+1 |
| Replace MockRuntime "execution" with real `core/execution_runtime/` | Execution team | Phase L+1 |
| Replace MockRuntime "projection" with real `core/projection/` | Projection team | Phase L+1 |
| Wire founder routes through full pipeline | Integration team | All mock replacements |

### Phase L+3 — Production

| Action | Owner | Depends on |
|--------|-------|------------|
| Remove demo data from Next.js | Frontend team | Phase L+2 |
| Remove scenario-based AI responses | AI team | Phase L+2 |
| Wire real LLM integration | AI team | Phase L+2 |
| Deprecate Flask SQLAlchemy models | Data team | Phase L+2 |
| All capabilities at "Operational" state | All | Phase L+3 |

## 3. Convergence Rules

1. **No destructive rewrites.** Existing tests must continue passing throughout migration.
2. **Adapters come first** — new interface is added, old interface is wrapped, old code can still run.
3. **Remove old code only when coverage proves no regression.**
4. **Flag day migrations are forbidden.** Every migration must be incremental.
5. **Every convergence step must be testable in isolation.**
6. **Mock runtimes remain until the real runtime is fully wired and tested.