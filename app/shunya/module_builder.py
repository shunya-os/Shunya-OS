"""Shunya OS — Module Builder: AI-powered entity type creation from natural language.

Users describe their workflow → ModuleBuilder generates EntityDefinition → User reviews/edits → Save.
"""
import json, re, logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from app import db
from app.models import EntityDefinition

logger = logging.getLogger("app.shunya.module_builder")

# ---------------------------------------------------------------------------
# Known field type patterns — matches natural language to schema types
# ---------------------------------------------------------------------------

FIELD_PATTERNS: List[Dict] = [
    # Name / Title fields
    {"patterns": [r"\bname\b", r"\btitle\b", r"\bcustomer\b", r"\bclient\b", r"\bpatient\b", r"\bstudent\b",
                  r"\bproduct\b", r"\bservice\b", r"\bitem\b", r"\bequipment\b", r"\bsupplier\b",
                  r"\bemployee\b", r"\bcandidate\b", r"\bapplicant\b", r"\bdoctor\b", r"\bphysician\b",
                  r"\bteacher\b", r"\binstructor\b", r"\bcourse\b", r"\bsubject\b", r"\btopic\b",
                  r"\blocation\b", r"\bdestination\b", r"\bvenue\b", r"\bcity\b", r"\bcountry\b"],
     "type": "text", "required": True, "searchable": True, "label_override": None},

    # Email
    {"patterns": [r"\bemail\b", r"\be-?mail\b"],
     "type": "email", "required": False, "searchable": True},

    # Phone
    {"patterns": [r"\bphone\b", r"\bmobile\b", r"\btelephone\b", r"\bcontact\s?number\b", r"\bcell\b"],
     "type": "phone", "required": False, "searchable": True},

    # Price / Amount / Budget
    {"patterns": [r"\bbudget\b", r"\bprice\b", r"\bcost\b", r"\bamount\b", r"\bfee\b",
                  r"\bdeposit\b", r"\bpayment\b", r"\brental\s*fee\b", r"\bcharges?\b"],
     "type": "price", "required": False, "searchable": False},

    # Number / Count
    {"patterns": [r"\bcount\b", r"\bquantity\b", r"\bpax\b", r"\bnumber of\b", r"\bguests?\b",
                  r"\bpassengers?\b", r"\bpeople\b", r"\badults?\b", r"\bkids?\b", r"\bchildren\b",
                  r"\bdays?\b", r"\bmonths?\b", r"\byears?\b", r"\bunits?\b",
                  r"\bage\b", r"\bweight\b", r"\bheight\b", r"\btemperature\b", r"\bscore\b"],
     "type": "number", "required": False, "searchable": False},

    # Date
    {"patterns": [r"\bdate\b", r"\bdates?\b", r"\bcheck-?in\b", r"\bcheck-?out\b", r"\bdue\s*date\b",
                  r"\bstart\s*date\b", r"\bend\s*date\b", r"\barrival\b", r"\bdeparture\b",
                  r"\breturn\s*date\b", r"\brental\s*period\b", r"\bdeadline\b", r"\bdelivery\s*date\b",
                  r"\bdatetime\b"],
     "type": "date", "required": False, "searchable": False},

    # Select / Status / Dropdown
    {"patterns": [r"\bstatus\b", r"\btype\b", r"\bcategory\b", r"\bdepartment\b", r"\bpriority\b",
                  r"\bseverity\b", r"\blevel\b", r"\bclass\b", r"\bgrade\b", r"\bgender\b",
                  r"\bblood\s*(?:group|type)\b", r"\bmarital\s*status\b", r"\brole\b"],
     "type": "select", "required": False, "searchable": False},

    # Textarea / Long description
    {"patterns": [r"\bdescription\b", r"\bdetails?\b", r"\bnotes\b", r"\bcomments\b", r"\bremarks?\b",
                  r"\bsummary\b", r"\baddress\b", r"\bterms?\b",
                  r"\bsymptoms?\b", r"\bdiagnos\w+\b", r"\breason\b", r"\bpurpose\b"],
     "type": "textarea", "required": False, "searchable": False},

    # URL
    {"patterns": [r"\bwebsite\b", r"\blink\b", r"\burl\b", r"\bsocial\s*media\b", r"\bprofile\b"],
     "type": "url", "required": False, "searchable": False},

    # Boolean / Yes-No
    {"patterns": [r"\bactive\b", r"\benabled?\b", r"\bverified\b", r"\bcompleted\b",
                  r"\bpaid\b", r"\bconfirme?d\b", r"\bapprove?d\b", r"\bconsent\b"],
     "type": "boolean", "required": False, "searchable": False},
]

