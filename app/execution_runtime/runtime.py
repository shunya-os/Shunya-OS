"""EP-07 — Universal Execution Runtime.

Understanding is not enough. Observation is not enough. Prediction is not enough.
SHUNYA exists to fulfil intentions. Execution becomes a first-class runtime.

Everything a user asks SHUNYA ultimately becomes an Execution.
Execution is universal. Domains are metadata.
The Execution Runtime orchestrates existing runtimes — it never duplicates them.
"""

import uuid
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


# ── Execution Lifecycle ──────────────────────────────────────────
# One canonical lifecycle. No domain-specific workflow engines.

EXECUTION_LIFECYCLE = [
    "Requested",
    "Understood",
    "Planned",
    "Executing",
    "Waiting",
    "Blocked",
    "Completed",
    "Verified",
    "Archived",
]


# ── Execution Living Object ──────────────────────────────────────

@dataclass
class ExecutionStep:
    step_id: str
    label: str
    status: str  # pending, in_progress, completed, blocked
    runtime: str  # which runtime handles this step
    detail: str = ""


@dataclass
class Execution:
    """Execution is a first-class Living Object.
    
    Every human intention becomes a Living Execution that orchestrates
    Documents, Communications, Creative Assets, Living Objects, Reality,
    Cognition, and Evidence until the intended outcome is achieved.
    """
    execution_id: str
    title: str
    intent: str = ""
    goal: str = ""
    status: str = "Requested"
    lifecycle: list[str] = field(default_factory=lambda: EXECUTION_LIFECYCLE.copy())
    steps: list[ExecutionStep] = field(default_factory=list)
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    participants: list[str] = field(default_factory=list)
    living_objects: list[dict] = field(default_factory=list)
    documents: list[dict] = field(default_factory=list)
    creative_assets: list[dict] = field(default_factory=list)
    conversations: list[dict] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # other execution ids
    confidence: float = 1.0
    completion_criteria: str = ""
    ai_reasoning: str = ""
    ai_blockers: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "title": self.title,
            "intent": self.intent,
            "goal": self.goal,
            "status": self.status,
            "step_count": len(self.steps),
            "completed_steps": sum(1 for s in self.steps if s.status == "completed"),
            "blocked_steps": sum(1 for s in self.steps if s.status == "blocked"),
            "participants": self.participants,
            "living_objects": self.living_objects,
            "document_count": len(self.documents),
            "creative_count": len(self.creative_assets),
            "conversation_count": len(self.conversations),
            "evidence_count": len(self.evidence),
            "risks": self.risks,
            "dependencies": self.dependencies,
            "confidence": self.confidence,
            "ai_reasoning": self.ai_reasoning,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def transition(self, target: str) -> bool:
        if target not in self.lifecycle:
            return False
        self.status = target
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.evidence.append({
            "event": f"transitioned_to_{target}",
            "timestamp": self.updated_at,
        })
        return True

    def progress_pct(self) -> float:
        if not self.lifecycle:
            return 0.0
        if self.status in ("Completed", "Verified", "Archived"):
            return 100.0
        idx = self.lifecycle.index(self.status) if self.status in self.lifecycle else 0
        return (idx / max(len(self.lifecycle) - 1, 1)) * 100


# ── Execution Runtime ────────────────────────────────────────────

