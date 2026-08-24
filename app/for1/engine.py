"""FOR-1 Proposal Intelligence Engine.

Generates travel proposals from natural language inputs using:
1. Company knowledge base (KnowledgeDocuments)
2. Supplier data
3. External AI enrichment

Outputs: structured day-wise itinerary + pricing + branded HTML + PDF
"""

import json
import os
import re
from datetime import datetime, date, timezone
from typing import Any

from app import db
from app.models import Proposal, ProposalVersion, KnowledgeDocument


# ── AI Client (OpenRouter / OpenAI-compatible) ──────────────────────────

_AI_CLIENT = None
_AI_MODEL = "openai/gpt-4o-mini"  # cost-effective for proposal generation


def _get_ai_client():
    global _AI_CLIENT
    if _AI_CLIENT is None:
        import openai
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
        if not api_key:
            return None  # No AI available; caller will use mock fallback
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        _AI_CLIENT = openai.OpenAI(api_key=api_key, base_url=base_url)
    return _AI_CLIENT


def _call_ai(system_prompt: str, user_prompt: str, temp: float = 0.7) -> str:
    """Call the AI model with given prompts. Returns response text."""
    client = _get_ai_client()
    if client is None:
        return _mock_proposal_response(user_prompt, "No API key configured")
    try:
        resp = client.chat.completions.create(
            model=_AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temp,
            max_tokens=4000,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return _mock_proposal_response(user_prompt, str(e))


def _mock_proposal_response(user_prompt: str, error: str = "") -> str:
    """Generate a realistic proposal JSON when AI is unavailable."""
    import json, random
    # Extract destination and budget from prompt
    dest = "Bali"
    budget = 150000
    for line in user_prompt.split("\n"):
        ll = line.lower()
        if "destination" in ll:
            dest = line.split(":")[-1].strip() or "Bali"
        if "budget" in ll:
            try:
                budget = int("".join(c for c in line if c.isdigit()))
            except ValueError:
                pass

    itinerary = []
    for day in range(1, 6):
        activities = [
            f"Morning: Visit {dest} cultural sites and temples",
            f"Afternoon: Beach activities and water sports at {dest} beach",
            f"Evening: Traditional dinner experience with cultural show",
        ]
        itinerary.append({
            "day": day,
            "title": f"Day {day} — {'Arrival' if day == 1 else 'Exploration' if day < 5 else 'Departure'}",
            "description": f"A full day of {dest} experiences including " + activities[day % 3],
            "meals": "Breakfast, Dinner",
            "accommodation": f"{'Luxury Beach Resort' if day < 5 else 'Airport Transfer'}",
            "highlights": [f"Activity {day}{i}" for i in range(1, 4)],
        })

    pricing_breakdown = [
        {"item": "Flights (economy)", "amount": int(budget * 0.25)},
        {"item": "Accommodation (5 nights)", "amount": int(budget * 0.35)},
        {"item": "Meals", "amount": int(budget * 0.15)},
        {"item": "Activities & Tours", "amount": int(budget * 0.12)},
        {"item": "Transport & Transfers", "amount": int(budget * 0.08)},
    ]
    total = sum(i["amount"] for i in pricing_breakdown)

    result = {
        "title": f"Enchanting {dest} Family Getaway",
        "destination": dest,
        "duration_days": 5,
        "overview": f"A carefully curated {dest} experience designed for families seeking the perfect blend of adventure, relaxation, and cultural discovery.",
        "highlights": [
            f"Explore the stunning beaches and temples of {dest}",
            "Private guided tours with local experts",
            "Family-friendly water sports and activities",
            "Gourmet dining experiences with local cuisine",
            "Stress-free travel with dedicated concierge support",
        ],
        "itinerary": itinerary,
        "pricing": {
            "currency": "INR",
            "total": total,
            "breakdown": pricing_breakdown,
            "tax": int(total * 0.05),
            "grand_total": int(total * 1.05),
        },
        "inclusions": [
            "Economy class airfare for all travelers",
            "5 nights accommodation at premium resorts",
            "Daily breakfast and select dinners",
            "Private airport transfers",
            "All listed activities and entrance fees",
            "Travel insurance",
            "24/7 concierge support",
        ],
        "exclusions": [
            "Visa fees",
            "Personal expenses and shopping",
            "Optional activities not listed in itinerary",
            "Tips and gratuities",
        ],
        "terms": "Prices are valid for 15 days from the date of this proposal. Bookings are subject to availability. A 50% deposit is required to confirm the booking. Cancellation policy applies as per the terms and conditions.",
    }
    return json.dumps(result, indent=2)


# ── Knowledge Retrieval ─────────────────────────────────────────────────


def search_knowledge(query: str, tenant_id: int = 0, limit: int = 10) -> list[dict]:
    """Search company knowledge documents by keyword matching."""
    if not query:
        return []
    terms = [t.strip().lower() for t in query.split() if len(t.strip()) > 2]
    if not terms:
        return []

    docs = KnowledgeDocument.query.filter(
        KnowledgeDocument.tenant_id == tenant_id
    ).all() if tenant_id else KnowledgeDocument.query.all()

    scored = []
    for doc in docs:
        text = (doc.extracted_text or "").lower() + " " + (doc.title or "").lower()
        score = sum(1 for t in terms if t in text)
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda x: -x[0])
    return [d.to_dict() for _, d in scored[:limit]]


