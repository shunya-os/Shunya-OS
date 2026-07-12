"""Tests for Shunya OS database models and entity code functions."""

import uuid
from datetime import datetime, date, timedelta
from app.models import (
    Tenant, TeamMember, EntityDefinition, Entity, ActivityLog,
    BusinessGroup, Business, Brand,
    next_entity_code, compute_all_prefixes, ensure_entity_prefixes,
    _compute_entity_prefix, get_code_prefix,
)


# =============================================================================
# BusinessGroup
# =============================================================================

class TestBusinessGroup:
    def test_create_business_group(self, db, admin_user):
        """Create a BusinessGroup and verify its fields."""
        bg = BusinessGroup(
            name="Reliance Industries",
            owner_id=admin_user.id,
            description="Conglomerate",
            industry="conglomerate",
        )
        db.session.add(bg)
        db.session.flush()

        assert bg.id is not None
        assert bg.name == "Reliance Industries"
        assert bg.owner_id == admin_user.id
        assert bg.description == "Conglomerate"
        assert bg.industry == "conglomerate"
        assert bg.created_at is not None

    def test_business_group_to_dict(self, db, admin_user):
        """BusinessGroup.to_dict returns expected keys."""
        bg = BusinessGroup(name="Tata Group", owner_id=admin_user.id)
        db.session.add(bg)
        db.session.flush()

        d = bg.to_dict()
        assert d["id"] == bg.id
        assert d["name"] == "Tata Group"
        assert "industry" in d

    def test_business_group_businesses_relation(self, db, admin_user):
        """BusinessGroup.businesses lists child businesses."""
        bg = BusinessGroup(name="Group", owner_id=admin_user.id)
        db.session.add(bg)
        db.session.flush()

        b1 = Business(name="Biz A", owner_id=admin_user.id, business_type="retail", group_id=bg.id)
        b2 = Business(name="Biz B", owner_id=admin_user.id, business_type="tech", group_id=bg.id)
        db.session.add_all([b1, b2])
        db.session.flush()

        assert len(bg.businesses) == 2
        assert {b.name for b in bg.businesses} == {"Biz A", "Biz B"}


# =============================================================================
# Business
# =============================================================================

class TestBusiness:
    def test_create_business(self, db, admin_user):
        """Create a Business and verify its fields."""
        b = Business(
            name="Test Travel Co",
            owner_id=admin_user.id,
            business_type="travel",
            description="A travel company",
        )
        db.session.add(b)
        db.session.flush()

        assert b.id is not None
        assert b.name == "Test Travel Co"
        assert b.owner_id == admin_user.id
        assert b.business_type == "travel"
        assert b.is_active is True
        assert b.created_at is not None

    def test_business_brands_relation(self, db, business):
        """Business.brands lists child brands."""
        Brand(name="Premium", business_id=business.id, is_default=True)
        Brand(name="Economy", business_id=business.id)
        db.session.flush()

        assert len(business.brands) == 2
        assert {br.name for br in business.brands} == {"Premium", "Economy"}

    def test_business_tenant_count(self, db, business, tenant):
        """Business.tenant_count reflects number of tenants across brands."""
        brand = Brand(name="Default", business_id=business.id, is_default=True)
        db.session.add(brand)
        db.session.flush()

        # Link tenant to brand via brand_id — the property counts tenants
        tenant.brand_id = brand.id
        db.session.flush()

        assert business.tenant_count == 1

    def test_business_to_dict(self, db, business):
        """Business.to_dict returns expected keys."""
        d = business.to_dict()
        assert d["id"] == business.id
        assert d["name"] == "Test Business"
        assert d["business_type"] == "travel"
        assert "brand_count" in d
        assert "is_active" in d


# =============================================================================
# Brand
# =============================================================================