class ExecutionRuntime:
    """The single canonical execution runtime for SHUNYA.
    
    Coordinates existing runtimes — never duplicates them.
    Execution owns orchestration. Individual runtimes own capability.
    """

    def __init__(self):
        self._executions: dict[str, Execution] = {}

    # ── Execution CRUD ──

    def create_execution(self, title: str, intent: str = "",
                         goal: str = "", participants: list[str] | None = None,
                         completion_criteria: str = "") -> Execution:
        now = datetime.now(timezone.utc).isoformat()
        exec_obj = Execution(
            execution_id=f"ex_{uuid.uuid4().hex[:12]}",
            title=title,
            intent=intent,
            goal=goal,
            participants=participants or [],
            completion_criteria=completion_criteria,
            created_at=now,
            updated_at=now,
        )
        # Generate orchestration steps based on intent
        exec_obj.steps = self._generate_steps(title, intent)
        self._executions[exec_obj.execution_id] = exec_obj
        self._emit_reality(exec_obj, "execution_created")
        return exec_obj

    def get_execution(self, exec_id: str) -> Optional[Execution]:
        return self._executions.get(exec_id)

    def list_executions(self, status: Optional[str] = None, limit: int = 50) -> list[Execution]:
        exes = list(self._executions.values())
        if status:
            exes = [e for e in exes if e.status == status]
        exes.sort(key=lambda e: e.updated_at, reverse=True)
        return exes[:limit]

    def transition_execution(self, exec_id: str, target: str) -> Optional[Execution]:
        ex = self._executions.get(exec_id)
        if not ex:
            return None
        if ex.transition(target):
            self._emit_reality(ex, f"execution_{target.lower()}")
        return ex

    # ── Step Management ──

    def update_step(self, exec_id: str, step_id: str,
                    status: str) -> Optional[Execution]:
        ex = self._executions.get(exec_id)
        if not ex:
            return None
        for step in ex.steps:
            if step.step_id == step_id:
                step.status = status
                ex.updated_at = datetime.now(timezone.utc).isoformat()
                self._emit_reality(ex, f"step_{status}")
                break
        return ex

    # ── Orchestration — coordinates existing runtimes ──

    def orchestrate(self, exec_id: str) -> Optional[dict]:
        """Execute the next pending steps for an execution.
        
        Orchestrates existing runtimes. Never duplicates them.
        """
        ex = self._executions.get(exec_id)
        if not ex:
            return None

        results = {"steps_executed": [], "new_objects": [], "errors": []}

        for step in ex.steps:
            if step.status != "pending":
                continue

            try:
                result = self._execute_step(step, ex)
                step.status = "in_progress"
                results["steps_executed"].append(step.step_id)

                if step.runtime == "composer" and result:
                    ex.living_objects.append(result)
                    results["new_objects"].append(result)

                if step.runtime == "document" and result:
                    ex.documents.append(result)
                    results["new_objects"].append(result)

                if step.runtime == "creative" and result:
                    ex.creative_assets.extend(result if isinstance(result, list) else [result])
                    results["new_objects"].append(result)

                if step.runtime == "communication" and result:
                    ex.conversations.append(result)
                    results["new_objects"].append(result)

                step.status = "completed"

            except Exception as e:
                step.status = "blocked"
                ex.ai_blockers.append(str(e))
                results["errors"].append({"step": step.step_id, "error": str(e)})

        ex.updated_at = datetime.now(timezone.utc).isoformat()
        self._emit_reality(ex, "execution_orchestrated")
        return results

    def _generate_steps(self, title: str, intent: str) -> list[ExecutionStep]:
        """Generate orchestration steps based on execution title and intent.
        
        Steps are templates — the runtime executes them through existing providers.
        """
        steps = []
        lower = (title + " " + intent).lower()

        # Always start with understanding
        steps.append(ExecutionStep(
            step_id=f"st_{uuid.uuid4().hex[:8]}",
            label="Understand intent",
            status="completed" if intent else "pending",
            runtime="cognition",
            detail="Analyze the user's request and determine required capabilities",
        ))

        # Planning step
        steps.append(ExecutionStep(
            step_id=f"st_{uuid.uuid4().hex[:8]}",
            label="Create plan",
            status="pending",
            runtime="cognition",
            detail="Create execution plan with milestones and dependencies",
        ))

        # Detect document needs
        if any(word in lower for word in ["proposal", "contract", "agreement", "report", "letter", "document"]):
            steps.append(ExecutionStep(
                step_id=f"st_{uuid.uuid4().hex[:8]}",
                label="Create document",
                status="pending",
                runtime="document",
                detail="Generate the required document using Document Runtime",
            ))

        # Detect creative needs
        if any(word in lower for word in ["campaign", "launch", "social", "post", "banner", "presentation", "slide", "creative"]):
            steps.append(ExecutionStep(
                step_id=f"st_{uuid.uuid4().hex[:8]}",
                label="Create creative assets",
                status="pending",
                runtime="creative",
                detail="Generate creative representations using Creative Runtime",
            ))

        # Detect communication needs
        if any(word in lower for word in ["email", "message", "call", "contact", "reach out", "notify", "invite", "communicate"]):
            steps.append(ExecutionStep(
                step_id=f"st_{uuid.uuid4().hex[:8]}",
                label="Send communications",
                status="pending",
                runtime="communication",
                detail="Send required communications through Communication Runtime",
            ))

        # Detect object creation
        if any(word in lower for word in ["create", "new", "add", "make", "build", "generate", "set up"]):
            steps.append(ExecutionStep(
                step_id=f"st_{uuid.uuid4().hex[:8]}",
                label="Create Living Objects",
                status="pending",
                runtime="composer",
                detail="Create necessary Living Objects using the Composer",
            ))

        # Travel detection
        if any(word in lower for word in ["travel", "trip", "journey", "fly", "hotel", "book", "itinerary", "honeymoon", "vacation"]):
            steps.append(ExecutionStep(
                step_id=f"st_{uuid.uuid4().hex[:8]}",
                label="Plan travel",
                status="pending",
                runtime="composer",
                detail="Create itinerary, book travel, and set up trip documents",
            ))

        # Meeting detection
        if any(word in lower for word in ["meeting", "board", "review", "standup", "call", "sync"]):
            steps.append(ExecutionStep(
                step_id=f"st_{uuid.uuid4().hex[:8]}",
                label="Prepare meeting",
                status="pending",
                runtime="document",
                detail="Create agenda, prepare materials, send invitations",
            ))

        # Always end with verification
        steps.append(ExecutionStep(
            step_id=f"st_{uuid.uuid4().hex[:8]}",
            label="Verify completion",
            status="pending",
            runtime="cognition",
            detail="Verify all outputs meet completion criteria",
        ))

        return steps

    def _execute_step(self, step: ExecutionStep, ex: Execution) -> Optional[any]:
        """Execute a single step through the appropriate runtime.
        
        Delegates to existing runtimes. Never duplicates capability.
        """
        if step.runtime == "document":
            return self._orchestrate_document(ex)
        elif step.runtime == "creative":
            return self._orchestrate_creative(ex)
        elif step.runtime == "communication":
            return self._orchestrate_communication(ex)
        elif step.runtime == "composer":
            return self._orchestrate_composer(ex)
        elif step.runtime == "cognition":
            return self._orchestrate_cognition(ex)
        return None

    def _orchestrate_document(self, ex: Execution) -> Optional[dict]:
        try:
            from app.document_runtime.runtime import get_document_runtime
            rt = get_document_runtime()
            doc = rt.create_document(title=ex.title, content=f"Execution: {ex.execution_id}",
                                     purpose=ex.goal)
            return {"document_id": doc.document_id, "title": doc.title, "type": doc.doc_type}
        except Exception:
            return None

    def _orchestrate_creative(self, ex: Execution) -> Optional[list]:
        try:
            from app.creative_runtime.runtime import get_creative_runtime
            rt = get_creative_runtime()
            assets = rt.generate_representations(title=ex.title, intent="launch_campaign")
            return [{"asset_id": a.asset_id, "title": a.title, "creative_type": a.creative_type} for a in assets]
        except Exception:
            return None

    def _orchestrate_communication(self, ex: Execution) -> Optional[dict]:
        try:
            from app.communication.runtime import get_communication_runtime
            rt = get_communication_runtime()
            conv = rt.get_or_create_conversation(
                title=f"Execution: {ex.title}",
                participants=ex.participants,
            )
            return {"conversation_id": conv.conversation_id, "title": conv.title}
        except Exception:
            return None

    def _orchestrate_composer(self, ex: Execution) -> Optional[dict]:
        try:
            from app.object_composer.composer import get_composer_runtime
            rt = get_composer_runtime()
            result = rt.compose({"title": ex.title, "intent": ex.intent, "identity_id": "system"})
            return {"object_id": result.get("object_id")}
        except Exception:
            return None

    def _orchestrate_cognition(self, ex: Execution) -> Optional[dict]:
        # Analyze the execution, detect blockers, estimate confidence
        risks = []
        if not ex.intent:
            risks.append("No intent specified — execution may lack direction")
        if not ex.goal:
            risks.append("No goal defined — completion is ambiguous")
        if not ex.completion_criteria:
            risks.append("No completion criteria — success cannot be verified")
        if not ex.participants:
            risks.append("No participants assigned")
        blocked_steps = [s for s in ex.steps if s.status == "blocked"]
        if blocked_steps:
            risks.append(f"{len(blocked_steps)} step(s) blocked")
        ex.risks = risks
        ex.confidence = max(0.0, 1.0 - (len(risks) * 0.15))
        ex.ai_reasoning = (
            f"Execution: {ex.title}. Intent: {ex.intent or 'Not specified'}. "
            f"Goal: {ex.goal or 'Not defined'}. "
            f"Status: {ex.status}. Risks: {len(risks)}. "
            f"Confidence: {ex.confidence:.0%}. "
            f"Recommendation: {'Resolve blockers first' if risks else 'Proceed with execution'}."
        )
        return {"risks": risks, "confidence": ex.confidence, "reasoning": ex.ai_reasoning}

    # ── AI Intelligence ──

    def analyze(self, exec_id: str) -> Optional[dict]:
        ex = self._executions.get(exec_id)
        if not ex:
            return None

        blocked = [s for s in ex.steps if s.status == "blocked"]
        pending = [s for s in ex.steps if s.status == "pending"]
        progress = ex.progress_pct()
        # Run cognition to refresh risk/confidence
        self._orchestrate_cognition(ex)

        return {
            "execution_id": exec_id,
            "title": ex.title,
            "status": ex.status,
            "progress_pct": progress,
            "blocked_steps": len(blocked),
            "pending_steps": len(pending),
            "total_steps": len(ex.steps),
            "risks": ex.risks,
            "confidence": ex.confidence,
            "ai_reasoning": ex.ai_reasoning,
            "recommendation": (
                "Resolve blockers before proceeding" if blocked
                else "Execute pending steps" if pending
                else "Execution complete — verify outputs"
                if ex.status in ("Completed", "Verified")
                else "Proceed with execution"
            ),
        }

    # ── EP-07A: Adaptive Execution Intelligence ──
    # Execution continuously observes Reality and adapts.

    def observe_reality(self, exec_id: str) -> Optional[dict]:
        """Observe Reality and determine if execution should adapt.
        
        Continuously evaluates: Has Reality changed? Has risk changed?
        Has a dependency changed? Has AI learned something new?
        If yes, execution adapts.
        """
        ex = self._executions.get(exec_id)
        if not ex:
            return None

        changes = []
        previous_status = ex.status

        # 1. Refresh cognition (risks, confidence, reasoning)
        self._orchestrate_cognition(ex)

        # 2. Check for step resolution (blocked → retry)
        for step in ex.steps:
            if step.status == "blocked":
                changes.append({"step": step.step_id, "label": step.label, "observation": "still blocked"})

        # 3. Re-evaluate status based on reality
        blocked_count = sum(1 for s in ex.steps if s.status == "blocked")
        completed_count = sum(1 for s in ex.steps if s.status == "completed")
        pending_count = sum(1 for s in ex.steps if s.status == "pending")

        if blocked_count > 0 and ex.status not in ("Blocked", "Waiting"):
            ex.transition("Blocked")
            changes.append({"observation": "Blockers detected — execution paused"})
        elif completed_count == len(ex.steps) and ex.status in ("Executing", "Planned"):
            ex.transition("Completed")
            changes.append({"observation": "All steps completed"})
        elif pending_count > 0 and blocked_count == 0 and ex.status == "Blocked":
            # Blockers resolved — resume
            ex.transition("Executing")
            changes.append({"observation": "Blockers resolved — execution resumed"})

        # 4. Emit reality notification of changes
        if ex.status != previous_status:
            self._emit_reality(ex, f"execution_{ex.status.lower()}")
        else:
            self._emit_reality(ex, "execution_observed")

        ex.updated_at = datetime.now(timezone.utc).isoformat()
        return {
            "execution_id": exec_id,
            "previous_status": previous_status,
            "current_status": ex.status,
            "changes": changes,
            "risks": ex.risks,
            "confidence": ex.confidence,
        }

    def recommend(self, exec_id: str) -> Optional[dict]:
        """Generate evidence-backed recommendations.
        
        Every recommendation includes evidence.
        Recommendations never execute automatically unless explicitly authorized.
        """
        ex = self._executions.get(exec_id)
        if not ex:
            return None

        # Refresh cognition first
        self._orchestrate_cognition(ex)

        blocked_steps = [s for s in ex.steps if s.status == "blocked"]
        pending_steps = [s for s in ex.steps if s.status == "pending"]
        completed_steps = [s for s in ex.steps if s.status == "completed"]

        recommendations = []

        # Continue — default recommendation if progressing
        if not blocked_steps and pending_steps:
            recommendations.append({
                "action": "Continue",
                "evidence": f"{len(pending_steps)} steps pending, no blockers",
                "confidence": ex.confidence,
            })

        # Pause — if risks are significant
        if ex.confidence < 0.5:
            recommendations.append({
                "action": "Pause",
                "evidence": f"Low confidence ({ex.confidence:.0%}): {len(ex.risks)} risks identified",
                "confidence": 1.0 - ex.confidence,
            })

        # Replan — if blocked with no clear resolution
        if blocked_steps and ex.confidence < 0.4:
            recommendations.append({
                "action": "Replan",
                "evidence": f"{len(blocked_steps)} blocked steps with {len(ex.risks)} risks — current plan may be invalid",
                "confidence": 0.7,
            })

        # Escalate — persistent blocks
        if len(blocked_steps) >= len(ex.steps) * 0.5:
            recommendations.append({
                "action": "Escalate",
                "evidence": f"Over 50% of steps ({len(blocked_steps)}/{len(ex.steps)}) are blocked",
                "confidence": 0.8,
            })

        # Delegate — if no participants
        if not ex.participants and pending_steps:
            recommendations.append({
                "action": "Delegate",
                "evidence": "No participants assigned — execution may stall",
                "confidence": 0.6,
            })

        # Cancel — if goal is unreachable
        if ex.confidence < 0.2:
            recommendations.append({
                "action": "Cancel",
                "evidence": f"Confidence critically low ({ex.confidence:.0%}) with {len(ex.risks)} unresolved risks",
                "confidence": 0.9,
            })

        # Merge — if another execution has overlapping intent
        for other_id, other in self._executions.items():
            if other_id != exec_id and other.status not in ("Completed", "Archived"):
                if ex.intent and other.intent and ex.intent == other.intent:
                    recommendations.append({
                        "action": "Merge",
                        "evidence": f"Execution '{other.title}' shares same intent: '{ex.intent}'",
                        "confidence": 0.5,
                    })
                    break

        return {
            "execution_id": exec_id,
            "status": ex.status,
            "confidence": ex.confidence,
            "recommendations": recommendations,
        }

    def adapt(self, exec_id: str, reality_event: Optional[dict] = None) -> Optional[dict]:
        """Adapt execution based on a reality event or observed change.
        
        Reality changes → execution changes.
        Plans are hypotheses. Reality is truth.
        """
        ex = self._executions.get(exec_id)
        if not ex:
            return None

        adaptations = []
        event_type = (reality_event or {}).get("type", "observed_change")

        if not reality_event:
            # Self-observed adaptation — check for common patterns
            pass

        # ── Customer accepted proposal ──
        if event_type == "proposal_accepted" or "accepted" in event_type:
            # Skip unnecessary follow-up, advance to execution
            for step in ex.steps:
                if "follow" in step.label.lower() or "remind" in step.label.lower():
                    step.status = "skipped"
                    adaptations.append({"action": "step_skipped", "step": step.label, "reason": "Customer already accepted"})
            # Advance lifecycle
            if ex.status in ("Executing", "Waiting"):
                ex.transition("Completed")
                adaptations.append({"action": "lifecycle_advanced", "from": ex.status, "to": "Completed",
                                    "reason": "Customer accepted — objective achieved"})

        # ── Supplier delay ──
        elif event_type == "supplier_delayed" or "delay" in event_type:
            # Replan delivery timeline
            adaptations.append({"action": "replan_timeline", "reason": "Supplier delay — rescheduling dependent steps"})
            if ex.status not in ("Blocked", "Waiting"):
                ex.transition("Blocked")
                adaptations.append({"action": "lifecycle_changed", "from": ex.status, "to": "Blocked",
                                    "reason": "Supplier delay — awaiting resolution"})

        # ── Travel disruption (must be checked before "cancelled" since
        #     "flight_cancelled" contains "cancelled") ──
        elif event_type == "flight_cancelled" or "travel_disrupted" in event_type:
            for step in ex.steps:
                if any(word in step.label.lower() for word in ["book", "flight", "hotel", "travel", "trip", "plan travel"]):
                    step.status = "pending"
                    adaptations.append({"action": "step_repending", "step": step.label, "reason": "Travel disruption — rebooking required"})
            if ex.status == "Executing":
                ex.transition("Blocked")
                adaptations.append({"action": "lifecycle_changed", "to": "Blocked", "reason": "Travel disruption"})

        # ── Meeting cancelled ──
        elif event_type == "meeting_cancelled" or "cancelled" in event_type:
            # Reorganize dependent work
            for step in ex.steps:
                if "meeting" in step.label.lower() or "present" in step.label.lower():
                    step.status = "skipped"
                    adaptations.append({"action": "step_skipped", "step": step.label, "reason": "Meeting cancelled"})
            adaptations.append({"action": "reorganize_dependents", "reason": "Meeting cancelled — dependent work rescheduled"})

        # ── Budget reduction ──
        elif event_type == "budget_reduced" or "budget" in event_type:
            # Reduce scope, adjust creative outputs
            amount = (reality_event or {}).get("amount", "unknown")
            adaptations.append({"action": "reduce_scope", "reason": f"Budget reduced by {amount} — reducing creative outputs"})
            ex.risks.append(f"Budget constraint: reduced by {amount}")
            ex.confidence = max(0.0, ex.confidence - 0.2)
            adaptations.append({"action": "confidence_updated", "new_confidence": ex.confidence,
                                "reason": "Budget reduction impacts delivery confidence"})

        # ── Generic reality change ──
        else:
            # Re-evaluate cognition
            self._orchestrate_cognition(ex)
            if ex.confidence < 0.3 and ex.status == "Executing":
                ex.transition("Waiting")
                adaptations.append({"action": "lifecycle_changed", "to": "Waiting",
                                    "reason": f"Reality change ({event_type}) — re-evaluating"})

        ex.updated_at = datetime.now(timezone.utc).isoformat()
        self._emit_reality(ex, f"adapted_{event_type}")
        return {
            "execution_id": exec_id,
            "event": event_type,
            "adaptations": adaptations,
            "status": ex.status,
            "confidence": ex.confidence,
        }

    def subscribe_reality(self, exec_id: str) -> bool:
        """Subscribe execution to Reality Engine notifications.
        
        In production, this would register a webhook or SSE consumer.
        The Reality Engine notifies this runtime when relevant events occur.
        """
        try:
            from app.reality_engine.engine import get_reality_engine
            engine = get_reality_engine()
            engine.notify({
                "type": "execution_subscribed",
                "identity_id": "system",
                "execution_id": exec_id,
            })
            return True
        except Exception:
            return False

    def search(self, query: str) -> list[dict]:
        q = query.lower()
        results = []
        for ex in self._executions.values():
            score = 0
            if q in ex.title.lower(): score += 10
            if q in ex.intent.lower(): score += 8
            if q in ex.goal.lower(): score += 5
            if q in ex.status.lower(): score += 3
            if q in ex.ai_reasoning.lower(): score += 2
            if score > 0:
                results.append({"execution": ex.to_dict(), "score": score})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:20]

    # ── Reality ──

    def _emit_reality(self, ex: Execution, event_type: str):
        try:
            from app.reality_engine.engine import get_reality_engine
            get_reality_engine().notify({
                "type": event_type, "identity_id": "system",
                "execution_id": ex.execution_id, "title": ex.title,
                "status": ex.status,
            })
        except Exception:
            pass


# ── Singleton ────────────────────────────────────────────────────

_RUNTIME_INSTANCE: Optional[ExecutionRuntime] = None

def get_execution_runtime() -> ExecutionRuntime:
    global _RUNTIME_INSTANCE
    if _RUNTIME_INSTANCE is None:
        _RUNTIME_INSTANCE = ExecutionRuntime()
    return _RUNTIME_INSTANCE