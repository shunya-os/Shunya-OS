"""
Universal Search — DuckDuckGo Web Search + AI Company Analysis.

Provides:
  GET  /api/v1/search     — Web search via DuckDuckGo (with requests fallback)
  POST /api/v1/search     — Same search via POST body {q: string}
  POST /api/v1/ai/analyze — Company analysis combining business context + web search

All endpoints require a valid session with identity_id.
"""
from flask import Blueprint, jsonify, request, session, current_app
from sqlalchemy import text
import logging
import json
from urllib.parse import quote
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

search_bp = Blueprint("search", __name__, url_prefix="/api/v1")


def _founder_required() -> bool:
    return bool(session.get("identity_id"))


# ---------------------------------------------------------------------------
# DuckDuckGo Web Search (primary: duckduckgo_search, fallback: requests API)
# ---------------------------------------------------------------------------


def _web_search(query: str, max_results: int = 8) -> list[dict]:
    """Search the web via DuckDuckGo. Returns [{title, snippet, url}, ...]."""
    results = []

    # --- Primary: duckduckgo_search / ddgs library ---
    try:
        # Try both the new 'ddgs' package and old 'duckduckgo_search' package
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
        for r in raw:
            results.append(
                {
                    "title": (r.get("title") or "").strip(),
                    "snippet": (r.get("body") or "").strip(),
                    "url": (r.get("href") or "").strip(),
                }
            )
        if results:
            return results
    except ImportError:
        logger.info("duckduckgo_search not installed — falling back to requests API")
    except Exception as e:
        logger.warning(f"duckduckgo_search failed: {e}")

    # --- Fallback: requests-based DuckDuckGo instant answer API ---
    try:
        import requests

        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=10,
            headers={"User-Agent": "SHUNYA-OS/1.0"},
        )
        if resp.ok:
            data = resp.json()
            # Abstract (disambiguation / topic summary)
            abstract = data.get("AbstractText", "")
            abstract_src = data.get("AbstractSource", "")
            abstract_url = data.get("AbstractURL", "")
            if abstract:
                results.append(
                    {"title": abstract_src or "DuckDuckGo", "snippet": abstract, "url": abstract_url}
                )

            # Related topics
            related = data.get("RelatedTopics", [])
            for entry in related[:max_results]:
                # Some entries are nested under "Topics"
                topics = entry.get("Topics", [entry])
                for t in topics:
                    if "Text" in t and "FirstURL" in t:
                        results.append(
                            {
                                "title": t.get("Text", "").split(" - ")[0] if " - " in t.get("Text", "") else t.get("Text", ""),
                                "snippet": t.get("Text", ""),
                                "url": t.get("FirstURL", ""),
                            }
                        )
                    if len(results) >= max_results:
                        break
                if len(results) >= max_results:
                    break

            # Results from the web search API (if available via !bang redirects)
            results_list = data.get("Results", [])
            for r in results_list[:max_results]:
                results.append(
                    {
                        "title": r.get("Text", "").split(" - ")[0] if " - " in r.get("Text", "") else r.get("Text", ""),
                        "snippet": r.get("Text", ""),
                        "url": r.get("FirstURL", ""),
                    }
                )

    except Exception as e:
        logger.warning(f"DuckDuckGo API fallback failed: {e}")

    # Deduplicate by URL
    seen_urls = set()
    deduped = []
    for r in results:
        if r["url"] and r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            deduped.append(r)

    return deduped[:max_results]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@search_bp.route("/search", methods=["GET", "POST"])
def api_search():
    """Web search via DuckDuckGo.

    GET  /api/v1/search?q=query
    POST /api/v1/search  {q: "query"}
    """
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        q = (body.get("q") or "").strip()
    else:
        q = (request.args.get("q") or "").strip()

    if not q or len(q) < 2:
        return jsonify({"success": True, "data": []})

    results = _web_search(q)

    return jsonify({"success": True, "data": results})


