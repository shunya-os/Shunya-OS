"""G5 — Universal Marketing, Growth, Attribution & Learning Engine tests.

Tests:
1. Campaign event lifecycle
2. Multi-touch interaction recording
3. Canonical attribution with evidence/confidence
4. G4 → G5 integration (opportunity+outcome linkage)
5. Revenue/outcome attribution
6. Growth learning/intelligence
7. Multi-touch attribution for identity
8. Tenant/security isolation
9. Full end-to-end campaign → outcome path
"""

import pytest
from datetime import datetime, timezone


class TestCampaignEvents:
    """Campaign lifecycle event stream — immutable, append-only."""

    def test_record_campaign_created_event(self, app, client):
        from app.g5.service import record_campaign_event
        from app.marketing_os.service import create_campaign
        with app.app_context():
            camp = create_campaign(name="Event Test", tenant_id=1)
            event = record_campaign_event(
                campaign_id=camp.id,
                tenant_id=1,
                event_type="campaign_created",
                description="Campaign created for testing",
                new_state="draft",
                trigger_source="user",
            )
            assert event["campaign_id"] == camp.id
            assert event["event_type"] == "campaign_created"
            assert event["new_state"] == "draft"

    def test_get_campaign_events(self, app, client):
        from app.g5.service import record_campaign_event, get_campaign_events
        from app.marketing_os.service import create_campaign
        with app.app_context():
            camp = create_campaign(name="Events List", tenant_id=1)
            record_campaign_event(camp.id, 1, "campaign_created", new_state="draft")
            record_campaign_event(camp.id, 1, "campaign_activated", new_state="active")
            events = get_campaign_events(camp.id, 1)
            assert len(events) >= 2
            assert events[0]["campaign_id"] == camp.id

    def test_campaign_event_type_filter(self, app, client):
        from app.g5.service import record_campaign_event, get_campaign_events
        from app.marketing_os.service import create_campaign
        with app.app_context():
            camp = create_campaign(name="Event Filter", tenant_id=1)
            record_campaign_event(camp.id, 1, "campaign_created", new_state="draft")
            record_campaign_event(camp.id, 1, "campaign_activated", new_state="active")
            created_events = get_campaign_events(camp.id, 1, event_type="campaign_created")
            assert all(e["event_type"] == "campaign_created" for e in created_events)


class TestTouchpointInteractions:
    """Multi-touch interaction recording — multiple interactions per identity."""

    def test_record_interaction_minimal(self, app, client):
        from app.g5.service import record_interaction
        with app.app_context():
            interaction = record_interaction(
                tenant_id=1,
                interaction_type="website_visit",
                identity_ref="test@example.com",
            )
            assert interaction["tenant_id"] == 1
            assert interaction["interaction_type"] == "website_visit"
            assert interaction["identity_ref"] == "test@example.com"

    def test_record_interaction_full(self, app, client):
        from app.g5.service import record_interaction
        with app.app_context():
            interaction = record_interaction(
                tenant_id=1,
                interaction_type="advertisement",
                campaign_id=42,
                identity_ref="person_1",
                person_name="Test Person",
                person_email="test@example.com",
                source="facebook",
                channel="social",
                referrer="facebook.com/ad",
                utm_source="facebook",
                utm_medium="cpc",
                utm_campaign="summer_sale",
                utm_term="travel",
                utm_content="banner_1",
                session_ref="sess_abc",
                tracking_id="track_123",
                description="Clicked on summer sale ad",
                engagement_duration_seconds=120,
                engagement_depth=3,
                content_ref="ad_creative_1",
                evidence={"browser": "Chrome", "ip": "1.2.3.4"},
                source_confidence=80,
            )
            assert interaction["campaign_id"] == 42
            assert interaction["source"] == "facebook"
            assert interaction["utm_campaign"] == "summer_sale"
            assert interaction["engagement_duration_seconds"] == 120

    def test_multiple_interactions_per_identity(self, app, client):
        from app.g5.service import record_interaction, get_interactions
        with app.app_context():
            for i in range(5):
                record_interaction(
                    tenant_id=1,
                    interaction_type="website_visit",
                    identity_ref="multi@test.com",
                    campaign_id=100,
                    description=f"Visit {i}",
                )
            interactions = get_interactions(
                tenant_id=1, identity_ref="multi@test.com"
            )
            assert len(interactions) >= 5

    def test_interaction_tenant_isolation(self, app, client):
        from app.g5.service import record_interaction, get_interactions
        with app.app_context():
            record_interaction(tenant_id=1, identity_ref="tenant_iso@a.com")
            t2 = get_interactions(tenant_id=2, identity_ref="tenant_iso@a.com")
            assert len(t2) == 0


