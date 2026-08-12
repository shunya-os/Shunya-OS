"""FDA18 — Contextual AI Copilot.

SHUNYA's copilot understands the currently viewed object and answers
contextual questions. It follows the company-first data hierarchy:

1. Query company data/canonical state first
2. Use memory/context second where authoritative
3. Use internet/provider data only when company data is insufficient
4. Never fabricate missing information. Return UNKNOWN where truth
   cannot be established.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def answer_contextual(
    query: str,
    object_type: str,
    object_id: str,
    relationship_id: Optional[int],
    tenant_id: int,
) -> Dict[str, Any]:
    """Answer a contextual question about the current object.

    Returns a structured answer with reason, evidence, confidence, and
    recommended actions.
    """
    query_lower = query.lower().strip()

    # 1. Determine intent from the question
    intent = _classify_intent(query_lower)

    # 2. Gather context from canonical data sources
    context = _gather_context(object_type, object_id, relationship_id, tenant_id)

    # 3. Answer based on intent + context
    answer = _answer_by_intent(intent, query, context, object_type, object_id, tenant_id)

    return answer


def _classify_intent(query: str) -> str:
    """Classify the user's question intent."""
    intents = {
        "what_is_happening": [
            "what is happening", "what's happening", "what happened",
            "what's going on", "what is going on", "status", "update",
        ],
        "what_was_promised": [
            "what did we promise", "what was promised", "commitments",
            "what do we owe", "what is outstanding",
        ],
        "what_is_overdue": [
            "overdue", "past due", "late", "what is late", "what's overdue",
            "what is delayed",
        ],
        "what_should_i_do": [
            "what should i do", "next action", "what next", "what's next",
            "recommend", "suggest", "what is the next step",
        ],
        "why_stalled": [
            "why stalled", "why is this stalled", "why stuck", "why blocked",
            "what is blocking", "what's blocking",
        ],
        "show_evidence": [
            "show me the evidence", "what evidence", "evidence",
            "prove it", "how do you know",
        ],
        "draft_communication": [
            "draft", "write", "compose", "draft email", "draft message",
            "create communication",
        ],
        "who_is_involved": [
            "who is involved", "who is this", "who are they",
            "tell me about", "who",
        ],
        "what_changed": [
            "what changed", "what's changed", "what changed since",
            "recent changes", "what is new",
        ],
    }

    for intent, patterns in intents.items():
        for pattern in patterns:
            if pattern in query:
                return intent

    return "general_question"


def _gather_context(
    object_type: str,
    object_id: str,
    relationship_id: Optional[int],
    tenant_id: int,
) -> Dict[str, Any]:
    """Gather context about the current object for the copilot."""
    from app.workspace_objects.service import get_unified_workspace
    workspace = get_unified_workspace(object_id, object_type, tenant_id)
    return workspace


def _answer_by_intent(
    intent: str,
    query: str,
    context: Dict[str, Any],
    object_type: str,
    object_id: str,
    tenant_id: int,
) -> Dict[str, Any]:
    """Answer based on classified intent."""
    if intent == "what_is_happening":
        return _answer_what_is_happening(context, object_type)
    elif intent == "what_was_promised":
        return _answer_what_was_promised(context)
    elif intent == "what_is_overdue":
        return _answer_what_is_overdue(context)
    elif intent == "what_should_i_do":
        return _answer_what_should_i_do(context, object_type)
    elif intent == "why_stalled":
        return _answer_why_stalled(context)
    elif intent == "show_evidence":
        return _answer_show_evidence(context)
    elif intent == "draft_communication":
        return _answer_draft_communication(context, query)
    elif intent == "who_is_involved":
        return _answer_who_is_involved(context, object_type)
    elif intent == "what_changed":
        return _answer_what_changed(context)
    else:
        return _answer_general(query, context)


