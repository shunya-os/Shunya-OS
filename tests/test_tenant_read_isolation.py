"""Cross-tenant READ isolation — adversarial Tenant A / Tenant B verification.

The directive requires proving (not assuming) that every read path keeps
tenant B's records invisible to tenant A. This suite builds two fully
isolated tenants with UNIQUE SECRET RECORDS, authenticates as tenant A, and
attempts direct access, timeline, memory, AI-context and trace access to
tenant B's records across every path that was ever tenant-agnostic:

- /api/v1/workspace/objects/<id>             (lead/relationship/commitment/campaign)
- /api/v1/workspace/timeline                 (TimelineEntry, ActivityLog, Commitment)
- /api/v1/workspace/timeline/memory          (MemoryRecord)
- /api/v1/workspace/commitments/<id>         (commitment detail + timeline)
- /api/v1/workspace/copilot/context          (AI context assembly)
- /api/v1/intelligence/ask company-first evidence (docs, commitments, memory,
  invoices, leads, learning events)
- /api/v1/intelligence/traces/<id> + /correct (intelligence history)

Both directions are asserted: legitimate same-tenant reads succeed AND
cross-tenant reads return 404/empty — never weakened.
"""
from datetime import date, datetime, timedelta, timezone

import pytest

from app import db
from app.auth import TeamMember
from app.models import Organization, OrgMember, ActivityLog, KnowledgeDocument
from app.authz.services import seed_default_roles


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def two_tenants(app):
    """Org A + Org B with owner identities and unique secret records."""
    from app.models import Lead
    from app.relationship.models import (
        CanonicalRelationship, TimelineEntry, RelationshipMemory,
    )
    from app.commitments.models import Commitment
    from app.marketing.models import Campaign
    from app.memory.models import MemoryRecord
    from app.finance.models import FinInvoice
    from app.intelligence.models import LearningEvent, ReasoningTrace

    org_a = Organization(name="Tenant A", slug="tenant-a-secret")
    org_b = Organization(name="Tenant B", slug="tenant-b-secret")
    db.session.add_all([org_a, org_b])
    db.session.commit()
    seed_default_roles(org_a.id)
    seed_default_roles(org_b.id)

    tm_a = TeamMember(name="A Owner", email="a@test.invalid", role="owner",
                      is_active=True, identity_id="sid_a")
    tm_b = TeamMember(name="B Owner", email="b@test.invalid", role="owner",
                      is_active=True, identity_id="sid_b")
    db.session.add_all([tm_a, tm_b])
    db.session.flush()
    db.session.add_all([
        OrgMember(organization_id=org_a.id, identity_id="sid_a",
                  email=tm_a.email, role="owner", is_active=True),
        OrgMember(organization_id=org_b.id, identity_id="sid_b",
                  email=tm_b.email, role="owner", is_active=True),
    ])
    db.session.flush()

    # ── Leads (tenant-scoped by legacy tenant_id == org id) ──────────
    from app.models import set_lead_tenant_id, clear_lead_tenant_id
    set_lead_tenant_id(org_a.id)
    lead_a = Lead(code="LA1", customer_name="SECRET LEAD ALPHA", tenant_id=org_a.id)
    db.session.add(lead_a)
    db.session.flush()
    set_lead_tenant_id(org_b.id)
    lead_b = Lead(code="LB1", customer_name="SECRET LEAD BRAVO", tenant_id=org_b.id)
    db.session.add(lead_b)
    db.session.flush()
    clear_lead_tenant_id()

    # ── Relationships + timeline + AI memory + memory records ─────────
    rel_a = CanonicalRelationship(organization_id=org_a.id,
                                  display_name="SECRET REL ALPHA", status="active")
    rel_b = CanonicalRelationship(organization_id=org_b.id,
                                  display_name="SECRET REL BRAVO", status="active")
    db.session.add_all([rel_a, rel_b])
    db.session.flush()

    tl_a = TimelineEntry(organization_id=org_a.id, relationship_id=rel_a.id,
                         event_type="note", title="SECRET TIMELINE ALPHA")
    tl_b = TimelineEntry(organization_id=org_b.id, relationship_id=rel_b.id,
                         event_type="note", title="SECRET TIMELINE BRAVO")
    rm_a = RelationshipMemory(organization_id=org_a.id, relationship_id=rel_a.id,
                              summary="SECRET AI MEMORY ALPHA")
    rm_b = RelationshipMemory(organization_id=org_b.id, relationship_id=rel_b.id,
                              summary="SECRET AI MEMORY BRAVO")
    mem_a = MemoryRecord(relationship_id=rel_a.id, tenant_id=org_a.id,
                         memory_key="alpha_key", value="SECRET MEMORY ALPHA",
                         status="active", memory_type="fact")
    mem_b = MemoryRecord(relationship_id=rel_b.id, tenant_id=org_b.id,
                         memory_key="bravo_key", value="SECRET MEMORY BRAVO",
                         status="active", memory_type="fact")
    db.session.add_all([tl_a, tl_b, rm_a, rm_b, mem_a, mem_b])
    db.session.flush()

    # ── Commitments (scoped via relationship org) ─────────────────────
    _due = datetime.now(timezone.utc) + timedelta(days=1)
    comm_a = Commitment(relationship_id=rel_a.id, title="SECRET COMMITMENT ALPHA",
                        due_at=_due)
    comm_b = Commitment(relationship_id=rel_b.id, title="SECRET COMMITMENT BRAVO",
                        due_at=_due)
    db.session.add_all([comm_a, comm_b])
    db.session.flush()

    # ── Campaigns (tenant_id == org id) ───────────────────────────────
    camp_a = Campaign(tenant_id=org_a.id, name="SECRET CAMPAIGN ALPHA")
    camp_b = Campaign(tenant_id=org_b.id, name="SECRET CAMPAIGN BRAVO")
    db.session.add_all([camp_a, camp_b])
    db.session.flush()

    # ── Activity logs (scoped via lead) ───────────────────────────────
    act_a = ActivityLog(lead_id=lead_a.id, action="note_added", detail="SECRET ACTIVITY ALPHA")
    act_b = ActivityLog(lead_id=lead_b.id, action="note_added", detail="SECRET ACTIVITY BRAVO")
    db.session.add_all([act_a, act_b])
    db.session.flush()

    # ── Knowledge documents (AI context) ──────────────────────────────
    kd_a = KnowledgeDocument(organization_id=org_a.id, title="SECRET DOC ALPHA",
                             category="general")
    kd_b = KnowledgeDocument(organization_id=org_b.id, title="SECRET DOC BRAVO",
                             category="general")
    db.session.add_all([kd_a, kd_b])
    db.session.flush()

    # ── Invoices (AI context counts) ──────────────────────────────────
    inv_a = FinInvoice(organization_id=org_a.id, number="INV-ALPHA-1",
                       issue_date=date(2026, 1, 1))
    inv_b = FinInvoice(organization_id=org_b.id, number="INV-BRAVO-1",
                       issue_date=date(2026, 1, 2))
    db.session.add_all([inv_a, inv_b])
    db.session.flush()

    # ── Learning events (identity-owned) ──────────────────────────────
    learn_a = LearningEvent(identity_id="sid_a", learning_type="correction",
                            trigger_summary="SECRET LEARNING ALPHA")
    learn_b = LearningEvent(identity_id="sid_b", learning_type="correction",
                            trigger_summary="SECRET LEARNING BRAVO")
    db.session.add_all([learn_a, learn_b])
    db.session.flush()

    # ── Reasoning traces (identity-owned) ─────────────────────────────
    trc_a = ReasoningTrace(trace_id="trc_a_1", identity_id="sid_a",
                           reasoning_type="analysis", query_text="alpha q")
    trc_b = ReasoningTrace(trace_id="trc_b_1", identity_id="sid_b",
                           reasoning_type="analysis", query_text="bravo q")
    db.session.add_all([trc_a, trc_b])
    db.session.commit()

    return {
        "org_a": org_a.id, "org_b": org_b.id,
        "lead_a": lead_a.id, "lead_b": lead_b.id,
        "rel_a": rel_a.id, "rel_b": rel_b.id,
        "comm_a": comm_a.id, "comm_b": comm_b.id,
        "camp_a": camp_a.id, "camp_b": camp_b.id,
    }