# Status flow templates by domain
STATUS_TEMPLATES = {
    "lead": ["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"],
    "patient": ["registered", "checked_in", "in_consultation", "diagnosed", "treatment", "discharged", "follow_up"],
    "student": ["applied", "interviewed", "accepted", "enrolled", "active", "graduated", "withdrawn"],
    "order": ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "returned"],
    "project": ["draft", "active", "in_review", "completed", "archived"],
    "task": ["todo", "in_progress", "in_review", "done", "blocked"],
    "invoice": ["draft", "sent", "paid", "overdue", "cancelled"],
    "booking": ["inquiry", "confirmed", "deposit_paid", "completed", "cancelled", "refunded"],
    "appointment": ["scheduled", "confirmed", "in_progress", "completed", "no_show", "cancelled"],
    "shipment": ["label_created", "picked_up", "in_transit", "out_for_delivery", "delivered"],
    "expense": ["submitted", "approved", "reimbursed", "rejected"],
    "rental": ["reserved", "active", "overdue", "returned"],
    "subscription": ["trial", "active", "past_due", "cancelled", "expired"],
    "complaint": ["received", "investigating", "resolved", "closed"],
    "recruitment": ["sourced", "screened", "interviewed", "offered", "hired", "rejected"],
    "patient_appointment": ["scheduled", "confirmed", "arrived", "in_session", "completed", "no_show"],
    "default": ["new", "active", "archived"],
}

# Detect business domain from description
DOMAIN_KEYWORDS = {
    "lead": [r"\blead\b", r"\bsales?\b", r"\bprospect\b", r"\bcustomer\b", r"\benquir\w+\b"],
    "patient": [r"\bpatient\b", r"\bdoctor\b", r"\bhospital\b", r"\bclinic\b", r"\bmedical\b", r"\bhealth\b", r"\btreatment\b", r"\bdiagnos\w+\b"],
    "student": [r"\bstudent\b", r"\bschool\b", r"\bclass\b", r"\bcourse\b", r"\benroll\w+\b", r"\bacademy\b"],
    "order": [r"\border\b", r"\bproduct\b", r"\binventory\b", r"\bstock\b", r"\bshop\b", r"\bstore\b", r"\becommerce\b"],
    "project": [r"\bproject\b", r"\bmilestone\b", r"\bsprint\b", r"\bagency\b", r"\bdeliverable\b"],
    "task": [r"\btask\b", r"\btodo\b", r"\breminder\b", r"\bassign\w+\b"],
    "booking": [r"\bbooking\b", r"\breservation\b", r"\btravel\b", r"\btrip\b", r"\bhotel\b", r"\bflight\b", r"\bitinerary\b"],
    "invoice": [r"\binvoice\b", r"\bbill\b", r"\bpayment\b", r"\breceipt\b", r"\binvoice\b"],
    "appointment": [r"\bappointment\b", r"\bschedule\b", r"\bslot\b", r"\bbooking\b"],
    "expense": [r"\bexpense\b", r"\breimburs\w+\b", r"\bpetty\s*cash\b"],
    "rental": [r"\brental\b", r"\brent\b", r"\blease\b", r"\bhire\b", r"\bequipment\b", r"\breturn\s*date\b"],
    "subscription": [r"\bsubscription\b", r"\bplan\b", r"\btrial\b", r"\brenew\w+\b"],
    "complaint": [r"\bcomplaint\b", r"\bgrievance\b", r"\bissue\b", r"\bsupport\b", r"\bticket\b"],
    "recruitment": [r"\brecruit\w+\b", r"\bhiring\b", r"\bjob\b", r"\bcandidate\b", r"\bapplicant\b", r"\bresume\b"],
}


@dataclass
class GeneratedDefinition:
    """AI-generated entity definition ready for review."""
    type: str
    label: str
    icon: str
    schema: List[Dict]
    statuses: List[str]
    layout: str
    primary_field: str
    searchable_fields: List[str]
    description: str = ""
    confidence: float = 0.0