class TestBrand:
    def test_create_brand(self, db, business):
        """Create a Brand and verify its fields."""
        b = Brand(
            name="Luxury Travels",
            business_id=business.id,
            is_default=True,
            description="High-end travel brand",
            brand_color="#ff0000",
            brand_tagline="Travel in style",
        )
        db.session.add(b)
        db.session.flush()

        assert b.id is not None
        assert b.name == "Luxury Travels"
        assert b.business_id == business.id
        assert b.is_default is True
        assert b.brand_color == "#ff0000"
        assert b.brand_tagline == "Travel in style"
        assert b.created_at is not None

    def test_brand_is_default_flag(self, db, business):
        """Multiple brands, only one is_default=True."""
        b1 = Brand(name="Default", business_id=business.id, is_default=True)
        b2 = Brand(name="Secondary", business_id=business.id)
        db.session.add_all([b1, b2])
        db.session.flush()

        defaults = [br for br in Brand.query.filter_by(business_id=business.id).all() if br.is_default]
        assert len(defaults) == 1
        assert defaults[0].name == "Default"

    def test_brand_to_dict(self, db, brand):
        """Brand.to_dict returns expected keys."""
        d = brand.to_dict()
        assert d["id"] == brand.id
        assert d["name"] == "Test Brand"
        assert d["business_id"] == brand.business_id
        assert d["is_default"] is True
        assert "tenant_count" in d
        assert "logo_url" in d


# =============================================================================
# Tenant
# =============================================================================

class TestTenant:
    def test_create_tenant(self, db):
        """Create a Tenant with all fields."""
        t = Tenant(
            company_name="Acme Corp",
            slug="acme-corp",
            business_type="retail",
            brand_color="#00ff00",
            brand_color_secondary="#ff00ff",
            vertical_config={"vertical": "retail", "completed": True},
            plan="pro",
            max_team_members=25,
            is_active=True,
        )
        db.session.add(t)
        db.session.flush()

        assert t.id is not None
        assert t.company_name == "Acme Corp"
        assert t.slug == "acme-corp"
        assert t.business_type == "retail"
        assert t.plan == "pro"
        assert t.is_active is True
        assert t.onboarding_completed is False  # default
        assert t.created_at is not None

    def test_tenant_unique_slug(self, db):
        """Two tenants cannot share the same slug."""
        t1 = Tenant(company_name="A", slug="same-slug")
        t2 = Tenant(company_name="B", slug="same-slug")
        db.session.add(t1)
        db.session.flush()

        db.session.add(t2)
        import pytest
        with pytest.raises(Exception):
            db.session.flush()

    def test_tenant_to_dict(self, db, tenant):
        """Tenant.to_dict returns expected keys."""
        d = tenant.to_dict()
        assert d["id"] == tenant.id
        assert d["company_name"] == "Test Travel"
        assert d["slug"] == "test-travel"
        assert d["business_type"] == "travel"
        assert "vertical_config" in d
        assert "theme_config" in d
        assert "brand_tagline" in d


# =============================================================================
# EntityDefinition
# =============================================================================

class TestEntityDefinition:
    def test_create_with_schema(self, db, tenant):
        """Create an EntityDefinition with full schema."""
        ed = EntityDefinition(
            tenant_id=tenant.id,
            type="patient",
            label="Patient",
            label_plural="Patients",
            icon="🏥",
            primary_field="name",
            layout="table",
            statuses=["new", "in-progress", "discharged", "follow-up"],
            code_prefix="PAT",
            schema=[
                {"name": "name", "label": "Name", "type": "text", "required": True},
                {"name": "age", "label": "Age", "type": "number"},
                {"name": "blood_group", "label": "Blood Group", "type": "select",
                 "options": ["A+", "B+", "O+"]},
            ],
        )
        db.session.add(ed)
        db.session.flush()

        assert ed.id is not None
        assert ed.type == "patient"
        assert ed.label == "Patient"
        assert len(ed.statuses) == 4
        assert ed.code_prefix == "PAT"
        assert len(ed.schema) == 3
        assert ed.schema[0]["name"] == "name"

    def test_entity_definition_to_dict(self, db, lead_definition):
        """EntityDefinition.to_dict returns expected keys."""
        d = lead_definition.to_dict()
        assert d["type"] == "lead"
        assert d["label"] == "Lead"
        assert d["icon"] == "🎯"
        assert "schema" in d
        assert "statuses" in d
        assert "is_active" in d
        assert "primary_field" in d

    def test_entity_definition_unique_type_per_tenant(self, db, tenant):
        """Duplicate entity type for same tenant raises error."""
        EntityDefinition(tenant_id=tenant.id, type="order", label="Order", statuses=["new", "done"])
        db.session.flush()

        dup = EntityDefinition(tenant_id=tenant.id, type="order", label="Order 2", statuses=["a", "b"])
        db.session.add(dup)
        import pytest
        with pytest.raises(Exception):
            db.session.flush()