class TestCanonicalAttribution:
    """Persistent attribution preserving evidence and uncertainty."""

    def test_create_attribution_minimal(self, app, client):
        from app.g5.service import create_attribution
        with app.app_context():
            attr = create_attribution(
                tenant_id=1,
                target_type="interaction",
                target_id=1,
                source="facebook",
            )
            assert attr["target_type"] == "interaction"
            assert attr["attribution_state"] == "unknown"
            assert attr["confidence"] == 50

    def test_attribution_with_evidence(self, app, client):
        from app.g5.service import create_attribution
        with app.app_context():
            attr = create_attribution(
                tenant_id=1,
                target_type="opportunity",
                target_id=10,
                campaign_id=5,
                source="google_ads",
                channel="search",
                attribution_state="strongly_attributable",
                confidence=85,
                evidence_summary="Lead converted via tracked UTM parameters",
                is_first_known=True,
                evidence={"utm_source": "google", "conversion_id": "conv_123"},
            )
            assert attr["attribution_state"] == "strongly_attributable"
            assert attr["confidence"] == 85
            assert attr["is_first_known"] is True
            assert attr["evidence"]["utm_source"] == "google"

    def test_attribution_preserves_unknown(self, app, client):
        from app.g5.service import create_attribution
        with app.app_context():
            attr = create_attribution(
                tenant_id=1,
                target_type="relationship",
                target_id=99,
                source="unknown",
                attribution_state="unknown",
            )
            assert attr["attribution_state"] == "unknown"
            assert attr["confidence"] == 50

    def test_attribution_does_not_overwrite(self, app, client):
        from app.g5.service import create_attribution, get_attributions
        with app.app_context():
            a1 = create_attribution(
                tenant_id=1, target_type="interaction", target_id=42,
                attribution_state="unknown",
            )
            a2 = create_attribution(
                tenant_id=1, target_type="interaction", target_id=42,
                attribution_state="strongly_attributable", confidence=90,
            )
            # Both exist — no silent overwrite
            attrs = get_attributions(tenant_id=1, target_type="interaction", target_id=42)
            assert len(attrs) >= 2
            assert any(a["id"] == a1["id"] for a in attrs)
            assert any(a["id"] == a2["id"] for a in attrs)

    def test_attribution_revenue_link(self, app, client):
        from app.g5.service import create_attribution
        with app.app_context():
            attr = create_attribution(
                tenant_id=1,
                target_type="proposal",
                target_id=5,
                campaign_id=3,
                revenue_amount=50000.00,
                is_revenue_outcome=True,
                attribution_state="directly_linked",
                confidence=95,
            )
            assert attr["revenue_amount"] == 50000.00
            assert attr["is_revenue_outcome"] is True


class TestG4G5Integration:
    """G4 → G5 integration: campaign → opportunity → outcome path."""

    def test_attribute_opportunity_to_campaign(self, app, client):
        from app.g5.service import attribute_opportunity_to_campaign
        from app.marketing_os.service import create_campaign
        from app.commercial.models import CommercialOpportunity
        with app.app_context():
            camp = create_campaign(name="G4 Bridge Test", tenant_id=1)
            # No need to create a real opportunity — test with a non-existent one
            # to verify the not-found path
            result = attribute_opportunity_to_campaign(
                opportunity_id=99999,
                campaign_id=camp.id,
                tenant_id=1,
            )
            assert result is None, "Should return None for non-existent opportunity"

    def test_full_g4_g5_bridge(self, app, client):
        """Prove: Campaign → Attribution → Opportunity → Outcome."""
        from app.g5.service import (
            create_attribution, get_attribution_chain,
            record_interaction,
        )
        from app.marketing_os.service import create_campaign
        from app.commercial.service import create_opportunity
        with app.app_context():
            camp = create_campaign(name="Full Bridge", tenant_id=1)
            cid = camp.id

            # 1. Record interaction (touchpoint)
            interaction = record_interaction(
                tenant_id=1, campaign_id=cid,
                interaction_type="website_visit",
                identity_ref="bridge@test.com",
                source="organic_search",
            )

            # 2. Create attribution linking interaction to campaign
            attr = create_attribution(
                tenant_id=1, campaign_id=cid,
                target_type="interaction",
                target_id=interaction["id"],
                source="organic_search",
                attribution_state="strongly_attributable",
                confidence=75,
                interaction_id=interaction["id"],
            )

            # 3. Create a G4 opportunity with campaign_id link
            from app.commercial.service import create_opportunity as create_opp
            org_id = 1

            opp = create_opp(
                organization_id=org_id,
                title="Campaign Generated Opportunity",
                campaign_id=cid,
                source="campaign",
                created_by="g5_test",
            )

            # 4. Attribute the opportunity to the campaign
            opp_attr = create_attribution(
                tenant_id=1, campaign_id=cid,
                target_type="opportunity",
                target_id=opp.id,
                source="campaign_conversion",
                attribution_state="directly_linked",
                confidence=85,
                opportunity_id=opp.id,
                target_description=f"Opportunity: {opp.title}",
            )

            # 5. Verify attribution chain
            chain = get_attribution_chain(cid, 1)
            assert "error" not in chain
            assert chain["campaign"]["id"] == cid
            assert chain["total_attributions"] >= 2
            assert chain["total_interactions"] >= 1


