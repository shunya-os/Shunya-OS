"""SHUNYA — ItineraryRef CRUD routes.

POST /api/v1/objects/itinerary     — Create a new itinerary reference
GET  /api/v1/objects/itinerary     — List itineraries (filterable, paginated)
GET  /api/v1/objects/itinerary/<id> — Get a single itinerary by id
DELETE /api/v1/objects/itinerary/<id> — Delete an itinerary
"""
from datetime import datetime, date

from flask import request, jsonify
from werkzeug.exceptions import BadRequest, NotFound

from app import db
from app.auth_routes import login_required
from app.models import ItineraryRef
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


def _parse_date(value: str | None, field_name: str) -> date | None:
    """Parse an ISO date string (YYYY-MM-DD) or return None."""
    if not value or not str(value).strip():
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        raise BadRequest(
            f"'{field_name}' must be a valid ISO date (YYYY-MM-DD), got '{value}'"
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@objects_bp.route("/itinerary", methods=["POST"])
@login_required
def create_itinerary():
    """Create a new ItineraryRef.

    Request body:
    {
        "guest_name": "John Doe",     # required
        "destination": "Paris",       # required
        "start_date": "2025-06-01",   # optional, ISO date
        "end_date": "2025-06-10",     # optional, ISO date
        "pax": "2 Adults",            # optional
        "highlights": "Eiffel Tower", # optional
        "day_count": 5,               # optional, int (default 0)
        "file_path": "/path/to/file"  # optional
    }
    """
    data = _require_json()
    guest_name = _require_field(data, "guest_name", "Guest name")
    destination = _require_field(data, "destination", "Destination")

    # Parse optional fields
    start_date = _parse_date(data.get("start_date"), "start_date")
    end_date = _parse_date(data.get("end_date"), "end_date")

    raw_day_count = data.get("day_count")
    day_count = 0
    if raw_day_count is not None:
        try:
            day_count = int(raw_day_count)
        except (ValueError, TypeError):
            raise BadRequest("'day_count' must be a valid integer")

    itinerary = ItineraryRef(
        guest_name=guest_name,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        pax=data.get("pax", "").strip() if data.get("pax") else "",
        highlights=data.get("highlights", "").strip() if data.get("highlights") else "",
        day_count=day_count,
        file_path=data.get("file_path", "").strip() if data.get("file_path") else "",
    )
    db.session.add(itinerary)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": itinerary.to_dict(),
    }), 201


@objects_bp.route("/itinerary", methods=["GET"])
@login_required
def list_itineraries():
    """List itineraries, filterable by guest_name and destination.

    Query parameters:
        guest_name (str, optional) — filter by guest name (partial match)
        destination (str, optional) — filter by destination (partial match)
        page (int, optional) — page number (default: 1)
        per_page (int, optional) — items per page (default: 20, max: 100)

    Returns:
        200 — Paginated list of itineraries, ordered by created_at desc
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    query = ItineraryRef.query

    # Optional filters
    guest_name = request.args.get("guest_name")
    if guest_name:
        query = query.filter(ItineraryRef.guest_name.ilike(f"%{guest_name}%"))

    destination = request.args.get("destination")
    if destination:
        query = query.filter(ItineraryRef.destination.ilike(f"%{destination}%"))

    # Order by most recent first
    query = query.order_by(ItineraryRef.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "success": True,
        "data": [it.to_dict() for it in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })


@objects_bp.route("/itinerary/<int:id>", methods=["GET"])
@login_required
def get_itinerary(id: int):
    """Get a single itinerary by its id."""
    itinerary = db.session.get(ItineraryRef, id)
    if itinerary is None:
        raise NotFound(f"Itinerary with id {id} not found")

    return jsonify({
        "success": True,
        "data": itinerary.to_dict(),
    })


@objects_bp.route("/itinerary/<int:id>", methods=["DELETE"])
@login_required
def delete_itinerary(id: int):
    """Delete an itinerary by its id."""
    itinerary = db.session.get(ItineraryRef, id)
    if itinerary is None:
        raise NotFound(f"Itinerary with id {id} not found")

    db.session.delete(itinerary)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Itinerary {id} deleted successfully",
    })