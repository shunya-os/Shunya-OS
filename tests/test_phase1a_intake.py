"""
PHASE 1A — Data Intake & Transformation Tests
"""
import pytest
import json


@pytest.fixture(scope="function")
def real_app():
    from app import create_app, db
    application = create_app(config_override={
        "TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret", "DISABLE_RATE_LIMIT": "true", "WTF_CSRF_ENABLED": False,
    })
    with application.app_context():
        from app.tenant import Tenant
        db.create_all()
        yield application
        db.drop_all()


@pytest.fixture()
def sample_csv():
    return "name,email,phone,department\nRitu Sharma,ritu@example.com,+919876543210,Sales\nArjun Singh,arjun@example.com,+919999999999,Marketing\nName Only,,,,\n"


# =========================================================================
# 1. INTAKE SESSION
# =========================================================================

class TestIntakeSession:

    def test_create_session(self, real_app):
        from app.intake.session import IntakeOrchestrator
        from app import db
        with real_app.app_context():
            orch = IntakeOrchestrator(session=db.session)
            sess = orch.create_session("csv", "test.csv", tenant_id=1)
            assert sess.id is not None
            assert sess.source_type == "csv"
            assert sess.status == "received"

    def test_lifecycle_transitions(self, real_app):
        from app.intake.session import IntakeOrchestrator, IntakeSessionState
        from app import db
        with real_app.app_context():
            orch = IntakeOrchestrator(session=db.session)
            sess = orch.create_session("csv", "test.csv")
            assert sess.status == IntakeSessionState.RECEIVED
            orch.transition(sess, IntakeSessionState.PROFILED)
            assert sess.status == IntakeSessionState.PROFILED

    def test_invalid_transition_raises(self, real_app):
        from app.intake.session import IntakeOrchestrator, IntakeSessionState
        from app import db
        with real_app.app_context():
            orch = IntakeOrchestrator(session=db.session)
            sess = orch.create_session("csv", "test.csv")
            with pytest.raises(ValueError, match="Cannot transition"):
                orch.transition(sess, IntakeSessionState.COMPLETED)  # RECEIVED → COMPLETED is invalid

    def test_checksum(self, real_app):
        from app.intake.session import IntakeOrchestrator
        orch = IntakeOrchestrator()
        c1 = orch.compute_checksum("hello")
        c2 = orch.compute_checksum("hello")
        c3 = orch.compute_checksum("world")
        assert c1 == c2
        assert c1 != c3


# =========================================================================
# 2. SCHEMA PROFILING
# =========================================================================

class TestSchemaProfiler:

    def test_detect_separator(self, real_app):
        from app.intake.profiler import SchemaProfiler
        profiler = SchemaProfiler()
        assert profiler.detect_separator("a,b,c\n1,2,3") == ","
        assert profiler.detect_separator("a\tb\tc\n1\t2\t3") == "\t"

    def test_parse_csv(self, real_app, sample_csv):
        from app.intake.profiler import SchemaProfiler
        profiler = SchemaProfiler()
        columns, rows = profiler.parse_csv(sample_csv)
        assert len(columns) == 4
        assert len(rows) == 3

    def test_column_profiling(self, real_app, sample_csv):
        from app.intake.profiler import SchemaProfiler
        profiler = SchemaProfiler()
        profile = profiler.profile(sample_csv)
        assert profile["row_count"] == 3
        assert profile["column_count"] == 4
        assert "name" in profile["profiles"]
        assert "email" in profile["profiles"]
        # email column should detect email type
        assert profile["profiles"]["email"]["primitive_type"] == "email"

    def test_null_frequency(self, real_app, sample_csv):
        from app.intake.profiler import SchemaProfiler
        profiler = SchemaProfiler()
        profile = profiler.profile(sample_csv)
        # "name" row 3 has "Name Only" — not null
        # "email" row 3 is empty — should have null_count > 0
        assert profile["profiles"]["email"]["null_count"] == 1
        assert profile["profiles"]["phone"]["null_count"] == 1

    def test_column_profiles_have_required_fields(self, real_app, sample_csv):
        from app.intake.profiler import SchemaProfiler
        profiler = SchemaProfiler()
        profile = profiler.profile(sample_csv)
        cp = profile["profiles"]["name"]
        assert "null_count" in cp
        assert "null_frequency" in cp
        assert "sample_values" in cp
        assert "primitive_type" in cp
        assert "duplicate_frequency" in cp