class TestRevenueOutcomeLinkage:
    """Campaign → commercial outcome → revenue attribution."""

    def test_revenue_outcome_attribution(self, app, client):
        from app.g5.service import (
            create_attribution, get_attribution_chain,
        )
        from app.marketing_os.service import create_campaign
        with app.app_context():
            camp = create_campaign(name="Revenue Test", tenant_id=1, budget=1000)
            cid = camp.id

            # Create revenue attribution (directly)
            rev_attr = create_attribution(
                tenant_id=1, campaign_id=cid,
                target_type="proposal",
                target_id=1,
                revenue_amount=75000.00,
                is_revenue_outcome=True,
                attribution_state="directly_linked",
                confidence=95,
                proposal_id=1,
                target_description="Accepted Proposal #1",
            )

            # Verify chain shows revenue
            chain = get_attribution_chain(cid, 1)
            assert "error" not in chain
            assert chain["total_revenue"] >= 75000

    def test_non_revenue_outcome(self, app, client):
        """Non-revenue outcomes (e.g., awareness) should still work."""
        from app.g5.service import create_attribution
        with app.app_context():
            attr = create_attribution(
                tenant_id=1,
                target_type="interaction",
                target_id=77,
                is_revenue_outcome=False,
                attribution_state="correlated",
            )
            assert attr["is_revenue_outcome"] is False


class TestGrowthLearning:
    """Learning/insight grounded in actual outcomes."""

    def test_create_learning(self, app, client):
        from app.g5.service import create_learning, get_learnings
        with app.app_context():
            learning = create_learning(
                tenant_id=1,
                category="campaign_performance",
                title="Social media driving highest engagement",
                observation="Facebook ads have 3x better CTR than display",
                significance="significant",
                evidence_summary="Based on 500+ tracked interactions",
                confidence=78,
                recommendation="Increase Facebook budget by 20%",
                recommendation_confidence=72,
                recommendation_action="Increase social budget",
                is_actionable=True,
            )
            assert learning["title"] == "Social media driving highest engagement"
            assert learning["significance"] == "significant"
            assert learning["is_actionable"] is True

            learnings = get_learnings(tenant_id=1)
            assert len(learnings) >= 1
            return learning

    def test_insufficient_evidence_learning(self, app, client):
        from app.g5.service import create_learning
        with app.app_context():
            learning = create_learning(
                tenant_id=1,
                category="insufficient_evidence",
                title="Not enough data to assess",
                observation="Only 3 interactions recorded, need 50 minimum",
                confidence=10,
                is_actionable=False,
            )
            assert learning["confidence"] == 10
            assert learning["category"] == "insufficient_evidence"

    def test_learning_with_external_data(self, app, client):
        from app.g5.service import create_learning
        with app.app_context():
            learning = create_learning(
                tenant_id=1,
                category="external_information",
                title="Market trend: travel demand rising",
                data_source="external_current",
                external_source="news_api",
                external_context="Q3 travel demand up 15% YoY",
                confidence=60,
            )
            assert learning["data_source"] == "external_current"
            assert learning["external_source"] == "news_api"


