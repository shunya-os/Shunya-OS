"""
Field mapping — deterministic alias recognition for common human fields.
"""
from app.models import IntakeFieldMapping


# Configurable alias map — extensible, NOT hardcoded to travel
ALIAS_MAP = {
    # Name
    "name": "person.canonical_name",
    "full_name": "person.canonical_name",
    "customer_name": "person.canonical_name",
    "employee_name": "person.canonical_name",
    "contact_name": "person.canonical_name",
    "client_name": "person.canonical_name",
    "first_name": "person.first_name",  # Needs composition
    "last_name": "person.last_name",
    # Email
    "email": "identity.email",
    "email_address": "identity.email",
    "e_mail": "identity.email",
    "mail": "identity.email",
    # Phone
    "phone": "identity.phone",
    "mobile": "identity.phone",
    "mobile_number": "identity.phone",
    "contact_number": "identity.phone",
    "phone_number": "identity.phone",
    "telephone": "identity.phone",
    "cell": "identity.phone",
    "cell_phone": "identity.phone",
    # Reference
    "employee_id": "identity.employee_ref",
    "employee_code": "identity.employee_ref",
    "customer_id": "identity.customer_ref",
    "client_id": "identity.customer_ref",
    "supplier_id": "identity.supplier_ref",
    "member_id": "identity.customer_ref",
    "account_number": "identity.customer_ref",
    # Department
    "department": "employee.department",
    "dept": "employee.department",
    # Role
    "role": "employee.role",
    "designation": "employee.role",
    "title": "employee.role",
    "job_title": "employee.role",
    # Status
    "status": "employee.status",
    "employment_status": "employee.status",
}


class FieldMapper:
    """Maps source columns to canonical target fields using deterministic aliases."""

    def __init__(self, alias_map: dict = None):
        self._alias_map = alias_map or ALIAS_MAP

    def map_column(self, column_name: str) -> tuple[str, str, float]:
        """Map a source column to a target field.
        Returns (target_field, mapping_method, confidence)."""
        normalized = column_name.strip().lower().replace(" ", "_").replace("-", "_")
        if normalized in self._alias_map:
            target = self._alias_map[normalized]
            return target, "alias", 1.0
        return "", "unmapped", 0.0

    def map_all(self, columns: list[str]) -> list[dict]:
        """Map all columns and return mapping records."""
        results = []
        for col in columns:
            target, method, confidence = self.map_column(col)
            results.append({
                "source_column": col,
                "target_field": target,
                "mapping_method": method,
                "confidence": confidence,
                "mapping_status": "mapped" if target else "unmapped",
            })
        return results

    def save_mappings(self, session_id: int, mappings: list[dict], db_session=None) -> list[IntakeFieldMapping]:
        """Persist field mappings for an intake session."""
        session = db_session or __import__("flask").current_app.extensions["sqlalchemy"].session
        records = []
        for m in mappings:
            target_domain = m["target_field"].split(".")[0] if m["target_field"] else ""
            record = IntakeFieldMapping(
                session_id=session_id,
                source_column=m["source_column"],
                target_field=m["target_field"],
                target_domain=target_domain,
                mapping_status=m["mapping_status"],
                mapping_method=m["mapping_method"],
                confidence=m.get("confidence", 0.0),
            )
            session.add(record)
            records.append(record)
        session.commit()
        return records