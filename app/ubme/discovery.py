"""Business Discovery Engine — AI-assisted module generation from natural language.

Takes a founder's description of their business and generates a complete
ModuleDef including object types, fields, relationships, workflows, actions,
dashboards, navigation, and AI semantics — without manual configuration.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from app.ubme.models import (
    ActionDef, BusinessTemplate, DashboardCard, FieldDef, FieldType,
    ModuleDef, NavigationEntry, ObjectTypeDef, ViewDef, ViewType,
    WorkflowDef, WorkflowStateDef, WorkflowStateType, WorkflowTransitionDef,
)
from app.ubme import engine as ubme_engine

logger = logging.getLogger(__name__)

# ── LLM Provider ──────────────────────────────────────────────────────────

# Try to import the real provider; fall back to a rule-based generator
_llm_provider = None


def _get_llm_provider():
    global _llm_provider
    if _llm_provider is not None:
        return _llm_provider
    try:
        from core.inference_orchestrator import get_orchestrator
        orch = get_orchestrator()
        health = orch.health_check()
        if health.get("status") == "healthy":
            _llm_provider = orch
            return orch
    except Exception:
        pass
    return None


# ── Discovery Interview ───────────────────────────────────────────────────

def generate_module_from_description(description: str, business_name: str = "") -> dict[str, Any]:
    """Generate a complete ModuleDef from a natural language business description.

    Uses the LLM provider to generate structured JSON, with fallback to
    a rule-based generator if the LLM is unavailable.
    """
    provider = _get_llm_provider()
    if provider:
        return _generate_via_llm(provider, description, business_name)
    else:
        return _generate_via_rules(description, business_name)


def _build_discovery_prompt(description: str, business_name: str) -> str:
    """Build the prompt sent to the LLM for business discovery."""
    return f"""You are a business discovery engine. Given a business description, generate a complete business module definition as valid JSON. No explanations, no markdown — only JSON starting with {{.

The business describes themselves as: "{description}"
{"The business is called: " + business_name if business_name else ""}

Generate a JSON object with this exact structure:
{{
  "key": "lowercase_snake_case_key",
  "name": "Business Display Name",  
  "description": "Brief description",
  "icon": "emoji representing the business",
  "color": "#hex_color",
  "navigation": [
    {{"label": "ObjectTypePlural", "object_type": "object_type_key", "icon": "emoji"}}
  ],
  "object_types": [
    {{
      "key": "object_type_key",
      "name": "Object Type Name",
      "plural_name": "Plural",
      "description": "Description",
      "icon": "emoji",
      "color": "#hex",
      "category": "business",
      "fields": [
        {{
          "key": "field_name",
          "label": "Field Label",
          "field_type": "text|number|currency|date|datetime|email|phone|select|boolean|long_text|address|url|percentage|integer",
          "required": false,
          "display_in_list": true,
          "searchable": true,
          "order": 1,
          "options": ["option1", "option2"]
        }}
      ],
      "lifecycle": ["stage1", "stage2", "stage3"],
      "default_view": "list|table|calendar|timeline|detail",
      "calendar_field": "date_field_key",
      "ai_semantics": {{
        "description": "What this object represents",
        "common_intents": ["intent1", "intent2"],
        "business_terminology": {{"synonym": "canonical_name"}}
      }},
      "actions": [
        {{
          "key": "action_name",
          "label": "Action Label", 
          "icon": "emoji",
          "requires_confirmation": false
        }}
      ]
    }}
  ],
  "dashboard_cards": [
    {{
      "key": "card_key",
      "label": "Card Label",
      "card_type": "count|sum|recent|alert",
      "object_type": "object_type_key",
      "field": "field_for_sum",
      "filter_criteria": "status == 'active'",
      "icon": "emoji"
    }}
  ],
  "workflows": [
    {{
      "key": "lifecycle_name",
      "name": "Lifecycle Name",
      "object_type": "object_type_key",
      "states": [
        {{"key": "state1", "label": "State 1", "state_type": "initial"}},
        {{"key": "state2", "label": "State 2", "state_type": "intermediate"}},
        {{"key": "state3", "label": "State 3", "state_type": "final"}}
      ],
      "transitions": [
        {{"from_state": "state1", "to_state": "state2", "label": "Transition Label"}},
        {{"from_state": "state2", "to_state": "state3", "label": "Complete"}}
      ],
      "default_state": "state1"
    }}
  ]
}}

IMPORTANT RULES:
- Generate 4-8 object types appropriate for this business
- Each object type should have 5-10 relevant fields
- Include at least 1 workflow for the main object type
- Include 3-6 dashboard cards
- Include action definitions for each object type
- Use realistic business terminology and synonyms
- The lifecycle stages should reflect the actual business process
- All keys must be lowercase_snake_case
- Only output pure JSON, nothing else"""


def _generate_via_llm(orch, description: str, business_name: str) -> dict[str, Any]:
    """Generate module definition via Inference Orchestrator."""
    from core.inference_orchestrator import OrchestratorRequest

    prompt = _build_discovery_prompt(description, business_name)

    try:
        request = OrchestratorRequest(
            input_text=prompt,
            temperature=0.3,
            max_tokens=4096,
        )
        response = orch.process(request)
        if not response.success:
            logger.warning("Orchestrator processing failed: %s", response.error)
            return _generate_via_rules(description, business_name)
        content = response.content
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        data = json.loads(content)
        return _validate_and_fix_module(data, business_name or _guess_business_name(description))
    except Exception as e:
        logger.warning("LLM generation failed: %s. Falling back to rules.", e)
        return _generate_via_rules(description, business_name)


def _validate_and_fix_module(data: dict, fallback_name: str) -> dict:
    """Ensure the generated module has all required fields."""
    if not data.get("key"):
        data["key"] = _guess_key(fallback_name)
    if not data.get("name"):
        data["name"] = fallback_name
    if not data.get("icon"):
        data["icon"] = "🏢"
    if not data.get("color"):
        data["color"] = "#6366f1"
    if not data.get("object_types"):
        data["object_types"] = []
    if not data.get("navigation"):
        data["navigation"] = [
            {"label": ot.get("plural_name", ot["name"] + "s"), "object_type": ot["key"], "icon": ot.get("icon", "📦")}
            for ot in data["object_types"]
        ]
    return data


# ── Rule-based fallback generator ─────────────────────────────────────────

INDUSTRY_TEMPLATES: dict[str, dict] = {
    "clinic": {
        "name": "Medical Clinic", "key": "clinic", "icon": "🏥", "color": "#ec4899",
        "objects": [
            {"key": "patient", "name": "Patient", "fields": ["name", "email", "phone", "date_of_birth", "gender", "blood_group", "address", "allergies", "medical_history", "status"], "lifecycle": ["new", "active", "inactive", "archived"]},
            {"key": "doctor", "name": "Doctor", "fields": ["name", "specialization", "email", "phone", "license_number", "consultation_fee", "status"]},
            {"key": "appointment", "name": "Appointment", "fields": ["name", "patient_id", "doctor_id", "appointment_date", "duration_minutes", "reason", "status", "notes"], "lifecycle": ["scheduled", "checked_in", "in_progress", "completed", "cancelled", "no_show"]},
            {"key": "prescription", "name": "Prescription", "fields": ["name", "patient_id", "doctor_id", "appointment_id", "issue_date", "valid_until", "medications", "diagnosis", "instructions", "status"]},
            {"key": "bill", "name": "Bill", "fields": ["name", "patient_id", "total_amount", "insurance_claim", "due_date", "status", "notes"]},
        ],
        "dashboard": [
            {"key": "patients_today", "label": "Patients Today", "card_type": "count", "object_type": "patient", "icon": "👤"},
            {"key": "appointments_today", "label": "Today's Appointments", "card_type": "count", "object_type": "appointment", "filter_criteria": "status == 'scheduled'", "icon": "📅"},
            {"key": "revenue", "label": "Revenue", "card_type": "sum", "object_type": "bill", "field": "total_amount", "icon": "💰"},
            {"key": "unpaid", "label": "Unpaid Bills", "card_type": "alert", "object_type": "bill", "filter_criteria": "status == 'sent'", "icon": "🚨"},
        ],
    },
    "dental": {
        "name": "Dental Clinic", "key": "dental", "icon": "🦷", "color": "#0ea5e9",
        "objects": [
            {"key": "patient", "name": "Patient", "fields": ["name", "email", "phone", "date_of_birth", "dental_history", "allergies", "status"], "lifecycle": ["new", "active", "inactive"]},
            {"key": "dentist", "name": "Dentist", "fields": ["name", "specialization", "email", "phone", "license_number", "status"]},
            {"key": "appointment", "name": "Appointment", "fields": ["name", "patient_id", "dentist_id", "appointment_date", "procedure_type", "duration_minutes", "status", "notes"], "lifecycle": ["scheduled", "in_progress", "completed", "cancelled"]},
            {"key": "treatment", "name": "Treatment", "fields": ["name", "patient_id", "appointment_id", "tooth_number", "procedure", "cost", "status", "notes"]},
            {"key": "xray", "name": "X-Ray", "fields": ["name", "patient_id", "appointment_id", "tooth_area", "image_url", "findings", "date_taken"]},
            {"key": "payment", "name": "Payment", "fields": ["name", "patient_id", "treatment_id", "amount", "method", "payment_date", "status"]},
            {"key": "insurance", "name": "Insurance", "fields": ["name", "patient_id", "provider", "policy_number", "coverage_type", "valid_until", "status"]},
        ],
        "dashboard": [
            {"key": "patients", "label": "Total Patients", "card_type": "count", "object_type": "patient", "icon": "👤"},
            {"key": "appointments", "label": "Today's Appointments", "card_type": "count", "object_type": "appointment", "filter_criteria": "status == 'scheduled'", "icon": "📅"},
            {"key": "revenue", "label": "Revenue", "card_type": "sum", "object_type": "payment", "field": "amount", "icon": "💰"},
            {"key": "pending_payments", "label": "Pending Payments", "card_type": "alert", "object_type": "payment", "filter_criteria": "status == 'pending'", "icon": "🚨"},
        ],
    },
    "manufacturing": {
        "name": "Manufacturing", "key": "manufacturing", "icon": "🏭", "color": "#f59e0b",
        "objects": [
            {"key": "customer", "name": "Customer", "fields": ["name", "email", "phone", "company", "address", "status"]},
            {"key": "quotation", "name": "Quotation", "fields": ["name", "customer_id", "items", "total_amount", "valid_until", "status"], "lifecycle": ["draft", "sent", "accepted", "rejected", "expired"]},
            {"key": "purchase_order", "name": "Purchase Order", "fields": ["name", "vendor_id", "items", "total_amount", "delivery_date", "status"], "lifecycle": ["draft", "approved", "ordered", "received", "cancelled"]},
            {"key": "vendor", "name": "Vendor", "fields": ["name", "contact_person", "email", "phone", "material_type", "payment_terms", "status"]},
            {"key": "inventory", "name": "Inventory Item", "fields": ["name", "sku", "category", "quantity", "unit_price", "reorder_level", "location", "status"]},
            {"key": "production_order", "name": "Production Order", "fields": ["name", "product", "quantity", "start_date", "end_date", "assigned_to", "status"], "lifecycle": ["planned", "in_progress", "completed", "on_hold", "cancelled"]},
            {"key": "invoice", "name": "Invoice", "fields": ["name", "customer_id", "purchase_order_id", "amount", "due_date", "status", "items"], "lifecycle": ["draft", "sent", "paid", "overdue", "cancelled"]},
        ],
        "dashboard": [
            {"key": "active_orders", "label": "Active Production", "card_type": "count", "object_type": "production_order", "filter_criteria": "status == 'in_progress'", "icon": "🏭"},
            {"key": "pending_quotes", "label": "Pending Quotes", "card_type": "count", "object_type": "quotation", "filter_criteria": "status == 'sent'", "icon": "📄"},
            {"key": "low_stock", "label": "Low Stock Items", "card_type": "alert", "object_type": "inventory", "filter_criteria": "status == 'low'", "icon": "⚠️"},
            {"key": "revenue", "label": "Revenue", "card_type": "sum", "object_type": "invoice", "field": "amount", "icon": "💰"},
        ],
    },
    "legal": {
        "name": "Law Firm", "key": "law_firm", "icon": "⚖️", "color": "#8b5cf6",
        "objects": [
            {"key": "client", "name": "Client", "fields": ["name", "email", "phone", "company", "case_type", "status"], "lifecycle": ["lead", "active", "inactive", "archived"]},
            {"key": "case", "name": "Case", "fields": ["name", "client_id", "case_type", "court", "filing_date", "opposing_counsel", "status", "notes"], "lifecycle": ["filed", "discovery", "trial", "judgment", "appeal", "closed"]},
            {"key": "hearing", "name": "Hearing", "fields": ["name", "case_id", "hearing_date", "court_room", "judge", "outcome", "notes"]},
            {"key": "document", "name": "Document", "fields": ["name", "case_id", "document_type", "filed_date", "file_url", "status", "notes"]},
            {"key": "billing", "name": "Billing Entry", "fields": ["name", "client_id", "case_id", "hours", "rate", "amount", "description", "status"], "lifecycle": ["draft", "submitted", "approved", "paid", "overdue"]},
        ],
        "dashboard": [
            {"key": "active_cases", "label": "Active Cases", "card_type": "count", "object_type": "case", "filter_criteria": "status != 'closed'", "icon": "⚖️"},
            {"key": "hearings", "label": "Upcoming Hearings", "card_type": "count", "object_type": "hearing", "icon": "📅"},
            {"key": "pending_bills", "label": "Outstanding Bills", "card_type": "sum", "object_type": "billing", "field": "amount", "filter_criteria": "status == 'submitted'", "icon": "💰"},
            {"key": "overdue", "label": "Overdue Bills", "card_type": "alert", "object_type": "billing", "filter_criteria": "status == 'overdue'", "icon": "🚨"},
        ],
    },
    "retail": {
        "name": "Retail Store", "key": "retail", "icon": "🛒", "color": "#10b981",
        "objects": [
            {"key": "product", "name": "Product", "fields": ["name", "sku", "category", "unit_price", "cost_price", "quantity", "reorder_level", "status"]},
            {"key": "customer", "name": "Customer", "fields": ["name", "email", "phone", "loyalty_points", "status"]},
            {"key": "sale", "name": "Sale", "fields": ["name", "customer_id", "items", "total_amount", "payment_method", "sale_date", "status"], "lifecycle": ["pending", "completed", "refunded"]},
            {"key": "supplier", "name": "Supplier", "fields": ["name", "contact_person", "email", "phone", "payment_terms", "status"]},
            {"key": "purchase_order", "name": "Purchase Order", "fields": ["name", "supplier_id", "items", "total_amount", "expected_date", "status"], "lifecycle": ["draft", "ordered", "received", "cancelled"]},
        ],
        "dashboard": [
            {"key": "sales_today", "label": "Sales Today", "card_type": "count", "object_type": "sale", "icon": "🛒"},
            {"key": "revenue", "label": "Revenue", "card_type": "sum", "object_type": "sale", "field": "total_amount", "icon": "💰"},
            {"key": "low_stock", "label": "Low Stock Alerts", "card_type": "alert", "object_type": "product", "filter_criteria": "status == 'low'", "icon": "⚠️"},
            {"key": "top_customers", "label": "Top Customers", "card_type": "recent", "object_type": "customer", "icon": "👤"},
        ],
    },
    "restaurant": {
        "name": "Restaurant", "key": "restaurant", "icon": "🍽️", "color": "#ef4444",
        "objects": [
            {"key": "menu_item", "name": "Menu Item", "fields": ["name", "category", "price", "cost", "description", "ingredients", "available", "status"]},
            {"key": "order", "name": "Order", "fields": ["name", "table_number", "items", "total_amount", "order_type", "status", "notes"], "lifecycle": ["taken", "preparing", "served", "completed", "cancelled"]},
            {"key": "customer", "name": "Customer", "fields": ["name", "phone", "email", "preferences", "status"]},
            {"key": "reservation", "name": "Reservation", "fields": ["name", "customer_name", "guest_count", "reservation_date", "table_number", "special_requests", "status"], "lifecycle": ["confirmed", "seated", "completed", "cancelled", "no_show"]},
            {"key": "invoice", "name": "Invoice", "fields": ["name", "order_id", "customer_id", "total_amount", "payment_method", "payment_date", "status"]},
        ],
        "dashboard": [
            {"key": "orders", "label": "Active Orders", "card_type": "count", "object_type": "order", "filter_criteria": "status != 'completed'", "icon": "🍽️"},
            {"key": "reservations", "label": "Today's Reservations", "card_type": "count", "object_type": "reservation", "filter_criteria": "status == 'confirmed'", "icon": "📅"},
            {"key": "revenue", "label": "Revenue Today", "card_type": "sum", "object_type": "invoice", "field": "total_amount", "icon": "💰"},
            {"key": "low_stock", "label": "Low Stock", "card_type": "alert", "object_type": "menu_item", "filter_criteria": "available == false", "icon": "⚠️"},
        ],
    },
    "real_estate": {
        "name": "Real Estate Agency", "key": "real_estate", "icon": "🏠", "color": "#14b8a6",
        "objects": [
            {"key": "property", "name": "Property", "fields": ["name", "property_type", "price", "bedrooms", "bathrooms", "area_sqft", "address", "city", "status", "description"], "lifecycle": ["listed", "under_offer", "sold", "rented", "withdrawn"]},
            {"key": "client", "name": "Client", "fields": ["name", "email", "phone", "client_type", "budget_range", "preferences", "status"]},
            {"key": "viewing", "name": "Viewing", "fields": ["name", "property_id", "client_id", "scheduled_date", "agent_id", "feedback", "status"], "lifecycle": ["scheduled", "completed", "cancelled", "no_show"]},
            {"key": "offer", "name": "Offer", "fields": ["name", "property_id", "client_id", "offer_amount", "offer_date", "status"], "lifecycle": ["submitted", "negotiating", "accepted", "rejected", "withdrawn"]},
            {"key": "commission", "name": "Commission", "fields": ["name", "property_id", "agent_id", "amount", "percentage", "status", "payment_date"]},
        ],
        "dashboard": [
            {"key": "properties", "label": "Listed Properties", "card_type": "count", "object_type": "property", "filter_criteria": "status == 'listed'", "icon": "🏠"},
            {"key": "viewings", "label": "Today's Viewings", "card_type": "count", "object_type": "viewing", "filter_criteria": "status == 'scheduled'", "icon": "📅"},
            {"key": "pending_offers", "label": "Pending Offers", "card_type": "count", "object_type": "offer", "filter_criteria": "status == 'submitted'", "icon": "📄"},
            {"key": "commissions", "label": "Unpaid Commissions", "card_type": "sum", "object_type": "commission", "field": "amount", "filter_criteria": "status == 'pending'", "icon": "💰"},
        ],
    },
}


def _generate_via_rules(description: str, business_name: str) -> dict[str, Any]:
    """Rule-based fallback: match description to known industry templates."""
    desc_lower = description.lower()
    best_match = None
    best_score = 0

    for keyword, template in INDUSTRY_TEMPLATES.items():
        score = 0
        if keyword in desc_lower:
            score += 3
        # Check for the name words
        name_words = set(template["name"].lower().split())
        desc_words = set(w for w in desc_lower.split() if len(w) > 2)
        common = name_words & desc_words
        score += len(common)
        if score > best_score:
            best_score = score
            best_match = template

    if not best_match:
        # Generic fallback - match by most related words
        for keyword, template in INDUSTRY_TEMPLATES.items():
            name_words = set(template["name"].lower().split())
            desc_words = set(w for w in desc_lower.split() if len(w) > 2)
            common = name_words & desc_words
            if len(common) > best_score:
                best_score = len(common)
                best_match = template
    if not best_match:
        best_match = INDUSTRY_TEMPLATES["manufacturing"]

    name = business_name or best_match["name"]
    key = _guess_key(name)

    object_types = []
    for obj_def in best_match["objects"]:
        fields = _generate_fields_for_type(obj_def["key"])
        lifecycle = obj_def.get("lifecycle")
        ot = ObjectTypeDef(
            key=obj_def["key"],
            name=obj_def["name"],
            plural_name=obj_def["name"] + "s",
            description=f"{obj_def['name']} in the {name}",
            icon=_get_field_icon(obj_def["key"]),
            color=best_match["color"],
            fields=fields,
            lifecycle=lifecycle,
            default_view="calendar" if obj_def["key"] in ("appointment", "hearing", "viewing", "reservation") else "list",
            calendar_field=_find_date_field(fields),
            ai_semantics=_generate_semantics(obj_def["key"], obj_def["name"]),
            actions=_generate_actions(obj_def["key"]),
        )
        object_types.append(ot)

    dashboard_cards = []
    for card_def in best_match["dashboard"]:
        dashboard_cards.append(DashboardCard(**card_def))

    return {
        "key": key,
        "name": name,
        "description": f"Complete {name.lower()} business management",
        "icon": best_match["icon"],
        "color": best_match["color"],
        "navigation": [
            {"label": ot.plural_name, "object_type": ot.key, "icon": ot.icon}
            for ot in object_types
        ],
        "object_types": [ot.to_dict() for ot in object_types],
        "dashboard_cards": [c.to_dict() for c in dashboard_cards],
        "workflows": _generate_workflows(object_types),
    }


def _generate_fields_for_type(type_key: str) -> list[FieldDef]:
    """Generate appropriate fields for a common object type."""
    common = [
        FieldDef(key="name", label="Name", field_type=FieldType.TEXT, required=True, searchable=True, display_in_list=True, order=1),
        FieldDef(key="status", label="Status", field_type=FieldType.SELECT, options=["active", "inactive"], default="active", display_in_list=True, order=99),
    ]

    type_specific = {
        "customer": [
            FieldDef(key="email", label="Email", field_type=FieldType.EMAIL, searchable=True, display_in_list=True, order=2),
            FieldDef(key="phone", label="Phone", field_type=FieldType.PHONE, order=3),
            FieldDef(key="company", label="Company", field_type=FieldType.TEXT, order=4),
            FieldDef(key="address", label="Address", field_type=FieldType.ADDRESS, order=5),
            FieldDef(key="notes", label="Notes", field_type=FieldType.LONG_TEXT, order=6),
        ],
        "patient": [
            FieldDef(key="email", label="Email", field_type=FieldType.EMAIL, searchable=True, display_in_list=True, order=2),
            FieldDef(key="phone", label="Phone", field_type=FieldType.PHONE, order=3),
            FieldDef(key="date_of_birth", label="Date of Birth", field_type=FieldType.DATE, order=4),
            FieldDef(key="blood_group", label="Blood Group", field_type=FieldType.SELECT, options=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], order=5),
            FieldDef(key="address", label="Address", field_type=FieldType.ADDRESS, order=6),
            FieldDef(key="allergies", label="Allergies", field_type=FieldType.LONG_TEXT, order=7),
            FieldDef(key="medical_history", label="Medical History", field_type=FieldType.LONG_TEXT, order=8),
        ],
        "invoice": [
            FieldDef(key="customer_id", label="Customer", field_type=FieldType.RELATIONSHIP, relationship_type="one_to_many", target_object_type="customer", display_in_list=True, order=2),
            FieldDef(key="amount", label="Amount", field_type=FieldType.CURRENCY, display_in_list=True, order=3),
            FieldDef(key="due_date", label="Due Date", field_type=FieldType.DATE, display_in_list=True, order=4),
            FieldDef(key="items", label="Line Items", field_type=FieldType.JSON, order=5),
            FieldDef(key="notes", label="Notes", field_type=FieldType.LONG_TEXT, order=6),
        ],
        "product": [
            FieldDef(key="sku", label="SKU", field_type=FieldType.TEXT, searchable=True, display_in_list=True, order=2),
            FieldDef(key="category", label="Category", field_type=FieldType.TEXT, display_in_list=True, order=3),
            FieldDef(key="unit_price", label="Unit Price", field_type=FieldType.CURRENCY, display_in_list=True, order=4),
            FieldDef(key="quantity", label="Quantity", field_type=FieldType.INTEGER, display_in_list=True, order=5),
            FieldDef(key="status", label="Status", field_type=FieldType.SELECT, options=["active", "low", "out_of_stock", "discontinued"], default="active", display_in_list=True, order=6),
        ],
    }

    if type_key in type_specific:
        return common[:-1] + type_specific[type_key] + [common[-1]]
    else:
        return common


def _find_date_field(fields: list[FieldDef]) -> str:
    for f in fields:
        if f.field_type in (FieldType.DATE, FieldType.DATETIME):
            return f.key
    return ""


def _get_field_icon(type_key: str) -> str:
    icons = {
        "customer": "👤", "patient": "👤", "client": "👤",
        "doctor": "👨‍⚕️", "dentist": "👨‍⚕️", "vendor": "🤝", "supplier": "🤝",
        "appointment": "📅", "hearing": "📅", "viewing": "📅", "reservation": "📅",
        "prescription": "💊", "treatment": "💊", "xray": "🩻",
        "invoice": "🧾", "bill": "🧾", "billing": "🧾",
        "payment": "💳", "commission": "💳",
        "order": "📋", "sale": "🛒", "quotation": "📄",
        "property": "🏠", "case": "⚖️", "document": "📄",
        "product": "📦", "inventory": "📦", "menu_item": "🍽️",
        "production_order": "🏭", "purchase_order": "📋",
        "insurance": "🏛️", "offer": "🤝",
    }
    return icons.get(type_key, "📦")


def _generate_semantics(type_key: str, type_name: str) -> dict:
    semantics = {
        "description": f"A {type_name.lower()} in the business",
        "common_intents": [f"view {type_name.lower()}", f"create {type_name.lower()}", f"update {type_name.lower()}"],
        "business_terminology": {},
    }
    synonyms = {
        "customer": {"client": "customer", "buyer": "customer"},
        "patient": {"visitor": "patient"},
        "doctor": {"physician": "doctor"},
        "invoice": {"bill": "invoice", "charge": "invoice"},
        "vendor": {"supplier": "vendor", "partner": "vendor"},
    }
    if type_key in synonyms:
        semantics["business_terminology"] = synonyms[type_key]
    return semantics


def _generate_actions(type_key: str) -> list[ActionDef]:
    actions = {
        "customer": [{"key": "view_profile", "label": "View Profile", "icon": "👤"}, {"key": "send_email", "label": "Send Email", "icon": "📧"}],
        "patient": [{"key": "view_profile", "label": "View Profile", "icon": "👤"}, {"key": "schedule_appointment", "label": "Schedule Appointment", "icon": "📅"}],
        "appointment": [{"key": "confirm", "label": "Confirm", "icon": "✅", "requires_confirmation": True}, {"key": "cancel", "label": "Cancel", "icon": "❌", "requires_confirmation": True}],
        "invoice": [{"key": "send", "label": "Send", "icon": "📧", "requires_confirmation": True}, {"key": "mark_paid", "label": "Mark Paid", "icon": "✅", "requires_confirmation": True}],
        "order": [{"key": "confirm", "label": "Confirm", "icon": "✅"}, {"key": "cancel", "label": "Cancel", "icon": "❌", "requires_confirmation": True}],
        "production_order": [{"key": "start", "label": "Start Production", "icon": "🏭"}, {"key": "complete", "label": "Complete", "icon": "✅", "requires_confirmation": True}],
    }
    return [ActionDef(**a) for a in actions.get(type_key, [])]


def _generate_workflows(object_types: list) -> list[dict]:
    """Generate workflow definitions for object types with lifecycles."""
    workflows = []
    for ot in object_types:
        if not ot.lifecycle or len(ot.lifecycle) < 2:
            continue
        states = []
        transitions = []
        for i, stage in enumerate(ot.lifecycle):
            state_type = WorkflowStateType.INITIAL if i == 0 else (WorkflowStateType.FINAL if i == len(ot.lifecycle) - 1 else WorkflowStateType.INTERMEDIATE)
            states.append(WorkflowStateDef(key=stage, label=stage.replace("_", " ").title(), state_type=state_type))
            if i > 0:
                transitions.append(WorkflowTransitionDef(from_state=ot.lifecycle[i-1], to_state=stage, label=f"Move to {stage.replace('_', ' ').title()}"))
        if states:
            workflows.append({
                "key": f"{ot.key}_lifecycle",
                "name": f"{ot.name} Lifecycle",
                "object_type": ot.key,
                "states": [s.to_dict() for s in states],
                "transitions": [t.to_dict() for t in transitions],
                "default_state": ot.lifecycle[0],
            })
    return workflows


def _guess_key(name: str) -> str:
    """Convert a business name to a key."""
    key = name.lower().strip()
    key = re.sub(r'[^a-z0-9\s]', '', key)
    key = key.replace(' ', '_')
    return key[:40]


def _guess_business_name(description: str) -> str:
    """Extract a business name from a description."""
    # Try to extract "I run a/an/the X" or "I'm running a/an/the X"
    match = re.search(r"(?:i\s+(?:run|manage|operate|own|have|start(?:ed)?)\s+(?:a\s+|an\s+|the\s+|my\s+)?)(.+)", description, re.IGNORECASE)
    if match:
        return match.group(1).strip().capitalize()
    return description[:50].strip().capitalize()