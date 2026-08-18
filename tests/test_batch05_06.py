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
# PROD-38: Context-Aware Decision (removed — lead lifecycle eliminated from universal execution)
# =============================================================================


# =============================================================================
# PROD-39: Multi-Step Decision (removed — lead lifecycle eliminated from universal execution)
# =============================================================================


# =============================================================================
# PROD-40: Loop Multi-Action Support (removed — lead lifecycle eliminated from universal execution)
# =============================================================================


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