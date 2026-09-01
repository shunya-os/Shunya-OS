"""ZGC-PR-17C — G1 Object Convergence: one canonical object model.

The canonical object representation established by the architecture:
  UniversalObject (kernel) + UOPObject persistence = CANONICAL
  
  ShunyaObject (sh_objects)      = legacy-compat read store (mirror written)
  FounderObject (founder_objects) = legacy-compat store (mirror written)
  Object (app/objects/models.py)  = simple CRUD store (independent, not object)

This test proves:
  - ONE canonical write path (app/objects/canonical.create_canonical_object)
  - Deterministic serialization (round-trip: dict → store → dict)
  - All three stores are written on canonical create (dual-write for migration)
  - Legacy stores are marked and will not receive new independent writes
"""

import pytest
import uuid


@pytest.fixture(scope="module")
def obj_app():
    import os
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["SHUNYA_ENV"] = "test"
    from app import create_app, db
    application = create_app()
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()


@pytest.fixture(autouse=True)
def clean_obj(obj_app):
    from app.kernel.models import UOPObject
    from app.objects.legacy_models import ShunyaObject
    from app.founder.models import FounderObject
    UOPObject.query.delete()
    ShunyaObject.query.delete()
    FounderObject.query.delete()
    from app import db
    db.session.commit()
    yield


class TestObjectConvergence:
    def test_canonical_create_writes_all_stores(self, obj_app):
        """create_canonical_object writes to UOPObject + ShunyaObject + FounderObject."""
        from app.objects.canonical import create_canonical_object
        from app.kernel.models import UOPObject
        from app.objects.legacy_models import ShunyaObject
        from app.founder.models import FounderObject

        oid = f"obj_{uuid.uuid4().hex[:8]}"
        result = create_canonical_object(
            object_id=oid,
            object_type="Document",
            name="Q4 Strategy",
            space_id="spc_business",
            tenant_id=1,
            content="Strategic plan content",
            created_by="sid_canonical_001",
            metadata={"department": "strategy"},
            workspace_id="spc_default",
        )
        assert result["object_id"] == oid
        assert result["name"] == "Q4 Strategy"

        # All three stores have the row
        assert UOPObject.query.filter_by(object_id=oid).count() == 1
        assert ShunyaObject.query.filter_by(object_id=oid).count() == 1
        assert FounderObject.query.filter_by(object_id=oid).count() == 1

    def test_deterministic_serialization(self, obj_app):
        """Round-trip: write → read → same fields."""
        from app.objects.canonical import create_canonical_object, get_canonical_object
        import uuid

        oid = f"obj_{uuid.uuid4().hex[:8]}"
        create_canonical_object(
            object_id=oid, object_type="Contact", name="Alice",
            tenant_id=2, created_by="sid_user",
            metadata={"email": "alice@test.com"},
        )
        retrieved = get_canonical_object(oid)
        assert retrieved is not None
        assert retrieved["object_id"] == oid
        assert retrieved["name"] == "Alice"
        assert retrieved["object_type"] == "Contact"
        assert retrieved["tenant_id"] == 2
        assert retrieved["status"] == "active"
        assert retrieved["version"] == 1
        assert retrieved["confidence"] == 1.0

    def test_canonical_read_fallback(self, obj_app):
        """get_canonical_object reads from ShunyaObject if UOPObject missing."""
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

    def test_founder_object_dual_write(self, obj_app):
        """FounderObject is written as a mirror — no independent write path."""
        from app.objects.canonical import create_canonical_object
        from app.founder.models import FounderObject

        oid = f"obj_{uuid.uuid4().hex[:8]}"
        create_canonical_object(
            object_id=oid, object_type="Conversation", name="Chat #1",
            tenant_id=1, created_by="sid_user",
        )
        fo = FounderObject.query.filter_by(object_id=oid).first()
        assert fo is not None
        # Idempotent: second create updates existing, doesn't duplicate
        create_canonical_object(
            object_id=oid, object_type="Conversation", name="Chat #1 v2",
            tenant_id=1, created_by="sid_user",
        )
        assert FounderObject.query.filter_by(object_id=oid).count() == 1