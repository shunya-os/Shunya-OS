"""
Pytest configuration for Shunya OS tests — canonical infrastructure.

Provides fixtures backed by the production create_app() factory and the
global db instance. Replaces the old _test_db approach that had dead-code
inline model definitions.

Exposes:
    app, client, db, tenant, test_tenant, admin_user, logged_in_client
    real_app  (alias for app — backward compat for phase test files)
"""

import os

# Prevent uncontrolled external AI provider calls during tests.
# LocalProvider is deterministic and makes zero network I/O.
# Real provider tests must explicitly override this env var.
os.environ.setdefault("SHUNYA_AI_PROVIDERS", "local")

import pytest
from app import create_app, db


# ---------------------------------------------------------------------------
# App and database fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def app():
    """Create a full Flask app via the production factory.

    Uses the production db instance so ALL models are registered
    (Person, PersonIdentity, Relationship, IntakeSession, etc.).
    Replaces the old _test_db approach that only had Lead and ActivityLog.

    Imports all model modules before create_all() so every table
    that tests may reference is created in the in-memory SQLite.
    """
    application = create_app(config_override={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "DISABLE_RATE_LIMIT": "true",
        "WTF_CSRF_ENABLED": False,
    })
    with application.app_context():
        # Register all models before create_all — some are only imported
        # lazily inside create_app's context processor / middleware.
        from app import models  # noqa: F401
        from app.tenant import Tenant  # noqa: F401
        from app.communication import models as _comm_models  # noqa: F401
        from app.privacy import models as _privacy_models  # noqa: F401
        from app.human_context import models as _hc_models  # noqa: F401
        from app.memory import models as _mem_models  # noqa: F401
        from app.evidence import models as _ev_models  # noqa: F401
        from app.execution import models as _exec_models  # noqa: F401 — registers IdempotencyRecord, Outcome
        from app.marketing import models as _mkt_models  # noqa: F401
        from app.document import models as _doc_models  # noqa: F401
        from app.llm import models as _llm_models  # noqa: F401
        from app.auth import TeamMember  # noqa: F401
        from app.production.identity.workspace_model import Workspace  # noqa: F401
        from app.production.identity_repository import SHUNYAIdentityModel  # noqa: F401
        from app.founder.workspace_models import (  # noqa: F401
            MissingContext,
            NextAction,
            WorkspaceEvent,
            WorkspaceHealthSnapshot,
            WorkspaceNavigation,
        )
        from app.founder.models import (  # noqa: F401
            BusinessRelationship,
            FounderConversation,
            FounderMessage,
            FounderObject,
            FounderSpace,
        )
        from app.integration.models import (  # noqa: F401
            CachedEmail, IntegrationConnection, Notification,
            NotificationPreference,
        )
        from app.automation.models import (  # noqa: F401
            AutomationLog, AutomationRule,
        )
        from app.intelligence.models import (  # noqa: F401
            AnomalyRecord, LearningEvent, ReasoningTrace,
        )
        from app.enterprise.models import (  # noqa: F401
            AuditRecord, EnterpriseRole, EnterpriseTeamMember,
        )
        # Enterprise Security — CRUD Audit Log
        from app.security.audit import AuditLog  # noqa: F401
        # ACT-02 — Execution Log
        from app.execution_log.models import ExecutionLog  # noqa: F401
        # FDA26 — Developer/Integration Platform models
        from app.platform.models import (  # noqa: F401
            WebhookDelivery,
            WebhookSubscription,
        )
        db.create_all()
        yield application
        db.drop_all()


# Alias for backward compatibility with phase test files that use `real_app`
@pytest.fixture(scope="function")
def real_app(app):
    """Alias for the app fixture — backward compat with existing tests."""
    return app


@pytest.fixture(scope="function")
def client(app):
    """Test client bound to the app."""
    return app.test_client()


@pytest.fixture(scope="function")
def tenant(app):
    """Create a sample tenant for multi-tenant tests."""
    from app import db
    from app.tenant import Tenant
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
def test_tenant(tenant):
    """Return the tenant's ID for use as tenant_id parameter."""
    return tenant.id


@pytest.fixture(scope="function")
def admin_user(app):
    """Create an admin TeamMember for auth-required tests."""
    from app import db
    from app.auth import TeamMember
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
def logged_in_client(app, client, admin_user):
    """Return a test client with an active session logged in as admin_user."""
    with client.session_transaction() as session:
        session["user_id"] = admin_user.id
        session["_fresh"] = True
    return client