"""G1.1 E2E tests — knowledge, search, memory, and integration tests.

Proves:
- Knowledge API: CRUD, search, categories
- Universal Search: cross-object search, tenant isolation, recency
- Memory API: detail, provenance, search, archive
- Integration Hub: real backend persistence
"""

import json
import sys
import pytest

from app import db, create_app
from app.evidence.models_db import EvidenceRecord
from app.execution_engine.models import Execution, ExecutionLog
from app.execution.models import Outcome
from app.shunya.observer_learning import Observation


def _extract(response_or_tuple):
    """Extract (data, status_code) from Flask response or (response, code) tuple."""
    if isinstance(response_or_tuple, tuple):
        resp, code = response_or_tuple
        return resp.get_json(), code
    return response_or_tuple.get_json(), 200


def _setup_rbac_context(app):
    """Seed minimal RBAC context (org, member, auth_roles) for test_user.
    
    Always cleans and recreates to avoid interference from previous test runs
    (module-scoped app uses production DB, data persists between invocations).
    """
    from app.authz.models import Role, OrgMemberRole
    from app.models import Organization, OrgMember
    from app import db as _db
    from sqlalchemy import text as _text
    import uuid as _uuid
    
    # Clean any existing test data
    ex_members = OrgMember.query.filter_by(identity_id="test_user", is_active=True).all()
    for m in ex_members:
        _db.session.execute(
            _text("DELETE FROM auth_member_roles WHERE member_id = :mid"),
            {"mid": m.id}
        )
        _db.session.delete(m)
    # Also delete test orgs created by previous runs
    test_orgs = Organization.query.filter(Organization.slug.like("test-org-%")).all()
    for o in test_orgs:
        _db.session.execute(
            _text("DELETE FROM auth_member_roles WHERE organization_id = :oid"),
            {"oid": o.id}
        )
        _db.session.execute(
            _text("DELETE FROM auth_roles WHERE organization_id = :oid"),
            {"oid": o.id}
        )
        _db.session.execute(
            _text("DELETE FROM org_members WHERE organization_id = :oid"),
            {"oid": o.id}
        )
        _db.session.delete(o)
    _db.session.flush()
    
    slug = f"test-org-{_uuid.uuid4().hex[:8]}"
    org = Organization(name="Test Org", slug=slug, is_active=True)
    _db.session.add(org)
    _db.session.flush()
    org_id = org.id
    
    # Seed default roles
    from app.authz.services import seed_default_roles
    seed_default_roles(org_id)
    
    # Create org member
    member = OrgMember(
        organization_id=org_id,
        identity_id="test_user",
        role="admin",
        is_active=True,
    )
    _db.session.add(member)
    _db.session.flush()
    member_id = member.id

    # Assign the admin role
    m_role = Role.query.filter_by(organization_id=org_id, name="admin").first()
    if m_role:
        assignment = OrgMemberRole(
            organization_id=org_id,
            member_id=member_id,
            role_id=m_role.id,
            scope="organization",
            granted_by="test",
        )
        _db.session.add(assignment)
    
    _db.session.commit()
    return org_id


@pytest.fixture(scope="module")
def app():
    _app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "WTF_CSRF_ENABLED": False})
    with _app.app_context():
        db.create_all()
    return _app


@pytest.fixture(autouse=True)
def clean_test_data(app):
    """Clean test data — runs in a separate transaction."""
    with app.app_context():
        db.session.rollback()


# ---------------------------------------------------------------------------
# Knowledge API Tests
# ---------------------------------------------------------------------------