@pytest.fixture()
def alice(client, two_tenants):
    """Authenticated tenant-A owner."""
    with client.session_transaction() as sess:
        sess["identity_id"] = "sid_a"
        sess["current_org_id"] = two_tenants["org_a"]
        sess["user_id"] = "sid_a"
    return two_tenants


ALPHA = ["SECRET LEAD ALPHA", "SECRET REL ALPHA", "SECRET TIMELINE ALPHA",
         "SECRET AI MEMORY ALPHA", "SECRET MEMORY ALPHA", "SECRET COMMITMENT ALPHA",
         "SECRET CAMPAIGN ALPHA", "SECRET ACTIVITY ALPHA", "SECRET DOC ALPHA",
         "INV-ALPHA-1", "SECRET LEARNING ALPHA"]
BRAVO = ["SECRET LEAD BRAVO", "SECRET REL BRAVO", "SECRET TIMELINE BRAVO",
         "SECRET AI MEMORY BRAVO", "SECRET MEMORY BRAVO", "SECRET COMMITMENT BRAVO",
         "SECRET CAMPAIGN BRAVO", "SECRET ACTIVITY BRAVO", "SECRET DOC BRAVO",
         "INV-BRAVO-1", "SECRET LEARNING BRAVO"]

# Sources whose CONTENT (not just a count) enters ask() company evidence.
EVIDENCE_ALPHA = ["Tenant A", "SECRET DOC ALPHA", "SECRET COMMITMENT ALPHA",
                  "SECRET MEMORY ALPHA", "SECRET LEARNING ALPHA"]