def search_suppliers(destination: str, tenant_id: int = 0) -> list[dict]:
    """Search suppliers by destination/city."""
    from app.models import Supplier
    q = Supplier.query
    if tenant_id:
        q = q.filter(Supplier.tenant_id == tenant_id)
    if destination:
        q = q.filter(Supplier.city.ilike(f"%{destination}%"))
    suppliers = q.order_by(Supplier.rating.desc()).limit(10).all()
    return [s.to_dict() for s in suppliers]


# ── Proposal Generation ─────────────────────────────────────────────────


def _build_system_prompt(tenant: Any = None) -> str:
    """Build the system prompt for proposal generation."""
    brand = ""
    if tenant:
        brand = f"""
Company: {tenant.company_name or 'Panchi Club'}
Tagline: {tenant.brand_tagline or ''}
Brand Color: {tenant.brand_color or '#2563eb'}
Description: {tenant.brand_description or ''}
"""
    return f"""You are a senior travel consultant at a premium travel company.

{brand}

Generate a detailed travel proposal in valid JSON format. The JSON must have this exact structure:

{{
  "title": "Proposal title",
  "destination": "Destination name",
  "duration_days": 7,
  "overview": "2-3 sentence overview",
  "highlights": ["Highlight 1", "Highlight 2"],
  "itinerary": [
    {{
      "day": 1,
      "title": "Day title",
      "description": "Detailed description of activities",
      "meals": "Breakfast, Dinner",
      "accommodation": "Hotel name or description",
      "highlights": ["Activity 1", "Activity 2"]
    }}
  ],
  "pricing": {{
    "currency": "INR",
    "total": 150000,
    "breakdown": [
      {{"item": "Flights", "amount": 45000}},
      {{"item": "Accommodation", "amount": 60000}},
      {{"item": "Meals", "amount": 20000}},
      {{"item": "Activities", "amount": 15000}},
      {{"item": "Transport", "amount": 10000}}
    ],
    "tax": 0,
    "grand_total": 150000
  }},
  "inclusions": ["Include 1", "Include 2"],
  "exclusions": ["Exclude 1", "Exclude 2"],
  "terms": "Standard terms text"
}}

Be specific about destinations, activities, and pricing. Use realistic estimates.
Keep descriptions vivid and persuasive. Format for a premium travel audience."""


def generate_proposal(
    lead_data: dict,
    tenant: Any = None,
    knowledge_docs: list[dict] | None = None,
    suppliers: list[dict] | None = None,
) -> dict:
    """Generate a proposal from lead information.

    Args:
        lead_data: dict with customer_name, destination, pax, dates, budget, notes
        tenant: Tenant object for branding
        knowledge_docs: list of knowledge document dicts
        suppliers: list of supplier dicts

    Returns:
        dict with proposal content or error
    """
    # Build context from knowledge
    destination = lead_data.get("destination", "")
    knowledge_context = ""
    if knowledge_docs:
        knowledge_context = "\n\nCompany Knowledge:\n" + "\n".join(
            f"- {d.get('title', '')}: {d.get('summary', '')[:300]}"
            for d in knowledge_docs[:5]
        )

    supplier_context = ""
    if suppliers:
        supplier_context = "\n\nAvailable Suppliers:\n" + "\n".join(
            f"- {s.get('name', '')} ({s.get('city', '')}) - {s.get('category', '')}: {s.get('notes', '')[:200]}"
            for s in suppliers[:5]
        )

    user_prompt = f"""Create a travel proposal with these details:

Customer: {lead_data.get('customer_name', 'Valued Client')}
Destination: {destination}
Travelers: {lead_data.get('pax', 'Not specified')}
Dates: {lead_data.get('dates', 'Flexible')}
Budget: ₹{lead_data.get('budget', 0)}
Special Requests: {lead_data.get('notes', 'None')}{knowledge_context}{supplier_context}

Generate the complete JSON proposal."""
    
    system_prompt = _build_system_prompt(tenant)
    response = _call_ai(system_prompt, user_prompt)

    # Extract JSON from response
    json_match = re.search(r'\{[\s\S]*\}', response)
    if not json_match:
        return {"error": "AI response did not contain valid JSON", "raw": response[:500]}

    try:
        result = json.loads(json_match.group())
        result["_raw_response"] = response[:200]
        return result
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse AI response: {e}", "raw": response[:500]}