class ModuleBuilder:
    """Generates entity definitions from natural language descriptions."""

    @staticmethod
    def generate(description: str) -> GeneratedDefinition:
        """Parse a natural language description into a structured entity definition."""
        desc_lower = description.lower()

        # 1. Extract entity type name from description
        entity_type = ModuleBuilder._extract_type(description)
        label = entity_type.replace("_", " ").title()
        icon = ModuleBuilder._guess_icon(entity_type, description)

        # 2. Extract fields from description
        schema = ModuleBuilder._extract_fields(description, entity_type)

        # 3. Determine layout
        layout = ModuleBuilder._guess_layout(entity_type, schema)

        # 4. Generate status pipeline
        statuses = ModuleBuilder._generate_statuses(entity_type, description)

        # 5. Determine primary field
        primary_field = ModuleBuilder._find_primary_field(schema)

        # 6. Searchable fields
        searchable = [f["name"] for f in schema if f.get("searchable")]

        confidence = ModuleBuilder._calculate_confidence(schema, description)

        return GeneratedDefinition(
            type=entity_type,
            label=label,
            icon=icon,
            schema=schema,
            statuses=statuses,
            layout=layout,
            primary_field=primary_field,
            searchable_fields=searchable,
            description=description,
            confidence=confidence,
        )

    @staticmethod
    def _extract_type(description: str) -> str:
        """Extract the entity type from description."""
        desc_lower = description.lower()

        # Check for explicit "I need to track [X]" patterns
        patterns = [
            r"(?:track|manage|store|log|record|handle)\s+(?:my\s+)?(?:company\s+)?(?:business\s+)?(\w+(?:\s+\w+)?)(?:\s+(?:details?|data|information|records?))?",
            r"(?:create|build|make|set up|add)\s+(?:a\s+|an\s+)?(?:new\s+)?(?:system\s+(?:to|for)\s+)?(\w+(?:\s+\w+)?)",
            r"(?:need|want|require)\s+(?:a\s+|an\s+)?(?:new\s+)?(?:system\s+(?:to|for|track)\s+)?(\w+(?:\s+\w+)?)",
            r"(\w+)\s+(?:management|tracking|system)",
            r"(?:for|of)\s+(?:our\s+)?(?:company\s+)?(?:team\s+)?(\w+(?:\s+\w+)?)",
        ]

        for p in patterns:
            m = re.search(p, desc_lower)
            if m:
                raw = m.group(1).strip()
                if len(raw) > 2 and len(raw.split()) <= 3:
                    # Convert spaces to underscores
                    return raw.replace(" ", "_").lower()

        # Try to find the primary noun that represents the entity
        # Look for the first meaningful noun after keywords
        capture_patterns = [
            r"(?:track|manage)\s+(?:my\s+)?(?:company\s+)?(\w+)",
            r"(\w+)\s+(?:tracking|management|system)",
            r"(?:for|of)\s+(\w+)\s+(?:in|at|with)",
        ]

        for p in capture_patterns:
            m = re.search(p, desc_lower)
            if m:
                return m.group(1).lower().replace(" ", "_")

        # Fallback: take first meaningful word
        words = desc_lower.split()
        for w in words:
            if len(w) > 3 and w not in ("need", "want", "have", "this", "that", "with", "from", "track", "manage", "store", "keep"):
                return w.lower()

        return "record"

    @staticmethod
    def _extract_fields(description: str, entity_type: str) -> List[Dict]:
        """Extract fields from the description — matches natural language to schema types."""
        desc_lower = description.lower()
        seen_fields = set()
        schema = []

        # Always add a primary name/title field
        primary_field_name = ModuleBuilder._guess_primary_field_name(entity_type)
        schema.append({
            "name": primary_field_name,
            "label": primary_field_name.replace("_", " ").title(),
            "type": "text",
            "required": True,
            "searchable": True,
        })
        seen_fields.add(primary_field_name)

        # Detect explicit field mentions in description
        # Pattern: "field1, field2, field3" or "field1 and field2"
        # Look for list patterns like "item name, customer, rental period, return date"
        field_list_match = re.search(r"(?:fields?\s*(?:like|such as|including|are)?\s*:?\s*)?(.+?)(?:\s*(?:and\s+)?I\s+(?:need|want|require)|\.|$)", desc_lower)
        if field_list_match:
            list_text = field_list_match.group(1)

        # Track each comma-separated term
        # First check for explicit list
        list_items = re.findall(r'(?:^|,|\band\b)\s*([a-zA-Z][a-zA-Z\s]{2,50}?)(?=\s*[,\n]|\sand\s|\.|$)', desc_lower)

        for item_text in list_items:
            item_clean = item_text.strip()
            if not item_clean or len(item_clean) < 3:
                continue

            # Match against field patterns
            for pattern_config in FIELD_PATTERNS:
                for p in pattern_config["patterns"]:
                    if re.search(p, item_clean.lower()):
                        field_name = ModuleBuilder._item_to_field_name(item_clean, pattern_config)

                        if field_name not in seen_fields:
                            schema.append({
                                "name": field_name,
                                "label": item_clean.title(),
                                "type": pattern_config.get("type", "text"),
                                "required": pattern_config.get("required", False),
                                "searchable": pattern_config.get("searchable", False),
                            })
                            seen_fields.add(field_name)
                        break

        # Also scan individual words — but only if we didn't get enough from list extraction
        # to avoid adding redundant single-word fields
        if len(schema) < 4:
            for word in re.findall(r'\b[a-zA-Z]{3,}\b', desc_lower):
                if word not in seen_fields:
                    # Skip entity type name words and parts of existing field names
                    if any(word == part for part in entity_type.split('_')):
                        continue
                    if any(word in sf.split('_') for sf in seen_fields):
                        continue
                    for pattern_config in FIELD_PATTERNS:
                        for p in pattern_config["patterns"]:
                            if re.fullmatch(p.strip("\\b"), word) or re.search(p, word):
                                field_name = word.replace(" ", "_")
                                if field_name not in seen_fields:
                                    schema.append({
                                        "name": field_name,
                                        "label": word.title(),
                                        "type": pattern_config.get("type", "text"),
                                        "required": pattern_config.get("required", False),
                                        "searchable": pattern_config.get("searchable", False),
                                    })
                                    seen_fields.add(field_name)
                                break

        # Don't add too many fields (max 15)
        if len(schema) > 15:
            schema = schema[:15]

        return schema

    @staticmethod
    def _item_to_field_name(item_text: str, config: Dict) -> str:
        """Convert a natural language item name to a snake_case field name."""
        # Use the matched pattern to extract a clean name
        field_type = config.get("type", "text")
        item_lower = item_text.lower().strip()

        # Map common phrases
        name_mapping = {
            "customer": "customer_name", "client": "customer_name", "patient": "patient_name",
            "student": "student_name", "employee": "employee_name",
            "rental period": "rental_period", "return date": "return_date",
            "deposit": "deposit_amount", "rental fee": "rental_fee",
            "due date": "due_date", "start date": "start_date", "end date": "end_date",
            "check in": "check_in", "check out": "check_out",
            "number of": "count", "first name": "first_name", "last name": "last_name",
        }

        if item_lower in name_mapping:
            return name_mapping[item_lower]

        # Generic: convert to snake_case
        name = re.sub(r'[^a-zA-Z0-9\s]', '', item_lower)
        name = re.sub(r'\s+', '_', name.strip())
        return name[:40]

    @staticmethod
    def _guess_primary_field_name(entity_type: str) -> str:
        """Guess the primary field name based on entity type."""
        type_map = {
            "lead": "customer_name",
            "patient": "patient_name",
            "student": "student_name",
            "order": "order_name",
            "project": "project_name",
            "task": "title",
            "booking": "booking_name",
            "invoice": "invoice_title",
            "appointment": "title",
            "expense": "description",
            "rental": "item_name",
            "subscription": "plan_name",
            "complaint": "subject",
            "recruitment": "candidate_name",
            "product": "product_name",
            "supplier": "supplier_name",
            "employee": "employee_name",
        }
        return type_map.get(entity_type, "name")

    @staticmethod
    def _guess_icon(entity_type: str, description: str) -> str:
        """Guess appropriate icon emoji."""
        icons = {
            "lead": "👤", "patient": "🏥", "student": "🎓", "order": "📦",
            "project": "📊", "task": "✅", "booking": "📅", "invoice": "💰",
            "appointment": "📋", "expense": "💸", "rental": "🔧", "subscription": "🔄",
            "complaint": "⚠️", "recruitment": "👥", "product": "🏷️", "supplier": "🚚",
            "employee": "🧑‍💼", "shipment": "📬", "inventory": "📦", "account": "🏦",
        }
        for key, icon in icons.items():
            if key in entity_type or key in description.lower():
                return icon
        return "📋"

    @staticmethod
    def _guess_layout(entity_type: str, schema: List[Dict]) -> str:
        """Determine the best layout for this entity type."""
        # Kanban: entities with defined status flow (sales, tasks, patients)
        kanban_types = {"lead", "task", "patient", "student", "order", "project",
                        "recruitment", "appointment", "complaint", "rental"}
        if entity_type in kanban_types:
            return "kanban"

        # Calendar: date-heavy entities
        calendar_types = {"appointment", "booking", "event", "meeting", "schedule"}
        if entity_type in calendar_types:
            return "calendar"

        # Cards: visually rich
        cards_types = {"product", "service", "itinerary", "portfolio"}
        if entity_type in cards_types:
            return "cards"

        # Default to table
        return "table"

    @staticmethod
    def _generate_statuses(entity_type: str, description: str) -> List[str]:
        """Generate appropriate status pipeline."""
        desc_lower = description.lower()

        # Check for specific domain
        best_domain = "default"
        best_score = 0

        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = sum(1 for k in keywords if re.search(k, desc_lower))
            if score > best_score:
                best_score = score
                best_domain = domain

        # Check for exact entity type match
        for template_name in STATUS_TEMPLATES:
            if template_name == entity_type or entity_type.startswith(template_name) or template_name.startswith(entity_type):
                best_domain = template_name
                break

        result = STATUS_TEMPLATES.get(best_domain, STATUS_TEMPLATES["default"])

        # If many fields detected, use a more detailed pipeline
        return result

    @staticmethod
    def _find_primary_field(schema: List[Dict]) -> str:
        """Find the best primary field (first text or name field)."""
        for f in schema:
            if f.get("name") in ("customer_name", "patient_name", "student_name",
                                 "name", "title", "subject", "description",
                                 "item_name", "supplier_name", "product_name"):
                return f["name"]
        return schema[0]["name"] if schema else "name"

    @staticmethod
    def _calculate_confidence(schema: List[Dict], description: str) -> float:
        """How confident we are in this generation (0-1)."""
        if not schema:
            return 0.2

        # More fields = more information extracted = higher confidence
        field_count = len(schema)

        # Check if description has structured lists (higher confidence)
        has_commas = "," in description
        has_field_keywords = any(kw in description.lower() for kw in ["track", "manage", "field", "column", "detail"])

        base = 0.6
        if field_count >= 3:
            base += 0.15
        if field_count >= 5:
            base += 0.1
        if has_commas:
            base += 0.05
        if has_field_keywords:
            base += 0.05

        return min(base, 0.95)


