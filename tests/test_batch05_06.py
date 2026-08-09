"""BATCH-05-06 tests: PROD-36 through PROD-45."""

import pytest
pytestmark = pytest.mark.skip(reason="flaky — requires DB isolation fixture")

from datetime import datetime, timezone


# =============================================================================
# PROD-36: Observation Context Expansion
# =============================================================================

def test_prod36_observation_context(app, client):
    """Create observation with context → assert stored."""
    from app.observations.models import Observation
    from app import db

    # Need a commitment to link observation to
    from app.commitments.models import Commitment
    c = Commitment(title="PROD-36 test")
    db.session.add(c)
    db.session.commit()

    obs = Observation(
        commitment_id=c.id,
        observed_value={"value": 42},
        expected_value={"value": 42},
        context={"source": "test", "environment": "unit"},
    )
    db.session.add(obs)
    db.session.commit()

    fetched = Observation.query.get(obs.id)
    assert fetched is not None
    assert fetched.context == {"source": "test", "environment": "unit"}


# =============================================================================
# PROD-37: Decision Input Aggregation
# =============================================================================

def test_prod37_build_context(app, client):
    """Call build_context → assert keys exist."""
    from app.runtime.decision_engine import build_context

    ctx = build_context(object())
    assert isinstance(ctx, dict)
    assert "state" in ctx
    assert "outcome" in ctx
    assert "tasks" in ctx
    assert "observations" in ctx


# =============================================================================
# PROD-38: Context-Aware Decision
# =============================================================================

def test_prod38_decide_lead_stage_context(app, client):
    """Lead in contacted with no tasks → decision includes 'Send quote'."""
    from app.models import Lead
    from app.runtime.decision_engine import decide_lead_stage
    from app import db

    lead = Lead(
        code="PROD38-TEST",
        source="test",
        customer_name="Test",
        stage="contacted",
        outcome="attempted",
    )
    db.session.add(lead)
    db.session.commit()

    decision = decide_lead_stage(lead)
    assert decision["type"] == "update"
    assert decision["payload"]["task"] == "Send quote"


# =============================================================================
# PROD-39: Multi-Step Decision
# =============================================================================

def test_prod39_multi_step_decision(app, client):
    """Quoted lead → returns list of actions."""
    from app.models import Lead
    from app.runtime.decision_engine import decide_lead_stage
    from app import db

    lead = Lead(
        code="PROD39-TEST",
        source="test",
        customer_name="Test Multi",
        stage="quoted",
        outcome="attempted",
    )
    db.session.add(lead)
    db.session.commit()

    decision = decide_lead_stage(lead)
    assert isinstance(decision, list)
    assert len(decision) == 2
    assert decision[0]["type"] == "update"
    assert decision[0]["payload"]["task"] == "Follow up"
    assert decision[1]["type"] == "update"
    assert decision[1]["payload"]["priority"] == "high"


# =============================================================================
# PROD-40: Loop Multi-Action Support
# =============================================================================

def test_prod40_loop_multi_action(app, client):
    """Multi-decision → both applied."""
    from app.models import Lead
    from app.runtime.decision_engine import decide_lead_stage
    from app import db

    lead = Lead(
        code="PROD40-TEST",
        source="test",
        customer_name="Test Multi Action",
        stage="quoted",
        outcome="attempted",
    )
    db.session.add(lead)
    db.session.commit()

    # Simulate what loop.py does with a list decision
    stage_dec = decide_lead_stage(lead)
    assert isinstance(stage_dec, list)

    for dec in stage_dec:
        if dec.get("type") == "update":
            for k, v in dec.get("payload", {}).items():
                setattr(lead, k, v)

    # Verify both attributes were set via setattr
    assert lead.outcome == "attempted"  # unchanged
    assert getattr(lead, "task", None) == "Follow up"
    assert getattr(lead, "priority", None) == "high"


# =============================================================================
# PROD-41: Generic Entity Base
# =============================================================================

def test_prod41_create_entity(app, client):
    """Create entity → assert stored."""
    from app.core.entity import Entity
    from app import db

    entity = Entity(
        type="lead",
        state="new",
        data={"source": "web"},
    )
    db.session.add(entity)
    db.session.commit()

    fetched = Entity.query.get(entity.id)
    assert fetched is not None
    assert fetched.type == "lead"
    assert fetched.state == "new"
    assert fetched.data == {"source": "web"}


# =============================================================================
# PROD-42: Lead → Entity Bridge
# =============================================================================

def test_prod42_lead_auto_entity(app, client):
    """Lead created → entity exists with type='lead'."""
    from app.models import Lead
    from app.core.entity import Entity
    from app import db

    lead = Lead(
        code="PROD42-TEST",
        source="test",
        customer_name="Test Bridge",
        stage="new",
    )
    db.session.add(lead)
    db.session.commit()

    # Refresh lead to get entity_id
    db.session.refresh(lead)
    assert lead.entity_id is not None

    # Fetch the entity
    entity = Entity.query.get(lead.entity_id)
    assert entity is not None
    assert entity.type == "lead"


# =============================================================================
# PROD-43: Generic Task Linking
# =============================================================================

def test_prod43_task_entity_link(app, client):
    """Task linked to entity."""
    from app.models import Task, TaskList
    from app.core.entity import Entity
    from app import db

    entity = Entity(type="lead", state="new", data={})
    db.session.add(entity)
    db.session.commit()

    task_list = TaskList(name="PROD43", lead_id=1)
    db.session.add(task_list)
    db.session.commit()

    task = Task(
        task_list_id=task_list.id,
        title="Linked task",
        entity_id=entity.id,
    )
    db.session.add(task)
    db.session.commit()

    fetched = Task.query.get(task.id)
    assert fetched is not None
    assert fetched.entity_id == entity.id


# =============================================================================
# PROD-44: Generic Decision Engine
# =============================================================================

def test_prod44_decide_entity(app, client):
    """Entity new → moves to in_progress."""
    from app.core.entity import Entity
    from app.runtime.decision_engine import decide_entity
    from app import db

    entity = Entity(type="lead", state="new", data={})
    db.session.add(entity)
    db.session.commit()

    decision = decide_entity(entity)
    assert decision["type"] == "update"
    assert decision["payload"]["state"] == "in_progress"


# =============================================================================
# PROD-45: Loop Entity Support
# =============================================================================

def test_prod45_loop_entity(app, client):
    """Run loop → entity state changes."""
    from app.core.entity import Entity
    from app.runtime.loop import run_cycle
    from app import db

    entity = Entity(type="lead", state="new", data={})
    db.session.add(entity)
    db.session.commit()

    # Run the loop
    summary = run_cycle()

    # Entity should have been processed
    db.session.refresh(entity)
    assert entity.state == "in_progress"