# =============================================================================
# Entity
# =============================================================================

class TestEntity:
    def test_create_entity(self, db, tenant, lead_definition, admin_user):
        """Create an Entity and verify its fields."""
        entity = Entity(
            tenant_id=tenant.id,
            definition_id=lead_definition.id,
            code="PC11072601",
            status="new",
            data={"name": "John Doe", "email": "john@test.com", "budget": 50000},
            created_by=admin_user.id,
        )
        db.session.add(entity)
        db.session.flush()

        assert entity.id is not None
        assert entity.code == "PC11072601"
        assert entity.status == "new"
        assert entity.data["name"] == "John Doe"
        assert entity.data["budget"] == 50000
        assert entity.created_at is not None
        assert entity.updated_at is not None
        assert entity.is_archived is False

    def test_entity_display_name_uses_primary_field(self, db, tenant, lead_definition):
        """Entity.display_name returns the primary field value."""
        entity = Entity(
            tenant_id=tenant.id,
            definition_id=lead_definition.id,
            data={"name": "Alice Wonderland"},
        )
        db.session.add(entity)
        db.session.flush()

        assert entity.display_name == "Alice Wonderland"

    def test_entity_display_name_fallback_to_code(self, db, tenant, lead_definition):
        """Entity.display_name falls back to code when data lacks primary field."""
        entity = Entity(
            tenant_id=tenant.id,
            definition_id=lead_definition.id,
            code="PC01010101",
            data={},
        )
        db.session.add(entity)
        db.session.flush()

        assert entity.display_name == "PC01010101"

    def test_entity_status_defaults_to_first_definition_status(self, db, tenant, lead_definition):
        """Entity status should default to the first status in the definition's statuses list."""
        entity = Entity(
            tenant_id=tenant.id,
            definition_id=lead_definition.id,
            data={"name": "Default Status Test"},
        )
        db.session.add(entity)
        db.session.flush()

        # lead_definition has statuses=["new", "contacted", "qualified", "converted", "lost"]
        assert entity.status == "new"

    def test_entity_update(self, db, tenant, lead_definition):
        """Update an Entity's data and status."""
        entity = Entity(
            tenant_id=tenant.id,
            definition_id=lead_definition.id,
            data={"name": "Update Me"},
            status="new",
        )
        db.session.add(entity)
        db.session.flush()

        entity.status = "qualified"
        entity.data["budget"] = 100000
        db.session.flush()

        updated = db.session.get(Entity, entity.id)
        assert updated.status == "qualified"
        assert updated.data["budget"] == 100000

    def test_entity_delete_cascade_activity(self, db, tenant, lead_definition):
        """Deleting an Entity cascades to its ActivityLog records."""
        entity = Entity(
            tenant_id=tenant.id,
            definition_id=lead_definition.id,
            data={"name": "Delete Test"},
        )
        db.session.add(entity)
        db.session.flush()

        log = ActivityLog(
            tenant_id=tenant.id,
            entity_id=entity.id,
            user_id=None,
            action="created",
            detail="Entity created",
        )
        db.session.add(log)
        db.session.flush()

        assert ActivityLog.query.count() == 1

        db.session.delete(entity)
        db.session.flush()

        assert ActivityLog.query.count() == 0

    def test_entity_to_dict(self, db, tenant, lead_definition):
        """Entity.to_dict returns expected keys."""
        entity = Entity(
            tenant_id=tenant.id,
            definition_id=lead_definition.id,
            code="PC99010101",
            data={"name": "Dict Test"},
        )
        db.session.add(entity)
        db.session.flush()

        d = entity.to_dict()
        assert d["id"] == entity.id
        assert d["code"] == "PC99010101"
        assert d["entity_type"] == "lead"
        assert d["status"] == "new"
        assert d["data"]["name"] == "Dict Test"
        assert "created_at" in d
        assert "updated_at" in d
        assert "is_archived" in d


# =============================================================================
# ActivityLog
# =============================================================================

