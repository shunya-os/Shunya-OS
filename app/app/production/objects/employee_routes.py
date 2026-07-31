"""SHUNYA — Employee Profile routes.

CRUD for EmployeeProfile (Person + EmployeeProfile).
Mounted at /api/v1/objects/employee.
"""
from datetime import datetime

from flask import request, jsonify, g
from werkzeug.exceptions import BadRequest, NotFound

from app import db
from app.auth_routes import login_required
from app.models import Person, PersonIdentity, EmployeeProfile
from app.production.objects import objects_bp


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _require_json() -> dict:
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Request body must be valid JSON")
    return data


def _require_field(data: dict, field: str, label: str = "") -> str:
    label = label or field
    value = data.get(field)
    if not value or not str(value).strip():
        raise BadRequest(f"'{label}' is required")
    return str(value).strip()


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def _employee_to_dict(person: Person, profile: EmployeeProfile) -> dict:
    """Serialize an employee (Person + EmployeeProfile) to the standard envelope."""
    identities = PersonIdentity.query.filter_by(person_id=person.id).all()
    email = next(
        (i.identity_value for i in identities if i.identity_type == "email"), ""
    )
    phone = next(
        (i.identity_value for i in identities if i.identity_type == "phone"), ""
    )

    return {
        "id": profile.id,
        "person_id": person.id,
        "person_name": person.canonical_name,
        "email": email,
        "phone": phone,
        "employee_code": profile.employee_code or "",
        "department": profile.department or "",
        "role": profile.role or "",
        "status": profile.status or "active",
        "joined_at": profile.joined_at.isoformat() if profile.joined_at else None,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@objects_bp.route("/employee", methods=["POST"])
@login_required
def create_employee():
    """Create a new employee (Person + EmployeeProfile).

    Request body:
    {
        "name": "Jane Smith",           # required → Person.canonical_name
        "email": "jane@acme.com",       # optional → PersonIdentity
        "phone": "+1-555-0123",         # optional → PersonIdentity
        "employee_code": "EMP001",      # optional → EmployeeProfile.employee_code
        "department": "Engineering",    # optional → EmployeeProfile.department
        "role": "Senior Engineer",      # optional → EmployeeProfile.role
        "joined_at": "2025-01-15"       # optional → EmployeeProfile.joined_at (ISO date)
    }
    """
    data = _require_json()
    name = _require_field(data, "name", "Name")

    # -- Create Person --
    person = Person(
        tenant_id=getattr(g, "tenant_id", None),
        canonical_name=name,
        preferred_name=data.get("preferred_name", ""),
        status="active",
    )
    db.session.add(person)
    db.session.flush()  # get person.id

    # -- Attach PersonIdentity records --
    email = data.get("email", "").strip()
    if email:
        db.session.add(
            PersonIdentity(
                person_id=person.id,
                identity_type="email",
                identity_value=email,
                normalized_value=email.lower().strip(),
            )
        )

    phone = data.get("phone", "").strip()
    if phone:
        db.session.add(
            PersonIdentity(
                person_id=person.id,
                identity_type="phone",
                identity_value=phone,
                normalized_value=phone,
            )
        )

    # -- Parse joined_at --
    joined_at = None
    joined_at_raw = data.get("joined_at", "").strip()
    if joined_at_raw:
        try:
            joined_at = datetime.fromisoformat(joined_at_raw)
        except (ValueError, TypeError):
            raise BadRequest(
                f"Invalid 'joined_at' format '{joined_at_raw}'. Expected ISO date (e.g., 2025-01-15)."
            )

    # -- Create EmployeeProfile --
    profile = EmployeeProfile(
        person_id=person.id,
        tenant_id=getattr(g, "tenant_id", None),
        employee_code=data.get("employee_code", "").strip() or None,
        department=data.get("department", ""),
        role=data.get("role", ""),
        joined_at=joined_at,
        status="active",
    )
    db.session.add(profile)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": _employee_to_dict(person, profile),
    }), 201


@objects_bp.route("/employee", methods=["GET"])
@login_required
def list_employees():
    """List employees, paginated and filterable.

    Query params:
        page (int, default 1)
        per_page (int, default 20, max 100)
        department (str) — filter by department
        status (str) — filter by status (default shows all)
        tenant_id (int) — filter by tenant
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    # Build query with Person join for name enrichment
    query = EmployeeProfile.query.join(Person, EmployeeProfile.person_id == Person.id)

    # Filters
    department = request.args.get("department")
    if department:
        query = query.filter(EmployeeProfile.department == department)

    status = request.args.get("status")
    if status:
        query = query.filter(EmployeeProfile.status == status)

    tenant_id = request.args.get("tenant_id", type=int)
    if tenant_id:
        query = query.filter(EmployeeProfile.tenant_id == tenant_id)

    # Order by newest first
    query = query.order_by(EmployeeProfile.created_at.desc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    employees = []
    for profile in pagination.items:
        person = Person.query.get(profile.person_id)
        if person:
            employees.append(_employee_to_dict(person, profile))

    return jsonify({
        "success": True,
        "data": employees,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    })


@objects_bp.route("/employee/<int:employee_id>", methods=["GET"])
@login_required
def get_employee(employee_id: int):
    """Get a single employee by EmployeeProfile id with person details."""
    profile = EmployeeProfile.query.get(employee_id)
    if not profile:
        raise NotFound("Employee not found")

    person = Person.query.get(profile.person_id)
    if not person:
        raise NotFound("Associated person record not found")

    return jsonify({
        "success": True,
        "data": _employee_to_dict(person, profile),
    })


@objects_bp.route("/employee/<int:employee_id>", methods=["PUT"])
@login_required
def update_employee(employee_id: int):
    """Update employee fields. Does NOT update person_id.

    Request body (all fields optional):
    {
        "department": "Engineering",
        "role": "Lead Engineer",
        "status": "active",
        "employee_code": "EMP001",
        "joined_at": "2025-06-01"
    }
    """
    profile = EmployeeProfile.query.get(employee_id)
    if not profile:
        raise NotFound("Employee not found")

    data = _require_json()

    # Update allowed fields (person_id is NOT updated)
    if "department" in data:
        profile.department = data["department"]
    if "role" in data:
        profile.role = data["role"]
    if "status" in data:
        profile.status = data["status"]
    if "employee_code" in data:
        code = data["employee_code"].strip()
        profile.employee_code = code or None

    if "joined_at" in data:
        joined_at_raw = data["joined_at"].strip()
        if joined_at_raw:
            try:
                profile.joined_at = datetime.fromisoformat(joined_at_raw)
            except (ValueError, TypeError):
                raise BadRequest(
                    f"Invalid 'joined_at' format '{joined_at_raw}'. Expected ISO date."
                )
        else:
            profile.joined_at = None

    db.session.commit()

    person = Person.query.get(profile.person_id)
    return jsonify({
        "success": True,
        "data": _employee_to_dict(person, profile) if person else None,
    })


@objects_bp.route("/employee/<int:employee_id>", methods=["DELETE"])
@login_required
def delete_employee(employee_id: int):
    """Soft-delete an employee by setting status to 'inactive'."""
    profile = EmployeeProfile.query.get(employee_id)
    if not profile:
        raise NotFound("Employee not found")

    profile.status = "inactive"
    db.session.commit()

    person = Person.query.get(profile.person_id)
    return jsonify({
        "success": True,
        "data": _employee_to_dict(person, profile) if person else None,
        "message": "Employee soft-deleted (status set to inactive)",
    }), 200