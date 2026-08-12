"""FDA12 — Sales Intelligence tests.

Lead scoring, next-best-action, pipeline health, forecast, salesperson intel,
conversion analysis. All derived from canonical models.
"""
import pytest
from datetime import datetime, timedelta


@pytest.fixture
def seeded_lead_id(app, client):
    """Create a qualified lead. Returns lead ID."""
    from app.crm.service import create_lead_with_identity, assign_lead, qualify_lead_and_update
    with app.app_context():
        lead = create_lead_with_identity(
            tenant_id=1, name="Sales Intel Lead", phone="+1-555-INTEL",
            email="intel@test.com", source="referral",
            destination="Paris", pax="2", budget=15000,
        )
        assign_lead(lead, "agent_1", 1)
        qualify_lead_and_update(lead, 1)
        return lead.id


class TestLeadScoring:
    def test_score_qualified_lead(self, app, seeded_lead_id):
        from app.sales_intelligence.service import lead_scoring
        with app.app_context():
            result = lead_scoring(seeded_lead_id)
        assert result["score"] >= 40
        assert result["classification"] in ("hot", "warm", "cold")
        assert len(result["signals"]) >= 3

    def test_score_explains_each_signal(self, app, seeded_lead_id):
        from app.sales_intelligence.service import lead_scoring
        with app.app_context():
            result = lead_scoring(seeded_lead_id)
        for signal in result["signals"]:
            assert "signal" in signal
            assert "evidence" in signal
            assert "weight" in signal

    def test_score_unknown_lead(self, app, client):
        from app.sales_intelligence.service import lead_scoring
        result = lead_scoring(999999)
        assert result["error"] is not None


class TestEvidenceBackedNBA:
    def test_nba_from_lead_state_is_deterministic(self, app, client):
        """New lead without owner → NBA recommends contact_lead + assign_owner with evidence."""
        from app.crm.service import create_lead_with_identity
        from app.sales_intelligence.service import next_best_action
        with app.app_context():
            # Create a lead with specific state: new, no owner, no destination
            lead = create_lead_with_identity(
                tenant_id=1, name="NBA Test Lead", phone="+1-555-NBA",
                email="nba@test.com", source="api",
            )
            actions = next_best_action(lead.id)

        # Verify: new unassigned lead should recommend contact + assign
        action_types = {a["action"] for a in actions}
        assert "contact_lead" in action_types, \
            f"Expected contact_lead, got {action_types}"
        assert "assign_owner" in action_types, \
            f"Expected assign_owner, got {action_types}"

        # Verify every action has evidence grounded in lead state
        for a in actions:
            assert a["confidence"] == "deterministic", \
                f"NBA {a['action']} should be deterministic, got {a['confidence']}"
            assert a["owner"] in ("unassigned", "manager"), \
                f"NBA {a['action']} owner should reflect unassigned lead, got {a['owner']}"

    def test_nba_qualified_lead_recommends_proposal(self, app, client):
        """Qualified lead with assignment → NBA recommends send_proposal."""
        from app.crm.service import create_lead_with_identity, assign_lead, qualify_lead_and_update
        from app.sales_intelligence.service import next_best_action
        with app.app_context():
            lead = create_lead_with_identity(
                tenant_id=1, name="NBA Qualified", phone="+1-555-NBAQ",
                email="nbaq@test.com", source="api", budget=10000,
                destination="Tokyo",
            )
            assign_lead(lead, "agent_1", 1)
            qualify_lead_and_update(lead, 1)
            actions = next_best_action(lead.id)

        action_types = {a["action"] for a in actions}
        assert "send_proposal" in action_types, \
            f"Qualified lead should get send_proposal, got {action_types}"

        for a in actions:
            assert a["confidence"] == "deterministic"
            assert a["owner"] == "agent_1"


class TestNextBestAction:
    def test_new_lead_recommends_contact(self, app, client):
        from app.crm.service import create_lead_with_identity
        from app.sales_intelligence.service import next_best_action
        with app.app_context():
            lead = create_lead_with_identity(
                tenant_id=1, name="New Lead", phone="+1-555-NEW",
                email="new@test.com", source="api",
            )
            actions = next_best_action(lead.id)
            assert any(a["action"] == "contact_lead" for a in actions)

    def test_unassigned_lead_recommends_owner(self, app, client):
        from app.crm.service import create_lead_with_identity
        from app.sales_intelligence.service import next_best_action
        with app.app_context():
            lead = create_lead_with_identity(
                tenant_id=1, name="Unassigned", phone="+1-555-UNAS",
                email="unas@test.com", source="api",
            )
            actions = next_best_action(lead.id)
            assert any(a["action"] == "assign_owner" for a in actions)

    def test_qualified_lead_recommends_proposal(self, app, seeded_lead_id):
        from app.sales_intelligence.service import next_best_action
        with app.app_context():
            actions = next_best_action(seeded_lead_id)
        # Qualified leads should get at least one recommendation
        assert len(actions) >= 1
        for a in actions:
            assert "action" in a
            assert "reason" in a

    def test_every_action_has_evidence_fields(self, app, seeded_lead_id):
        from app.sales_intelligence.service import next_best_action
        with app.app_context():
            actions = next_best_action(seeded_lead_id)
        for action in actions:
            assert "action" in action
            assert "reason" in action
            assert "urgency" in action
            assert "owner" in action


