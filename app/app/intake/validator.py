"""
Validation — row-level and field-level validation for intake candidates.
"""
import re
from typing import Optional
from app.shunya.identity import normalize_email, normalize_phone


class ValidationMessage:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKING = "blocking"


class RowValidator:
    """Validates intake rows at field and row level."""

    @staticmethod
    def validate_email(value: str) -> tuple[str, str]:
        """Returns (status, message)."""
        if not value or not value.strip():
            return ValidationMessage.INFO, ""
        normalized = normalize_email(value)
        if "@" not in normalized or "." not in normalized.split("@")[-1]:
            return ValidationMessage.ERROR, f"Invalid email format: {value}"
        return ValidationMessage.INFO, ""

    @staticmethod
    def validate_phone(value: str) -> tuple[str, str]:
        """Returns (status, message)."""
        if not value or not value.strip():
            return ValidationMessage.INFO, ""
        normalized = normalize_phone(value)
        digits_only = normalized.lstrip("+")
        if len(digits_only) < 7:
            return ValidationMessage.ERROR, f"Phone too short: {value}"
        return ValidationMessage.INFO, ""

    @staticmethod
    def validate_required(value, field_name: str) -> tuple[str, str]:
        if not value or str(value).strip() == "":
            return ValidationMessage.BLOCKING, f"Missing required field: {field_name}"
        return ValidationMessage.INFO, ""

    def validate_row(self, row: dict, field_mappings: list[dict]) -> tuple[str, list[dict]]:
        """Validate a single row against field mappings. Returns (overall_status, messages)."""
        messages = []
        worst = ValidationMessage.INFO

        has_name = False
        has_email = False
        has_phone = False

        for mapping in field_mappings:
            col = mapping["source_column"]
            target = mapping["target_field"]
            value = row.get(col, "")

            if target == "person.canonical_name" and value:
                has_name = True
            elif target == "identity.email":
                status, msg = self.validate_email(value)
                if status == ValidationMessage.ERROR:
                    messages.append({"field": col, "severity": status, "message": msg})
                    worst = self._worsen(worst, status)
                if value:
                    has_email = True
            elif target == "identity.phone":
                status, msg = self.validate_phone(value)
                if status == ValidationMessage.ERROR:
                    messages.append({"field": col, "severity": status, "message": msg})
                    worst = self._worsen(worst, status)
                if value:
                    has_phone = True

        # At least one identifier should exist
        if not has_name and not has_email and not has_phone:
            messages.append({"field": "_row", "severity": ValidationMessage.BLOCKING,
                             "message": "Row has no name, email, or phone — insufficient identity"})
            worst = self._worsen(worst, ValidationMessage.BLOCKING)

        return worst, messages

    @staticmethod
    def _worsen(current: str, new: str) -> str:
        order = ["info", "warning", "error", "blocking"]
        return new if order.index(new) > order.index(current) else current