class TestActivityLog:
    def test_create_activity_log(self, db, tenant, lead_definition):
        """Create an ActivityLog entry."""
        entity = Entity(
            tenant_id=tenant.id,
            definition_id=lead_definition.id,
            data={"name": "Activity Test"},
        )
        db.session.add(entity)
        db.session.flush()

        log = ActivityLog(
            tenant_id=tenant.id,
            entity_id=entity.id,
            user_id=None,
            action="created",
            detail="Lead created via web form",
            metadata_json={"source": "website", "referrer": "google.com"},
        )
        db.session.add(log)
        db.session.flush()

        assert log.id is not None
        assert log.action == "created"
        assert log.detail == "Lead created via web form"
        assert log.metadata_json["source"] == "website"
        assert log.created_at is not None
        assert log.governance_level == "auto"


# =============================================================================
# Entity Code — next_entity_code
# =============================================================================

class TestNextEntityCode:
    def test_next_entity_code_lead_starts_with_pc(self, db, tenant, lead_definition):
        """next_entity_code('lead') returns code starting with PC."""
        code = next_entity_code(db.session, tenant.id, "lead")
        assert code.startswith("PC"), f"Expected PC prefix, got {code}"

    def test_next_entity_code_ticket_starts_with_ti(self, db, tenant):
        """next_entity_code('ticket') returns code starting with TI (first 2 letters)."""
        # Create definition so prefix is computed
        ed = EntityDefinition(
            tenant_id=tenant.id,
            type="ticket",
            label="Ticket",
            statuses=["open", "closed"],
            code_prefix="TI",
        )
        db.session.add(ed)
        db.session.flush()

        code = next_entity_code(db.session, tenant.id, "ticket")
        assert code.startswith("TI"), f"Expected TI prefix, got {code}"

    def test_next_entity_code_includes_date(self, db, tenant, lead_definition):
        """next_entity_code includes date part in DDMMYY format."""
        ref = date(2026, 7, 12)
        code = next_entity_code(db.session, tenant.id, "lead", ref_date=ref)
        # Expected format: PC120726##
        assert code.startswith("PC120726"), f"Expected date 120726, got {code}"

    def test_next_entity_code_increments_sequence(self, db, tenant, lead_definition):
        """next_entity_code increments the sequence number."""
        ref = date(2026, 7, 12)
        code1 = next_entity_code(db.session, tenant.id, "lead", ref_date=ref)
        code2 = next_entity_code(db.session, tenant.id, "lead", ref_date=ref)
        code3 = next_entity_code(db.session, tenant.id, "lead", ref_date=ref)

        assert code1.endswith("01")
        assert code2.endswith("02")
        assert code3.endswith("03")

    def test_next_entity_code_different_type_different_prefix(self, db, tenant):
        """Different entity types get different code prefixes."""
        lead_def = EntityDefinition(
            tenant_id=tenant.id, type="lead", label="Lead",
            statuses=["new"], code_prefix="PC",
        )
        ticket_def = EntityDefinition(
            tenant_id=tenant.id, type="ticket", label="Ticket",
            statuses=["open"], code_prefix="TI",
        )
        db.session.add_all([lead_def, ticket_def])
        db.session.flush()

        lead_code = next_entity_code(db.session, tenant.id, "lead")
        ticket_code = next_entity_code(db.session, tenant.id, "ticket")

        assert lead_code.startswith("PC")
        assert ticket_code.startswith("TI")


# =============================================================================
# Entity Code — compute_all_prefixes
# =============================================================================