class TestCampaignIntelligence:
    """Grounded intelligence — what is working, what is not."""

    def test_campaign_intelligence_empty(self, app, client):
        from app.g5.service import campaign_intelligence
        with app.app_context():
            intel = campaign_intelligence(999999, 1)
            assert "error" in intel

    def test_campaign_intelligence_with_data(self, app, client):
        from app.g5.service import (
            campaign_intelligence, record_interaction, create_attribution,
            create_learning, get_campaign_events,
        )
        from app.marketing_os.service import create_campaign
        with app.app_context():
            camp = create_campaign(name="Intel Test", tenant_id=1, budget=5000)
            cid = camp.id

            # Record some interactions
            record_interaction(tenant_id=1, campaign_id=cid,
                               interaction_type="advertisement",
                               source="facebook")
            record_interaction(tenant_id=1, campaign_id=cid,
                               interaction_type="website_visit",
                               source="google")

            # Create revenue attribution
            create_attribution(tenant_id=1, campaign_id=cid,
                               target_type="proposal", target_id=1,
                               revenue_amount=50000, is_revenue_outcome=True)

            # Create learning
            create_learning(tenant_id=1, campaign_id=cid,
                            category="channel_effectiveness",
                            title="Facebook drives more visits",
                            significance="significant",
                            is_actionable=True,
                            recommendation="Increase social spend",
                            recommendation_action="Increase social budget")

            intel = campaign_intelligence(cid, 1)
            assert "error" not in intel
            assert intel["campaign"]["id"] == cid
            assert intel["assessment"]["has_response"] is True
            assert intel["assessment"]["has_conversion"] is True
            assert intel["assessment"]["has_learning"] is True
            assert intel["assessment"]["total_interactions"] >= 2
            assert float(intel["assessment"]["total_revenue"]) >= 50000
            assert len(intel["actionable_recommendations"]) >= 1


class TestMultiTouchAttribution:
    """Multi-touch attribution — preserves multiple touchpoints over time."""

    def test_multi_touch_for_identity(self, app, client):
        from app.g5.service import (
            record_interaction, multi_touch_attribution_for_identity,
        )
        with app.app_context():
            id_ref = "multi_touch@test.com"

            # Record touchpoints over time
            record_interaction(tenant_id=1, identity_ref=id_ref,
                               interaction_type="first_discovery",
                               source="facebook_ad", campaign_id=1)
            record_interaction(tenant_id=1, identity_ref=id_ref,
                               interaction_type="email_interaction",
                               source="email", campaign_id=1)
            record_interaction(tenant_id=1, identity_ref=id_ref,
                               interaction_type="website_visit",
                               source="direct", campaign_id=2)

            result = multi_touch_attribution_for_identity(id_ref, 1)
            assert result["total_touchpoints"] >= 3
            assert result["identity_ref"] == id_ref
            assert len(result["campaigns_touched"]) >= 1
            assert result["first_touch"] is not None
            assert result["last_touch"] is not None

    def test_multi_touch_no_data(self, app, client):
        from app.g5.service import multi_touch_attribution_for_identity
        with app.app_context():
            result = multi_touch_attribution_for_identity("nonexistent@test.com", 1)
            assert result["total_touchpoints"] == 0


class TestTenantSecurity:
    """All G5 data must be tenant-safe."""

    def test_interaction_tenant_isolation(self, app, client):
        from app.g5.service import record_interaction, get_interactions
        with app.app_context():
            record_interaction(tenant_id=1, identity_ref="tenant_a@test.com")
            record_interaction(tenant_id=2, identity_ref="tenant_b@test.com")
            a = get_interactions(tenant_id=1)
            b = get_interactions(tenant_id=2)
            assert all(i["tenant_id"] == 1 for i in a)
            assert all(i["tenant_id"] == 2 for i in b)

    def test_attribution_tenant_isolation(self, app, client):
        from app.g5.service import create_attribution, get_attributions
        with app.app_context():
            create_attribution(tenant_id=1, target_type="interaction", target_id=1)
            create_attribution(tenant_id=2, target_type="interaction", target_id=2)
            a1 = get_attributions(tenant_id=1)
            a2 = get_attributions(tenant_id=2)
            assert all(a["tenant_id"] == 1 for a in a1)
            assert all(a["tenant_id"] == 2 for a in a2)

    def test_learning_tenant_isolation(self, app, client):
        from app.g5.service import create_learning, get_learnings
        with app.app_context():
            create_learning(tenant_id=1, title="Tenant A insight")
            create_learning(tenant_id=2, title="Tenant B insight")
            l1 = get_learnings(tenant_id=1)
            l2 = get_learnings(tenant_id=2)
            assert all(l["tenant_id"] == 1 for l in l1)
            assert all(l["tenant_id"] == 2 for l in l2)

    def test_campaign_events_tenant_isolation(self, app, client):
        from app.g5.service import record_campaign_event, get_campaign_events
        with app.app_context():
            record_campaign_event(campaign_id=1, tenant_id=1, event_type="campaign_created")
            record_campaign_event(campaign_id=2, tenant_id=2, event_type="campaign_created")
            e1 = get_campaign_events(campaign_id=1, tenant_id=1)
            e2 = get_campaign_events(campaign_id=2, tenant_id=2)
            assert all(e["tenant_id"] == 1 for e in e1)
            assert all(e["tenant_id"] == 2 for e in e2)