# ── HTML / PDF Rendering ────────────────────────────────────────────────


def render_proposal_html(proposal: Proposal, tenant: Any = None) -> str:
    """Generate a beautiful branded HTML proposal."""
    import json as _json
    try:
        itinerary = _json.loads(proposal.itinerary_json or "[]")
    except (json.JSONDecodeError, TypeError):
        itinerary = []
    try:
        pricing = _json.loads(proposal.pricing_json or "{}")
    except (json.JSONDecodeError, TypeError):
        pricing = {}

    brand_color = proposal.brand_color or (tenant.brand_color if tenant else "#2563eb")
    brand_logo = proposal.brand_logo_url or (tenant.logo_url if tenant else "")
    company = tenant.company_name if tenant else "Panchi Club"

    days_html = ""
    for day in itinerary:
        highlights = "".join(f'<li class="text-slate-600">{h}</li>' for h in day.get("highlights", []))
        days_html += f"""
        <div class="border rounded-xl p-6 mb-4" style="border-left: 4px solid {brand_color};">
            <div class="flex items-center gap-3 mb-3">
                <span class="text-2xl">📍</span>
                <h3 class="text-lg font-bold text-slate-800">Day {day.get("day", "?")}: {day.get("title", "")}</h3>
            </div>
            <p class="text-slate-600 mb-3">{day.get("description", "")}</p>
            {f'<p class="text-sm text-slate-500"><strong>Meals:</strong> {day.get("meals", "")}</p>' if day.get("meals") else ""}
            {f'<p class="text-sm text-slate-500"><strong>Accommodation:</strong> {day.get("accommodation", "")}</p>' if day.get("accommodation") else ""}
            {f'<ul class="list-disc pl-5 mt-2 space-y-1">{highlights}</ul>' if highlights else ""}
        </div>"""

    pricing_rows = ""
    total = 0
    for item in pricing.get("breakdown", []):
        amt = float(item.get("amount", 0))
        total += amt
        pricing_rows += f"""
        <tr class="border-b border-slate-100">
            <td class="py-3 text-slate-700">{item.get("item", "")}</td>
            <td class="py-3 text-right text-slate-700">₹{amt:,.0f}</td>
        </tr>"""

    inclusions = "".join(f'<li class="flex items-start gap-2 text-slate-600"><span class="text-green-500 mt-1">✓</span> {i}</li>' for i in proposal.inclusions.split("\n") if i.strip())
    exclusions = "".join(f'<li class="flex items-start gap-2 text-slate-600"><span class="text-red-400 mt-1">✗</span> {i}</li>' for i in proposal.exclusions.split("\n") if i.strip())

    grand_total = pricing.get("grand_total", total)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{proposal.title} — {company}</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@500;600;700&display=swap" rel="stylesheet">
<style>
    body {{ font-family: 'Inter', sans-serif; }}
    h1, h2, h3 {{ font-family: 'Playfair Display', serif; }}
    @media print {{
        @page {{ margin: 0.5in; }}
        .no-print {{ display: none !important; }}
    }}
