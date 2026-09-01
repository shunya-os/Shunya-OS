"""
§4 — Canonical object access layer.

Provides read/write access to objects through the canonical UOPObject store,
with transparent fallback to FounderObject for backward compatibility.

This is the consolidation layer: writers write to both stores during migration,
readers read from the canonical store (UOPObject) first, with fallback.
"""

import json
from datetime import datetime, timezone
from app import db
from app.kernel.models import UOPObject


def get_canonical_object(object_id: str) -> dict | None:
    """Get an object from the canonical store, falling back to legacy stores.

    Resolution order: UOPObject (canonical) → ShunyaObject (legacy compat) →
    FounderObject (legacy compat).
    """
    obj = UOPObject.query.filter_by(object_id=object_id).first()
    if obj:
        return obj.to_protocol_dict()

    # Fallback to ShunyaObject (sh_objects — workspace/reality_engine compat)
    from app.objects.legacy_models import ShunyaObject
    so = ShunyaObject.query.filter_by(object_id=object_id).first()
    if so:
        return {
            "object_id": so.object_id,
            "tenant_id": 1,
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
        }

    # Fallback to FounderObject
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


def list_canonical_objects(space_id: str = "", object_type: str = "", limit: int = 50) -> list[dict]:
    """List objects from canonical store with optional filters."""
    query = UOPObject.query.filter(UOPObject.is_archived == False)
    if space_id:
        query = query.filter(UOPObject.space_id == space_id)
    if object_type:
        query = query.filter(UOPObject.object_type == object_type)
    results = query.order_by(UOPObject.updated_at.desc()).limit(limit).all()

    # Supplement with FounderObject results for coverage
    from app.founder.models import FounderObject
    fo_query = FounderObject.query.filter(FounderObject.status == "active")
    if space_id:
        fo_query = fo_query.filter(FounderObject.space_id == space_id)
    if object_type:
        fo_query = fo_query.filter(FounderObject.object_type == object_type)
    fo_results = fo_query.order_by(FounderObject.updated_at.desc()).limit(limit).all()

    # Merge — UOPObject results first, then supplement with FO results not already in UOP
    existing_ids = {r["object_id"] for r in [obj.to_protocol_dict() for obj in results]}
    for fo in fo_results:
        if fo.object_id not in existing_ids:
            results.append(fo)

    return [
        r.to_protocol_dict() if isinstance(r, UOPObject) else {
            "object_id": r.object_id,
            "tenant_id": 1,
            "space_id": r.space_id or "",
            "object_type": r.object_type or "Document",
            "name": r.name or "Untitled",
            "status": r.status or "active",
            "version": 1,
            "confidence": 1.0,
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "updated_at": r.updated_at.isoformat() if r.updated_at else "",
            "created_by": r.created_by or "",
            "updated_by": "",
            "evidence": [],
            "relationships": [],
            "metadata": {"migrated": False},
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
    """Create an object in ALL active stores — canonical primary with legacy mirrors.

    Canonical: UOPObject (sh_uop_objects) — kernel UniversalObject protocol.
    Legacy mirrors: ShunyaObject (sh_objects) — workspace/reality_engine consumer.
                     FounderObject (founder_objects) — founder journey / AI consumer.
    During migration all three are written. New consumers target UOPObject.
    Legacy mirrors are read-only post-migration.
    """
    now = datetime.now(timezone.utc).isoformat()

    # 1. Write to canonical store (UOPObject — kernel protocol)
    existing_uop = UOPObject.query.filter_by(object_id=object_id).first()
    if existing_uop:
        # Update existing — upsert semantics
        existing_uop.name = name
        existing_uop.object_type = object_type
        existing_uop.space_id = space_id
        existing_uop.tenant_id = tenant_id
        existing_uop.updated_at = now
        existing_uop.updated_by = created_by
        existing_uop.status = "active"
        existing_uop.metadata_json = json.dumps(metadata or {})
        existing_uop.evidence_json = json.dumps(evidence or [])
        existing_uop.relationships_json = json.dumps(relationships or [])
        uop = existing_uop
    else:
        uop = UOPObject(
            object_id=object_id,
            tenant_id=tenant_id,
            space_id=space_id,
            object_type=object_type,
            name=name,
            status="active",
            version=1,
            confidence=1.0,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
            evidence_json=json.dumps(evidence or []),
            relationships_json=json.dumps(relationships or []),
            metadata_json=json.dumps(metadata or {}),
            is_archived=False,
        )
        db.session.add(uop)

    # 2. Write to legacy ShunyaObject (sh_objects) — workspace/reality_engine compat
    from app.objects.legacy_models import ShunyaObject
    existing_sh = ShunyaObject.query.filter_by(object_id=object_id).first()
    if not existing_sh:
        w_id = workspace_id or space_id or "spc_default"
        sh = ShunyaObject(
            object_id=object_id,
            workspace_id=w_id,
            object_type=object_type,
            name=name,
            status="active",
            data=metadata or {},
            created_by=created_by,
        )
        db.session.add(sh)

    # 3. Write to legacy FounderObject (founder_objects) — founder journey/AI compat
    from app.founder.models import FounderObject
    existing_fo = FounderObject.query.filter_by(object_id=object_id).first()
    if not existing_fo:
        fo = FounderObject(
            object_id=object_id,
            space_id=space_id,
            object_type=object_type,
            name=name,
            content=content or "",
            status="active",
            created_by=created_by,
        )
        db.session.add(fo)

    db.session.commit()
    return uop.to_protocol_dict()