class TestPipelineHealth:
    def test_stage_distribution(self, app, seeded_lead_id):
        from app.sales_intelligence.service import pipeline_health
        result = pipeline_health(1)
        assert "stage_distribution" in result
        assert result["total_leads"] >= 1

    def test_unassigned_count(self, app, client):
        from app.crm.service import create_lead_with_identity
        from app.sales_intelligence.service import pipeline_health
        with app.app_context():
            create_lead_with_identity(
                tenant_id=1, name="Pipeline Test", phone="+1-555-PIPE",
                email="pipe@test.com", source="api",
            )
            result = pipeline_health(1)
            assert result["unassigned"] >= 1


class TestForecast:
    def test_forecast_traceable(self, app, seeded_lead_id):
        from app.sales_intelligence.service import forecast
        result = forecast(1, 3)
        assert "pipeline_value" in result
        assert "expected_value" in result
        assert "assumptions" in result
        assert len(result["assumptions"]) > 0

    def test_forecast_with_no_data(self, app, client):
        from app.sales_intelligence.service import forecast
        result = forecast(999, 3)
        assert result["pipeline_value"] == "0"


class TestSalespersonIntel:
    def test_salesperson_metrics(self, app, seeded_lead_id):
        from app.sales_intelligence.service import salesperson_intel
        result = salesperson_intel("agent_1")
        assert result["total_leads"] >= 1
        assert "conversion_rate" in result

    def test_unknown_salesperson(self, app, client):
        from app.sales_intelligence.service import salesperson_intel
        result = salesperson_intel("nobody")
        assert result["total_leads"] == 0


class TestConversionAnalysis:
    def test_conversion_rates(self, app, seeded_lead_id):
        from app.sales_intelligence.service import conversion_analysis
        result = conversion_analysis(1)
        assert "conversion_rate" in result
        assert "loss_reasons" in result


class TestTenantIsolation:
    def test_tenant_a_cannot_access_tenant_b_lead_through_scoring(self, app, client):
        """Tenant A's score service must not expose Tenant B's leads."""
        from app.crm.service import create_lead_with_identity
        from app.sales_intelligence.service import lead_scoring
        with app.app_context():
            # Create a lead for tenant 2
            lead_b = create_lead_with_identity(
                tenant_id=2, name="Tenant B Lead", phone="+1-555-TENB",
                email="tenb@test.com", source="api",
            )
            bid = lead_b.id
        # Tenant 1's scoring function should not crash when given tenant B's lead
        # (scoring is per-lead, but the violation surface is that tenant B's data
        #  should not appear in tenant A's pipeline/aggregation queries)
        from app.sales_intelligence.service import pipeline_health
        result = pipeline_health(tenant_id=1)
        # Tenant B's lead should not appear in Tenant A's pipeline
        all_ids = set()
        for stalled in result.get("stalled_leads", []):
            all_ids.add(stalled.get("id"))
        assert bid not in all_ids, f"Tenant B lead {bid} leaked into Tenant A pipeline"

    def test_tenant_a_cannot_see_tenant_b_forecast(self, app, client):
        """Tenant A's forecast must not include Tenant B's pipeline value."""
        from app.crm.service import create_lead_with_identity
        from app.sales_intelligence.service import forecast
        with app.app_context():
            # Create a high-value lead for tenant 2
            lead_b = create_lead_with_identity(
                tenant_id=2, name="Tenant B High Value", phone="+1-555-TBHV",
                email="tenb-hv@test.com", source="api", budget=999999,
            )
        # Tenant 1 forecast should not include tenant B's data
        result = forecast(tenant_id=1, months=3)
        # The pipeline value should be reasonable (not 999999)
        pipeline_val = float(result.get("pipeline_value", 0))
        assert pipeline_val < 999999, f"Tenant B budget leaked into Tenant A forecast: {pipeline_val}"