EVIDENCE_BRAVO = ["Tenant B", "SECRET DOC BRAVO", "SECRET COMMITMENT BRAVO",
                  "SECRET MEMORY BRAVO", "SECRET LEARNING BRAVO"]


# ---------------------------------------------------------------------------
# Direct object access
# ---------------------------------------------------------------------------

def test_same_tenant_lead_read_succeeds(client, alice):
    resp = client.get(f"/api/v1/workspace/objects/{alice['lead_a']}?type=lead")
    assert resp.status_code == 200, resp.get_data(as_text=True)[:300]
    assert "SECRET LEAD ALPHA" in resp.get_data(as_text=True)


def test_cross_tenant_lead_read_denied(client, alice):
    resp = client.get(f"/api/v1/workspace/objects/{alice['lead_b']}?type=lead")
    assert resp.status_code == 404, resp.get_data(as_text=True)[:300]
    assert "SECRET LEAD BRAVO" not in resp.get_data(as_text=True)


def test_cross_tenant_lead_read_denied_without_type_hint(client, alice):
    resp = client.get(f"/api/v1/workspace/objects/{alice['lead_b']}")
    assert resp.status_code == 404


def test_cross_tenant_relationship_read_denied(client, alice):
    resp = client.get(f"/api/v1/workspace/objects/{alice['rel_b']}?type=relationship")
    assert resp.status_code == 404
    assert "SECRET REL BRAVO" not in resp.get_data(as_text=True)


def test_cross_tenant_commitment_read_denied(client, alice):
    resp = client.get(f"/api/v1/workspace/objects/{alice['comm_b']}?type=commitment")
    assert resp.status_code == 404
    assert "SECRET COMMITMENT BRAVO" not in resp.get_data(as_text=True)


def test_cross_tenant_campaign_read_denied(client, alice):
    resp = client.get(f"/api/v1/workspace/objects/{alice['camp_b']}?type=campaign")
    assert resp.status_code == 404
    assert "SECRET CAMPAIGN BRAVO" not in resp.get_data(as_text=True)


# ---------------------------------------------------------------------------
# Timeline + memory
# ---------------------------------------------------------------------------

def test_cross_tenant_timeline_returns_no_events(client, alice):
    resp = client.get(f"/api/v1/workspace/timeline?relationship_id={alice['rel_b']}")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "SECRET TIMELINE BRAVO" not in body
    assert "SECRET COMMITMENT BRAVO" not in body
    assert "SECRET ACTIVITY BRAVO" not in body


def test_same_tenant_timeline_returns_events(client, alice):
    resp = client.get(
        f"/api/v1/workspace/timeline?object_type=lead&object_id={alice['lead_a']}"
        f"&relationship_id={alice['rel_a']}")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "SECRET TIMELINE ALPHA" in body
    assert "SECRET COMMITMENT ALPHA" in body


def test_cross_tenant_memory_timeline_empty(client, alice):
    resp = client.get(f"/api/v1/workspace/timeline/memory?relationship_id={alice['rel_b']}")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "SECRET MEMORY BRAVO" not in body


def test_same_tenant_memory_timeline_visible(client, alice):
    resp = client.get(f"/api/v1/workspace/timeline/memory?relationship_id={alice['rel_a']}")
    assert resp.status_code == 200
    assert "SECRET MEMORY ALPHA" in resp.get_data(as_text=True)


# ---------------------------------------------------------------------------
# Commitment detail
# ---------------------------------------------------------------------------

def test_cross_tenant_commitment_detail_denied(client, alice):
    resp = client.get(f"/api/v1/workspace/commitments/{alice['comm_b']}")
    assert resp.status_code == 404
    assert "SECRET COMMITMENT BRAVO" not in resp.get_data(as_text=True)


def test_same_tenant_commitment_detail_visible(client, alice):
    resp = client.get(f"/api/v1/workspace/commitments/{alice['comm_a']}")
    assert resp.status_code == 200
    assert "SECRET COMMITMENT ALPHA" in resp.get_data(as_text=True)


# ---------------------------------------------------------------------------
# Copilot context (AI context assembly)
# ---------------------------------------------------------------------------

