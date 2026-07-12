"""Planner — Converts a decision or goal into an ordered sequence of steps.

Planner answers: in what sequence should we act?

This package provides both:
- SequentialPlanner with DependencyGraph (dependency-aware topological
  ordering of action steps, ported from the TS half-done repo)
- Legacy Planner (simple onboarding plans for entity types)

The default PlanStep and Plan exports are the dependency-aware versions
from SequentialPlanner. The legacy onboarding types are available as
OnboardingPlanStep and OnboardingPlan.
"""
# New-style re-exports (dependency-aware)
from app.shunya.planner.sequential_planner import (
    SequentialPlanner,
    DependencyGraph,
    PlanStep,  # new: id:str-based
    Plan,      # new: steps-only
)

from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from app import db
from app.models import Entity, EntityDefinition


# ═══════════════════════════════════════════════════════════════════════ #
# Legacy onboarding types (kept for backward compatibility)
# ═══════════════════════════════════════════════════════════════════════ #


@dataclass
class OnboardingPlanStep:
    """A single step in an onboarding plan (legacy, order-based)."""
    order: int
    action: str
    description: str
    responsible_role: str = "agent"
    estimated_minutes: int = 15
    depends_on: List[int] = field(default_factory=list)
    is_optional: bool = False


@dataclass
class OnboardingPlan:
    """An ordered onboarding plan (legacy, title-based)."""
    title: str
    steps: List[OnboardingPlanStep] = field(default_factory=list)
    total_estimated_minutes: int = 0


# ═══════════════════════════════════════════════════════════════════════ #
# Legacy Planner — uses OnboardingPlanStep / OnboardingPlan internally.
# ═══════════════════════════════════════════════════════════════════════ #


class Planner:
    """Converts decisions into ordered plans (legacy onboarding)."""

    @staticmethod
    def create_onboarding_plan(entity_type: str) -> OnboardingPlan:
        """Create a plan for onboarding a new entity."""
        plans = {
            "lead": OnboardingPlan(
                title="New Lead Onboarding",
                steps=[
                    OnboardingPlanStep(1, "review", "Review lead details and requirements", estimated_minutes=5),
                    OnboardingPlanStep(2, "contact", "Contact customer within SLA", estimated_minutes=10),
                    OnboardingPlanStep(3, "discover", "Discovery call: understand needs and preferences", estimated_minutes=30),
                    OnboardingPlanStep(4, "proposal", "Prepare and send proposal", estimated_minutes=45),
                    OnboardingPlanStep(5, "followup", "Follow up on proposal", estimated_minutes=10),
                ],
                total_estimated_minutes=100,
            ),
            "patient": OnboardingPlan(
                title="New Patient Onboarding",
                steps=[
                    OnboardingPlanStep(1, "review", "Review patient intake form", estimated_minutes=5),
                    OnboardingPlanStep(2, "schedule", "Schedule initial consultation", estimated_minutes=10),
                    OnboardingPlanStep(3, "consult", "Conduct consultation", estimated_minutes=30),
                    OnboardingPlanStep(4, "plan", "Create treatment plan", estimated_minutes=20),
                ],
                total_estimated_minutes=65,
            ),
        }
        return plans.get(entity_type, OnboardingPlan(
            title="New Record Processing",
            steps=[
                OnboardingPlanStep(1, "review", "Review the record", estimated_minutes=5),
                OnboardingPlanStep(2, "action", "Take required action", estimated_minutes=15),
            ],
            total_estimated_minutes=20,
        ))

    @staticmethod
    def get_next_steps(entity: Entity) -> List[OnboardingPlanStep]:
        """Get the next incomplete steps for an entity."""
        plan = Planner.create_onboarding_plan(
            entity.definition.type if entity.definition else "default"
        )
        return plan.steps[:3]

    @staticmethod
    def estimate_completion(plan: OnboardingPlan, completed_steps: List[int]) -> dict:
        """Estimate time to completion based on remaining steps."""
        remaining = [s for s in plan.steps if s.order not in completed_steps]
        total_minutes = sum(s.estimated_minutes for s in remaining)
        return {
            "remaining_steps": len(remaining),
            "estimated_minutes": total_minutes,
            "estimated_hours": round(total_minutes / 60, 1),
        }


__all__ = [
    # New dependency-aware planner
    "SequentialPlanner",
    "DependencyGraph",
    "PlanStep",
    "Plan",
    # Legacy onboarding planner
    "Planner",
    "OnboardingPlanStep",
    "OnboardingPlan",
]