"""
SHUNYA — Relationship-Aware Assistant (Phase 16, computation-only)
"""
import hashlib, json
from datetime import datetime, timezone
from typing import Optional


class AssistanceType:
    CONTEXTUAL = "contextual"
    RELATIONSHIP = "relationship"
    EXECUTION = "execution"
    LEARNING = "learning"
    GROWTH = "growth"
    BRAND = "brand"
    PLAN = "plan"
    INFERENCE = "inference"


class AssistanceState:
    PENDING = "pending"
    READY = "ready"
    DELIVERED = "delivered"
    FAILED = "failed"


class AssistantService:
    """Phase 16 — Relationship-Aware Assistant.

    Consumes closed intelligence layers to provide relationship-aware assistance.
    Does NOT own Phase 17 continuous surface, Phase 16A communication, or Phase 14C inference.
    """

    def __init__(self):
        self._sessions: dict[str, dict] = {}
        self._assistance: dict[str, dict] = {}
        self._idempotency: set[str] = set()
        self._version = "16.1"

    def create_session(self, tenant_id: int, person_id: int,
                        context_snapshot: Optional[dict] = None,
                        relationship_refs: Optional[list] = None,
                        idempotency_key: Optional[str] = None) -> dict:
        """Create a relationship-aware assistance session."""
        idem = idempotency_key or f"{tenant_id}:{person_id}"
        if idem in self._idempotency:
            return {"duplicate": True}
        self._idempotency.add(idem)
        sid = hashlib.sha256(f"{tenant_id}:{person_id}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16]
        self._sessions[sid] = {
            "session_id": sid,
            "tenant_id": tenant_id,
            "person_id": person_id,
            "context_snapshot": context_snapshot or {},
            "relationship_refs": relationship_refs or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return {"session_id": sid}

    def get_context(self, session_id: str, tenant_id: int) -> dict:
        """Assemble relevant context for this session from Phase 10 contracts."""
        sess = self._sessions.get(session_id)
        if not sess or sess.get("tenant_id") != tenant_id:
            return self._err("session_not_found", tenant_id)
        return {
            "session_id": session_id,
            "context": sess.get("context_snapshot", {}),
            "relationships": sess.get("relationship_refs", []),
            "person_id": sess.get("person_id"),
        }

    def recommend_action(self, session_id: str, tenant_id: int,
                          relevance_input: Optional[dict] = None,
                          execution_refs: Optional[list] = None,
                          learning_signals: Optional[list] = None,
                          growth_refs: Optional[list] = None,
                          brand_refs: Optional[list] = None) -> dict:
        """Recommend the most relevant next action for this relationship context."""
        sess = self._sessions.get(session_id)
        if not sess or sess.get("tenant_id") != tenant_id:
            return self._err("session_not_found", tenant_id)

        assistance_id = hashlib.sha256(
            f"{session_id}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]

        # Build recommendation from available intelligence
        recommendations = []
        if relevance_input:
            recommendations.append({
                "type": AssistanceType.CONTEXTUAL,
                "source": "relevance",
                "priority": relevance_input.get("category", "not_relevant"),
                "evidence": relevance_input.get("reasons", []),
            })
        if execution_refs:
            for ref in execution_refs:
                recommendations.append({
                    "type": AssistanceType.EXECUTION,
                    "source": "execution",
                    "exec_id": ref,
                    "priority": "attention_worthy",
                })
        if learning_signals:
            recommendations.append({
                "type": AssistanceType.LEARNING,
                "source": "learning",
                "signal_count": len(learning_signals),
            })
        if growth_refs:
            recommendations.append({
                "type": AssistanceType.GROWTH,
                "source": "growth",
                "campaign_refs": growth_refs,
            })
        if brand_refs:
            recommendations.append({
                "type": AssistanceType.BRAND,
                "source": "brand",
                "brand_refs": brand_refs,
            })

        result = {
            "assistance_id": assistance_id,
            "session_id": session_id,
            "state": AssistanceState.READY,
            "recommendations": recommendations,
            "provenance": {
                "relevance": relevance_input is not None,
                "execution": execution_refs is not None,
                "learning": learning_signals is not None,
                "growth": growth_refs is not None,
                "brand": brand_refs is not None,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._assistance[assistance_id] = result
        return result

    def request_inference(self, capability: str, context: dict,
                           tenant_id: int = 1) -> dict:
        """Handoff to Phase 14C — does NOT call a provider directly."""
        if not hasattr(self, "_inference_callback") or not self._inference_callback:
            return {"phase_14c_status": "not_connected",
                    "inference_required": True,
                    "capability": capability,
                    "result": None,
                    "provenance": {"deferred": True}}
        return self._inference_callback(capability, context, tenant_id)

    def set_inference_callback(self, callback):
        self._inference_callback = callback

    def list_assistance(self, session_id: str, tenant_id: int) -> dict:
        sess = self._sessions.get(session_id)
        if not sess or sess.get("tenant_id") != tenant_id:
            return self._err("session_not_found", tenant_id)
        items = [a for a in self._assistance.values()
                 if a["session_id"] == session_id]
        return {"assistance_items": items, "count": len(items)}

    def mark_delivered(self, assistance_id: str, tenant_id: int) -> dict:
        a = self._assistance.get(assistance_id)
        if not a:
            return self._err("assistance_not_found", tenant_id)
        # Verify tenant ownership through session
        sess = self._sessions.get(a.get("session_id", ""))
        if not sess or sess.get("tenant_id") != tenant_id:
            return self._err("tenant_mismatch", tenant_id)
        a["state"] = AssistanceState.DELIVERED
        return {"assistance_id": assistance_id, "state": AssistanceState.DELIVERED}

    def _err(self, reason: str, tenant_id: int = 1) -> dict:
        return {"error": reason, "tenant_id": tenant_id,
                "timestamp": datetime.now(timezone.utc).isoformat()}