def _answer_what_is_happening(
    context: Dict[str, Any],
    object_type: str,
) -> Dict[str, Any]:
    """Answer: What is happening with this object?"""
    identity = context.get("identity", {})
    ctx = context.get("context", {})
    commitments = context.get("commitments", [])
    timeline = context.get("timeline", [])
    intelligence = context.get("intelligence", {})

    summary_parts = []

    # Identity
    name = identity.get("name") or ctx.get("customer_name") or ctx.get("display_name") or "Unknown"
    status = identity.get("status") or ctx.get("status") or "unknown"
    summary_parts.append(f"**{name}** — Status: **{status}**")

    # Object-type specific
    if object_type == "lead":
        source = ctx.get("source", "unknown")
        stage = ctx.get("stage", "new")
        budget = ctx.get("budget", 0)
        summary_parts.append(f"Source: {source}, Stage: {stage}, Budget: ₹{budget}")

    elif object_type in ("customer", "relationship"):
        rel_type = ctx.get("relationship_type", "customer")
        email = ctx.get("email", "")
        company = ctx.get("company_name", "")
        summary_parts.append(f"Type: {rel_type}")
        if company:
            summary_parts.append(f"Company: {company}")
        if email:
            summary_parts.append(f"Email: {email}")

    # Active commitments
    active = [c for c in commitments if c.get("status") in ("pending", "in_progress")]
    if active:
        summary_parts.append(f"\n**Active commitments ({len(active)}):**")
        for c in active[:5]:
            due = f" due {c.get('due_at', '')[:10]}" if c.get("due_at") else ""
            summary_parts.append(f"- {c['title']} ({c['status']}{due})")
    else:
        summary_parts.append("\nNo active commitments.")

    # Recent timeline
    recent = timeline[:3]
    if recent:
        summary_parts.append(f"\n**Recent activity:**")
        for e in recent:
            summary_parts.append(f"- {e.get('title', '')} ({e.get('time', '')[:10] if e.get('time') else ''})")

    # Intelligence
    if intelligence:
        health = intelligence.get("health_score", 50)
        risk = intelligence.get("retention_risk", 50)
        summary_parts.append(f"\n**Health: {health}/100** | Retention Risk: {risk}/100")

    answer = "\n".join(summary_parts)

    return {
        "answer": answer,
        "reason": "Compiled from canonical identity, commitments, timeline, and intelligence data.",
        "evidence": "identity, commitments, timeline, intelligence",
        "confidence": "high" if context.get("identity") else "medium",
        "authority": "canonical_data",
        "expected_action": "Review the details above and take appropriate action.",
        "execution_authorized": False,
        "intent": "what_is_happening",
    }


def _answer_what_was_promised(context: Dict[str, Any]) -> Dict[str, Any]:
    """Answer: What did we promise this customer/relationship?"""
    commitments = context.get("commitments", [])
    ctx = context.get("context", {})

    if not commitments:
        return {
            "answer": "No commitments found for this relationship.",
            "reason": "Queried commitments table — no records found.",
            "evidence": "commitments",
            "confidence": "high",
            "authority": "canonical_data",
            "expected_action": "Create a new commitment if one is needed.",
            "execution_authorized": False,
            "intent": "what_was_promised",
        }

    lines = [f"**{len(commitments)} commitment(s) found:**"]
    for c in commitments:
        status = c.get("status", "unknown")
        due = f" (due: {c.get('due_at', '')[:10]})" if c.get("due_at") else ""
        owner = f" — Owner: {c['owner']}" if c.get("owner") else ""
        lines.append(f"- {c['title']} [{status}]{due}{owner}")

    return {
        "answer": "\n".join(lines),
        "reason": "Queried commitments table linked to this relationship.",
        "evidence": "commitments",
        "confidence": "high",
        "authority": "canonical_data",
        "expected_action": "Review commitments and follow up on pending items.",
        "execution_authorized": False,
        "intent": "what_was_promised",
    }


def _safe_parse_due(due_str: str):
    """Safely parse a due date string to timezone-aware UTC datetime."""
    from datetime import datetime, timezone
    if not due_str:
        return None
    try:
        ds = due_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ds)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError):
        return None