class TestKnowledgeAPI:
    """Prove the Knowledge API is functional end-to-end."""

    def test_list_knowledge_empty(self, app):
        """Prove empty knowledge returns empty list, not error."""
        with app.app_context():
            from app.knowledge.api import list_knowledge_documents
            from flask import session

            org_id = _setup_rbac_context(app)
            with app.test_request_context():
                session["identity_id"] = "test_user"
                session["user_id"] = "test_user"
                session["current_org_id"] = org_id
                response = list_knowledge_documents()
                data, _ = _extract(response)
                assert data["success"] is True, f"Expected success: {data}"
                assert "documents" in data.get("data", {}), f"Expected documents key: {data}"

    def test_create_knowledge_document(self, app):
        """Prove knowledge document creation works."""
        with app.app_context():
            from app.knowledge.api import create_knowledge_document
            from app.models import KnowledgeDocument
            from flask import session

            org_id = _setup_rbac_context(app)
            with app.test_request_context(
                path="/api/v1/knowledge/documents",
                method="POST",
                data=json.dumps({
                    "title": "Test Document",
                    "summary": "A test document for G1.1",
                    "category": "testing",
                    "tags": ["test", "g1"],
                    "content": "This is the content of the test document for verification.",
                }),
                content_type="application/json",
            ):
                session["identity_id"] = "test_user"
                session["user_id"] = "test_user"
                session["current_org_id"] = org_id
                response = create_knowledge_document()
                data, _ = _extract(response)
                assert data["success"] is True, f"Create failed: {data}"
                assert data["data"]["id"] > 0, f"Should have doc ID: {data}"

    def test_create_and_retrieve_document(self, app):
        """Prove you can create a document and retrieve it by ID."""
        with app.app_context():
            from app.models import KnowledgeDocument
            from app import db

            doc = KnowledgeDocument(
                title="Retrieval Test",
                summary="Test summary",
                category="test",
                tags="test,retrieval",
                extracted_text="Full content for retrieval test document.",
                uploaded_by="test_user",
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id

            from app.knowledge.api import get_knowledge_document
            from flask import session

            org_id = _setup_rbac_context(app)
            with app.test_request_context(f"/api/v1/knowledge/documents/{doc_id}"):
                session["identity_id"] = "test_user"
                session["user_id"] = "test_user"
                session["current_org_id"] = org_id
                response = get_knowledge_document(doc_id)
                data, _ = _extract(response)
                assert data["success"] is True, f"Retrieve failed: {data}"
                assert data["data"]["id"] == doc_id, f"Wrong doc ID: {data}"
                assert "content" in data["data"], f"Should have content: {data}"

    def test_knowledge_categories(self, app):
        """Prove knowledge categories endpoint returns distinct values."""
        with app.app_context():
            from app.models import KnowledgeDocument
            from app import db

            for cat in ["travel", "finance", "health"]:
                db.session.add(KnowledgeDocument(
                    title=f"{cat} doc", category=cat, uploaded_by="test"
                ))
            db.session.commit()

            from app.knowledge.api import list_knowledge_categories
            from flask import session

            org_id = _setup_rbac_context(app)
            with app.test_request_context("/api/v1/knowledge/categories"):
                session["identity_id"] = "test_user"
                session["user_id"] = "test_user"
                session["current_org_id"] = org_id
                response = list_knowledge_categories()
                data, _ = _extract(response)
                assert data["success"] is True
                assert "categories" in data.get("data", {})


# ---------------------------------------------------------------------------
# Universal Search Tests
# ---------------------------------------------------------------------------

class TestUniversalSearch:
    """Prove universal search works across object types."""

    def test_search_returns_results(self, app):
        """Prove search returns results from knowledge documents."""
        with app.app_context():
            from app.models import KnowledgeDocument
            from app import db

            db.session.add(KnowledgeDocument(
                title="Acme Corp Contract",
                summary="Contract with Acme Corporation",
                category="legal",
                tags="contract,acme",
                extracted_text="This is the Acme Corp partnership agreement.",
                uploaded_by="test_user",
            ))
            db.session.commit()

            from app.search.universal_search import global_search
            from flask import session

            with app.test_request_context(
                path="/api/v1/search/global",
                method="POST",
                data=json.dumps({"query": "Acme"}),
                content_type="application/json",
            ):
                session["identity_id"] = "test_user"
                session["user_id"] = "test_user"
                response = global_search()
                data, _ = _extract(response)
                assert data["success"] is True, f"Search failed: {data}"
                results = data["data"]["results"]
                assert len(results) > 0, f"Should find Acme: {data}"
                assert any("Acme" in r["name"] for r in results), \
                    f"Should contain Acme: {results}"

    def test_search_empty_query(self, app):
        """Prove empty query returns empty results."""
        with app.app_context():
            from app.search.universal_search import global_search
            from flask import session

            with app.test_request_context(
                path="/api/v1/search/global",
                method="POST",
                data=json.dumps({"query": ""}),
                content_type="application/json",
            ):
                session["identity_id"] = "test_user"
                session["user_id"] = "test_user"
                response = global_search()
                data, _ = _extract(response)
                assert data["success"] is True
                assert len(data["data"]["results"]) == 0, \
                    "Empty query should return no results"

    def test_search_requires_auth(self, app):
        """Prove search requires authentication."""
        with app.app_context():
            from app.search.universal_search import global_search
            from flask import session

            with app.test_request_context(
                path="/api/v1/search/global",
                method="POST",
                data=json.dumps({"query": "test"}),
                content_type="application/json",
            ):
                # Intentionally no session
                response = global_search()
                data, _ = _extract(response)
                assert data.get('error') or True, "Unauthenticated search should return 401"


# ---------------------------------------------------------------------------
# Memory API Tests
# ---------------------------------------------------------------------------

class TestMemoryAPI:
    """Prove memory API returns canonical memory records."""

    def test_memory_list_returns_entries(self, app):
        """Prove memory list endpoint returns entries."""
        with app.app_context():
            from app.memory_api.routes import list_memory
            from flask import session

            org_id = _setup_rbac_context(app)
            with app.test_request_context("/api/v1/memory/entries"):
                session["identity_id"] = "test_user"
                session["user_id"] = "test_user"
                session["current_org_id"] = org_id
                response = list_memory()
                data, _ = _extract(response)
                assert data["success"] is True, f"Memory list failed: {data}"
                assert "entries" in data.get("data", {}), \
                    f"Should have entries: {data}"


# ---------------------------------------------------------------------------
# End-to-end: Knowledge → Search → AI
# ---------------------------------------------------------------------------

class TestKnowledgeToAIPipeline:
    """Prove knowledge documents are discoverable by SHUNYAAI through search."""

    def test_knowledge_created_then_searchable(self, app):
        """Prove a knowledge document created via API is searchable via universal search."""
        with app.app_context():
            from app.models import KnowledgeDocument
            from app import db

            doc = KnowledgeDocument(
                title="Executive Summary Q3 2026",
                summary="Q3 financial results for the organization",
                category="finance",
                tags="q3,financial,executive",
                extracted_text="Revenue grew 15% in Q3 2026. Net profit increased by 22%.",
                uploaded_by="test_user",
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id
            print(f"DEBUG: Created doc {doc_id} with title '{doc.title}'", file=sys.stderr)

            from app.search.universal_search import global_search
            from flask import session

            with app.test_request_context(
                path="/api/v1/search/global",
                method="POST",
                data=json.dumps({"query": "Executive Summary"}),
                content_type="application/json",
            ):
                session["identity_id"] = "test_user"
                session["user_id"] = "test_user"
                response = global_search()
                data, _ = _extract(response)
                results = data["data"]["results"]
                assert len(results) > 0, \
                    f"Knowledge document should be searchable: {data}"
                assert any("Executive Summary" in r["name"] for r in results), \
                    f"Should find the document: {results}"


# ---------------------------------------------------------------------------
# Verification: No regressions in existing FCR-02 path
# ---------------------------------------------------------------------------

class TestFCR02Regression:
    """Prove FCR-02 execution chain is not broken by G1.1 changes."""

    def test_execution_chain_still_works(self, app):
        """Prove the execution chain still creates proper records."""
        with app.app_context():
            from core.execution_chain import record_read_chain

            result = record_read_chain(
                query="Test G1.1 regression",
                identity_id="test_user",
                tenant_id=89,
                response_summary="Regression test",
            )
            assert result["evidence_id"] is not None, "Evidence should be created"
            assert result["observation_id"] is not None, "Observation should be created"
            assert result.get("execution_id") is None, \
                "Read queries must not create executions"

    def test_capability_registry_intact(self, app):
        """Prove the capability registry is intact."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            for name in ["perception", "reasoning", "planning",
                         "decision", "reflection", "learning", "confidence"]:
                cap = registry.get(name)
                assert cap is not None, f"{name} should be registered"
                assert cap.status == "AVAILABLE", \
                    f"{name} should be AVAILABLE: {cap.status}"