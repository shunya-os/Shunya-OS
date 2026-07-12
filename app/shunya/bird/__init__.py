"""Bird — Shunya's AI Assistant interaction layer.

Bird is the assistant through which Shunya's intelligence becomes approachable.
It should feel caring, precise, context-aware, and grounded in company knowledge.

Interaction pattern: understand → clarify → explain → recommend → guide → act

This module uses db.session.query(Model) — never Model.query.
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import or_
from app import db
from app.models import Entity, EntityDefinition, KnowledgeEntry, Relationship, Opportunity, ActivityLog, LearningCandidate
from app.shunya.foundation import Result, NextAction, Priority
from app.shunya.next_best_action import NextBestActionEngine


class Bird:
    """The AI Assistant interface — routes intent to the right Shunya layer."""

    def __init__(self, tenant_id: int, user_id: int, user_role: str = "agent",
                 user_name: str = ""):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.user_role = user_role
        self.user_name = user_name

    # ------------------------------------------------------------------ #
    # Greeting
    # ------------------------------------------------------------------ #

    def greet(self) -> dict:
        """Personalized greeting with time-of-day AND relationship context."""
        hour = datetime.utcnow().hour

        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        # Real counts from DB
        ctx = self.get_user_context(self.tenant_id, self.user_id)

        # Build a contextual message
        parts = []
        if ctx["total_open"] > 0:
            parts.append(f"You have {ctx['total_open']} open item{'s' if ctx['total_open'] != 1 else ''}")
        if ctx["overdue_count"] > 0:
            parts.append(f"{ctx['overdue_count']} overdue")
        if ctx["recent_activity_count"] > 0:
            parts.append(f"{ctx['recent_activity_count']} recent update{'s' if ctx['recent_activity_count'] != 1 else ''}")

        if parts:
            message = " | ".join(parts)
        else:
            message = "Ready to make today productive?"

        return {
            "greeting": f"{greeting}, {self.user_name}!",
            "icon": "🧠",
            "message": message,
            "context": ctx,
            "suggestions": self._quick_suggestions(),
        }

    def _quick_suggestions(self) -> list:
        """Quick action suggestions for the greeting."""
        suggestions = []
        defs = db.session.query(EntityDefinition).filter_by(
            tenant_id=self.tenant_id, is_active=True
        ).limit(4).all()
        for d in defs:
            count = db.session.query(Entity).filter_by(
                tenant_id=self.tenant_id, definition_id=d.id, is_archived=False
            ).count()
            suggestion = f"Review {d.label_plural or d.label} ({count})"
            suggestions.append({
                "icon": d.icon,
                "text": suggestion,
                "action": f"/entities/{d.type}",
            })
        return suggestions

    # ------------------------------------------------------------------ #
    # Query Engine
    # ------------------------------------------------------------------ #

    def handle_query(self, query: str) -> dict:
        """Process a natural language query through the Shunya layers.

        Searches entities, knowledge base, relationships, and returns
        real data counts and summaries — never a 'needs_web_search' stub.
        """
        q = query.lower().strip()

        # --- Detect intent ---
        show_patterns = ["show me", "list", "find", "get", "display", "view", "what"]
        count_patterns = ["how many", "count of", "total", "number of"]
        search_patterns = ["search for", "look for", "find", "do we have", "tell me about"]

        is_show = any(p in q for p in show_patterns)
        is_count = any(p in q for p in count_patterns)
        is_search = any(p in q for p in search_patterns)

        # --- Entity type keywords ---
        entity_keywords = ["lead", "ticket", "invoice", "booking", "order",
                           "patient", "student", "client", "customer", "deal",
                           "opportunity", "project", "task", "contact", "supplier"]

        matched_type = None
        for kw in entity_keywords:
            if kw in q:
                matched_type = kw
                break

        # Try to match an actual EntityDefinition label/type
        if not matched_type:
            defs = db.session.query(EntityDefinition).filter_by(
                tenant_id=self.tenant_id, is_active=True
            ).all()
            for d in defs:
                if d.type in q or d.label.lower() in q:
                    matched_type = d.type
                    break

        # 1. COUNT queries
        if is_count:
            if matched_type:
                definition = db.session.query(EntityDefinition).filter_by(
                    tenant_id=self.tenant_id, type=matched_type, is_active=True
                ).first()
                if definition:
                    count = db.session.query(Entity).filter_by(
                        tenant_id=self.tenant_id, definition_id=definition.id,
                        is_archived=False
                    ).count()
                    return {
                        "query": query,
                        "response": f"I found **{count}** {definition.label_plural or definition.label}.",
                        "response_type": "count",
                        "count": count,
                        "entity_type": matched_type,
                        "label": definition.label,
                        "verification_badge": "data" if count > 0 else "empty",
                    }
            # Count everything
            counts = self._count_by_type(self.tenant_id)
            if counts:
                lines = [f"**{c['label']}**: {c['count']}" for c in counts[:8]]
                return {
                    "query": query,
                    "response": "Here's what I found:\n" + "\n".join(lines),
                    "response_type": "counts",
                    "counts": counts,
                    "verification_badge": "data",
                }

        # 2. SHOW / LIST queries
        if is_show and matched_type:
            results = self._search_entities_by_type(matched_type, self.tenant_id)
            if results:
                lines = []
                for r in results[:5]:
                    label = r["display_name"]
                    status = r.get("status", "")
                    status_tag = f" [{status}]" if status else ""
                    lines.append(f"• **{label}**{status_tag}")
                return {
                    "query": query,
                    "response": f"I found {len(results)} record{'s' if len(results) != 1 else ''}:\n" + "\n".join(lines),
                    "response_type": "list",
                    "results": results[:5],
                    "total": len(results),
                    "entity_type": matched_type,
                    "verification_badge": "data",
                }

        # 3. SEARCH queries — search entities + knowledge
        if is_search or not matched_type:
            entities = self._search_entities(q, self.tenant_id)
            knowledge = self._search_knowledge(q, self.tenant_id)

            response_parts = []
            if knowledge:
                response_parts.append("📚 **From Knowledge Base**")
                for k in knowledge[:3]:
                    response_parts.append(f"• {k['question']} → {k['answer'][:200]}")

            if entities:
                response_parts.append(f"\n📋 **Matching Records** ({len(entities)} found)")
                for e in entities[:5]:
                    response_parts.append(f"• {e['display_name']} ({e.get('entity_type', 'record')})")

            if response_parts:
                return {
                    "query": query,
                    "response": "\n".join(response_parts),
                    "response_type": "search_results",
                    "entities_found": len(entities),
                    "knowledge_found": len(knowledge),
                    "verification_badge": "data" if entities or knowledge else "no_results",
                }

        # 4. Relationship queries
        if "relationship" in q or "customer" in q or "client" in q:
            rels = db.session.query(Relationship).filter_by(
                tenant_id=self.tenant_id
            ).order_by(Relationship.created_at.desc()).limit(5).all()
            if rels:
                lines = [f"• {r.display_name} (health: {r.health})" for r in rels]
                return {
                    "query": query,
                    "response": f"I found {len(rels)} relationship{'s' if len(rels) != 1 else ''}:\n" + "\n".join(lines),
                    "response_type": "relationships",
                    "results": [r.to_dict() for r in rels],
                    "verification_badge": "data",
                }

        # 5. Fallback — count everything
        counts = self._count_by_type(self.tenant_id)
        if counts:
            lines = [f"**{c['label']}**: {c['count']}" for c in counts[:8]]
            return {
                "query": query,
                "response": "I searched but couldn't match your query exactly. Here's a summary:\n" + "\n".join(lines),
                "response_type": "fallback_counts",
                "counts": counts,
                "verification_badge": "data",
            }

        return {
            "query": query,
            "response": "I searched your data but couldn't find matching records. Try asking differently, or upload a document on the **Ingest** page and I'll learn from it.",
            "response_type": "empty",
            "verification_badge": "no_results",
        }

    # ------------------------------------------------------------------ #
    # Internal Search Helpers
    # ------------------------------------------------------------------ #

    def _search_entities(self, query: str, tenant_id: int) -> list:
        """Search all Entity records by matching query against data JSONB fields using ilike.

        Returns top 5 matches.
        """
        results = []
        defs = db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, is_active=True
        ).all()

        for d in defs:
            searchable = d.searchable_fields or []
            if not searchable:
                # Fall back to schema field names
                searchable = [f.get("name", "") for f in (d.schema or []) if f.get("name")]

            filters = []
            for field_name in searchable:
                if field_name in ("name", "title", "description", "email", "phone", "notes", "address"):
                    filters.append(
                        Entity.data[field_name].as_string().ilike(f"%{query}%")
                    )

            if not filters:
                continue

            entities = db.session.query(Entity).filter(
                Entity.tenant_id == tenant_id,
                Entity.definition_id == d.id,
                Entity.is_archived == False,
                or_(*filters)
            ).order_by(Entity.created_at.desc()).limit(5).all()

            for e in entities:
                results.append({
                    "id": e.id,
                    "code": e.code,
                    "display_name": e.display_name,
                    "entity_type": d.label,
                    "entity_type_slug": d.type,
                    "status": e.status,
                    "data": {k: v for k, v in e.data.items() if k in searchable},
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                })

        return results[:5]

    def _search_entities_by_type(self, entity_type: str, tenant_id: int) -> list:
        """Search entities by their type."""
        results = []
        definition = db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type=entity_type, is_active=True
        ).first()
        if not definition:
            # Try partial match
            definition = db.session.query(EntityDefinition).filter(
                EntityDefinition.tenant_id == tenant_id,
                EntityDefinition.is_active == True,
                EntityDefinition.type.ilike(f"%{entity_type}%")
            ).first()
        if not definition:
            return []

        entities = db.session.query(Entity).filter_by(
            tenant_id=tenant_id, definition_id=definition.id, is_archived=False
        ).order_by(Entity.created_at.desc()).limit(20).all()

        for e in entities:
            results.append({
                "id": e.id,
                "code": e.code,
                "display_name": e.display_name,
                "status": e.status,
                "data": e.data,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            })
        return results

    def _search_knowledge(self, query: str, tenant_id: int) -> list:
        """Search KnowledgeEntry by question/answer similarities."""
        entries = db.session.query(KnowledgeEntry).filter(
            KnowledgeEntry.tenant_id == tenant_id,
            or_(
                KnowledgeEntry.question.ilike(f"%{query}%"),
                KnowledgeEntry.answer.ilike(f"%{query}%"),
            )
        ).order_by(KnowledgeEntry.use_count.desc()).limit(5).all()

        return [{
            "id": e.id,
            "question": e.question,
            "answer": e.answer[:300],
            "source": e.source,
            "confidence": e.confidence,
        } for e in entries]

    def _count_by_type(self, tenant_id: int) -> list:
        """Return counts per entity type for 'show me everything' type queries."""
        counts = []
        defs = db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, is_active=True
        ).all()
        for d in defs:
            count = db.session.query(Entity).filter_by(
                tenant_id=tenant_id, definition_id=d.id, is_archived=False
            ).count()
            if count > 0:
                counts.append({
                    "type": d.type,
                    "label": d.label_plural or d.label,
                    "icon": d.icon,
                    "count": count,
                })

        # Sort by count descending
        counts.sort(key=lambda x: x["count"], reverse=True)
        return counts

    # ------------------------------------------------------------------ #
    # Next Action Advisory
    # ------------------------------------------------------------------ #

    def suggest_next_action(self) -> dict:
        """Return real advisory context from the NextBestActionEngine."""
        nba = NextBestActionEngine.get_for_user(
            self.tenant_id, self.user_id, self.user_role
        )
        return {
            "next_actions": [{
                "title": a.title,
                "description": a.description,
                "action_type": a.action_type,
                "target_url": a.target_url,
                "priority": a.priority.value,
                "reason": a.reason,
                "expected_outcome": a.expected_outcome,
            } for a in (nba or [])[:5]],
            "total_actions": len(nba) if nba else 0,
        }

    # ------------------------------------------------------------------ #
    # User Context
    # ------------------------------------------------------------------ #

    def get_user_context(self, tenant_id: int, user_id: int) -> dict:
        """Return open counts across types, overdue items, recent activity count."""
        from app.models import ActivityLog

        now = datetime.utcnow()
        three_days_ago = now - timedelta(days=3)
        seven_days_ago = now - timedelta(days=7)

        # Open entities
        open_count = db.session.query(Entity).filter(
            Entity.tenant_id == tenant_id,
            Entity.is_archived == False,
            Entity.status.in_(["new", "pending", "open", "active", "in_progress"])
        ).count()

        # Overdue items (status = pending/new, created > 5 days ago)
        overdue = db.session.query(Entity).filter(
            Entity.tenant_id == tenant_id,
            Entity.is_archived == False,
            Entity.status.in_(["new", "pending"]),
            Entity.created_at < seven_days_ago,
        ).count()

        # Recent activity
        recent = db.session.query(ActivityLog).filter(
            ActivityLog.tenant_id == tenant_id,
            ActivityLog.created_at >= three_days_ago,
        ).count()

        # Open opportunities
        opp_count = db.session.query(Opportunity).filter(
            Opportunity.tenant_id == tenant_id,
            Opportunity.status == "open"
        ).count()

        return {
            "total_open": open_count + opp_count,
            "entities_open": open_count,
            "opportunities_open": opp_count,
            "overdue_count": overdue,
            "recent_activity_count": recent,
        }

    # ------------------------------------------------------------------ #
    # Explanation & Formatting
    # ------------------------------------------------------------------ #

    def explain(self, action: str, details: dict) -> dict:
        """Explain a recommendation with trade-offs and reasoning."""
        return {
            "observation": details.get("observation", ""),
            "trade_offs": details.get("trade_offs", []),
            "recommendation": details.get("recommendation", ""),
            "reason": details.get("reason", ""),
            "next_action": details.get("next_action", ""),
            "confidence": details.get("confidence", 0.5),
        }

    def format_message(self, template: str, **kwargs) -> str:
        """Format a message following the Bird interaction pattern."""
        templates = {
            "attention": (
                "🧠 **{title}**\n\n"
                "What I see: {observation}\n"
                "Why it matters: {reason}\n"
                "What I recommend: {recommendation}\n"
                "Next step: {next_action}"
            ),
            "correction": (
                "📝 Noted! I've updated my understanding.\n\n"
                "{detail}\n\n"
                "I'll get this right going forward."
            ),
            "decision": (
                "✅ **{title}**\n\n"
                "Here's what I did:\n{summary}\n\n"
                "What happens next: {next_step}\n"
                "Anything else?"
            ),
        }
        formatter = templates.get(template, templates["attention"])
        return formatter.format(**kwargs)

    # ------------------------------------------------------------------ #
    # Memory Compounding — Learn from Past Outcomes (D7)
    # ------------------------------------------------------------------ #

    def learn_from_outcome(self, outcome_id: int, entity_type: str,
                           action_taken: str, result: str, rating: int) -> dict:
        """Learn from an outcome by storing it as a learning candidate.

        Queries ActivityLog for that outcome.
        If rating >= 4: marks this action as 'confirmed good'
        If rating <= 2: marks this action as 'avoid repeating'
        """
        # Query the ActivityLog for this outcome
        activity = db.session.query(ActivityLog).filter_by(
            id=outcome_id, tenant_id=self.tenant_id
        ).first()

        # Build evidence from the activity if found
        evidence = []
        if activity:
            evidence.append({
                "activity_id": activity.id,
                "action": activity.action,
                "detail": (activity.detail or "")[:500],
                "metadata": activity.metadata_json or {},
                "timestamp": activity.created_at.isoformat() if activity.created_at else None,
            })

        # Determine status based on rating
        if rating >= 4:
            status = "confirmed_good"
        elif rating <= 2:
            status = "avoid_repeating"
        else:
            status = "neutral"

        # Create the learning candidate
        candidate = LearningCandidate(
            tenant_id=self.tenant_id,
            pattern=f"outcome:{entity_type}:{action_taken}",
            evidence=evidence,
            confidence=rating / 5.0,
            category="outcome",
            status=status,
            related_outcomes=[outcome_id] if outcome_id else [],
            source_observations=[{
                "entity_type": entity_type,
                "action_taken": action_taken,
                "result": result,
                "rating": rating,
            }],
        )
        db.session.add(candidate)
        db.session.commit()

        return {
            "id": candidate.id,
            "pattern": candidate.pattern,
            "confidence": candidate.confidence,
            "status": candidate.status,
            "timestamp": candidate.created_at.isoformat() if candidate.created_at else None,
        }

    def get_learned_preferences(self, entity_type: str = None) -> list:
        """Return learned patterns from learning candidates.

        Returns list of dicts: {action, confidence, evidence_count, last_applied, trend}
        Sorts by confidence descending.
        If entity_type is None, returns all.
        """
        query = db.session.query(LearningCandidate).filter(
            LearningCandidate.tenant_id == self.tenant_id,
            LearningCandidate.category == "outcome",
        )

        if entity_type:
            query = query.filter(
                LearningCandidate.pattern.ilike(f"outcome:{entity_type}:%")
            )

        candidates = query.order_by(LearningCandidate.confidence.desc()).all()

        results = []
        for c in candidates:
            # Parse pattern to extract action
            pattern_parts = c.pattern.split(":", 2)
            action = pattern_parts[2] if len(pattern_parts) > 2 else c.pattern

            # Determine trend based on status
            if c.status == "confirmed_good":
                trend = "positive"
            elif c.status == "avoid_repeating":
                trend = "negative"
            else:
                trend = "neutral"

            results.append({
                "action": action,
                "confidence": c.confidence,
                "evidence_count": len(c.evidence or []),
                "last_applied": c.updated_at.isoformat() if c.updated_at else None,
                "trend": trend,
                "pattern": c.pattern,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })

        return results

    def adjust_suggestion(self, suggestion: dict, entity_type: str) -> dict:
        """Adjust a suggestion based on learned preferences.

        Checks if a similar action was tried before.
        If yes, adjusts confidence and adds context:
        'Last time we did X, the outcome was Y'
        Returns adjusted suggestion with learned_context field.
        """
        action = suggestion.get("action", "")
        if not action:
            suggestion["learned_context"] = None
            return suggestion

        # Find similar past outcomes
        preferences = self.get_learned_preferences(entity_type)
        similar = [p for p in preferences if p["action"] == action]

        learned_context = None
        adjusted_confidence = suggestion.get("confidence", 0.5)

        if similar:
            best = similar[0]  # Already sorted by confidence desc
            if best["trend"] == "positive":
                adjusted_confidence = min(1.0, adjusted_confidence + 0.15)
                learned_context = (
                    f"Last time we did '{action}', the outcome was positive "
                    f"(confidence: {best['confidence']:.1f}, "
                    f"evidence: {best['evidence_count']} time(s))"
                )
            elif best["trend"] == "negative":
                adjusted_confidence = max(0.1, adjusted_confidence - 0.25)
                learned_context = (
                    f"⚠️ Last time we tried '{action}', the outcome was unfavorable "
                    f"(confidence: {best['confidence']:.1f}). "
                    f"Consider a different approach."
                )

        if not learned_context:
            # No prior experience with this action on this entity type
            learned_context = f"No prior experience with '{action}' on {entity_type}."

        suggestion["confidence"] = round(adjusted_confidence, 2)
        suggestion["learned_context"] = learned_context
        return suggestion