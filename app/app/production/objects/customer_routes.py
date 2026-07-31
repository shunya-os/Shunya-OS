"""SHUNYA — Customer Profile creation route.

POST /api/v1/objects/customer
Creates a new Person + CustomerProfile from the provided fields.
"""
from datetime import datetime

from flask import request, jsonify, g
from werkzeug.exceptions import BadRequest

from app import db
from app.auth_routes import login_required
from app.models import Person, PersonIdentity, CustomerProfile
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

def _customer_to_dict(person: Person, profile: CustomerProfile) -> dict:
    """Serialize a customer (Person + CustomerProfile) to the standard envelope."""
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
        "company_name": person.canonical_name,
        "contact_person": person.preferred_name or "",
        "email": email,
        "phone": phone,
        "lifetime_value": float(profile.lifetime_value or 0),
        "segment": profile.segment or "",
        "preferred_channel": profile.preferred_channel or "",
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@objects_bp.route("/customer", methods=["POST"])
@login_required
def create_customer():
    """Create a new customer (Person + CustomerProfile).

    Request body:
    {
        "company_name": "Acme Corp",      # required → Person.canonical_name
        "contact_person": "Jane Doe",     # optional → Person.preferred_name
        "email": "jane@acme.com",         # optional → PersonIdentity
        "phone": "+1-555-0123",           # optional → PersonIdentity
        "address": "123 Main St",         # stored as note (extensible)
        "gst_number": "GSTIN1234",        # stored as note (extensible)
        "segment": "enterprise",          # optional → CustomerProfile.segment
        "preferred_channel": "email"      # optional → CustomerProfile.preferred_channel
    }
    """
    data = _require_json()
    company_name = _require_field(data, "company_name", "Company name")

    # -- Create Person --
    person = Person(
        tenant_id=getattr(g, "tenant_id", None),
        canonical_name=company_name,
        preferred_name=data.get("contact_person", ""),
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

    # Store address / gst_number as additional identities or as profile metadata
    # For simplicity we store address/gst as identity records with type "address"/"gstin"
    address = data.get("address", "").strip()
    if address:
        db.session.add(
            PersonIdentity(
                person_id=person.id,
                identity_type="address",
                identity_value=address,
                normalized_value=address,
            )
        )

    gst_number = data.get("gst_number", "").strip()
    if gst_number:
        db.session.add(
            PersonIdentity(
                person_id=person.id,
                identity_type="gstin",
                identity_value=gst_number,
                normalized_value=gst_number.upper(),
            )
        )

    # -- Create CustomerProfile --
    profile = CustomerProfile(
        person_id=person.id,
        tenant_id=getattr(g, "tenant_id", None),
        segment=data.get("segment", ""),
        preferred_channel=data.get("preferred_channel", ""),
    )
    db.session.add(profile)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": _customer_to_dict(person, profile),
    }), 201