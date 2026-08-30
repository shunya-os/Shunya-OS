"""
§4 — Object convergence migration: founder_objects + objects → sh_uop_objects.

Migrates all active objects from legacy stores into the canonical UOPObject store.
Run once after schema verification.
"""
import uuid
from datetime import datetime, timezone
from app import create_app, db
from app.kernel.models import UOPObject


def migrate_founder_objects():
    """Migrate all active FounderObject records to UOPObject."""
    from app.founder.models import FounderObject

    migrated = 0
    skipped = 0
    for fo in FounderObject.query.filter(FounderObject.status != "deleted").all():
        # Check if already migrated
        existing = UOPObject.query.filter_by(object_id=fo.object_id).first()
        if existing:
            skipped += 1
            continue

        obj = UOPObject(
            object_id=fo.object_id,
            tenant_id=1,
            space_id=fo.space_id or "",
            object_type=fo.object_type or "Document",
            name=fo.name or "Untitled",
            status=fo.status or "active",
            version=1,
            confidence=1.0,
            created_at=fo.created_at.isoformat() if fo.created_at else datetime.now(timezone.utc).isoformat(),
            updated_at=fo.updated_at.isoformat() if fo.updated_at else datetime.now(timezone.utc).isoformat(),
            created_by=fo.created_by or "",
            updated_by=fo.created_by or "",
            evidence_json="[]",
            relationships_json="[]",
            metadata_json='{"migrated_from": "founder_objects", "content": "' + (fo.content[:200] if fo.content else "") + '"}',
            is_archived=(fo.status == "archived"),
        )
        db.session.add(obj)
        migrated += 1

    db.session.commit()
    return migrated, skipped


def migrate_objects_table():
    """Migrate all records from the simple objects table to UOPObject."""
    from app.objects.models import Object as SimpleObject
    import json

    migrated = 0
    skipped = 0
    for so in SimpleObject.query.all():
        object_id = f"obj_{uuid.uuid4().hex[:16]}"
        existing = UOPObject.query.filter_by(object_id=object_id).first()
        if existing:
            skipped += 1
            continue

        state = so.state or {}
        context = so.context or {}

        obj = UOPObject(
            object_id=object_id,
            tenant_id=so.tenant_id or 1,
            space_id="",
            object_type=so.object_type or "Generic",
            name=state.get("name", so.object_type or "Object"),
            status="active",
            version=1,
            confidence=1.0,
            created_at=so.created_at.isoformat() if so.created_at else datetime.now(timezone.utc).isoformat(),
            updated_at=so.updated_at.isoformat() if so.updated_at else datetime.now(timezone.utc).isoformat(),
            created_by="",
            updated_by="",
            evidence_json=json.dumps(context.get("evidence", [])),
            relationships_json=json.dumps(context.get("relationships", [])),
            metadata_json=json.dumps({
                "migrated_from": "objects",
                "legacy_id": so.id,
                "state": {k: str(v) for k, v in state.items()} if state else {},
                "context": {k: str(v) for k, v in context.items()} if context else {},
            }),
            is_archived=False,
        )
        db.session.add(obj)
        migrated += 1

    db.session.commit()
    return migrated, skipped


def migrate_sh_objects():
    """Migrate sh_objects records to UOPObject."""
    from app.objects.legacy_models import ShObject

    migrated = 0
    skipped = 0
    for so in ShObject.query.filter_by(is_deleted=False).all():
        object_id = so.object_id or f"sh_{uuid.uuid4().hex[:16]}"
        existing = UOPObject.query.filter_by(object_id=object_id).first()
        if existing:
            skipped += 1
            continue

        import json
        obj = UOPObject(
            object_id=object_id,
            tenant_id=1,
            space_id=so.workspace_id or "",
            object_type=so.object_type or "Generic",
            name=so.name or "Untitled",
            status=so.status or "active",
            version=1,
            confidence=1.0,
            created_at=so.created_at.isoformat() if so.created_at else datetime.now(timezone.utc).isoformat(),
            updated_at=so.updated_at.isoformat() if so.updated_at else datetime.now(timezone.utc).isoformat(),
            created_by=so.created_by or "",
            updated_by="",
            evidence_json="[]",
            relationships_json="[]",
            metadata_json=json.dumps({
                "migrated_from": "sh_objects",
                "legacy_id": so.id,
                "data": so.data if isinstance(so.data, str) else json.dumps(so.data) if so.data else "{}",
            }),
            is_archived=so.is_deleted,
        )
        db.session.add(obj)
        migrated += 1

    db.session.commit()
    return migrated, skipped


def run():
    print("=== §4 Object Convergence Migration ===")
    before = UOPObject.query.count()
    print(f"UOPObject before: {before}")

    f_migrated, f_skipped = migrate_founder_objects()
    print(f"FounderObject: {f_migrated} migrated, {f_skipped} skipped")

    o_migrated, o_skipped = migrate_objects_table()
    print(f"Objects table: {o_migrated} migrated, {o_skipped} skipped")

    try:
        s_migrated, s_skipped = migrate_sh_objects()
        print(f"ShObjects: {s_migrated} migrated, {s_skipped} skipped")
    except Exception as e:
        print(f"ShObjects migration skipped (table may not exist): {e}")

    after = UOPObject.query.count()
    print(f"\nUOPObject after: {after}")
    print("Migration complete.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        run()