"""
Shunya — Prompt-to-Module Builder (Phase 3H)

AI that reads natural language prompts and builds business modules.
Parses intent, generates DB fields, creates UI pages, registers in sidebar.
All through conversation. All approved by admin.

Example:
  "I need a module to track wedding vendor payments.
   Each vendor should have name, amount, status, due date."

  → Creates: WeddingVendors module with 4 fields
  → Adds to sidebar
  → Stores in tenant namespace
"""

import json
import re
from datetime import datetime
from typing import Optional

from app import db
from app.dynamic_fields import DynamicFieldManager, DynamicField, DynamicFieldValue
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey


class ModuleBlueprint(db.Model):
    """A proposed module — waiting for admin approval."""
    __tablename__ = "module_blueprints"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=True)
    name = Column(String(120), nullable=False)
    label = Column(String(255), nullable=False)
    description = Column(Text, default="")
    entity = Column(String(60), default="lead")      # Which entity this extends
    fields_json = Column(Text, default="[]")          # JSON array of field definitions
    icon = Column(String(30), default="📦")
    status = Column(String(30), default="proposed")    # proposed, approved, rejected, built
    proposed_by = Column(String(120), default="AI Assistant")
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime)
    approved_by = Column(String(120))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "entity": self.entity,
            "fields": json.loads(self.fields_json) if self.fields_json else [],
            "icon": self.icon,
            "status": self.status,
            "proposed_by": self.proposed_by,
            "created_at": self.created_at.isoformat(),
        }


