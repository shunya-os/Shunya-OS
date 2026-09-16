"""
Canonical object access layer — routes through core/object_service.py.

NEW objects go through the canonical object service (sh_objects).
READ operations read from sh_objects first, with fallback to legacy stores
(UOPObject, FounderObject) for historical data.

This is a migration compatibility layer. NEW consumers should use
core/object_service.py directly.
"""

import json
from datetime import datetime, timezone
from app import db
from core.object_service import get_object_service


def get_canonical_object(object_id: str, organization_id: int) -> dict | None:
    """Get an object from the canonical store (sh_objects).

    Canonical store only — the founder_objects fallback was removed in R6B-2.4
    because it was reachable in production and not tenant-scoped (a legacy read
    may never become the authoritative source of tenant-visible truth).
    Resolution order: sh_objects (canonical) → UOPObject (migration compat).

    ``organization_id`` is MANDATORY. It previously defaulted to None, which
    made an unscoped call possible: with no organization the query matched an
    object belonging to ANY tenant. An unscoped canonical read is not an
    acceptable authorization surface, so a missing organization now fails
    closed instead of silently widening scope. The UOPObject compatibility
    fallback is tenant-scoped by the same rule.
    """
    if not organization_id:
        raise ValueError(
            "get_canonical_object() requires an explicit organization_id — "
            "an unscoped canonical read could return another tenant's object. "
            "Missing ownership MUST FAIL CLOSED."
        )
    from app.objects.legacy_models import ShunyaObject
    so = (
        ShunyaObject.query
        .filter_by(object_id=object_id)
        .filter(ShunyaObject.organization_id == int(organization_id))
        .first()
    )
    if so:
        return {
            "object_id": so.object_id,
            "tenant_id": so.organization_id,
            "space_id": so.workspace_id or "",
            "object_type": so.object_type,
            "name": so.name,
            "status": so.status,
            "version": 1,
            "confidence": 1.0,
            "created_at": so.created_at.isoformat() if so.created_at else "",
            "updated_at": so.updated_at.isoformat() if so.updated_at else "",
            "created_by": so.created_by or "",
            "updated_by": "",
            "evidence": [],
            "relationships": [],
            "metadata": so.data or {},
            "organization_id": so.organization_id,
        }

    # Fallback to UOPObject (sh_uop_objects — migration compat store).
    # Scoped by the same organization; an unscoped compat read is not allowed.
    from app.kernel.models import UOPObject
    uop = UOPObject.query.filter_by(object_id=object_id).first()
    if uop:
        row = uop.to_protocol_dict()
        row_org = row.get("organization_id") or row.get("tenant_id")
        if row_org and int(row_org) == int(organization_id):
            return row
        return None

    # No founder_objects fallback (R6B-2.4): canonical absence is authoritative.
    return None


def list_canonical_objects(organization_id: int, workspace_id: str = "",
                           object_type: str = "", limit: int = 50) -> list[dict]:
    """List objects from the canonical store for exactly ONE organization.

    ``organization_id`` is MANDATORY and ``workspace_id`` is now actually
    applied. Previously this function took no organization at all and silently
    ignored its ``space_id`` argument, i.e. it was an unscoped, unfiltered
    tenant read. It has no production callers, but the signature must not
    permit an unscoped listing to be reintroduced by accident.
    """
    if not organization_id:
        raise ValueError(
            "list_canonical_objects() requires an explicit organization_id — "
            "an unscoped canonical listing would expose every tenant. "
            "Missing ownership MUST FAIL CLOSED."
        )
    from app.objects.legacy_models import ShunyaObject
    query = (ShunyaObject.query
             .filter(ShunyaObject.is_deleted == False)
             .filter(ShunyaObject.organization_id == int(organization_id)))
    if workspace_id:
        query = query.filter(ShunyaObject.workspace_id == workspace_id)
    if object_type:
        query = query.filter(ShunyaObject.object_type == object_type)
    results = query.order_by(ShunyaObject.updated_at.desc()).limit(limit).all()

    return [
        {
            "object_id": r.object_id,
            "tenant_id": r.organization_id,
            "space_id": r.workspace_id or "",
            "object_type": r.object_type,
            "name": r.name,
            "status": r.status,
            "version": 1,
            "confidence": 1.0,
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "updated_at": r.updated_at.isoformat() if r.updated_at else "",
            "created_by": r.created_by or "",
            "updated_by": "",
            "evidence": [],
            "relationships": [],
            "metadata": r.data or {},
            "organization_id": r.organization_id,
        }
        for r in results
    ]


def create_canonical_object(
    object_id: str,
    object_type: str,
    name: str,
    space_id: str = "",
    tenant_id: int = 0,
    content: str = "",
    created_by: str = "",
    metadata: dict = None,
    evidence: list = None,
    relationships: list = None,
    workspace_id: str = "",
    identity_id: str | None = None,
) -> dict:
    """Create an object through the canonical object service.

    Routes through core/object_service.py → sh_objects.
    Legacy writes to UOPObject and FounderObject are removed —
    new consumers should read from sh_objects via get_canonical_object().

    Callers MUST provide a valid tenant_id. 0 = unknown/legacy (no mutation).
    Callers MUST also provide the authenticated ``identity_id``: this is a
    compatibility wrapper, not an authorization bypass, so it is gated by the
    same identity authorization as every other canonical write. It carries no
    machine/system scope.
    """
    from app.objects.legacy_models import ShunyaObject
    from app import db
    from app.authz.workspace_context import assert_object_access

    if not tenant_id:
        return {"error": "tenant_id is required — cannot create object without organization context"}

    if not workspace_id and not space_id:
        return {"error": "workspace_id or space_id is required — cannot create object without workspace context"}

    if not identity_id:
        return {"error": "identity_id is required — canonical create must be authorization-gated"}

    # Check if object already exists — if so, update in place (upsert)
    existing = ShunyaObject.query.filter_by(object_id=object_id).first()
    if existing:
        # The upsert path is a WRITE, so it is authorized against the row's
        # PERSISTED ownership exactly like ObjectService.update().
        assert_object_access(identity_id, existing.organization_id,
                             existing.workspace_id)
        existing.name = name
        existing.object_type = object_type
        existing.data = metadata or {}
        existing.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return {
            "object_id": object_id,
            "tenant_id": tenant_id,
            "space_id": space_id,
            "object_type": object_type,
            "name": name,
            "status": "active",
            "version": 1,
            "confidence": 1.0,
            "created_at": existing.created_at.isoformat() if existing.created_at else "",
            "updated_at": existing.updated_at.isoformat() if existing.updated_at else "",
            "created_by": existing.created_by or created_by,
            "updated_by": created_by,
            "evidence": evidence or [],
            "relationships": relationships or [],
            "metadata": metadata or {},
            "organization_id": existing.organization_id or tenant_id,
        }

    svc = get_object_service()
    org_id = tenant_id
    w_id = workspace_id or space_id

    obj = svc.create(
        object_type=object_type,
        name=name,
        organization_id=org_id,
        data=metadata or {},
        created_by=created_by,
        workspace_id=w_id,
        object_id=object_id,
        identity_id=identity_id,
    )

    return {
        "object_id": obj.get("object_id", object_id),
        "tenant_id": org_id,
        "space_id": space_id,
        "object_type": object_type,
        "name": name,
        "status": "active",
        "version": 1,
        "confidence": 1.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": created_by,
        "updated_by": created_by,
        "evidence": evidence or [],
        "relationships": relationships or [],
        "metadata": metadata or {},
        "organization_id": org_id,
    }