class TestEndToEndPath:
    """Complete campaign → tracked response → relationship/lead → opportunity → proposal/action → acceptance → outcome → revenue → attribution → learning."""

    def test_full_g5_g4_end_to_end(self, app, client):
        from app.g5.service import (
            record_interaction, create_attribution, create_learning,
            get_attribution_chain,
        )
        from app.marketing_os.service import create_campaign, capture_lead
        from app.commercial.service import create_opportunity, create_proposal
        from app.commercial.models import CommercialOpportunity
        from app.models import Organization
        from app.crm.service import convert_to_customer
        from app.models import Lead
        from app import db

        with app.app_context():
            # 1. Create campaign
            camp = create_campaign(
                name="E2E G5-G4 Bridge",
                tenant_id=1,
                objective="leads",
                budget=10000,
                utm_source="google",
                utm_campaign="e2e_test",
                utm_medium="cpc",
            )
            cid = camp.id

            # 2. Record campaign event
            from app.g5.service import record_campaign_event
            record_campaign_event(cid, 1, "campaign_created",
                                  new_state="draft")
            record_campaign_event(cid, 1, "campaign_activated",
                                  new_state="active")

            # 3. Capture tracked response (lead from campaign)
            lead_result = capture_lead(
                tenant_id=1,
                name="E2E Lead",
                phone="+1-555-E2E",
                email="e2e@test.com",
                campaign_id=cid,
                utm_source="google",
                utm_campaign="e2e_test",
            )
            lead_id = lead_result["lead_id"]

            # 4. Record interaction
            interaction = record_interaction(
                tenant_id=1, campaign_id=cid,
                interaction_type="email_interaction",
                identity_ref="e2e@test.com",
                person_name="E2E Lead",
                person_email="e2e@test.com",
                utm_source="google",
                utm_campaign="e2e_test",
                source="google_ads",
            )

            # 5. Create attribution for the interaction
            create_attribution(
                tenant_id=1, campaign_id=cid,
                target_type="interaction",
                target_id=interaction["id"],
                source="google_ads",
                channel="cpc",
                utm_source="google",
                utm_campaign="e2e_test",
                utm_medium="cpc",
                attribution_state="directly_linked",
                confidence=90,
                identity_ref="e2e@test.com",
                is_first_known=True,
            )

            # 6. Create G4 Commercial Opportunity (via the campaign)
            org_id = 1

            opp = create_opportunity(
                organization_id=org_id,
                title="E2E Commercial Opportunity",
                campaign_id=cid,
                source="campaign",
                created_by="g5_test",
            )

            # 7. Create attribution linking opportunity to campaign
            create_attribution(
                tenant_id=1, campaign_id=cid,
                target_type="opportunity",
                target_id=opp.id,
                source="campaign_conversion",
                attribution_state="strongly_attributable",
                confidence=85,
                opportunity_id=opp.id,
                target_description=f"Opportunity: {opp.title}",
            )

            # 8. Create a Proposal (commercial action) - then transition to accepted
            prop = create_proposal(
                organization_id=org_id,
                opportunity_id=opp.id,
                title="E2E Proposal",
                total_value=50000,
                created_by="g5_test",
            )
            # Transition to accepted
            from app.commercial.service import transition_proposal
            transition_proposal(prop, "accepted", "Accepted in E2E test", triggered_by="g5_test")

            # 9. Attribute outcome to campaign
            create_attribution(
                tenant_id=1, campaign_id=cid,
                target_type="proposal",
                target_id=prop.id,
                revenue_amount=50000.00,
                is_revenue_outcome=True,
                attribution_state="directly_linked",
                confidence=95,
                opportunity_id=opp.id,
                proposal_id=prop.id,
                target_description=f"Accepted: {prop.title}",
            )

            # 10. Record conversion event
            record_campaign_event(
                cid, 1, "conversion_occurred",
                description=f"Revenue outcome: 50000 from proposal #{prop.id}",
                payload={"revenue_amount": 50000, "proposal_id": prop.id},
            )

            # 11. Create learning grounded in the outcome
            create_learning(
                tenant_id=1, campaign_id=cid,
                category="campaign_performance",
                title="Google Ads campaign generating revenue",
                observation="E2E campaign produced 50000 in attributed revenue",
                significance="significant",
                confidence=90,
                recommendation="Continue Google Ads investment",
                recommendation_confidence=85,
                recommendation_action="Maintain Google Ads budget",
                is_actionable=True,
            )

            # 12. Verify the complete attribution chain
            chain = get_attribution_chain(cid, 1)
            assert "error" not in chain, f"Chain has error: {chain.get('error')}"
            assert chain["campaign"]["id"] == cid
            assert chain["campaign"]["name"] == "E2E G5-G4 Bridge"
            assert chain["total_attributions"] >= 3, f"Expected >=3 attributions, got {chain['total_attributions']}"
            assert chain["total_interactions"] >= 1
            assert chain["total_revenue"] >= 50000.0, f"Expected >=50000 revenue, got {chain['total_revenue']}"
            assert len(chain["g4_opportunities"]) >= 1, "Should have G4 opportunities linked"
            assert len(chain["learnings"]) >= 1, "Should have learnings"

            # 13. Verify the end-to-end learning/intelligence
            from app.g5.service import campaign_intelligence
            intel = campaign_intelligence(cid, 1)
            assert "error" not in intel
            assert intel["assessment"]["has_response"] is True
            assert intel["assessment"]["has_conversion"] is True
            assert intel["assessment"]["has_learning"] is True
            assert intel["assessment"]["total_revenue"] == "50000.0"
            assert intel["assessment"]["roi_known"] is True
            assert intel["confidence_summary"] == "sufficient"