def _answer_what_is_overdue(context: Dict[str, Any]) -> Dict[str, Any]:
    """Answer: What is overdue?"""
    from datetime import datetime, timezone

    commitments = context.get("commitments", [])
    overdue = []
    now = datetime.now(timezone.utc)
    for c in commitments:
        due = c.get("due_at")
        if due and c.get("status") in ("pending", "in_progress"):
            due_dt = _safe_parse_due(due)
            if due_dt and due_dt < now:
                days = (now - due_dt).days
                overdue.append({**c, "days_overdue": days})

    if not overdue:
        return {
            "answer": "Nothing is overdue.",
            "reason": "Checked all active commitments against current time.",
            "evidence": "commitments",
            "confidence": "high",
            "authority": "canonical_data",
            "expected_action": "No action required.",
            "execution_authorized": False,
            "intent": "what_is_overdue",
        }

    overdue.sort(key=lambda x: x["days_overdue"], reverse=True)
    lines = [f"**{len(overdue)} item(s) overdue:**"]
    for c in overdue:
        lines.append(
            f"- {c['title']} — {c['days_overdue']} day(s) overdue"
            f" (owner: {c.get('owner', 'unassigned')})"
        )

    return {
        "answer": "\n".join(lines),
        "reason": "Compared commitment due dates to current UTC time.",
        "evidence": "commitments with due dates",
        "confidence": "high",
        "authority": "canonical_data",
        "expected_action": "Follow up on overdue items.",
        "execution_authorized": False,
        "intent": "what_is_overdue",
    }


def _answer_what_should_i_do(
    context: Dict[str, Any],
    object_type: str,
) -> Dict[str, Any]:
    """Answer: What should I do next?"""
    ctx = context.get("context", {})
    commitments = context.get("commitments", [])
    actions = context.get("actions", [])
    intelligence = context.get("intelligence", {})

    recommendations = []

    # Check for overdue items
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    for c in commitments:
        due = c.get("due_at")
        if due and c.get("status") in ("pending", "in_progress"):
            due_dt = _safe_parse_due(due)
            if due_dt and due_dt < now:
                days = (now - due_dt).days
                recommendations.append({
                        "action": f"Follow up on overdue commitment: {c['title']}",
                        "reason": f"{days} day(s) overdue",
                        "urgency": "high",
                        "confidence": "high",
                    })

    # Check for stalled leads
    if object_type == "lead":
        status = ctx.get("status", "new")
        if status == "new":
            recommendations.append({
                "action": "Qualify this lead",
                "reason": "Lead is in new state — needs qualification",
                "urgency": "medium",
                "confidence": "high",
            })
        elif status == "in_progress":
            recommendations.append({
                "action": "Follow up and move toward conversion",
                "reason": "Lead is in progress",
                "urgency": "medium",
                "confidence": "high",
            })

    # Check for high retention risk
    if intelligence:
        risk = intelligence.get("retention_risk", 50)
        if risk > 70:
            recommendations.append({
                "action": "Prioritize retention — customer at risk",
                "reason": f"Retention risk score: {risk}/100",
                "urgency": "high",
                "confidence": "medium",
            })

    # Available actions from the workspace
    for a in actions:
        if a.get("type") == "transition":
            recommendations.append({
                "action": a.get("label", ""),
                "reason": "Available action for this object",
                "urgency": "medium",
                "confidence": "high",
            })

    if not recommendations:
        recommendations.append({
            "action": "Review the object details",
            "reason": "No urgent actions detected",
            "urgency": "low",
            "confidence": "high",
        })

    return {
        "answer": f"**{len(recommendations)} recommendation(s):**\n" + "\n".join(
            f"- {r['action']} ({r['reason']}) — urgency: {r['urgency']}"
            for r in recommendations[:5]
        ),
        "reason": "Analyzed commitments, overdue items, lead status, and object state.",
        "evidence": "commitments, lead status, intelligence, available actions",
        "confidence": "high",
        "authority": "deterministic_analysis",
        "expected_action": "Follow the highest urgency recommendation.",
        "execution_authorized": False,
        "intent": "what_should_i_do",
    }