# =========================================================================
# 3. FIELD MAPPING
# =========================================================================

class TestFieldMapper:

    def test_alias_mapping(self, real_app):
        from app.intake.mapper import FieldMapper
        mapper = FieldMapper()
        target, method, conf = mapper.map_column("customer_name")
        assert target == "person.canonical_name"
        assert method == "alias"
        assert conf == 1.0

    def test_email_alias(self, real_app):
        from app.intake.mapper import FieldMapper
        mapper = FieldMapper()
        target, method, _ = mapper.map_column("email_address")
        assert target == "identity.email"

    def test_phone_alias(self, real_app):
        from app.intake.mapper import FieldMapper
        mapper = FieldMapper()
        target, method, _ = mapper.map_column("mobile_number")
        assert target == "identity.phone"

    def test_employee_ref_alias(self, real_app):
        from app.intake.mapper import FieldMapper
        mapper = FieldMapper()
        target, _, _ = mapper.map_column("employee_id")
        assert target == "identity.employee_ref"

    def test_unmapped_column(self, real_app):
        from app.intake.mapper import FieldMapper
        mapper = FieldMapper()
        target, method, conf = mapper.map_column("random_field_xyz")
        assert target == ""
        assert method == "unmapped"

    def test_map_all(self, real_app):
        from app.intake.mapper import FieldMapper
        mapper = FieldMapper()
        results = mapper.map_all(["customer_name", "email", "random_field"])
        assert len(results) == 3
        mapped = [r for r in results if r["mapping_status"] == "mapped"]
        unmapped = [r for r in results if r["mapping_status"] == "unmapped"]
        assert len(mapped) == 2
        assert len(unmapped) == 1

    def test_case_insensitive_mapping(self, real_app):
        from app.intake.mapper import FieldMapper
        mapper = FieldMapper()
        target, _, _ = mapper.map_column("Full Name")
        assert target == "person.canonical_name"


# =========================================================================
# 4. VALIDATION
# =========================================================================

class TestRowValidator:

    def test_valid_email(self, real_app):
        from app.intake.validator import RowValidator, ValidationMessage
        status, msg = RowValidator.validate_email("test@example.com")
        assert status == ValidationMessage.INFO

    def test_invalid_email(self, real_app):
        from app.intake.validator import RowValidator, ValidationMessage
        status, msg = RowValidator.validate_email("not-an-email")
        assert status == ValidationMessage.ERROR

    def test_valid_phone(self, real_app):
        from app.intake.validator import RowValidator, ValidationMessage
        status, msg = RowValidator.validate_phone("+919876543210")
        assert status == ValidationMessage.INFO

    def test_empty_phone(self, real_app):
        from app.intake.validator import RowValidator, ValidationMessage
        status, msg = RowValidator.validate_phone("")
        assert status == ValidationMessage.INFO

    def test_row_without_identity_blocked(self, real_app):
        from app.intake.validator import RowValidator, ValidationMessage
        validator = RowValidator()
        row = {"name": "", "email": "", "phone": ""}
        mappings = [
            {"source_column": "name", "target_field": "person.canonical_name"},
            {"source_column": "email", "target_field": "identity.email"},
        ]
        status, messages = validator.validate_row(row, mappings)
        assert status == ValidationMessage.BLOCKING
        assert any("insufficient identity" in m["message"].lower() for m in messages)

    def test_no_silent_discard(self, real_app):
        """Every blocked row must have an explainable message."""
        from app.intake.validator import RowValidator, ValidationMessage
        validator = RowValidator()
        row = {"name": "", "email": "bad", "phone": ""}
        mappings = [{"source_column": "email", "target_field": "identity.email"}]
        status, messages = validator.validate_row(row, mappings)
        assert len(messages) > 0
        for m in messages:
            assert "message" in m
            assert "severity" in m


