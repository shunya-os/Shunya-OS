"""
Shunya — Interface Layer (Phase 2)

Unified multi-channel abstraction. Routes incoming requests from any channel
(WhatsApp, Telegram, Web) through the Shunya pipeline.
Every request gets the same treatment: Knowledge → Reasoning → Planner → Governance → Executor → Observer.
"""

from datetime import datetime
from typing import Optional
from .knowledge import KnowledgeLayer
from ._legacy_reasoning import ReasoningLayer
from .planner import PlannerLayer
from .governance import GovernanceLayer
from .executor import ExecutorLayer, OutboundMessage, ChannelType, MessageType
from .observer_learning import ObserverLayer, LearningLayer


class ShunyaInterface:
    """
    Unified entry point for all channels.

    Inbound:  Channel → Interface → Knowledge → Reasoning → Planner → Governance → Executor → Observer
    Outbound: Interface → Executor → any channel
    """

    def __init__(self, db_session=None, knowledge_store=None):
        self.knowledge = KnowledgeLayer(db_session)
        self.reasoning = ReasoningLayer(self.knowledge, knowledge_store)
        self.planner = PlannerLayer()
        self.governance = GovernanceLayer()
        self.executor = ExecutorLayer()
        self.observer = ObserverLayer(db_session)
        self.learning = LearningLayer(self.observer, knowledge_store, db_session)
        self._db = db_session
        self._store = knowledge_store
        self._results: list[dict] = []

    def process_message(self, text: str, channel: str = "whatsapp",
                        sender: str = "", lead_id: Optional[int] = None,
                        customer_name: str = "") -> dict:
        """Process an incoming message through the full Shunya pipeline."""
        # Parse inquiry
        from app.services import parse_inquiry_text, _cached_or_new_code
        parsed = parse_inquiry_text(text)

        inquiry = {
            "customer_name": customer_name or parsed.get("name") or sender[:20],
            "destination": parsed.get("destination", ""),
            "pax": f"{parsed.get('adults') or 0} adults" if parsed.get("adults") else "",
            "dates": parsed.get("dates", ""),
            "notes": text,
            "phone": sender,
            "source": channel,
            "budget": parsed.get("budget", 0),
        }

        # Run full pipeline
        profile = self.reasoning.analyze_inquiry(inquiry)
        strategy = self.reasoning.suggest_approach(profile)
        plan = self.planner.create_itinerary(profile, strategy)
        proposal = self.planner.generate_proposal_text(plan)

        # Governance check
        gov = self.governance.validate_plan(plan.to_dict(), {
            "destination": inquiry["destination"],
            "budget": inquiry.get("budget", ""),
            "pax": inquiry.get("pax", ""),
            "dates": inquiry.get("dates", ""),
            "domain": "travel",
            "notes": text,
        })

        result = {
            "success": gov.approved,
            "confidence": profile.reasoning_result.confidence,
            "destination": inquiry["destination"],
            "occasion": profile.occasion,
            "group_type": profile.group_type,
            "proposal": proposal if gov.approved else "Blocked by governance",
            "governance": gov.to_dict(),
            "reasoning": profile.reasoning_result.to_dict(),
            "channel": channel,
            "sender": sender,
        }

        # Auto-reply via executor
        if gov.approved:
            reply = f"✈️ *{profile.occasion.title()} Trip to {inquiry['destination']}*\n\n"
            reply += f"👥 {profile.group_type.title()} · 📅 {inquiry['dates'] or 'TBD'}\n"
            reply += f"💰 Est. ₹{plan.total_estimated_cost:,.0f}\n\n"
            reply += f"*Day 1:* {plan.days[0].title if plan.days else 'Arrival'}\n"
            reply += f"*Day 2:* {plan.days[1].title if len(plan.days) > 1 else 'Explore'}\n"
            if len(plan.days) > 2:
                reply += f"*Day 3:* {plan.days[2].title if len(plan.days) > 2 else 'Departure'}\n"

            channel_type = ChannelType.WHATSAPP if channel == "whatsapp" else ChannelType.TELEGRAM
            delivery = self.executor.send(OutboundMessage(
                channel=channel_type, recipient=sender, text=reply,
            ))

            # Observe
            self.observer.observe(
                "proposal_sent", f"Inquiry processed: {inquiry['destination']}",
                lead_id=lead_id, channel=channel, success=delivery.success,
                metadata={"confidence": profile.reasoning_result.confidence}
            )

        result["delivery"] = delivery.to_dict() if gov.approved else None
        self._results.append(result)
        return result

    def pipeline_stats(self) -> dict:
        return {
            "total_processed": len(self._results),
            "governance": self.governance.stats,
            "executor": self.executor.stats,
            "observer": self.observer.stats(),
        }