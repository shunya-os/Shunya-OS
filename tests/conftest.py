"""Shunya OS pytest configuration — fresh temp file per test."""
import pytest, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# JSONB → JSON for SQLite
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

@compiles(JSONB, "sqlite")
def _jsonb_sqlite(element, compiler, **kw):
    return compiler.visit_JSON(element, **kw)

from app import create_app, db as _db
from app.models import Tenant, TeamMember, EntityDefinition, Entity, Business, Brand


@pytest.fixture(scope="function")
def app():
    """Create a fresh app for each test using an isolated temp SQLite file."""
    import tempfile as _tf, config as _cfg
    db_fd, db_path = _tf.mkstemp(suffix=".db")
    os.close(db_fd)

    # Override config BEFORE create_app so engine binds to temp path (Flask-SQLAlchemy 3.x quirk)
    original_uri = _cfg.TestConfig.SQLALCHEMY_DATABASE_URI
    _cfg.TestConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

    from app import create_app, db as _db
    app = create_app("test")

    with app.app_context():
        _db.create_all()
    yield app
    with app.app_context():
        _db.session.close()
        _db.engine.dispose()
    # Remove cached engine so the next test's app doesn't reuse it
    try:
        if app in _db.engines:
            del _db.engines[app]
    except RuntimeError:
        pass  # No app context available, engine already disposed

    _cfg.TestConfig.SQLALCHEMY_DATABASE_URI = original_uri
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        yield _db


@pytest.fixture(scope="function")
def tenant(db):
    t = Tenant(company_name="Test Travel", slug="test-travel",
               business_type="travel", brand_color="#2563eb",
               vertical_config={"vertical": "travel", "completed": True})
    db.session.add(t); db.session.flush()
    return t


@pytest.fixture(scope="function")
def admin_user(db, tenant):
    import hashlib
    u = TeamMember(tenant_id=tenant.id, name="Test Admin",
                   email="admin@test.com", role="admin",
                   password_hash=hashlib.sha256(b"pw123").hexdigest())
    db.session.add(u); db.session.flush()
    return u


@pytest.fixture(scope="function")
def logged_in_client(client, tenant, admin_user, db):
    """Create a properly authenticated client with real UserSession."""
    from app.models import UserSession
    from app.utils import generate_token, hash_token
    from datetime import datetime, timedelta

    token = generate_token(48)
    token_hash = hash_token(token)
    sess = UserSession(
        user_id=admin_user.id,
        token=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.session.add(sess)
    db.session.commit()

    with client.session_transaction() as s:
        s["session_token"] = token
    return client


@pytest.fixture(scope="function")
def lead_definition(db, tenant):
    d = EntityDefinition(tenant_id=tenant.id, type="lead", label="Lead",
        label_plural="Leads", icon="🎯", primary_field="name", layout="kanban",
        statuses=["new","contacted","qualified","converted","lost"], code_prefix="PC",
        schema=[{"name":"name","label":"Name","type":"text","required":True}])
    db.session.add(d); db.session.flush()
    return d


@pytest.fixture(scope="function")
def business(db, admin_user):
    b = Business(name="Test Biz", owner_id=admin_user.id, business_type="travel")
    db.session.add(b); db.session.flush()
    return b


@pytest.fixture(scope="function")
def brand(db, business):
    b = Brand(name="Test Brand", business_id=business.id, is_default=True)
    db.session.add(b); db.session.flush()
    return b