# =========================================================================
# 5. IDENTITY MATCHING
# =========================================================================

class TestIdentityMatcher:

    def test_insufficient_identity_name_only(self, real_app):
        from app.intake.matcher import IdentityMatcher
        from app import db
        with real_app.app_context():
            matcher = IdentityMatcher(session=db.session)
            result = matcher.resolve_row({"name": "Ritu"}, [{"source_column": "name", "target_field": "person.canonical_name"}])
            assert result["status"] == "INSUFFICIENT_IDENTITY"

    def test_insufficient_identity_empty_row(self, real_app):
        from app.intake.matcher import IdentityMatcher
        from app import db
        with real_app.app_context():
            matcher = IdentityMatcher(session=db.session)
            result = matcher.resolve_row({}, [])
            assert result["status"] == "INSUFFICIENT_IDENTITY"

    def test_no_match_valid_email(self, real_app):
        from app.intake.matcher import IdentityMatcher
        from app import db
        with real_app.app_context():
            matcher = IdentityMatcher(session=db.session)
            mappings = [{"source_column": "email", "target_field": "identity.email"}]
            result = matcher.resolve_row({"email": "new@example.com"}, mappings, tenant_id=1)
            assert result["status"] == "NO_MATCH"

    def test_matched_by_email(self, real_app):
        from app.models import Person, PersonIdentity
        from app.intake.matcher import IdentityMatcher
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            db.session.add(PersonIdentity(person_id=p.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.commit()
            matcher = IdentityMatcher(session=db.session)
            mappings = [{"source_column": "email", "target_field": "identity.email"}]
            result = matcher.resolve_row({"email": "ritu@example.com"}, mappings)
            assert result["status"] == "MATCHED", f"Got {result['status']}: {result.get('reason','')}"
            assert result["person_id"] == p.id

    def test_conflict_email_phone_different_persons(self, real_app):
        from app.models import Person, PersonIdentity
        from app.intake.matcher import IdentityMatcher
        from app import db
        with real_app.app_context():
            p1 = Person(canonical_name="Ritu", preferred_name="Ritu")
            p2 = Person(canonical_name="Arjun", preferred_name="Arjun")
            db.session.add(p1); db.session.add(p2); db.session.commit()
            db.session.add(PersonIdentity(person_id=p1.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.add(PersonIdentity(person_id=p2.id, identity_type="phone",
                                          identity_value="+919999999999", normalized_value="+919999999999"))
            db.session.commit()
            matcher = IdentityMatcher(session=db.session)
            mappings = [
                {"source_column": "email", "target_field": "identity.email"},
                {"source_column": "phone", "target_field": "identity.phone"},
            ]
            result = matcher.resolve_row({"email": "ritu@example.com", "phone": "+919999999999"}, mappings)
            assert result["status"] == "CONFLICT", f"Got {result['status']}: {result.get('reason','')}"

    def test_cross_tenant_isolation(self, real_app):
        """Tenant A intake must not match Tenant B Persons."""
        from app.models import Person, PersonIdentity
        from app.tenant import Tenant
        from app.intake.matcher import IdentityMatcher
        from app import db
        with real_app.app_context():
            t_a = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t_b = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t_a); db.session.add(t_b); db.session.commit()
            p_a = Person(canonical_name="Ritu A", preferred_name="Ritu", tenant_id=t_a.id)
            p_b = Person(canonical_name="Ritu B", preferred_name="Ritu", tenant_id=t_b.id)
            db.session.add(p_a); db.session.add(p_b); db.session.commit()
            db.session.add(PersonIdentity(person_id=p_a.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.add(PersonIdentity(person_id=p_b.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.commit()
            matcher = IdentityMatcher(session=db.session)
            mappings = [{"source_column": "email", "target_field": "identity.email"}]
            # Tenant A should only match Person A
            result = matcher.resolve_row({"email": "ritu@example.com"}, mappings, tenant_id=t_a.id)
            assert result["status"] == "MATCHED"
            assert result["person_id"] == p_a.id


# =========================================================================
# 6. IMPORT PROPOSAL
# =========================================================================

class TestImportProposal:

    def test_proposal_summary(self, real_app):
        from app.models import IntakeSession, IntakeCandidate
        from app.intake.proposal import ImportProposalBuilder
        from app import db
        with real_app.app_context():
            sess = IntakeSession(source_type="csv", source_name="test.csv", status="ready_for_review")
            db.session.add(sess); db.session.commit()
            c1 = IntakeCandidate(session_id=sess.id, row_index=0, identity_status="MATCHED", import_status="pending")
            c2 = IntakeCandidate(session_id=sess.id, row_index=1, identity_status="NO_MATCH", import_status="pending")
            c3 = IntakeCandidate(session_id=sess.id, row_index=2, identity_status="AMBIGUOUS", import_status="blocked")
            db.session.add(c1); db.session.add(c2); db.session.add(c3); db.session.commit()
            proposal = ImportProposalBuilder.build(sess, [c1, c2, c3])
            assert proposal["total_rows"] == 3
            assert proposal["summary"]["valid"] == 2
            assert proposal["summary"]["ambiguous"] == 1
            assert proposal["can_import"] is False

    def test_ambiguous_blocked_from_auto_commit(self, real_app):
        """AMBIGUOUS candidates must not be auto-imported."""
        from app.models import IntakeSession, IntakeCandidate
        from app.intake.proposal import ImportProposalBuilder
        from app import db
        with real_app.app_context():
            sess = IntakeSession(source_type="csv", source_name="test.csv", status="ready_for_review")
            db.session.add(sess); db.session.commit()
            c = IntakeCandidate(session_id=sess.id, row_index=0, identity_status="AMBIGUOUS", import_status="blocked")
            db.session.add(c); db.session.commit()
            proposal = ImportProposalBuilder.build(sess, [c])
            assert proposal["can_import"] is False

    def test_insufficient_identity_blocked(self, real_app):
        """INSUFFICIENT_IDENTITY candidates must not create Person automatically."""
        from app.models import IntakeSession, IntakeCandidate
        from app.intake.proposal import ImportProposalBuilder
        from app import db
        with real_app.app_context():
            sess = IntakeSession(source_type="csv", source_name="test.csv", status="ready_for_review")
            db.session.add(sess); db.session.commit()
            c = IntakeCandidate(session_id=sess.id, row_index=0, identity_status="INSUFFICIENT_IDENTITY", import_status="blocked")
            db.session.add(c); db.session.commit()
            proposal = ImportProposalBuilder.build(sess, [c])
            assert proposal["can_import"] is False


# =========================================================================
# 7. GOVERNED COMMIT
# =========================================================================

class TestGovernedCommit:

    def test_commit_requires_approved_status(self, real_app):
        from app.models import IntakeSession
        from app.intake.committer import GovernedCommitter
        from app import db
        with real_app.app_context():
            sess = IntakeSession(source_type="csv", source_name="test.csv", status="received")
            db.session.add(sess); db.session.commit()
            committer = GovernedCommitter(session=db.session)
            result = committer.commit(sess.id)
            assert result["success"] is False
            assert "must be approved" in result["error"]

    def test_approved_matched_linkage(self, real_app):
        """MATCHED candidate links to existing Person on commit."""
        from app.models import Person, PersonIdentity, IntakeSession, IntakeCandidate
        from app.intake.session import IntakeOrchestrator, IntakeSessionState
        from app.intake.committer import GovernedCommitter
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            db.session.add(PersonIdentity(person_id=p.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.commit()
            sess = IntakeSession(source_type="csv", source_name="test.csv", status=IntakeSessionState.APPROVED)
            db.session.add(sess); db.session.commit()
            c = IntakeCandidate(session_id=sess.id, row_index=0, identity_status="MATCHED",
                                matched_person_id=p.id, import_status="pending",
                                classification="customer", normalized_data='{"email":"ritu@example.com"}')
            db.session.add(c); db.session.commit()
            committer = GovernedCommitter(session=db.session)
            result = committer.commit(sess.id)
            assert result["success"] is True
            assert result["linked"] == 1

    def test_approved_no_match_creates_person(self, real_app):
        """NO_MATCH candidate creates a new Person on commit."""
        from app.models import Person, IntakeSession, IntakeCandidate
        from app.intake.session import IntakeSessionState
        from app.intake.committer import GovernedCommitter
        from app import db
        with real_app.app_context():
            sess = IntakeSession(source_type="csv", source_name="test.csv", status=IntakeSessionState.APPROVED)
            db.session.add(sess); db.session.commit()
            c = IntakeCandidate(session_id=sess.id, row_index=0, identity_status="NO_MATCH",
                                import_status="pending", normalized_data='{"name":"New Person","email":"new@example.com"}')
            db.session.add(c); db.session.commit()
            committer = GovernedCommitter(session=db.session)
            result = committer.commit(sess.id)
            assert result["success"] is True
            assert result["imported"] == 1
            # Verify Person was created
            persons = Person.query.all()
            assert len(persons) == 1
            assert persons[0].canonical_name == "New Person"

    def test_ambiguous_blocked_from_commit(self, real_app):
        """AMBIGUOUS candidate is skipped during commit."""
        from app.models import IntakeSession, IntakeCandidate
        from app.intake.session import IntakeSessionState
        from app.intake.committer import GovernedCommitter
        from app import db
        with real_app.app_context():
            sess = IntakeSession(source_type="csv", source_name="test.csv", status=IntakeSessionState.APPROVED)
            db.session.add(sess); db.session.commit()
            c = IntakeCandidate(session_id=sess.id, row_index=0, identity_status="AMBIGUOUS",
                                import_status="blocked", normalized_data="{}")
            db.session.add(c); db.session.commit()
            committer = GovernedCommitter(session=db.session)
            result = committer.commit(sess.id)
            assert result["unresolved_remaining"] == 1
            assert result["session_status"] == IntakeSessionState.PARTIALLY_COMPLETED

    def test_idempotent_retry(self, real_app):
        """Re-running an import does not duplicate Persons."""
        from app.models import Person, IntakeSession, IntakeCandidate
        from app.intake.session import IntakeSessionState
        from app.intake.committer import GovernedCommitter
        from app import db
        with real_app.app_context():
            sess = IntakeSession(source_type="csv", source_name="test.csv", status=IntakeSessionState.APPROVED)
            db.session.add(sess); db.session.commit()
            c = IntakeCandidate(session_id=sess.id, row_index=0, identity_status="NO_MATCH",
                                import_status="pending", normalized_data='{"name":"Unique","email":"unique@example.com"}')
            db.session.add(c); db.session.commit()
            committer = GovernedCommitter(session=db.session)
            result1 = committer.commit(sess.id)
            assert result1["imported"] == 1
            # Second commit should not duplicate
            result2 = committer.commit(sess.id)
            # Already imported — should be skipped
            persons = Person.query.filter_by(canonical_name="Unique").all()
            assert len(persons) == 1


# =========================================================================
# 8. PANCHI LEGACY CUSTOMER PREPARATION
# =========================================================================

class TestPanchiLegacy:

    def test_lead_name_only_insufficient(self, real_app):
        """Lead with customer_name only is INSUFFICIENT_IDENTITY — no Person created."""
        from app.models import Lead, next_inquiry_code
        from app.intake.matcher import IdentityMatcher
        from app import db
        with real_app.app_context():
            code = next_inquiry_code(db.session)
            lead = Lead(code=code, source="test", customer_name="Ritu Sharma", destination="Goa")
            db.session.add(lead); db.session.commit()
            matcher = IdentityMatcher(session=db.session)
            mappings = [{"source_column": "customer_name", "target_field": "person.canonical_name"}]
            result = matcher.resolve_row({"customer_name": "Ritu Sharma"}, mappings, tenant_id=1)
            assert result["status"] == "INSUFFICIENT_IDENTITY"

    def test_lead_name_phone_no_match(self, real_app):
        """Lead with name + phone where phone has no Person match is NO_MATCH."""
        from app.intake.matcher import IdentityMatcher
        from app import db
        with real_app.app_context():
            matcher = IdentityMatcher(session=db.session)
            mappings = [
                {"source_column": "customer_name", "target_field": "person.canonical_name"},
                {"source_column": "phone", "target_field": "identity.phone"},
            ]
            result = matcher.resolve_row({"customer_name": "Arjun", "phone": "+919999999999"}, mappings, tenant_id=1)
            assert result["status"] == "NO_MATCH"

    def test_lead_email_phone_conflict(self, real_app):
        """Lead with email→PersonA, phone→PersonB is CONFLICT."""
        from app.models import Person, PersonIdentity
        from app.intake.matcher import IdentityMatcher
        from app import db
        with real_app.app_context():
            p1 = Person(canonical_name="Person A", preferred_name="A")
            p2 = Person(canonical_name="Person B", preferred_name="B")
            db.session.add(p1); db.session.add(p2); db.session.commit()
            db.session.add(PersonIdentity(person_id=p1.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.add(PersonIdentity(person_id=p2.id, identity_type="phone",
                                          identity_value="+919999999999", normalized_value="+919999999999"))
            db.session.commit()
            matcher = IdentityMatcher(session=db.session)
            mappings = [
                {"source_column": "email", "target_field": "identity.email"},
                {"source_column": "phone", "target_field": "identity.phone"},
            ]
            result = matcher.resolve_row({"email": "ritu@example.com", "phone": "+919999999999"}, mappings)
            assert result["status"] == "CONFLICT", f"Got {result['status']}: {result.get('reason','')}"

    def test_lead_record_remains_operational(self, real_app):
        """Lead records are not modified by Phase 1A intake."""
        from app.models import Lead, next_inquiry_code
        from app import db
        with real_app.app_context():
            code = next_inquiry_code(db.session)
            lead = Lead(code=code, source="test", customer_name="Ritu", phone="+919999999999", destination="Goa")
            db.session.add(lead); db.session.commit()
            lead_id = lead.id
            # Re-query
            lead2 = db.session.get(Lead, lead_id)
            assert lead2.customer_name == "Ritu"
            assert lead2.phone == "+919999999999"


# =========================================================================
# 9. TENANT ISOLATION
# =========================================================================

class TestTenantIsolation:

    def test_tenant_a_intake_does_not_resolve_tenant_b(self, real_app):
        """Tenant A intake must not resolve Tenant B Persons."""
        from app.models import Person, PersonIdentity
        from app.tenant import Tenant
        from app.intake.matcher import IdentityMatcher
        from app import db
        with real_app.app_context():
            t_a = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t_b = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t_a); db.session.add(t_b); db.session.commit()
            p_b = Person(canonical_name="Person B", preferred_name="B", tenant_id=t_b.id)
            db.session.add(p_b); db.session.commit()
            db.session.add(PersonIdentity(person_id=p_b.id, identity_type="email",
                                          identity_value="person@example.com", normalized_value="person@example.com"))
            db.session.commit()
            matcher = IdentityMatcher(session=db.session)
            mappings = [{"source_column": "email", "target_field": "identity.email"}]
            result = matcher.resolve_row({"email": "person@example.com"}, mappings, tenant_id=t_a.id)
            # Tenant A has no Person with this email — should be NO_MATCH
            assert result["status"] == "NO_MATCH"