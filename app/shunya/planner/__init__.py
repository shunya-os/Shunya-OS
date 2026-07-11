"""Planner — Converts a decision or goal into an ordered sequence of steps.

Planner answers: in what sequence should we act?
Separating Reasoning from Planning prevents one component from being all-powerful.
"""
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from app import db
from app.models import Entity, EntityDefinition


@dataclass
class PlanStep:
    """A single step in a plan."""
    order: int
    action: str
    description: str
    responsible_role: str = "agent"
    estimated_minutes: int = 15
    depends_on: List[int] = field(default_factory=list)
    is_optional: bool = False


@dataclass
class Plan:
    """An ordered plan of steps to achieve a goal."""
    title: str
    steps: List[PlanStep] = field(default_factory=list)
    total_estimated_minutes: int = 0


class Planner:
    """Converts decisions into ordered plans."""

    @staticmethod
    def create_onboarding_plan(entity_type: str) -> Plan:
        """Create a plan for onboarding a new entity."""
        plans = {
            "lead": Plan(
                title="New Lead Onboarding",
                steps=[
                    PlanStep(1, "review", "Review lead details and requirements", estimated_minutes=5),
                    PlanStep(2, "contact", "Contact customer within SLA", estimated_minutes=10),
                    PlanStep(3, "discover", "Discovery call: understand needs and preferences", estimated_minutes=30),
                    PlanStep(4, "proposal", "Prepare and send proposal", estimated_minutes=45),
                    PlanStep(5, "followup", "Follow up on proposal", estimated_minutes=10),
                ],
                total_estimated_minutes=100,
            ),
            "patient": Plan(
                title="New Patient Onboarding",
                steps=[
                    PlanStep(1, "review", "Review patient intake form", estimated_minutes=5),
                    PlanStep(2, "schedule", "Schedule initial consultation", estimated_minutes=10),
                    PlanStep(3, "consult", "Conduct consultation", estimated_minutes=30),
                    PlanStep(4, "plan", "Create treatment plan", estimated_minutes=20),
                ],
                total_estimated_minutes=65,
            ),
        }
        return plans.get(entity_type, Plan(
            title="New Record Processing",
            steps=[
                PlanStep(1, "review", "Review the record", estimated_minutes=5),
                PlanStep(2, "action", "Take required action", estimated_minutes=15),
            ],
            total_estimated_minutes=20,
        ))

    @staticmethod
    def get_next_steps(entity: Entity) -> List[PlanStep]:
        """Get the next incomplete steps for an entity."""
        plan = Planner.create_onboarding_plan(
            entity.definition.type if entity.definition else "default"
        )
        # Return the first 3 steps
        return plan.steps[:3]

    @staticmethod
    def estimate_completion(plan: Plan, completed_steps: List[int]) -> dict:
        """Estimate time to completion based on remaining steps."""
        remaining = [s for s in plan.steps if s.order not in completed_steps]
        total_minutes = sum(s.estimated_minutes for s in remaining)
        return {
            "remaining_steps": len(remaining),
            "estimated_minutes": total_minutes,
            "estimated_hours": round(total_minutes / 60, 1),
        }