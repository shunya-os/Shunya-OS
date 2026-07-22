# ADR-006 — Space Architecture

**Status:** Proposed
**Date:** 2026-07-21
**Author:** Hermes Agent (Nous Research)

## Context

Everything in SHUNYA exists inside one or more Spaces. Spaces provide context, isolation, and permission boundaries. Existing systems use organizations (Tenants) and workspaces as the only scoping mechanism. The GENESIS directive requires:

1. Spaces are universal — Personal, Family, Organization, Community, Project, Research, and future types
2. Everything (Objects, Conversations, Relationships) lives in one or more Spaces
3. Spaces nest and relate (a Project Space lives inside an Organization Space)
4. Spaces have their own permissions, membership, and lifecycle
5. A human can exist in multiple Spaces simultaneously

## Decision

Implement `Space` as a kernel primitive with:
- Space type (personal, family, organization, community, project, research)
- Members (identities with roles)
- Parent space (nesting)
- Own permission boundary
- Own conversation (for space-level discussions)
- Every Object references its containing Space

## Consequences

- Positive: Universal scoping model
- Positive: Spaces replace both Tenant and Workspace as the primary scope
- Positive: Humans control their Personal Space, Organizations control Organizational Spaces
- Negative: Existing Tenant/Workspace models need mapping
- Risk: Existing code references tenant_id/workspace_id directly

## Implementation

New `kernel/space.py` module. The existing `Tenant` becomes a legacy adapter for organizational Spaces. The existing `Workspace` maps to a Project-type Space.