class TestRoutesAPI:
    """G5 API route integration tests."""

    def test_events_api(self, app, client):
        r = client.post("/api/v1/marketing/campaigns", json={
            "name": "API Event Test", "tenant_id": 1,
        })
        cid = r.get_json()["id"]
        r = client.post(f"/api/v1/growth/campaigns/{cid}/events", json={
            "event_type": "campaign_activated", "new_state": "active",
            "description": "Activated via API",
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["success"] is True
        assert data["event"]["event_type"] == "campaign_activated"

    def test_interactions_api(self, app, client):
        r = client.post("/api/v1/growth/interactions", json={
            "tenant_id": 1,
            "interaction_type": "website_visit",
            "identity_ref": "api@test.com",
            "source": "google",
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["success"] is True
        assert data["interaction"]["source"] == "google"

    def test_attribution_api(self, app, client):
        r = client.post("/api/v1/growth/attributions", json={
            "tenant_id": 1, "target_type": "interaction",
            "target_id": 1, "source": "facebook",
            "attribution_state": "strongly_attributable",
            "confidence": 80,
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["success"] is True
        assert data["attribution"]["attribution_state"] == "strongly_attributable"

    def test_learnings_api(self, app, client):
        r = client.post("/api/v1/growth/learnings", json={
            "tenant_id": 1, "category": "campaign_performance",
            "title": "API Learning", "observation": "Test via API",
            "confidence": 75,
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["success"] is True
        assert data["learning"]["title"] == "API Learning"

    def test_intelligence_api(self, app, client):
        r = client.get("/api/v1/growth/intelligence/999999?tenant_id=1")
        assert r.status_code == 200
        data = r.get_json()
        assert "error" in data["intelligence"]

    def test_attribution_chain_api(self, app, client):
        r = client.post("/api/v1/marketing/campaigns", json={
            "name": "Chain API", "tenant_id": 1,
        })
        cid = r.get_json()["id"]
        r = client.get(f"/api/v1/growth/attributions/chain/{cid}?tenant_id=1")
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True
        assert "chain" in data