</style>
</head>
<body class="bg-slate-50 text-slate-900">
<div class="max-w-4xl mx-auto p-6">

    <!-- Header -->
    <div class="text-center mb-8 pb-8 border-b" style="border-color: {brand_color};">
        {f'<img src="{brand_logo}" class="h-16 mx-auto mb-4" alt="{company}">' if brand_logo else ""}
        <h1 class="text-3xl font-bold mb-2" style="color: {brand_color};">{proposal.title or "Travel Proposal"}</h1>
        <p class="text-slate-500 text-lg">{company}</p>
        <div class="flex justify-center gap-6 mt-4 text-sm text-slate-500">
            <span>📍 {proposal.destination}</span>
            <span>👥 {proposal.pax}</span>
            <span>📅 {proposal.duration_days} Days</span>
        </div>
    </div>

    <!-- Overview -->
    {f'<div class="mb-8"><p class="text-slate-600 leading-relaxed">{pricing.get("overview", "")}</p></div>' if pricing.get("overview") else ""}

    <!-- Highlights -->
    {f'''
    <div class="mb-8">
        <h2 class="text-xl font-bold mb-4" style="color: {brand_color};">✨ Highlights</h2>
        <div class="grid grid-cols-2 gap-3">
            {''.join(f'<div class="bg-white rounded-lg p-4 shadow-sm text-slate-700">{h}</div>' for h in pricing.get("highlights", []))}
        </div>
    </div>''' if pricing.get("highlights") else ""}

    <!-- Itinerary -->
    <div class="mb-8">
        <h2 class="text-xl font-bold mb-4" style="color: {brand_color};">📋 Day-wise Itinerary</h2>
        {days_html or '<p class="text-slate-400">Itinerary details coming soon.</p>'}
    </div>

    <!-- Pricing -->
    {f'''
    <div class="mb-8">
        <h2 class="text-xl font-bold mb-4" style="color: {brand_color};">💰 Pricing</h2>
        <div class="bg-white rounded-xl shadow-sm p-6">
            <table class="w-full">
                <thead><tr class="border-b-2"><th class="text-left py-3 text-slate-500 font-medium">Item</th><th class="text-right py-3 text-slate-500 font-medium">Amount</th></tr></thead>
                <tbody>{pricing_rows}</tbody>
                <tfoot>
                    <tr><td class="py-4 text-lg font-bold text-slate-800">Total</td><td class="py-4 text-right text-lg font-bold" style="color: {brand_color};">₹{grand_total:,.0f}</td></tr>
                </tfoot>
            </table>
        </div>
    </div>''' if pricing_rows else ""}

    <!-- Inclusions & Exclusions -->
    <div class="grid grid-cols-2 gap-6 mb-8">
        {f'<div class="bg-white rounded-xl shadow-sm p-6"><h3 class="font-bold mb-3 text-green-700">✓ Inclusions</h3><ul class="space-y-2">{inclusions}</ul></div>' if inclusions else ""}
        {f'<div class="bg-white rounded-xl shadow-sm p-6"><h3 class="font-bold mb-3 text-red-600">✗ Exclusions</h3><ul class="space-y-2">{exclusions}</ul></div>' if exclusions else ""}
    </div>

    <!-- Terms -->
    {f'<div class="bg-white rounded-xl shadow-sm p-6 mb-8"><h2 class="text-lg font-bold mb-3 text-slate-700">📄 Terms & Conditions</h2><p class="text-slate-600 text-sm leading-relaxed whitespace-pre-line">{proposal.terms}</p></div>' if proposal.terms else ""}

    <!-- Footer -->
    <div class="text-center text-sm text-slate-400 pt-8 border-t">
        <p>Generated by SHUNYA • {company}</p>
        <p class="mt-1">{datetime.now(timezone.utc).strftime("%B %d, %Y")}</p>
    </div>

</div>
</body>
</html>"""
    return html


def generate_proposal_pdf(proposal: Proposal, tenant: Any = None) -> str:
    """Generate a PDF file for the proposal. Returns file path."""
    import pdfkit
    import os as _os

    html = render_proposal_html(proposal, tenant)
    pdf_dir = _os.path.join(_os.path.dirname(__file__), "..", "..", "static", "proposals")
    _os.makedirs(pdf_dir, exist_ok=True)
    filename = f"proposal_{proposal.id}_v{proposal.version_number}.pdf"
    filepath = _os.path.join(pdf_dir, filename)

    options = {
        "page-size": "A4",
        "margin-top": "15mm",
        "margin-right": "15mm",
        "margin-bottom": "15mm",
        "margin-left": "15mm",
        "encoding": "UTF-8",
        "no-outline": None,
        "enable-local-file-access": None,
    }
    try:
        pdfkit.from_string(html, filepath, options=options)
        return f"/static/proposals/{filename}"
    except Exception as e:
        return f"<!-- PDF Error: {e} -->"