class TestComputeAllPrefixes:
    def test_no_conflicts(self):
        """compute_all_prefixes returns unique prefixes for all types."""
        types = ["lead", "ticket", "opportunity", "patient", "order", "invoice"]
        result = compute_all_prefixes(types)

        assert len(result) == len(types)
        assert set(result.keys()) == set(types)
        # All prefixes must be unique
        prefixes = list(result.values())
        assert len(prefixes) == len(set(prefixes)), f"Duplicate prefixes: {result}"

    def test_lead_maps_to_pc(self):
        """'lead' always resolves to PC via built-in override."""
        result = compute_all_prefixes(["lead", "ticket"])
        assert result["lead"] == "PC"

    def test_prefixes_are_uppercase(self):
        """All computed prefixes are uppercase."""
        types = ["lead", "ticket", "patient", "invoice"]
        result = compute_all_prefixes(types)
        for p in result.values():
            assert p == p.upper(), f"Prefix {p} is not uppercase"

    def test_conflicting_types_get_longer_prefix(self):
        """When first 2 letters conflict, longer prefix is used."""
        # "op" would conflict between "opportunity" and "operation"
        types = ["opportunity", "operation"]
        result = compute_all_prefixes(types)
        prefixes = list(result.values())
        assert len(prefixes) == len(set(prefixes))
        # Neither is just "OP" — one must be longer
        assert "OPP" in result.values() or "OPE" in result.values()

    def test_custom_types_do_not_conflict(self):
        """Custom entity types all get unique prefixes."""
        types = ["lead", "patient", "product", "purchase", "project"]
        result = compute_all_prefixes(types)
        prefixes = list(result.values())
        assert len(prefixes) == len(set(prefixes))


# =============================================================================
# ensure_entity_prefixes
# =============================================================================

class TestEnsureEntityPrefixes:
    def test_persists_to_db(self, db, tenant):
        """ensure_entity_prefixes computes and persists code_prefix for definitions without one."""
        lead_def = EntityDefinition(
            tenant_id=tenant.id, type="lead", label="Lead",
            statuses=["new"], code_prefix="",  # explicit empty
        )
        ticket_def = EntityDefinition(
            tenant_id=tenant.id, type="ticket", label="Ticket",
            statuses=["open"], code_prefix="",  # explicit empty
        )
        db.session.add_all([lead_def, ticket_def])
        db.session.flush()

        # Both should have empty code_prefix before
        assert lead_def.code_prefix == ""
        assert ticket_def.code_prefix == ""

        ensure_entity_prefixes(db.session, tenant.id)

        # Reload from DB
        db.session.refresh(lead_def)
        db.session.refresh(ticket_def)

        assert lead_def.code_prefix == "PC", f"Expected PC, got {lead_def.code_prefix}"
        assert ticket_def.code_prefix == "TI", f"Expected TI, got {ticket_def.code_prefix}"

    def test_skips_existing_prefixes(self, db, tenant):
        """ensure_entity_prefixes does NOT overwrite existing code_prefix values."""
        lead_def = EntityDefinition(
            tenant_id=tenant.id, type="lead", label="Lead",
            statuses=["new"], code_prefix="CUSTOM",
        )
        db.session.add(lead_def)
        db.session.flush()

        ensure_entity_prefixes(db.session, tenant.id)
        db.session.refresh(lead_def)

        # Should still be CUSTOM, not overwritten to PC
        assert lead_def.code_prefix == "CUSTOM"


# =============================================================================
# get_code_prefix
# =============================================================================

class TestGetCodePrefix:
    def test_get_code_prefix_from_definition(self, db, tenant, lead_definition):
        """get_code_prefix returns the prefix from the entity definition."""
        prefix = get_code_prefix(db.session, "lead", tenant.id)
        assert prefix == "PC"

    def test_get_code_prefix_computes_if_missing(self, db, tenant):
        """get_code_prefix computes a prefix when the definition has none."""
        ed = EntityDefinition(
            tenant_id=tenant.id, type="ticket", label="Ticket",
            statuses=["open"],
        )
        db.session.add(ed)
        db.session.flush()

        prefix = get_code_prefix(db.session, "ticket", tenant.id)
        assert prefix == "TI"

    def test_get_code_prefix_unknown_type(self, db, tenant):
        """get_code_prefix falls back to computing for unknown types."""
        # No definition exists for 'widget'
        prefix = get_code_prefix(db.session, "widget", tenant.id)
        assert prefix == "WI"


# =============================================================================
# _compute_entity_prefix (internal)
# =============================================================================

class TestComputeEntityPrefix:
    def test_builtin_lead_override(self):
        """_compute_entity_prefix returns PC for lead via built-in override."""
        result = _compute_entity_prefix("lead", [])
        assert result == "PC"

    def test_first_two_letters_default(self):
        """_compute_entity_prefix returns first 2 uppercase letters for unknown types."""
        result = _compute_entity_prefix("widget", ["lead"])
        assert result == "WI"
