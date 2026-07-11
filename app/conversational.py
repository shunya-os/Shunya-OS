"""Shunya OS — Conversational Form-Filling Engine.

Users describe what they want in natural language, the AI parses it,
extracts structured data, and presents a confirmation card.
No manual form filling needed.
"""
import re, json
from typing import Optional
from flask import g
from app import db
from app.models import EntityDefinition, Entity


class ConversationalEngine:
    """Parses natural language into structured entity data."""

    @staticmethod
    def parse_and_fill(text: str, entity_type: str, tenant_id: int) -> dict:
        """Parse natural language text into structured data for an entity type.
        
        Returns:
        - parsed_data: dict of field_name -> value
        - confidence: overall confidence (0-1)
        - missing_required: list of required fields not found
        - suggested_status: suggested initial status
        """
        definition = EntityDefinition.query.filter_by(
            tenant_id=tenant_id, type=entity_type, is_active=True
        ).first()
        if not definition:
            return {"error": f"Unknown entity type: {entity_type}"}

        text_lower = text.lower()
        parsed = {}
        missing = []
        confidence_scores = []

        for field in definition.schema:
            fname = field["name"]
            flabel = field.get("label", fname).lower()
            ftype = field.get("type", "text")

            value = None
            confidence = 0

            if ftype == "text":
                # Match patterns like "customer name: Sharma" or "for Sharma family"
                for pattern in [
                    rf"{flabel}\s*[:is]+\s*(.+?)(?:\n|$|,|\sand\s)",
                    rf"{fname}\s*[:is]+\s*(.+?)(?:\n|$|,|\sand\s)",
                ]:
                    m = re.search(pattern, text, re.IGNORECASE)
                    if m:
                        value = m.group(1).strip()
                        confidence = 0.9
                        break

                # Generic name extraction for customer_name/patient_name
                if not value and fname in ("customer_name", "patient_name", "name", "student_name"):
                    for prefix in ["for ", "called ", "named "]:
                        if prefix in text_lower:
                            idx = text_lower.find(prefix) + len(prefix)
                            rest = text[idx:].strip()
                            value = re.split(r'[,.]', rest)[0].strip()
                            confidence = 0.7
                            break

                # Extract from phrases like "Sharma family's Bali trip"
                if not value and fname == "customer_name":
                    m = re.search(r"(\w+\s+family|\w+\s+and\s+\w+)", text)
                    if m:
                        value = m.group(1).strip()
                        confidence = 0.6

            elif ftype == "number":
                # Match amounts like "budget 2.5L", "amount 50000"
                num_patterns = [
                    rf"{flabel}\s*[:is]+\s*(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)\s*(L|K|lakh|k|thousand)?",
                    rf"(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)\s*(L|K|lakh|k|thousand)?\s*(?:{flabel})",
                ]
                for pattern in num_patterns:
                    m = re.search(pattern, text, re.IGNORECASE)
                    if m:
                        raw = m.group(1).replace(",", "")
                        multiplier = (m.group(2) or "").lower()
                        value = float(raw)
                        if multiplier in ("l", "lakh"):
                            value *= 100000
                        elif multiplier in ("k", "thousand"):
                            value *= 1000
                        confidence = 0.8
                        break

                # Extract bare numbers
                if not value and fname == "budget":
                    nums = re.findall(r'(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)\s*(L|K|lakh|k)?', text)
                    if nums:
                        raw = nums[-1][0].replace(",", "")
                        mult = nums[-1][1].lower()
                        value = float(raw)
                        if mult in ("l", "lakh"): value *= 100000
                        elif mult in ("k", "thousand"): value *= 1000
                        confidence = 0.6

            elif ftype in ("dropdown", "select"):
                # Match options
                options = field.get("options", [])
                for opt in options:
                    if opt.lower() in text_lower:
                        value = opt
                        confidence = 0.9
                        break

            elif ftype == "textarea":
                # Grab everything after "notes:" or similar
                for prefix in [f"{flabel}:", f"{fname}:"]:
                    if prefix in text_lower:
                        idx = text_lower.find(prefix) + len(prefix)
                        value = text[idx:].strip()
                        confidence = 0.7
                        break

            if value:
                parsed[fname] = value
                confidence_scores.append(confidence)
            elif field.get("required"):
                missing.append(fname)

        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

        return {
            "parsed_data": parsed,
            "confidence": round(overall_confidence, 2),
            "missing_required": missing,
            "suggested_status": definition.statuses[0] if definition.statuses else "new",
        }

    @staticmethod
    def build_confirmation_card(parsed_data: dict, definition: EntityDefinition, code: str) -> dict:
        """Build a confirmation card for the user to review before creation."""
        fields_display = []
        for field in definition.schema:
            fname = field["name"]
            if fname in parsed_data:
                fields_display.append({
                    "label": field.get("label", fname),
                    "value": parsed_data[fname],
                    "type": field.get("type", "text"),
                })

        return {
            "icon": definition.icon,
            "title": f"New {definition.label}",
            "code": code,
            "fields": fields_display,
            "instructions": "Review and confirm, or tell me what to change.",
        }