"""Projection Runtime Adapter — wraps core/projection/ProjectionEngine for the canonical pipeline.

This adapter implements RuntimeInterface, registering for the
PROJECTION_ASSEMBLY and WORKSPACE_UPDATE pipeline stages. It
bridges the ProjectionEngine (which creates GraphProjections from
graph data) into the canonical pipeline.

When the pipeline executes projection_assembly, this adapter:
  1. Reads the current pipeline context (intent, object_id, identity_id)
  2. Assembles a workspace projection using the ProjectionEngine
  3. Attaches the projection to the PipelineContext
  4. Returns the projection result
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.projection import ProjectionEngine, ProjectionType
from core.runtime_pipeline import (
    PipelineContext,
    PipelineStage,
    RuntimeInterface,
)


class ProjectionRuntimeAdapter(RuntimeInterface):
    """Canonical Projection Runtime — assembles workspace views from pipeline state.

    Responsibilities:
      - Assemble workspace projections after pipeline execution
      - Cache projections for performance
      - Provide degraded projections when the knowledge graph is unavailable
      - Attach projections to the PipelineContext for downstream consumers

    Prohibitions:
      - Must never query the knowledge graph directly (uses callbacks)
      - Must never mutate pipeline state
      - Must never execute business actions
    """

    name: str = "projection"
    stages: list[PipelineStage] | None = None

    def __init__(self, engine: ProjectionEngine | None = None) -> None:
        self._engine = engine or ProjectionEngine()
        self.stages = [
            PipelineStage.PROJECTION_ASSEMBLY,
            PipelineStage.WORKSPACE_UPDATE,
        ]

    # ------------------------------------------------------------------
    # Pipeline stage handlers
    # ------------------------------------------------------------------

    def process(self, context: PipelineContext, stage: PipelineStage) -> dict[str, Any]:
        """Process the given pipeline stage.

        For PROJECTION_ASSEMBLY:
          - Assembles a workspace or object projection from pipeline state
          - Attaches the projection to the PipelineContext
          - Returns projection metadata

        For WORKSPACE_UPDATE:
          - Updates the workspace runtime with the assembled projection
          - Currently a pass-through — workspace runtime is the frontend
          - Logs the update for observability
        """
        if stage == PipelineStage.PROJECTION_ASSEMBLY:
            return self._assemble_projection(context)
        if stage == PipelineStage.WORKSPACE_UPDATE:
            return self._workspace_update(context)
        return {"status": "noop", "stage": stage.value}

    def _assemble_projection(self, context: PipelineContext) -> dict[str, Any]:
        """Assemble a projection based on the current pipeline context.

        The projection type is determined by the intent:
          - create_object / view_object → workspace projection
          - create_space → workspace projection
          - sign_in → workspace projection
          - talk_to_customer → conversation projection
          - default → workspace projection
        """
        intent = context.intent
        params = context.parameters or {}
        root_id = context.object_id or context.identity_id or "system"

        # Determine projection type from intent
        if intent in ("talk_to_customer", "understand_opportunity"):
            ptype = ProjectionType.CONVERSATION
        elif intent == "execute_work":
            ptype = ProjectionType.EXECUTION
        else:
            ptype = ProjectionType.WORKSPACE

        # Assemble the projection
        projection = self._engine.project(
            projection_type=ptype,
            root_id=root_id,
        )

        # Attach to pipeline context
        context.projection = {
            "projection_id": projection.projection_id,
            "projection_type": projection.projection_type,
            "root_node": {
                "node_id": projection.root_node.node_id if projection.root_node else None,
                "name": projection.root_node.name if projection.root_node else None,
                "type": projection.root_node.type if projection.root_node else None,
            } if projection.root_node else None,
            "node_count": len(projection.nodes),
            "edge_count": len(projection.edges),
            "evidence_count": len(projection.evidence),
            "metadata": {
                "timing_ms": projection.metadata.timing_ms,
                "degraded": projection.metadata.degraded,
                "source": projection.metadata.source,
            },
            "timestamp": projection.timestamp,
        }

        return {
            "status": "completed",
            "projection_id": projection.projection_id,
            "projection_type": str(projection.projection_type),
            "node_count": len(projection.nodes),
            "edge_count": len(projection.edges),
            "evidence_count": len(projection.evidence),
            "degraded": projection.metadata.degraded,
            "source": projection.metadata.source,
            "timing_ms": projection.metadata.timing_ms,
            "assembled_at": datetime.now(timezone.utc).isoformat(),
        }

    def _workspace_update(self, context: PipelineContext) -> dict[str, Any]:
        """Update the workspace runtime with the assembled projection.

        Currently a pass-through — the workspace runtime is the frontend.
        This stage exists to ensure the pipeline has a complete 11-stage
        trace. Future: push projection to WebSocket/SSE for live updates.
        """
        projection_id = (
            context.projection.get("projection_id", "unknown")
            if context.projection
            else "none"
        )
        return {
            "status": "completed",
            "projection_id": projection_id,
            "workspace_updated": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    def get_traces(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return recent projection engine traces."""
        return [
            {
                "operation": t.operation,
                "projection_type": t.projection_type,
                "root_id": t.root_id,
                "timing_ms": t.timing_ms,
                "degraded": t.degraded,
                "node_count": t.node_count,
                "edge_count": t.edge_count,
                "timestamp": t.timestamp,
            }
            for t in self._engine.get_traces(limit=limit)
        ]

    def health_check(self) -> dict[str, Any]:
        """Return health status of the projection runtime."""
        engine_health = self._engine.health_check()
        return {
            "status": engine_health.get("status", "healthy"),
            "runtime": "projection",
            "engine": engine_health,
            "supported_projections": [pt.value for pt in ProjectionType],
        }


__all__ = ["ProjectionRuntimeAdapter"]