"""ZGC-PR-17C — G1 Object Convergence: one canonical object model.

The canonical object representation established by the architecture:
  core/object_service.py → sh_objects = CANONICAL

  UOPObject (sh_uop_objects)      = MIGRATION compat (read-only after migration)
  FounderObject (founder_objects)  = LEGACY compat (being migrated to sh_objects)
  Object (app/objects/models.py)   = HISTORICAL (no new production writes)

This test proves:
  - ONE canonical write path (app/objects/canonical.create_canonical_object)
  - Deterministic serialization (round-trip: create → read → same fields)
  - Canonical write goes to sh_objects, NOT to legacy stores
  - Legacy stores are read-only for historical data
"""

import pytest
import uuid


@pytest.fixture(scope="module")
def obj_app():
    from app import create_app, db
    application = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
    with application.app_context():
        yield application


@pytest.fixture(autouse=True)
def clean_obj(obj_app):
    from app import db
    db.session.rollback()
    from sqlalchemy import text
    # Cascade delete all object stores (FK order matters)
    db.session.execute(text("DELETE FROM founder_messages"))
    db.session.execute(text("DELETE FROM founder_conversations"))
    db.session.execute(text("DELETE FROM founder_objects"))
    db.session.execute(text("DELETE FROM sh_uop_objects"))
    db.session.execute(text("DELETE FROM sh_objects"))
    db.session.execute(text("DELETE FROM objects"))
    # Ensure required workspace exists for FK constraint
    ws = db.session.execute(
        text("SELECT id FROM sh_workspaces WHERE id = 'spc_default'")
    ).first()
    if not ws:
        db.session.execute(
            text("""INSERT INTO sh_workspaces (id, name, workspace_type, created_by)
                    VALUES ('spc_default', 'Default', 'personal', 'system')""")
        )
    db.session.commit()
    yield


class TestObjectConvergence:
    def test_canonical_create_writes_sh_objects(self, obj_app):
        """create_canonical_object writes to sh_objects (canonical store)."""
        from app.objects.canonical import create_canonical_object
        from app.objects.legacy_models import ShunyaObject
        from app.kernel.models import UOPObject
        from app.founder.models import FounderObject

        oid = f"obj_{uuid.uuid4().hex[:8]}"
        result = create_canonical_object(
            object_id=oid,
            object_type="Document",
            name="Q4 Strategy",
            space_id="spc_business",
            tenant_id=1,
            created_by="sid_canonical_001",
            metadata={"department": "strategy"},
            workspace_id="spc_default",
        )
        assert result["name"] == "Q4 Strategy"

        # Canonical store (sh_objects) has the row
        so_count = ShunyaObject.query.filter_by(name="Q4 Strategy").count()
        assert so_count >= 1, "sh_objects must have the canonical object"

        # Legacy stores are NOT written by canonical create (G1.1-R3 simplification)
        uop_count = UOPObject.query.filter_by(object_id=oid).count()
        assert uop_count == 0, "UOPObject must NOT be written by canonical create"

        fo_count = FounderObject.query.filter_by(object_id=oid).count()
        assert fo_count == 0, "FounderObject must NOT be written by canonical create"

    def test_deterministic_serialization(self, obj_app):
        """Round-trip: write → read → same fields."""
        from app.objects.canonical import create_canonical_object, get_canonical_object
        from app import db
        from sqlalchemy import text

        # Ensure organization exists for FK constraint
        db.session.execute(
            text("""INSERT INTO organizations (id, name, slug)
                    VALUES (2, 'Test Org', 'test-org-2')
                    ON CONFLICT (id) DO NOTHING""")
        )
        db.session.commit()

        oid = f"obj_{uuid.uuid4().hex[:8]}"
        create_canonical_object(
            object_id=oid, object_type="Contact", name="Alice",
            tenant_id=2, created_by="sid_user",
            metadata={"email": "alice@test.com"},
        )
        retrieved = get_canonical_object(oid)
        assert retrieved is not None
        assert retrieved["name"] == "Alice"
        assert retrieved["object_type"] == "Contact"
        assert retrieved["tenant_id"] == 2
        assert retrieved["status"] == "active"

    def test_canonical_read_fallback(self, obj_app):
        """get_canonical_object reads from sh_objects (canonical store)."""
        from app.objects.canonical import get_canonical_object
        from app.objects.legacy_models import ShunyaObject
        from app import db

        oid = f"obj_{uuid.uuid4().hex[:8]}"
        sh = ShunyaObject(
            object_id=oid, workspace_id="spc_default",
            object_type="LegacyNote", name="Old Note", created_by="system",
        )
        db.session.add(sh)
        db.session.commit()

        retrieved = get_canonical_object(oid)
        assert retrieved is not None
        assert retrieved["name"] == "Old Note"

    def test_legacy_stores_are_not_written_by_canonical(self, obj_app):
        """Canonical create does NOT write to FounderObject (G1.1-R3 simplification)."""
        from app.objects.canonical import create_canonical_object
        from app.founder.models import FounderObject

        oid = f"obj_{uuid.uuid4().hex[:8]}"
        create_canonical_object(
            object_id=oid, object_type="Conversation", name="Chat #1",
            tenant_id=1, created_by="sid_user",
        )
        fo = FounderObject.query.filter_by(object_id=oid).first()
        assert fo is None, "FounderObject must NOT be written by canonical create"
        # Idempotent: second create doesn't write to FounderObject either
        create_canonical_object(
            object_id=oid, object_type="Conversation", name="Chat #1 v2",
            tenant_id=1, created_by="sid_user",
        )
        assert FounderObject.query.filter_by(object_id=oid).count() == 0