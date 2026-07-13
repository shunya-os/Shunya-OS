"""
Pytest configuration for Panchi Club tests.

Provides shared fixtures:
    app, client, db, tenant, admin_user, lead_definition, logged_in_client
"""

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.auth import TeamMember
from app.tenant import Tenant

# Create a local SQLAlchemy instance with ONLY the models we need
# (avoids index conflicts from full app model registry)
_test_db = SQLAlchemy()


class Lead(_test_db.Model):
    __tablename__ = "leads"
    id = _test_db.Column(_test_db.Integer, primary_key=True)
    code = _test_db.Column(_test_db.String(20), unique=True, nullable=False, index=True)
    source = _test_db.Column(_test_db.String(30), default="manual")
    customer_name = _test_db.Column(_test_db.String(255), index=True)
    phone = _test_db.Column(_test_db.String(30), index=True)
    email = _test_db.Column(_test_db.String(255))
    destination = _test_db.Column(_test_db.String(255))
    pax = _test_db.Column(_test_db.String(100))
    dates = _test_db.Column(_test_db.String(255))
    budget = _test_db.Column(_test_db.Numeric(12, 2), default=0)
    notes = _test_db.Column(_test_db.Text)
    status = _test_db.Column(_test_db.String(30), default="new", index=True)
    assigned_to = _test_db.Column(_test_db.String(120))
    created_at = _test_db.Column(_test_db.DateTime)
    updated_at = _test_db.Column(_test_db.DateTime)


class ActivityLog(_test_db.Model):
    __tablename__ = "activity_logs"
    id = _test_db.Column(_test_db.Integer, primary_key=True)
    lead_id = _test_db.Column(_test_db.Integer, _test_db.ForeignKey("leads.id"), nullable=False)
    action = _test_db.Column(_test_db.String(60), nullable=False)
    detail = _test_db.Column(_test_db.Text, default="")
    user = _test_db.Column(_test_db.String(120), default="")
    created_at = _test_db.Column(_test_db.DateTime)


# ---------------------------------------------------------------------------
# App and database fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def app():
    """Create a minimal Flask app with in-memory SQLite for each test.

    Uses a local SQLAlchemy instance to avoid index conflicts from
    the full app model registry (which includes ClientUser etc.).
    """
    application = Flask(__name__)
    application.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })
    _test_db.init_app(application)
    with application.app_context():
        _test_db.create_all()
        yield application
        _test_db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Test client bound to the app."""
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """Provide the SQLAlchemy database instance within the app context."""
    return _test_db


@pytest.fixture(scope="function")
def tenant(app, db):
    """Create a sample tenant for multi-tenant tests."""
    t = Tenant(
        company_name="Test Travel Co",
        slug="test-travel",
        business_type="travel",
        is_active=True,
    )
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture(scope="function")
def admin_user(app, db):
    """Create an admin TeamMember for auth-required tests."""
    user = TeamMember(
        name="Admin User",
        email="admin@test.com",
        role="admin",
        is_active=True,
    )
    user.set_password("password123")
    user.generate_token()
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope="function")
def lead_definition(app, db):
    """Return a dict describing the expected Lead field schema."""
    return {
        "fields": [
            "customer_name",
            "phone",
            "email",
            "destination",
            "pax",
            "dates",
            "budget",
            "notes",
        ],
        "required": ["customer_name", "destination"],
    }


@pytest.fixture(scope="function")
def logged_in_client(app, client, admin_user):
    """Return a test client with an active session logged in as admin_user."""
    with client.session_transaction() as session:
        session["user_id"] = admin_user.id
        session["_fresh"] = True
    return client