"""R6B-2.7 Window 5 — tenanted Person creation and lookup isolation.

``persons.tenant_id`` is NOT NULL (migration 0005_fda4_identity_schema). Two
production call sites created a Person WITHOUT a tenant, which would raise
NotNullViolation at runtime:

  * app/document/enrichment_pipeline.py::_find_or_create_person
  * app/identity/service.py::IdentityService.split

Additionally the document enrichment lookup was UNSCOPED — ``Person.query.all()``
could match a person belonging to another tenant and then link this tenant's
document to them.
"""
import pytest


class TestDocumentEnrichmentPerson:
    def _tenant(self, app, slug):
        from app import db
        from app.tenant import Tenant
        t = Tenant(company_name=slug.title(), slug=slug)
        db.session.add(t)
        db.session.commit()
        return t.id

    def test_creates_person_with_tenant(self, app):
        from app.document.enrichment_pipeline import _find_or_create_person
        tid = self._tenant(app, "enrich-a")

        p = _find_or_create_person("Asha Menon", tenant_id=tid)

        assert p is not None
        assert p.tenant_id == tid

    def test_creates_nothing_without_tenant(self, app):
        """No tenant → no creation, and above all NO NotNullViolation."""
        from app.document.enrichment_pipeline import _find_or_create_person
        from app.models import Person

        p = _find_or_create_person("No Tenant Person", tenant_id=None)

        assert p is None
        assert Person.query.filter_by(name="No Tenant Person").count() == 0

    def test_lookup_is_tenant_scoped(self, app):
        """A person in tenant B must not be matched for a tenant A document."""
        from app import db
        from app.document.enrichment_pipeline import _find_or_create_person
        from app.models import Person

        tid_a = self._tenant(app, "enrich-a2")
        tid_b = self._tenant(app, "enrich-b2")

        db.session.add(Person(name="Ravi Kumar", canonical_name="Ravi Kumar",
                              tenant_id=tid_b, status="active"))
        db.session.commit()

        made = _find_or_create_person("Ravi Kumar", tenant_id=tid_a)

        assert made is not None
        assert made.tenant_id == tid_a          # a NEW person in tenant A
        assert made.id != Person.query.filter_by(
            tenant_id=tid_b, name="Ravi Kumar").one().id

    def test_lookup_reuses_person_within_the_same_tenant(self, app):
        from app.document.enrichment_pipeline import _find_or_create_person
        tid = self._tenant(app, "enrich-c")

        first = _find_or_create_person("Meera Iyer", tenant_id=tid)
        again = _find_or_create_person("Meera Iyer", tenant_id=tid)

        assert first.id == again.id


class TestIdentitySplitTenancy:
    def test_split_inherits_tenant(self, app):
        from app import db
        from app.models import Person

        tid = None
        from app.tenant import Tenant
        t = Tenant(company_name="Split Tenant", slug="split-tenant")
        db.session.add(t)
        db.session.commit()
        tid = t.id

        source = Person(name="Source Person", canonical_name="Source Person",
                        tenant_id=tid, status="active")
        db.session.add(source)
        db.session.commit()

        from app.identity.service import IdentityService
        svc = IdentityService(session=db.session)
        result = svc.split(str(source.id), [], reason="test")

        assert result.get("success") is not False, result
        split = Person.query.filter(
            Person.canonical_name.like("%(split)%")).one()
        assert split.tenant_id == tid