def _answer_why_stalled(context: Dict[str, Any]) -> Dict[str, Any]:
    """Answer: Why is this lead/object stalled?"""
    from datetime import datetime, timezone
    ctx = context.get("context", {})
    timeline = context.get("timeline", [])
    commitments = context.get("commitments", [])

    reasons = []
    status = ctx.get("status", "unknown")

    # Check time since last activity
    if timeline:
        latest = timeline[0]
        latest_time = latest.get("time", "")
        try:
            if latest_time:
                dt = _safe_parse_due(latest_time)
                if dt:
                    days_since = (datetime.now(timezone.utc) - dt).days
                    if days_since > 7:
                        reasons.append(f"No activity for {days_since} days (last: {latest.get('title', '')})")
        except (ValueError, AttributeError):
            pass

    # Check for blocked commitments
    blocked = [c for c in commitments if c.get("status") == "blocked"]
    if blocked:
        reasons.append(f"{len(blocked)} commitment(s) are blocked")

    # Check for no commitments
    if not commitments:
        reasons.append("No commitments created — no active work tracked")

    # Status-specific
    if status == "new" and not timeline:
        reasons.append("Lead is new and has not been contacted yet")
    elif status == "on_hold":
        reasons.append("Object is on hold")

    if not reasons:
        reasons.append("No clear blocking factors identified")

    return {
        "answer": f"**Stall analysis:**\n" + "\n".join(f"- {r}" for r in reasons),
        "reason": "Analyzed timeline, commitments, and status for stall indicators.",
        "evidence": "timeline, commitments, status",
        "confidence": "high" if reasons else "medium",
        "authority": "deterministic_analysis",
        "expected_action": "Address the identified blocking factors.",
        "execution_authorized": False,
        "intent": "why_stalled",
    }


def _answer_show_evidence(context: Dict[str, Any]) -> Dict[str, Any]:
    """Answer: Show me the evidence."""
    evidence = context.get("evidence", [])
    timeline = context.get("timeline", [])
    commitments = context.get("commitments", [])

    items = []
    for e in evidence[:10]:
        items.append({
            "type": "evidence",
            "description": e.get("description", ""),
            "confidence": e.get("confidence", 0),
            "source": e.get("source", "unknown"),
        })
    for t in timeline[:10]:
        items.append({
            "type": "timeline",
            "description": t.get("title", ""),
            "time": t.get("time", ""),
            "source": t.get("source", "relationship_timeline"),
        })

    if not items:
        return {
            "answer": "No evidence records found for this object.",
            "reason": "Queried evidence and timeline tables — no records found.",
            "evidence": "evidence, timeline",
            "confidence": "high",
            "authority": "canonical_data",
            "expected_action": "No evidence to review.",
            "execution_authorized": False,
            "intent": "show_evidence",
        }

    answer_lines = [f"**{len(items)} evidence item(s) found:**"]
    for item in items[:10]:
        desc = item.get("description", "")[:100]
        if item["type"] == "evidence":
            answer_lines.append(f"- 📋 {desc} (confidence: {item.get('confidence', 0)})")
        else:
            answer_lines.append(f"- 📅 {desc} ({item.get('time', '')[:10]})")

    return {
        "answer": "\n".join(answer_lines),
        "reason": "Compiled evidence records and timeline entries.",
        "evidence": "evidence, timeline",
        "confidence": "high",
        "authority": "canonical_data",
        "expected_action": "Review the evidence above.",
        "execution_authorized": False,
        "intent": "show_evidence",
    }


def _answer_draft_communication(
    context: Dict[str, Any],
    query: str,
) -> Dict[str, Any]:
    """Answer: Draft a communication."""
    ctx = context.get("context", {})
    name = ctx.get("customer_name") or ctx.get("display_name") or "there"
    email = ctx.get("email", "")

    # Determine communication type from the query
    query_lower = query.lower()
    if "email" in query_lower:
        comm_type = "email"
        greeting = f"Dear {name},"
    elif "message" in query_lower or "text" in query_lower:
        comm_type = "message"
        greeting = f"Hi {name},"
    else:
        comm_type = "draft"
        greeting = f"Hello {name},"

    draft = f"{greeting}\n\n"
    draft += "I wanted to follow up regarding our recent conversation.\n\n"
    draft += "Please let me know if you have any questions.\n\n"
    draft += "Best regards"

    return {
        "answer": draft,
        "reason": f"Generated a {comm_type} draft for {name} based on the request.",
        "evidence": "relationship context, query intent",
        "confidence": "medium",
        "authority": "deterministic_generation",
        "expected_action": "Review and send the draft.",
        "execution_authorized": False,
        "intent": "draft_communication",
        "draft_type": comm_type,
        "recipient": name,
        "recipient_email": email,
    }


