# SHUNYA — Workspace Context Canonicalization Map

> Generated: 2026-08-27 | Directive: M2B (Extended)
> Purpose: Establish one canonical context flow from backend through frontend

## 1. Competing Context Models (Before Canonicalization)

| Model | Table | Purpose | Owner | Status |
|-------|-------|---------|-------|--------|
| OrgMember | org_members | Organization membership | FOR-2 / Organization | ✅ CANONICAL |
| Organization | organizations | Organization entity | FOR-2 / depths | ✅ CANONICAL |
| FounderSpace | founder_spaces | Space entity (personal/org) | Founder experience | ✅ CANONICAL (space concept) |
| Workspace (workspace/models) | user_workspaces | Workspace entity | Workspace experience | 🔄 CANONICAL INTENT |
| Workspace (production/identity) | workspaces | Alternative workspace | Production identity | 🔄 LEGACY — migrating |
| Workspace (objects/legacy) | sh_workspaces | Legacy workspace | Objects legacy | 🔄 LEGACY — read-only |
| Tenant | tenants | Legacy org entity | Multiple blueprints | 🔄 LEGACY — replacing with Organization |

## 2. Session Keys (Before Canonicalization)

| Key | Set By | Read By | Purpose | Status |
|-----|--------|---------|---------|--------|
| `user_id` | auth_routes, founder/routes, auth_oauth | Most routes | TeamMember.id | LEGACY — keep for transition |
| `identity_id` | __init__._resolve_identity_session, auth_routes, auth_oauth | Workspace resolution | SHUNYA identity string | ✅ CANONICAL |
| `current_org_id` | __init__, auth_routes, for2/routes, switch_routes | ~20+ blueprints | Active Organization.id | ✅ CANONICAL |
| `current_workspace_id` | auth_routes, workspace/models, workspace/routes | workspace/models | Active workspace | 🔄 SUPPLEMENTAL |
| `current_workspace_type` | Same as current_workspace_id | workspace/models | Workspace type | 🔄 SUPPLEMENTAL |
| `tenant_id` | (legacy, rarely set) | workspace_objects, reality_engine | Legacy tenant | 🔄 LEGACY |

**Key defect:** `current_org_id` and `current_workspace_id` are set independently by different code paths — they can drift.

## 3. Canonical Context Flow (Target)

```
USER REQUEST
    ↓
ResolveIdentitySession (before_request middleware)
    session["user_id"] → TeamMember → OrgMember → session["identity_id"], session["current_org_id"]
    ↓
CheckAuth (before_request middleware)
    session["user_id"] + session["identity_id"] → g.workspace_context = resolve_context()
    ↓
ROUTE HANDLER
    reads g.workspace_context for: identity_id, current_workspace, capabilities
    ↓
API RESPONSE
    includes workspace context where appropriate
    ↓
FRONTEND
    useActiveContext (Zustand) ← /api/v1/for2/whoami
    ↓
OperatingContextSelector (UI)
    shows current org | personal space
    ↓
User Switch
    POST /api/v1/for2/organizations/<id>/switch → session updated
    POST /api/v1/for2/organizations/switch/personal → FIX NEEDED (currently 404)
```

## 4. Context Switch Endpoints

| Endpoint | Method | Status | Sets | Notes |
|----------|--------|--------|------|-------|
| `/api/v1/for2/organizations/<int:org_id>/switch` | POST | ✅ EXISTS | `current_org_id`, redirects | Works correctly |
| `/api/v1/for2/organizations/switch/personal` | POST | ❌ **MISSING** | Should clear `current_org_id` | Frontend calls it — gets 404 |
| `/api/v1/workspace/switch` | POST | ✅ EXISTS | `current_workspace_id` | Alternative path |
| `/api/v1/production/identity/switch/<int:org_id>` | POST | ✅ EXISTS | `current_org_id` | Alternative path |

### Fix Required: Add Personal Switch Route

The `useActiveContext` Zustand store calls `/api/v1/for2/organizations/switch/personal` to switch to Personal workspace, but this route does not exist. This must be implemented.

## 5. Canonical Context Contract

### Backend → Frontend (via /api/v1/for2/whoami)

```json
{
  "authenticated": true,
  "identity_id": "sid_xxx",
  "email": "user@example.com",
  "name": "User Name",
  "current_organization": {
    "id": 7,
    "name": "Panchi Club",
    "slug": "panchi-club",
    "brand_color": "#2563eb",
    "business_type": "travel"
  },
  "current_organization_id": 7,
  "current_workspace": {
    "workspace_id": "spc_xxx",
    "name": "Panchi Club",
    "workspace_type": "organization"
  }
}
```

### Personal Context (no org)

```json
{
  "authenticated": true,
  "identity_id": "sid_xxx",
  "email": "user@example.com",
  "name": "User Name",
  "current_organization": null,
  "current_organization_id": null,
  "current_workspace": {
    "workspace_id": "spc_personal_xxx",
    "name": "Personal Workspace",
    "workspace_type": "personal"
  }
}
```

## 6. Personal Workspace Context Switch — Implementation

The `/api/v1/for2/organizations/switch/personal` endpoint must:

1. Clear `session["current_org_id"]`
2. Find or create the user's Personal workspace
3. Set `session["current_workspace_id"]` to personal workspace
4. Return `{"success": true, "redirect": "/workspace/"}`

This will be implemented in the `app/for2/routes.py` file alongside the existing org switch endpoint.