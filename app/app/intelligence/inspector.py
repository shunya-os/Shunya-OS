"""
SHUNYA Explainable Intelligence — Founder Inspector

An internal inspection capability for development and founder use.

Without changing the public UI, every surfaced insight is inspectable.
The inspector exposes: origin, evidence chain, reasoning chain,
confidence inputs, calculation timestamp, related objects, supporting observations.

This is a developer and founder capability only.
"""

from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone
import json

from app.intelligence.provenance import get_store as get_prov_store, ProvenanceStore
from app.intelligence.reasoning import get_engine, ReasoningEngine
from app.intelligence.observation import get_store as get_obs_store, ObservationStore
from app.intelligence.confidence import confidence_breakdown, ConfidenceInput
from app.intelligence.insight import get_compiler, InsightCompiler
from app.intelligence.scenario import list_scenarios, get_scenario


class FounderInspector:
    """Developer/founder inspection capability.

    Provides structured inspection data for any surfaced insight.
    Does not modify the public UI.
    """

    def __init__(
        self,
        provenance_store: Optional[ProvenanceStore] = None,
        observation_store: Optional[ObservationStore] = None,
        engine: Optional[ReasoningEngine] = None,
        compiler: Optional[InsightCompiler] = None,
    ):
        self.provenance = provenance_store or get_prov_store()
        self.observations = observation_store or get_obs_store()
        self.engine = engine or get_engine()
        self.compiler = compiler or get_compiler()

    def inspect_insight(self, insight_id: str) -> dict:
        """Return full inspection data for a single insight.

        Traces: origin → evidence chain → reasoning chain →
        confidence inputs → calculation timestamp → related objects →
        supporting observations.
        """
        # Resolve the provenance chain
        chain_nodes = self.provenance.resolve_statement(insight_id)
        chain = self.provenance.get_chain(
            next(
                (c.chain_id for c in [self.provenance.get_chain(f"chain_{obs_id}")
                 for obs_id in [o.observation_id for o in self.observations.get_active()]]
                 if c and c.get_node(insight_id)),
                ""
            )
        ) if not chain_nodes else None

        # Find the actual chain
        found_chain = None
        for cid in list(self.provenance._chains.keys()):
            c = self.provenance.get_chain(cid)
            if c and c.get_node(insight_id):
                found_chain = c
                break

        # Build inspection data
        inspection = {
            "insight_id": insight_id,
            "provenance": {
                "chain_found": found_chain is not None,
                "chain_id": found_chain.chain_id if found_chain else None,
                "chain_intact": found_chain.is_intact if found_chain else False,
                "node_count": found_chain.node_count if found_chain else 0,
                "nodes": [n.to_dict() for n in found_chain._nodes.values()] if found_chain else [],
            },
            "confidence": {
                "breakdown": None,
                "note": "Confidence breakdown available when ConfidenceInput is provided",
            },
            "observations": [
                {
                    "observation_id": o.observation_id,
                    "object_id": o.object_id,
                    "label": o.label,
                    "status": o.status.value,
                    "age_hours": round(o.age_hours, 1),
                    "evidence_count": len(o.evidence_ids),
                }
                for o in self.observations.get_active()
            ],
            "scenarios": {
                "available": list_scenarios(),
            },
            "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return inspection

    def inspect_chain(self, chain_id: str) -> dict:
        """Inspect a specific provenance chain by ID."""
        chain = self.provenance.get_chain(chain_id)
        if not chain:
            return {"error": f"Chain {chain_id} not found", "chain_id": chain_id}

        return {
            "chain_id": chain.chain_id,
            "root_id": chain._root_id,
            "leaf_id": chain._leaf_id,
            "node_count": chain.node_count,
            "is_intact": chain.is_intact,
            "integrity_issues": chain.verify_integrity(),
            "nodes": [n.to_dict() for n in chain._nodes.values()],
            "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def inspect_system(self) -> dict:
        """Return full system inspection: all chains, observations, insights."""
        return {
            "provenance": {
                "chain_count": self.provenance.chain_count,
                "integrity_issues": self.provenance.all_issues(),
            },
            "observations": {
                "total": self.observations.count,
                "active": len(self.observations.get_active()),
                "items": [o.to_dict() for o in self.observations.get_active()],
            },
            "insights": {
                "compiled": [i.to_dict() for i in self.compiler.compile_all()],
            },
            "scenarios": list_scenarios(),
            "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def render_inspection_html(self, insight_id: Optional[str] = None) -> str:
        """Render a minimal inspection HTML fragment.

        This is a developer-only view. It is not part of the public UI.
        It is returned as JSON or HTML fragment based on the request.
        """
        if insight_id:
            data = self.inspect_insight(insight_id)
        else:
            data = self.inspect_system()

        # Return as JSON for developer tools
        return json.dumps(data, indent=2, default=str)


# ─── Global inspector ───
_inspector: Optional[FounderInspector] = None


def get_inspector() -> FounderInspector:
    global _inspector
    if _inspector is None:
        _inspector = FounderInspector()
    return _inspector


def reset_inspector() -> None:
    global _inspector
    _inspector = None