def _answer_who_is_involved(
    context: Dict[str, Any],
    object_type: str,
) -> Dict[str, Any]:
    """Answer: Who is involved?"""
    identity = context.get("identity", {})
    ctx = context.get("context", {})
    relationships = context.get("relationships", [])
    commitments = context.get("commitments", [])

    lines = []

    if object_type == "lead":
        name = ctx.get("customer_name") or "Unknown"
        phone = ctx.get("phone", "")
        email = ctx.get("email", "")
        assigned = ctx.get("assigned_to", "")
        lines.append(f"**Lead:** {name}")
        if phone:
            lines.append(f"Phone: {phone}")
        if email:
            lines.append(f"Email: {email}")
        if assigned:
            lines.append(f"Assigned to: {assigned}")

    elif object_type in ("customer", "relationship"):
        name = ctx.get("display_name") or "Unknown"
        company = ctx.get("company_name", "")
        email = ctx.get("email", "")
        phone = ctx.get("phone", "")
        owner = ctx.get("internal_owner", "")
        lines.append(f"**Contact:** {name}")
        if company:
            lines.append(f"Company: {company}")
        if email:
            lines.append(f"Email: {email}")
        if phone:
            lines.append(f"Phone: {phone}")
        if owner:
            lines.append(f"Internal owner: {owner}")

    # Commitment owners
    owners = set()
    for c in commitments:
        if c.get("owner"):
            owners.add(c["owner"])
    if owners:
        lines.append(f"\n**People with commitments:** {', '.join(owners)}")

    # Related relationships
    for rel in relationships:
        lines.append(f"\n**Related:** {rel.get('display_name', '')} ({rel.get('relationship_type', '')})")

    return {
        "answer": "\n".join(lines) if lines else "No identity information available.",
        "reason": "Compiled from identity, context, and relationships data.",
        "evidence": "identity, context, relationships, commitments",
        "confidence": "high",
        "authority": "canonical_data",
        "expected_action": "Review the involved parties.",
        "execution_authorized": False,
        "intent": "who_is_involved",
    }


def _answer_what_changed(context: Dict[str, Any]) -> Dict[str, Any]:
    """Answer: What changed recently?"""
    timeline = context.get("timeline", [])

    if not timeline:
        return {
            "answer": "No recent changes detected.",
            "reason": "Checked timeline — no entries found.",
            "evidence": "timeline",
            "confidence": "high",
            "authority": "canonical_data",
            "expected_action": "No changes to review.",
            "execution_authorized": False,
            "intent": "what_changed",
        }

    recent = timeline[:5]
    lines = [f"**{len(recent)} recent event(s):**"]
    for e in recent:
        lines.append(f"- {e.get('title', '')} ({e.get('time', '')[:10] if e.get('time') else ''})")

    return {
        "answer": "\n".join(lines),
        "reason": "Queried timeline for most recent events.",
        "evidence": "timeline",
        "confidence": "high",
        "authority": "canonical_data",
        "expected_action": "Review the recent changes.",
        "execution_authorized": False,
        "intent": "what_changed",
    }


def _answer_general(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Answer a general question using available context."""
    identity = context.get("identity", {})
    name = identity.get("name") or "this object"

    return {
        "answer": (
            f"I understand you're asking about **{name}**. "
            "I can help with:\n"
            "- What is happening?\n"
            "- What was promised?\n"
            "- What is overdue?\n"
            "- What should I do next?\n"
            "- Why is this stalled?\n"
            "- Show me the evidence\n"
            "- Who is involved?\n"
            "- What changed?"
        ),
        "reason": "General question handler — no specific intent matched.",
        "evidence": "context",
        "confidence": "low",
        "authority": "deterministic_analysis",
        "expected_action": "Ask a more specific question from the supported list.",
        "execution_authorized": False,
        "intent": "general_question",
    }