# ---------------------------------------------------------------------------
# Preview & Save
# ---------------------------------------------------------------------------

def preview_from_description(description: str) -> dict:
    """Generate a preview of the entity definition from description."""
    generated = ModuleBuilder.generate(description)
    return {
        "type": generated.type,
        "label": generated.label,
        "icon": generated.icon,
        "schema": generated.schema,
        "statuses": generated.statuses,
        "layout": generated.layout,
        "primary_field": generated.primary_field,
        "searchable_fields": generated.searchable_fields,
        "confidence": generated.confidence,
        "description": description,
    }


def save_from_preview(preview: dict, tenant_id: int) -> EntityDefinition:
    """Save a preview dict as a real EntityDefinition."""
    # Clean field names
    schema = []
    for f in preview.get("schema", []):
        schema.append({
            "name": f.get("name", "field"),
            "label": f.get("label", "Field"),
            "type": f.get("type", "text"),
            "required": f.get("required", False),
            "searchable": f.get("searchable", False),
            "options": f.get("options", []),
        })

    searchable = [f["name"] for f in schema if f.get("searchable")]
    entity_type = preview.get("type", "record").strip().lower()

    definition = EntityDefinition(
        tenant_id=tenant_id,
        type=entity_type,
        label=preview.get("label", entity_type.title()),
        label_plural=preview.get("label_plural", f"{preview.get('label', entity_type.title())}s"),
        icon=preview.get("icon", "📋"),
        schema=schema,
        statuses=preview.get("statuses", ["new", "active", "archived"]),
        layout=preview.get("layout", "table"),
        primary_field=preview.get("primary_field", schema[0]["name"] if schema else "name"),
        searchable_fields=searchable,
    )
    db.session.add(definition)
    db.session.commit()
    return definition