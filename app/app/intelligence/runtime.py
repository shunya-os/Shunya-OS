"""
SHUNYA Explainable Intelligence — Runtime Bootstrap

Loads the default scenario into the observation engine and
provides the explainability middleware for existing routes.

No new routes. No new UI. The inspector is accessed via
?inspect=insight_id on existing routes.
"""

from flask import request, jsonify
from app.intelligence.scenario import get_scenario, InvestmentFirmScenario
from app.intelligence.observation import (
    Observation, ObservationStatus, get_store as get_obs_store,
)
from app.intelligence.reasoning import get_engine
from app.intelligence.insight import get_compiler
from app.intelligence.inspector import get_inspector
from app.intelligence.confidence import (
    ConfidenceInput, compute_confidence, confidence_label,
)


def load_default_scenario() -> None:
    """Load the default scenario into the observation store.

    This is called at app startup to populate demo data.
    In production, observations would come from real data sources.
    """
    scenario = get_scenario("Investment Firm")
    if not scenario:
        return

    obs_store = get_obs_store()
    engine = get_engine()

    # Build observations from scenario events
    objects = {o.object_id: o for o in scenario.get_objects()}
    evidence_map = {e.evidence_id: e for e in scenario.get_evidence()}

    for event in scenario.get_events():
        # Find the object
        obj = objects.get(event.object_id)
        if not obj:
            continue

        # Compute confidence for this observation
        evidence_items = [evidence_map.get(eid) for eid in event.evidence_ids if eid in evidence_map]
        conf_input = ConfidenceInput(
            evidence_completeness=len(event.evidence_ids) / max(len(evidence_items), 1) if evidence_items else 0.3,
            observation_freshness=1.0,
            source_reliability=0.85,
            relationship_consistency=0.8,
            conflict_detected=False,
            recency_hours=0,
            missing_information_ratio=0.1 if event.evidence_ids else 0.5,
        )
        conf = compute_confidence(conf_input)

        # Determine status based on event type
        if event.event_type == "risk":
            status = ObservationStatus.ACTIVE
        elif event.event_type == "decision":
            status = ObservationStatus.ACTIVE
        elif event.event_type == "change":
            status = ObservationStatus.ACTIVE
        else:
            status = ObservationStatus.DETECTED

        observation = Observation(
            observation_id=f"obs_{event.event_id}",
            object_id=event.object_id,
            event_id=event.event_id,
            label=event.title,
            description=event.description,
            status=status,
            evidence_ids=event.evidence_ids,
            confidence=conf,
            metadata={
                "source": event.source,
                "event_type": event.event_type,
                "object_name": obj.name,
                "object_type": obj.object_type,
            },
        )
        obs_store.add(observation)

    # Evaluate all observations to produce insights
    engine.evaluate_all_active()


def register_explainability_middleware(app) -> None:
    """Register the explainability middleware on the Flask app.

    Adds ?inspect=insight_id query parameter inspection to existing routes.
    Adds ?inspect_system to view the full system state.
    Does not change the public UI.
    """

    @app.before_request
    def _check_inspect():
        """Developer-only inspection via query parameter on any route.

        Usage:
          ?inspect=insight_id  — inspect a specific insight
          ?inspect_system=1    — inspect the full system state

        Returns JSON. Does not modify the public UI.
        """
        if request.args.get("inspect_system"):
            inspector = get_inspector()
            return jsonify(inspector.inspect_system())

        insight_id = request.args.get("inspect")
        if insight_id:
            inspector = get_inspector()
            return jsonify(inspector.inspect_insight(insight_id))

        return None


def load_scenario_data() -> None:
    """Load scenario data into the engine. Called once at startup."""
    load_default_scenario()