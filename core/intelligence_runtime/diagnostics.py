"""Diagnostics Engine — checks each intelligence component's health.

Each health check follows the same contract:
  - Returns a dict with at minimum {"status": "ok"/"degraded"/"error"}
  - Never raises — catches and reports failures as "error" status
  - Lazy imports inside try/except for graceful fallback

G3 Phase 7.1.
"""

from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

# Blueprint for the diagnostics API endpoint
diagnostics_bp = Blueprint("diagnostics", __name__, url_prefix="/api/v1")


@diagnostics_bp.route("/diagnostics", methods=["GET"])
def api_diagnostics():
    """GET /api/v1/diagnostics — run engine self-diagnostics."""
    engine = DiagnosticsEngine()
    result = engine.run_all()
    status_code = 200 if result["status"] == "ok" else 503
    return jsonify(result), status_code


class DiagnosticsEngine:
    """Probes every intelligence subsystem and reports detailed health."""

    @staticmethod
    def run_all() -> dict[str, Any]:
        """Run every diagnostic check and return a composite result."""
        results = {
            "memory_engine": DiagnosticsEngine._check_memory_engine(),
            "retrieval_layer": DiagnosticsEngine._check_retrieval_layer(),
            "context_engine": DiagnosticsEngine._check_context_engine(),
            "conversation_runtime": DiagnosticsEngine._check_conversation_runtime(),
            "planner": DiagnosticsEngine._check_planner(),
        }
        overall = all(r.get("status") == "ok" for r in results.values())
        return {
            "status": "ok" if overall else "degraded",
            "checks": results,
        }

    @staticmethod
    def _check_memory_engine() -> dict[str, Any]:
        """Verify MemoryEngine can store and recall an entry."""
        try:
            from core.intelligence_runtime import get_runtime

            runtime = get_runtime()
            engine = runtime.memory
            if engine is None:
                return {"status": "error", "detail": "MemoryEngine is None"}
            # Store a test entry
            test_key = "_diag_test"
            engine.store(test_key, "diagnostics", source="system")
            # Recall it
            entry = engine.get(test_key)
            engine.forget(test_key)
            if entry and entry.content == "diagnostics":
                return {
                    "status": "ok",
                    "detail": "store/recall verified",
                    "count": engine.count(),
                }
            return {"status": "degraded", "detail": "store/recall mismatch"}
        except Exception as e:
            logger.warning("Memory engine diag failed: %s", e)
            return {"status": "error", "detail": str(e)}

    @staticmethod
    def _check_retrieval_layer() -> dict[str, Any]:
        """Verify that at least some retrieval providers respond."""
        try:
            from core.intelligence_runtime import get_runtime

            runtime = get_runtime()
            rl = runtime.retrieval
            if rl is None:
                return {"status": "error", "detail": "RetrievalLayer is None"}
            providers = []
            if rl._graph_provider:
                providers.append("graph")
            if rl._canonical_provider:
                providers.append("canonical")
            if rl._object_provider:
                providers.append("object")
            if rl._memory_provider:
                providers.append("memory")
            if rl._internet_provider:
                providers.append("internet")
            if rl._knowledge_provider:
                providers.append("knowledge")
            additional = getattr(rl, "_additional_providers", {}) or {}
            extra_keys = list(additional.keys())
            if extra_keys:
                providers.extend(extra_keys)
            return {
                "status": "ok" if providers else "degraded",
                "providers_wired": len(providers),
                "providers": providers,
            }
        except Exception as e:
            logger.warning("Retrieval layer diag failed: %s", e)
            return {"status": "error", "detail": str(e)}

    @staticmethod
    def _check_context_engine() -> dict[str, Any]:
        """Verify ContextEngine frames are accessible."""
        try:
            from core.intelligence_runtime import get_runtime

            runtime = get_runtime()
            ce = runtime.context
            if ce is None:
                return {"status": "error", "detail": "ContextEngine is None"}
            frame = ce.get("_diag_session")
            frames_available = len(ce._frames)
            # Clean up the diagnostic frame
            if "_diag_session" in ce._frames:
                del ce._frames["_diag_session"]
            return {
                "status": "ok",
                "detail": "frame creation and access verified",
                "active_frames": frames_available,
            }
        except Exception as e:
            logger.warning("Context engine diag failed: %s", e)
            return {"status": "error", "detail": str(e)}

    @staticmethod
    def _check_conversation_runtime() -> dict[str, Any]:
        """Verify conversation messages flow correctly."""
        try:
            from core.intelligence_runtime import get_runtime

            runtime = get_runtime()
            cr = runtime.conversation
            if cr is None:
                return {"status": "error", "detail": "ConversationRuntime is None"}
            from core.intelligence_runtime.types import ContextFrame

            ctx = ContextFrame(conversation_id="_diag_conv")
            # Send a test message
            msg = cr.add_message("_diag_conv", "user", "diagnostics", context=ctx)
            if not msg:
                return {"status": "degraded", "detail": "add_message returned empty"}
            # Retrieve history
            history = cr.get_history("_diag_conv", limit=5)
            # Clean up
            cr._conversations.pop("_diag_conv", None)
            found = any(m.get("content") == "diagnostics" for m in history)
            return {
                "status": "ok" if found else "degraded",
                "detail": "message flow verified" if found else "message not found in history",
            }
        except Exception as e:
            logger.warning("Conversation runtime diag failed: %s", e)
            return {"status": "error", "detail": str(e)}

    @staticmethod
    def _check_planner() -> dict[str, Any]:
        """Verify the planner can classify an intent."""
        try:
            from core.intelligence_runtime import get_runtime

            runtime = get_runtime()
            p = runtime.planner
            if p is None:
                return {"status": "error", "detail": "ActionPlanner is None"}
            # Verify it has the decide method and business action detection
            has_decide = callable(getattr(p, "decide", None))
            has_detect = callable(getattr(p, "detect_business_action", None))
            return {
                "status": "ok" if has_decide and has_detect else "degraded",
                "has_decide_method": has_decide,
                "has_detect_business_action": has_detect,
            }
        except Exception as e:
            logger.warning("Planner diag failed: %s", e)
            return {"status": "error", "detail": str(e)}