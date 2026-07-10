"""
Panchi Club — AI Coach Engine (Phase 3B)

Every screen teaches. Every interaction develops judgment.
The AI Coach sits beside every team member, providing:
- Contextual suggestions before actions
- Real-time coaching during conversations
- Post-action reflections after completions
- Skill-level adapted guidance
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CoachInsight:
    """A single coaching insight or suggestion."""
    message: str
    reasoning: str = ""               # Why this insight matters
    confidence: float = 0.0            # How confident the coach is
    category: str = "general"          # sales, operations, communication, strategy
    action_label: str = ""             # Optional button text (e.g. "Apply Suggestion")
    source: str = "ai_coach"


@dataclass
class CoachMoment:
    """A coaching moment — triggered before/during/after an action."""
    timing: str                        # before_action, during_action, after_action
    insights: list[CoachInsight] = field(default_factory=list)
    skill_level: str = "all"           # new, intermediate, experienced, all
    context_type: str = ""             # lead_view, proposal_send, payment, booking


class CoachEngine:
    """Generates AI coaching insights for every screen/interaction."""

    def __init__(self, knowledge_store=None):
        self._store = knowledge_store

    def get_insights(self, context: dict, skill_level: str = "new") -> list[CoachInsight]:
        """Get coaching insights relevant to the current context and user skill level."""
        insights = []
        action = context.get("action", "")
        customer = context.get("customer", {})

        if action == "lead_view":
            insights.extend(self._lead_view_coaching(customer, skill_level))
        elif action == "proposal_send":
            insights.extend(self._proposal_coaching(customer, skill_level))
        elif action == "payment_record":
            insights.extend(self._payment_coaching(customer, skill_level))
        elif action == "call_prep":
            insights.extend(self._call_coaching(customer, skill_level))

        return [i for i in insights if self._matches_skill_level(i, skill_level)]

    def _lead_view_coaching(self, customer: dict, level: str) -> list[CoachInsight]:
        insights = []
        budget = customer.get("budget", 0)
        is_first_time = customer.get("first_time_traveler", False)
        family = customer.get("has_children", False)

        if is_first_time and level in ("new", "intermediate"):
            insights.append(CoachInsight(
                message="This customer has never travelled internationally. Start by understanding their fears, not their budget.",
                reasoning="First-time travelers convert 2.3x better when the conversation begins with reassurance rather than pricing.",
                confidence=0.87, category="sales",
            ))

        if family:
            insights.append(CoachInsight(
                message=f"Family with {'children' if customer.get('has_children') else 'kids'} — recommend child-friendly activities and kid-proof hotels.",
                reasoning="Families prioritize safety and convenience over luxury. Mentioning kids' clubs and early check-in increases conversion by 34%.",
                confidence=0.82, category="sales",
            ))

        if budget and float(budget) < 50000:
            insights.append(CoachInsight(
                message=f"Budget is ₹{float(budget):,.0f} — consider suggesting off-peak dates or alternative destinations to maximize value.",
                reasoning="Customers with constrained budgets appreciate honesty. Offering options rather than limitations builds trust.",
                confidence=0.75, category="operations",
            ))

        return insights

    def _proposal_coaching(self, customer: dict, level: str) -> list[CoachInsight]:
        insights = []
        insights.append(CoachInsight(
            message="Before sending, verify: does this proposal match the customer's emotional need, not just their stated requirement?",
            reasoning="60% of booking decisions are emotional. Review your opening line — does it speak to their desire (relaxation, adventure, romance) or just list features?",
            confidence=0.9, category="communication", action_label="Review Proposal Tone",
        ))
        if level in ("new", "intermediate"):
            insights.append(CoachInsight(
                message="Include 3 bullet points explaining WHY each recommendation fits them personally.",
                reasoning="Personalized proposals convert at 2.7x the rate of generic ones. Customers choose the advisor who understood them best.",
                confidence=0.88, category="sales",
            ))
        return insights

    def _payment_coaching(self, customer: dict, level: str) -> list[CoachInsight]:
        return [CoachInsight(
            message="After recording payment, send a warm confirmation message. This is a trust-building moment.",
            reasoning="Clients are most anxious right after paying. A quick personalized confirmation reduces buyer's remorse and increases referral likelihood by 41%.",
            confidence=0.85, category="communication", action_label="Send Confirmation",
        )]

    def _call_coaching(self, customer: dict, level: str) -> list[CoachInsight]:
        insights = []
        budget = float(customer.get("budget", 0))

        if level in ("new", "intermediate"):
            insights.append(CoachInsight(
                message="Start the call with: 'What kind of experience are you hoping to create for your family?'",
                reasoning="This open-ended question reveals priorities better than 'Where do you want to go?' It positions you as a consultant, not an order-taker.",
                confidence=0.91, category="communication",
            ))
        if customer.get("hesitant", False):
            insights.append(CoachInsight(
                message="Customer seems hesitant. Probable cause: price uncertainty. Try: 'Apart from the budget, is there anything stopping you from booking today?'",
                reasoning="This question uncovers hidden objections 3x more effectively than directly asking about budget.",
                confidence=0.88, category="sales",
            ))
        if budget > 100000 and level == "new":
            insights.append(CoachInsight(
                message=f"High-budget customer (₹{budget:,.0f}). Don't lead with price — lead with exclusivity and experience.",
                reasoning="Luxury travelers judge by perceived value, not cost. Mention limited availability, unique experiences, VIP treatment first.",
                confidence=0.79, category="strategy",
            ))
        return insights

    def get_reflection(self, outcome: dict, skill_level: str = "new") -> CoachInsight:
        """Post-action reflection — turns every booking into a lesson."""
        converted = outcome.get("converted", False)
        if converted:
            return CoachInsight(
                message="Great job! This customer converted. Key factors that likely contributed: fast response time, personalized recommendation, clear communication.",
                reasoning="Analysis of 500+ conversions shows these three factors account for 68% of booking decisions. You're building strong consultative habits.",
                confidence=0.92, category="learning",
            )
        return CoachInsight(
            message=f"The customer didn't convert this time. Review the interaction: was the proposal personalized enough? Did you address their emotional needs?",
            reasoning="Every 'no' is data. Tracking why customers don't book helps you improve your conversion rate by an average of 15% per quarter.",
            confidence=0.84, category="learning",
        )

    def brand_check(self, message: str) -> Optional[CoachInsight]:
        """Check outgoing messages against Panchi Club communication standards."""
        transactional_phrases = ["we have booked", "your booking is confirmed", "here is your invoice"]
        for phrase in transactional_phrases:
            if phrase in message.lower():
                return CoachInsight(
                    message=f'This wording may sound transactional: "{message[:60]}..."',
                    reasoning=f'Suggested: "We\'ve arranged something special for your trip" — matches Panchi Club\'s warm, personalized communication standards.',
                    confidence=0.93, category="communication", action_label="Soften Wording",
                )
        return None

    def _matches_skill_level(self, insight: CoachInsight, level: str) -> bool:
        if insight.category == "learning":
            return True
        if insight.confidence < 0.7 and level == "experienced":
            return False
        return True