def test_cross_tenant_copilot_context_denied(client, alice):
    resp = client.get(f"/api/v1/workspace/copilot/context"
                      f"?object_type=lead&object_id={alice['lead_b']}")
    assert resp.status_code == 404
    assert "SECRET LEAD BRAVO" not in resp.get_data(as_text=True)


# ---------------------------------------------------------------------------
# AI company-first evidence assembly (ask route)
# ---------------------------------------------------------------------------

def test_ask_evidence_contains_only_own_tenant(client, alice, monkeypatch):
    """Tenant A's ask() must assemble ZERO tenant-B records."""
    calls = {}

    def fake_process(self, **kwargs):
        calls["context"] = kwargs.get("context", "")
        return {
            "content": "Answer about my business.",
            "provider": "test", "model": "test",
            "model_invoked": True, "deterministic": False,
            "observability": {}, "paid_blocked": False,
        }

    monkeypatch.setattr(
        "core.inference_governance.InferenceGovernanceService.process", fake_process)

    resp = client.post("/api/v1/intelligence/ask",
                       json={"question": "What do we know?"})
    assert resp.status_code == 200, resp.get_data(as_text=True)[:400]
    body = resp.get_json()

    evidence_text = "\n".join(e["content"] for e in body["evidence_used"])
    for secret in EVIDENCE_ALPHA:
        assert secret in evidence_text, f"own-tenant secret missing: {secret}"
    for secret in EVIDENCE_BRAVO:
        assert secret not in evidence_text, f"CROSS-TENANT LEAK: {secret}"
    for secret in EVIDENCE_BRAVO:
        assert secret not in calls.get("context", ""), f"LEAK IN CONTEXT: {secret}"


def test_ask_evidence_other_tenant_sees_own_records(client, two_tenants, monkeypatch):
    """Same suite, authenticated as tenant B: B's records appear, A's do not."""
    with client.session_transaction() as sess:
        sess["identity_id"] = "sid_b"
        sess["current_org_id"] = two_tenants["org_b"]
        sess["user_id"] = "sid_b"

    def fake_process(self, **kwargs):
        return {
            "content": "Bravo answer", "provider": "test", "model": "test",
            "model_invoked": True, "deterministic": False,
            "observability": {}, "paid_blocked": False,
        }

    monkeypatch.setattr(
        "core.inference_governance.InferenceGovernanceService.process", fake_process)

    resp = client.post("/api/v1/intelligence/ask",
                       json={"question": "What do we know?"})
    assert resp.status_code == 200, resp.get_data(as_text=True)[:400]
    body = resp.get_json()
    evidence_text = "\n".join(e["content"] for e in body["evidence_used"])
    for secret in EVIDENCE_BRAVO:
        assert secret in evidence_text
    for secret in EVIDENCE_ALPHA:
        assert secret not in evidence_text, f"CROSS-TENANT LEAK: {secret}"


# ---------------------------------------------------------------------------
# Calendar (tenant-owned read path)
# ---------------------------------------------------------------------------

def test_calendar_events_isolated_per_tenant(client, alice):
    resp = client.get("/api/v1/calendar/events")
    assert resp.status_code == 200, resp.get_data(as_text=True)[:300]
    text = resp.get_data(as_text=True)
    assert "SECRET COMMITMENT ALPHA" in text
    assert "SECRET COMMITMENT BRAVO" not in text


def test_calendar_events_other_tenant_isolated(client, two_tenants):
    with client.session_transaction() as sess:
        sess["identity_id"] = "sid_b"
        sess["current_org_id"] = two_tenants["org_b"]
        sess["user_id"] = "sid_b"
    resp = client.get("/api/v1/calendar/events")
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "SECRET COMMITMENT BRAVO" in text
    assert "SECRET COMMITMENT ALPHA" not in text


# ---------------------------------------------------------------------------
# Intelligence history (traces)
# ---------------------------------------------------------------------------

def test_cross_tenant_trace_read_denied(client, alice):
    resp = client.get("/api/v1/intelligence/traces/trc_b_1")
    assert resp.status_code == 404
    assert "bravo q" not in resp.get_data(as_text=True)


def test_same_tenant_trace_read_visible(client, alice):
    resp = client.get("/api/v1/intelligence/traces/trc_a_1")
    assert resp.status_code == 200
    assert "alpha q" in resp.get_data(as_text=True)


def test_cross_tenant_trace_correction_denied(client, alice):
    resp = client.post("/api/v1/intelligence/traces/trc_b_1/correct",
                       json={"corrected_response": "tampered"})
    assert resp.status_code == 404
    from app.intelligence.models import ReasoningTrace
    trc = ReasoningTrace.query.filter_by(trace_id="trc_b_1").first()
    assert trc.corrected_response != "tampered"
    assert trc.is_corrected is not True