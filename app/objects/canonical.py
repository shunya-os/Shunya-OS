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


def get_canonical_object(object_id: str) -> dict | None:
    """Get an object from the canonical store, falling back to legacy stores.

    Resolution order: sh_objects (canonical) → UOPObject (migration compat) →
    FounderObject (legacy compat).
    """
    from app.objects.legacy_models import ShunyaObject
    so = ShunyaObject.query.filter_by(object_id=object_id).first()
    if so:
        return {
            "object_id": so.object_id,
            "tenant_id": so.organization_id or 1,
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

    # Fallback to UOPObject (sh_uop_objects — migration compat)
    from app.kernel.models import UOPObject
    uop = UOPObject.query.filter_by(object_id=object_id).first()
    if uop:
        return uop.to_protocol_dict()

    # Fallback to FounderObject (founder_objects — legacy compat)
    from app.founder.models import FounderObject
    fo = FounderObject.query.filter_by(object_id=object_id).first()
    if fo:
        return {
            "object_id": fo.object_id,
            "tenant_id": 1,
            "space_id": fo.space_id or "",
            "object_type": fo.object_type or "Document",
            "name": fo.name or "Untitled",
            "status": fo.status or "active",
            "version": 1,
            "confidence": 1.0,
            "created_at": fo.created_at.isoformat() if fo.created_at else "",
            "updated_at": fo.updated_at.isoformat() if fo.updated_at else "",
            "created_by": fo.created_by or "",
            "updated_by": "",
            "evidence": [],
            "relationships": [],
            "metadata": {"migrated": False},
        }
    return None


def list_canonical_objects(space_id: str = "", object_type: str = "",
                           limit: int = 50) -> list[dict]:
    """List objects from canonical store with optional filters."""
    from app.objects.legacy_models import ShunyaObject
    query = ShunyaObject.query.filter(ShunyaObject.is_deleted == False)
    if object_type:
        query = query.filter(ShunyaObject.object_type == object_type)
    results = query.order_by(ShunyaObject.updated_at.desc()).limit(limit).all()

    return [
        {
            "object_id": r.object_id,
            "tenant_id": r.organization_id or 1,
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
    tenant_id: int = 1,
    content: str = "",
    created_by: str = "",
    metadata: dict = None,
    evidence: list = None,
    relationships: list = None,
    workspace_id: str = "",
) -> dict:
    """Create an object through the canonical object service.

    Routes through core/object_service.py → sh_objects.
    Legacy writes to UOPObject and FounderObject are removed —
    new consumers should read from sh_objects via get_canonical_object().
    """
    from app.objects.legacy_models import ShunyaObject
    from app import db

    # Check if object already exists — if so, update in place (upsert)
    existing = ShunyaObject.query.filter_by(object_id=object_id).first()
    if existing:
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
    org_id = tenant_id if tenant_id and tenant_id > 0 else 1
    w_id = workspace_id or space_id or "spc_default"

    obj = svc.create(
        object_type=object_type,
        name=name,
        organization_id=org_id,
        data=metadata or {},
        created_by=created_by,
        workspace_id=w_id,
        object_id=object_id,
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