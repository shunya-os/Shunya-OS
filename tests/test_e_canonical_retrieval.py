"""E-stage — company-first retrieval: canonical business objects are searchable.

Observed live on 2026-10-09: the founder asked SHUNYA about the "Bali Honeymoon
Opportunity" they had just created in the UI; SHUNYA answered "insufficient
evidence" because the AI retrieval never searched canonical business objects —
and the universal search config for CommercialOpportunity listed columns that
do not exist (name/status/stage vs title/lifecycle_state), so the object type
was silently skipped even there.

This file pins:
  * search_canonical_objects finds opportunities by real columns, scoped by
    organization (canonical organization_id, not legacy tenant_id);
  * the RetrievalLayer ranks canonical business evidence above the internet;
  * the authority ordering across sources.
"""

import pytest


@pytest.fixture(scope="function")
def app():
    from app import create_app, db
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
        "DISABLE_RATE_LIMIT": True,
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


def _seed_opportunity(org_id, title):
    from app import db
    from app.commercial.models import CommercialOpportunity
    opp = CommercialOpportunity(
        organization_id=org_id, title=title,
        description="Seeded for retrieval tests.",
        lifecycle_state="discovered", confidence=50,
    )
    db.session.add(opp)
    db.session.commit()
    return opp.id


def test_opportunity_is_findable_by_its_real_columns(app):
    """Regression: the config listed name/status/stage (no such columns), so
    opportunities were silently skipped by the search loop."""
    from app.search.universal_search import search_canonical_objects

    opp_id = _seed_opportunity(989, "Bali Honeymoon Opportunity — Oct 2026")
    payload = search_canonical_objects("Honeymoon", org_id=989, limit=8)
    names = [r["name"] for r in payload["results"]]
    assert "Bali Honeymoon Opportunity — Oct 2026" in names
    hit = [r for r in payload["results"] if r["id"] == opp_id][0]
    assert hit["type"] == "opportunities"
    assert hit["status"] == "discovered", "lifecycle_state must be surfaced as status"


def test_opportunity_search_is_organization_scoped(app):
    from app.search.universal_search import search_canonical_objects

    _seed_opportunity(989, "Bali Honeymoon Opportunity — Oct 2026")
    # a different organization must not see it
    payload = search_canonical_objects("Honeymoon", org_id=990, limit=8)
    assert payload["results"] == []


def test_retrieval_ranks_canonical_above_internet(app):
    """Authority hierarchy in actual behavior: canonical business state outranks
    external internet evidence."""
    from core.intelligence_runtime.retrieval import RetrievalLayer

    layer = RetrievalLayer()
    layer.set_canonical_provider(lambda q: [{
        "type": "opportunities",
        "name": "Bali Honeymoon Opportunity — Oct 2026",
        "status": "discovered",
        "summary": "created today",
    }])
    layer.set_internet_provider(lambda q: [{
        "url": "https://example.com", "title": "Bali info",
        "snippet": "generic internet content",
    }])

    evidence = layer.retrieve("What is the status of the Bali Honeymoon Opportunity?")
    assert evidence, "retrieval returned nothing"
    assert evidence[0].source == "canonical", (
        f"expected canonical first, got {[(e.source, e.relevance) for e in evidence]}")
    sources = [e.source for e in evidence]
    assert sources.index("canonical") < sources.index("internet")
    assert "Bali Honeymoon Opportunity" in evidence[0].content


def test_retrieval_without_canonical_provider_still_works(app):
    """The layer must tolerate a missing canonical provider (older wirings)."""
    from core.intelligence_runtime.retrieval import RetrievalLayer

    layer = RetrievalLayer()
    evidence = layer.retrieve("anything")
    assert evidence == []