@search_bp.route("/ai/analyze", methods=["POST"])
def ai_analyze():
    """Company analysis — combines business data context + web search + AI.

    POST /api/v1/ai/analyze  {question: str}
    Returns {answer, sources, data_used}
    """
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify({"success": False, "error": "question is required"}), 400

    identity_id = session.get("identity_id")

    # 1. Build company context from database
    try:
        from app.search.context import build_context

        company_context = build_context(identity_id or "")
    except Exception as e:
        logger.warning(f"build_context failed: {e}")
        company_context = "No business data available."

    # 2. Get web search results
    web_results = _web_search(question, max_results=5)
    sources = []
    web_context_parts = [f"Web search results for '{question}':"]
    for r in web_results:
        web_context_parts.append(f"- {r['title']}: {r['snippet']} ({r['url']})")
        sources.append({"title": r["title"], "url": r["url"]})
    web_context = "\n".join(web_context_parts)

    # 3. Build AI prompt
    system_prompt = (
        "You are SHUNYA, an intelligent business analysis assistant. "
        "Analyze the user's business data and web search results to provide "
        "a thorough, data-driven answer. Be specific — cite numbers, names, "
        "and amounts where available. When using web search results, mention "
        "the source.\n\n"
        f"=== COMPANY DATA ===\n{company_context}\n\n"
        f"=== WEB SEARCH RESULTS ===\n{web_context}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    # 4. Send to AI provider chain
    try:
        from app.ai.provider import _registry

        # Try each provider in the chain
        provider = _registry.resolve()
        chain = _registry.chain
        last_error = ""
        answer = ""

        for p in chain:
            if not p.is_available():
                continue
            try:
                result = p.complete(messages, temperature=0.5, max_tokens=2048)
                if result.get("finish_reason") == "error":
                    last_error = result.get("error", "Provider error")
                    logger.warning(f"Analyze provider {p.name} failed: {last_error}")
                    continue
                answer = result.get("content", "")
                break
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Analyze provider {p.name} exception: {last_error}")
                continue

        if not answer:
            # Fallback: try a simpler response
            answer = (
                f"I analyzed your business data based on the available information. "
                f"Your question was: '{question}'. "
                f"I found {len(sources)} web sources and your business context contains "
                f"data from {len(company_context.split(chr(10)))} records. "
                f"Due to AI provider unavailability, I couldn't generate a full analysis. "
                f"Last error: {last_error}"
            )

        # 5. Build data_used summary
        data_used = {
            "company_context_lines": len(company_context.split("\n")),
            "web_results_count": len(web_results),
            "sources": sources,
        }

        return jsonify(
            {
                "success": True,
                "answer": answer,
                "sources": sources,
                "data_used": data_used,
            }
        )

    except ImportError:
        return jsonify(
            {
                "success": False,
                "error": "AI provider system not available",
                "answer": "",
                "sources": sources,
                "data_used": {"web_results_count": len(web_results)},
            }
        ), 503
    except Exception as e:
        logger.error(f"AI analyze endpoint error: {e}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "answer": "",
                "sources": sources,
                "data_used": {"web_results_count": len(web_results)},
            }
        ), 500


# ---------------------------------------------------------------------------
# Proactive AI Presence — Ambient Intelligence Insights
# ---------------------------------------------------------------------------