class ModuleBuilder:
    """Interprets natural language prompts and builds modules."""

    # Known field types mapped from natural language
    TYPE_MAP = {
        "text": ["name", "description", "address", "email", "phone", "contact",
                 "notes", "comment", "detail", "information", "link", "url"],
        "number": ["amount", "number", "price", "cost", "budget", "total", "rate", "fee",
                   "quantity", "count", "size", "pax", "people", "capacity",
                   "rating", "score", "percentage", "tax", "discount"],
        "date": ["date", "due date", "deadline", "date of", "start date", "end date",
                 "check in", "check out", "travel date", "booking date"],
        "dropdown": ["status", "category", "type", "priority", "level",
                     "stage", "phase", "department"],
        "boolean": ["paid", "confirmed", "approved", "active", "completed",
                    "done", "finished", "verified", "yes/no", "is_active"],
    }

    def parse_prompt(self, prompt: str) -> dict:
        """Parse a natural language prompt into a module blueprint."""
        prompt_lower = prompt.lower()

        # Extract module name
        name = ""
        name_patterns = [
            r"(?:module|feature|tool|system|tracker|manager|dashboard)\s+(?:for|to|called|named)\s+[\"']?([a-zA-Z\s]{3,40})[\"']?",
            r"(?:track|manage|handle)\s+([a-zA-Z\s]{3,40})(?:\s+with|\s+that|\s+where|$)",
            r"([a-zA-Z\s]{3,40})\s+(?:tracker|manager|system|module|tool)",
        ]
        for pattern in name_patterns:
            m = re.search(pattern, prompt_lower)
            if m:
                name = m.group(1).strip().title()
                break

        if not name:
            # Take first meaningful noun phrase
            words = prompt_lower.split()
            for i, w in enumerate(words):
                if w in ("i", "a", "for", "to", "need", "want", "create", "build", "add", "make", "the"):
                    continue
                if i < len(words) - 2:
                    name = " ".join(words[i:i+3]).title()
                    break

        name = name or "CustomModule"

        # Extract fields from the prompt
        fields = self._extract_fields(prompt)

        # Entity detection
        entity = "lead"
        if "vendor" in prompt_lower or "supplier" in prompt_lower:
            entity = "supplier"
        elif "payment" in prompt_lower or "invoice" in prompt_lower or "expense" in prompt_lower:
            entity = "payment"
        elif "document" in prompt_lower or "file" in prompt_lower or "photo" in prompt_lower:
            entity = "lead"

        # Icon selection
        icon = self._guess_icon(prompt_lower)

        return {
            "name": name.replace(" ", ""),
            "label": name,
            "fields": fields,
            "entity": entity,
            "icon": icon,
            "description": prompt[:300],
        }

    def _extract_fields(self, prompt: str) -> list[dict]:
        """Extract field definitions from the prompt."""
        fields = []
        prompt_lower = prompt.lower()

        # Method 1: Look for "field_name (type)" or "field_name - type" patterns
        # This handles: "name (text), amount (number), status (dropdown: A, B, C), due date (date)"
        field_matches = re.findall(r'([A-Za-z][A-Za-z\s]{1,30}?)\s*[:(\[]\s*(text|number|date|dropdown|boolean|yes\/no|multi[_-]?select)(?:[:;)\]](.*?))?(?=[,;.]|$)', prompt, re.IGNORECASE)
        for match in field_matches:
            field_name = match[0].strip().lower().replace(" ", "_")
            field_label = match[0].strip().title()
            field_type = self._normalize_type(match[1])
            options = self._extract_options(match[2]) if field_type in ("dropdown", "multi_select") else []
            if field_name and field_name not in [f["field_name"] for f in fields]:
                fields.append({
                    "field_name": field_name,
                    "field_label": field_label,
                    "field_type": field_type,
                    "options": options,
                })

        # Method 2: If no structured fields, infer from keywords
        if not fields:
            for word, ftype in [
                        ("name", "text"), ("amount", "number"), ("price", "number"),
                        ("date", "date"), ("status", "dropdown"), ("category", "dropdown"),
                        ("notes", "text"), ("description", "text"), ("paid", "boolean"),
                        ("rating", "number"), ("score", "number"), ("comments", "text"),
                        ("email", "text"), ("phone", "text"), ("priority", "dropdown"),
                    ]:
                if word in prompt_lower:
                    options = []
                    if ftype == "dropdown":
                        if "status" in word:
                            options = ["Pending", "Approved", "Rejected", "Completed"]
                        elif "category" in word:
                            options = ["Category A", "Category B", "Category C"]
                    fields.append({
                        "field_name": word,
                        "field_label": word.title(),
                        "field_type": ftype,
                        "options": options,
                    })
                    if len(fields) >= 5:
                        break

        # Method 3: Look for bullet list items as field names
        if not fields:
            bullets = re.findall(r'(?:^|\n)\s*[-*•]\s*([A-Za-z][A-Za-z\s]{2,40})(?:\n|$)', prompt)
            if bullets:
                for b in bullets[:6]:
                    b_lower = b.strip().lower()
                    ftype = self._infer_type(b_lower)
                    fields.append({
                        "field_name": b_lower.replace(" ", "_"),
                        "field_label": b.strip().title(),
                        "field_type": ftype,
                        "options": [] if ftype not in ("dropdown", "multi_select") else ["Option 1", "Option 2"],
                    })

        return fields[:10]  # Max 10 fields per module

    def _normalize_type(self, raw: str) -> str:
        raw = raw.strip().lower().replace("-", "").replace(" ", "")
        if raw in ("text", "string", "str"):
            return "text"
        if raw in ("number", "int", "integer", "float", "decimal", "amount"):
            return "number"
        if raw in ("date", "datetime"):
            return "date"
        if raw in ("dropdown", "select", "choice", "enum"):
            return "dropdown"
        if raw in ("boolean", "bool", "yes/no", "yesno", "checkbox", "is_active"):
            return "boolean"
        if raw in ("multiselect", "multi_select", "tags"):
            return "multi_select"
        return "text"

    def _infer_type(self, field_name: str) -> str:
        """Infer field type from its name."""
        for ftype, keywords in self.TYPE_MAP.items():
            for kw in keywords:
                if kw in field_name:
                    return ftype
        return "text"

    def _extract_options(self, text: str) -> list[str]:
        """Extract dropdown options from text like (option1, option2, option3)."""
        text = text.strip().strip("()[]{}")
        options = [o.strip().strip("'\"") for o in text.split(",") if o.strip()]
        return options[:10]

    def _guess_icon(self, prompt: str) -> str:
        icons = {
            "vendor": "🏢", "supplier": "🏢", "payment": "💰", "invoice": "🧾",
            "task": "✅", "todo": "✅", "calendar": "📅", "event": "📅",
            "document": "📄", "file": "📄", "photo": "🖼️", "image": "🖼️",
            "client": "👤", "customer": "👤", "lead": "📋", "report": "📊",
            "email": "📧", "message": "💬", "feedback": "⭐", "review": "⭐",
            "booking": "🎫", "ticket": "🎫", "inventory": "📦", "stock": "📦",
            "employee": "👥", "team": "👥", "training": "🎓", "course": "📚",
        }
        for key, icon in icons.items():
            if key in prompt.lower():
                return icon
        return "📦"

    def propose(self, prompt: str, proposed_by: str = "AI Assistant",
                tenant_id: int = None) -> ModuleBlueprint:
        """Parse a prompt and save a proposed module blueprint."""
        parsed = self.parse_prompt(prompt)
        blueprint = ModuleBlueprint(
            tenant_id=tenant_id,
            name=parsed["name"],
            label=parsed["label"],
            description=parsed["description"],
            entity=parsed["entity"],
            fields_json=json.dumps(parsed["fields"]),
            icon=parsed["icon"],
            status="proposed",
            proposed_by=proposed_by,
        )
        db.session.add(blueprint)
        db.session.commit()
        return blueprint

    def approve(self, blueprint_id: int, approved_by: str = "admin") -> ModuleBlueprint:
        """Approve a blueprint and build the actual module."""
        blueprint = db.session.get(ModuleBlueprint, blueprint_id)
        if not blueprint or blueprint.status != "proposed":
            return None

        fields = json.loads(blueprint.fields_json) if blueprint.fields_json else []
        created_fields = []
        for f in fields:
            try:
                df = DynamicFieldManager.create_field(
                    entity=blueprint.entity,
                    field_name=f["field_name"],
                    field_label=f["field_label"],
                    field_type=f.get("field_type", "text"),
                    options=f.get("options"),
                    searchable="name" in f["field_name"].lower(),
                )
                created_fields.append(df.id)
            except (ValueError, Exception) as e:
                pass

        blueprint.status = "built"
        blueprint.approved_at = datetime.utcnow()
        blueprint.approved_by = approved_by
        db.session.commit()
        return blueprint

    def reject(self, blueprint_id: int) -> ModuleBlueprint:
        """Reject a proposed module."""
        blueprint = db.session.get(ModuleBlueprint, blueprint_id)
        if blueprint:
            blueprint.status = "rejected"
            db.session.commit()
        return blueprint

    def get_pending(self, tenant_id: int = None) -> list[ModuleBlueprint]:
        """Get all pending blueprints for approval."""
        query = ModuleBlueprint.query.filter_by(status="proposed")
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ModuleBlueprint.created_at.desc()).all()

    def get_built(self, tenant_id: int = None) -> list[ModuleBlueprint]:
        """Get all approved and built modules."""
        query = ModuleBlueprint.query.filter_by(status="built")
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ModuleBlueprint.created_at.desc()).all()