def get_proactive_insights(identity_id: str) -> list[dict]:
    """Query sh_objects for the user's data and generate proactive insights.

    Returns a list of insight dicts with the structure:
      { title, description, type, confidence, evidence, source,
        action_label, action_payload }
    Types: 'reminder', 'opportunity', 'alert', 'suggestion'
    """
    if not identity_id:
        return []

    try:
        from app import db
        from sqlalchemy import text as _text

        rows = db.session.execute(
            _text(
                """
                SELECT object_id, object_type, name, status, data, created_at, updated_at
                FROM sh_objects
                WHERE created_by = :identity_id
                  AND is_deleted = false
                ORDER BY updated_at DESC
                """
            ),
            {"identity_id": identity_id},
        ).fetchall()
    except Exception as e:
        logger.warning(f"get_proactive_insights query failed: {e}")
        return []

    if not rows:
        return []

    now = datetime.now(timezone.utc)
    insights: list[dict] = []

    # Parse rows into a dict by type
    by_type: dict[str, list[dict]] = {}
    for row in rows:
        obj = {
            "object_id": row.object_id,
            "object_type": row.object_type,
            "name": row.name or "",
            "status": row.status or "",
            "data": row.data if isinstance(row.data, dict) else {},
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        t = row.object_type
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(obj)

    # ── 1. Invoice alerts ──
    invoices = by_type.get("invoice", [])
    for inv in invoices:
        inv_data = inv["data"]
        status = (inv_data.get("payment_status") or inv_data.get("status") or "draft").lower()
        if status in ("overdue", "past_due"):
            try:
                amount = float(inv_data.get("grand_total") or inv_data.get("amount") or 0)
            except (ValueError, TypeError):
                amount = 0.0
            customer = inv_data.get("customer_name") or inv.get("name") or f"INV-{inv['object_id'][:8]}"
            due_date = inv_data.get("due_date", "")
            days_overdue = ""
            if due_date:
                try:
                    dd = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
                    diff = (now - dd).days
                    days_overdue = f" {diff} days overdue"
                except (ValueError, TypeError):
                    pass
            insights.append(
                {
                    "title": f"Invoice {customer} is overdue",
                    "description": f"Invoice for {customer} — ${amount:,.2f}{days_overdue}. Send a payment reminder.",
                    "type": "alert",
                    "confidence": 0.9,
                    "evidence": f"Invoice status is '{status}', amount ${amount:,.2f}",
                    "source": "sh_objects",
                    "action_label": "Send Reminder",
                    "action_payload": {"object_id": inv["object_id"], "action": "send_reminder"},
                }
            )

    # ── 2. Proposals ready for review ──
    proposals = by_type.get("proposal", [])
    for prop in proposals:
        prop_data = prop["data"]
        prop_status = (prop_data.get("status") or prop.get("status") or "draft").lower()
        if prop_status in ("draft", "needs_review"):
            try:
                amount = float(prop_data.get("amount") or 0)
            except (ValueError, TypeError):
                amount = 0.0
            prop_name = prop.get("name") or f"Proposal {prop['object_id'][:8]}"
            amt_str = f" (${amount:,.2f})" if amount > 0 else ""
            insights.append(
                {
                    "title": f"{prop_name} is ready for review",
                    "description": f"{prop_name}{amt_str} — review and send to client.",
                    "type": "suggestion",
                    "confidence": 0.8,
                    "evidence": f"Proposal status is '{prop_status}'",
                    "source": "sh_objects",
                    "action_label": "Review Proposal",
                    "action_payload": {"object_id": prop["object_id"], "action": "review"},
                }
            )

    # ── 3. Task-related alerts ──
    tasks = by_type.get("task", [])
    for task in tasks:
        task_data = task["data"]
        t_status = (task_data.get("status") or task.get("status") or "pending").lower()
        due_date = task_data.get("due_date") or task_data.get("deadline") or ""
        if t_status not in ("completed", "done", "cancelled") and due_date:
            try:
                dd = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
                diff = (now - dd).days
                if diff >= 0:
                    task_name = task.get("name") or f"Task {task['object_id'][:8]}"
                    insights.append(
                        {
                            "title": f'Task "{task_name}" is overdue',
                            "description": f'"{task_name}" was due {diff} day{"s" if diff != 1 else ""} ago.',
                            "type": "alert",
                            "confidence": 0.85,
                            "evidence": f"Task due date {due_date}, status '{t_status}'",
                            "source": "sh_objects",
                            "action_label": "View Task",
                            "action_payload": {"object_id": task["object_id"], "action": "view"},
                        }
                    )
            except (ValueError, TypeError):
                pass

    # ── 4. Revenue opportunity ──
    if invoices:
        current_month_total = 0.0
        last_month_total = 0.0
        for inv in invoices:
            try:
                amount = float(inv["data"].get("grand_total") or inv["data"].get("amount") or 0)
            except (ValueError, TypeError):
                amount = 0.0
            inv_status = (inv["data"].get("payment_status") or inv["data"].get("status") or "draft").lower()
            if inv_status == "paid":
                updated = inv.get("updated_at")
                if updated:
                    try:
                        if hasattr(updated, "month"):
                            m = updated.month
                            y = updated.year
                        elif hasattr(updated, "month"):
                            m = updated.month
                            y = updated.year
                        else:
                            continue
                        if y == now.year and m == now.month:
                            current_month_total += amount
                        elif y == now.year and m == now.month - 1:
                            last_month_total += amount
                        elif now.month == 1 and y == now.year - 1 and m == 12:
                            last_month_total += amount
                    except Exception:
                        pass
        if last_month_total > 0 and current_month_total > 0:
            pct_change = ((current_month_total - last_month_total) / last_month_total) * 100
            direction = "above" if pct_change > 0 else "below"
            insights.append(
                {
                    "title": f"Revenue tracking {abs(pct_change):.0f}% {direction} last month",
                    "description": (
                        f"Revenue this month is ${current_month_total:,.2f} vs "
                        f"${last_month_total:,.2f} last month "
                        f"({direction} by {abs(pct_change):.1f}%)."
                    ),
                    "type": "opportunity",
                    "confidence": 0.6,
                    "evidence": f"Current month: ${current_month_total:,.2f}, Last month: ${last_month_total:,.2f}",
                    "source": "sh_objects",
                    "action_label": None,
                    "action_payload": None,
                }
            )

    # ── 5. Follow-up reminders ──
    contacts = by_type.get("contact", [])
    customers_list = by_type.get("customer", [])
    all_relationships = contacts + customers_list
    for rel in all_relationships[:10]:
        rel_name = rel.get("name") or ""
        if not rel_name:
            continue
        updated = rel.get("updated_at")
        if updated:
            try:
                days_since = (now - updated).days
            except Exception:
                days_since = 999
        else:
            days_since = 999
        if 7 <= days_since <= 30:
            insights.append(
                {
                    "title": f"Follow up with {rel_name}",
                    "description": (
                        f"It's been {days_since} days since last contact with {rel_name}. "
                        f"Consider reaching out."
                    ),
                    "type": "reminder",
                    "confidence": 0.7,
                    "evidence": f"Last updated {days_since} days ago",
                    "source": "sh_objects",
                    "action_label": "Contact",
                    "action_payload": {"object_id": rel["object_id"], "action": "follow_up"},
                }
            )

    # ── 6. High-value sent proposals ──
    sent_proposals = []
    for prop in proposals:
        prop_data = prop["data"]
        prop_status = (prop_data.get("status") or prop.get("status") or "draft").lower()
        if prop_status in ("sent", "pending", "under_review"):
            try:
                amount = float(prop_data.get("amount") or 0)
            except (ValueError, TypeError):
                amount = 0.0
            if amount > 0:
                sent_proposals.append(
                    {
                        "name": prop.get("name") or f"Proposal {prop['object_id'][:8]}",
                        "amount": amount,
                        "object_id": prop["object_id"],
                    }
                )
    if sent_proposals:
        top_proposal = max(sent_proposals, key=lambda p: p["amount"])
        insights.append(
            {
                "title": f"High-value proposal pending: {top_proposal['name']}",
                "description": (
                    f"{top_proposal['name']} (${top_proposal['amount']:,.2f}) "
                    f"is awaiting client response."
                ),
                "type": "opportunity",
                "confidence": 0.7,
                "evidence": f"Proposal amount ${top_proposal['amount']:,.2f}, status 'sent/pending'",
                "source": "sh_objects",
                "action_label": "Follow Up",
                "action_payload": {"object_id": top_proposal["object_id"], "action": "follow_up"},
            }
        )

    # Sort by confidence descending
    insights.sort(key=lambda i: i.get("confidence", 0), reverse=True)
    return insights


@search_bp.route("/ai/insights", methods=["GET"])
def api_proactive_insights():
    """Proactive AI presence — ambient insights based on user data.

    GET /api/v1/ai/insights
    Returns {success: true, data: [{title, description, type, confidence, ...}, ...]}
    """
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    identity_id = session.get("identity_id")
    insights = get_proactive_insights(identity_id or "")

    return jsonify({"success": True, "data": insights})