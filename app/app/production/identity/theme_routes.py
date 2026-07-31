"""SHUNYA — Organization Theme & Logo API.

RESTful endpoints for managing organization theme settings and logo upload.
All endpoints require authentication. Responses use standard envelope.

Endpoints:
    POST /<int:org_id>/logo   — Upload a logo file (multipart)
    GET  /<int:org_id>/theme   — Get current theme settings
    PUT  /<int:org_id>/theme   — Update theme settings (JSON)
"""

import os
import uuid

from flask import request, jsonify, current_app
from werkzeug.exceptions import NotFound, BadRequest
from werkzeug.utils import secure_filename

from app import db
from app.auth_routes import login_required
from app.tenant import Tenant, TenantTheme

from app.production.identity import identity_bp

# ---------------------------------------------------------------------------
# Allowed image extensions
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg", "webp"}

# Dynamically resolved upload root — relative to the Flask app root
# Using the same directory as BrandingEngine.UPLOAD_DIR: media/tenant/
UPLOAD_RELATIVE = "media/tenant"


def _get_upload_dir() -> str:
    """Return the absolute path to the logo upload directory, creating it if needed."""
    path = os.path.join(current_app.root_path, "..", UPLOAD_RELATIVE)
    os.makedirs(path, exist_ok=True)
    return os.path.abspath(path)


def _allowed_file(filename: str) -> bool:
    """Check if the file extension is an allowed image type."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _get_org_or_404(org_id: int) -> Tenant:
    """Fetch an active org by ID or raise NotFound."""
    org = db.session.get(Tenant, org_id)
    if not org or not org.is_active:
        raise NotFound("Organization not found")
    return org


def _get_or_create_theme(org: Tenant) -> TenantTheme:
    """Return the org's theme, creating a default one if it doesn't exist."""
    if not org.theme:
        theme = TenantTheme(tenant_id=org.id)
        db.session.add(theme)
        db.session.flush()
        return theme
    return org.theme


def _theme_to_dict(theme: TenantTheme) -> dict:
    """Serialize theme to response dict, using the same format as TenantTheme.to_dict()."""
    return {
        "primary_color": theme.primary_color,
        "accent_color": theme.accent_color,
        "bg_color": theme.bg_color,
        "sidebar_bg": theme.sidebar_bg,
        "font_family": theme.font_family,
        "logo_path": f"/media/tenant/{theme.logo_path}" if theme.logo_path else None,
        "logo_style": theme.logo_style,
        "welcome_message": theme.welcome_message,
        "company_motto": theme.company_motto,
        "custom_css": theme.custom_css,
    }


# ---------------------------------------------------------------------------
# POST /<int:org_id>/logo — Upload a logo
# ---------------------------------------------------------------------------


@identity_bp.route("/<int:org_id>/logo", methods=["POST"])
@login_required
def upload_logo(org_id: int):
    """Upload a logo image for the organization.

    Accepts multipart/form-data with a 'logo' file field.
    Saves the file to static/uploads/logo/ and updates TenantTheme.logo_path.
    Returns the new logo URL.
    """
    org = _get_org_or_404(org_id)

    # Validate file presence
    if "logo" not in request.files:
        raise BadRequest("No 'logo' file field found in the request. Use multipart/form-data with a 'logo' field.")

    file = request.files["logo"]
    if not file or not file.filename:
        raise BadRequest("No file selected or filename is empty.")

    # Validate extension
    if not _allowed_file(file.filename):
        raise BadRequest(
            f"File type not allowed. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Read file content
    file_data = file.read()
    if len(file_data) == 0:
        raise BadRequest("Uploaded file is empty.")

    # Generate a unique filename to avoid collisions
    ext = os.path.splitext(file.filename)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}{ext}"

    # Save to disk
    upload_dir = _get_upload_dir()
    dest_path = os.path.join(upload_dir, stored_filename)
    with open(dest_path, "wb") as f:
        f.write(file_data)

    # Update the theme record
    theme = _get_or_create_theme(org)
    theme.logo_path = stored_filename
    db.session.commit()

    logo_url = f"/media/tenant/{stored_filename}"

    return jsonify({
        "success": True,
        "data": {
            "logo_path": logo_url,
            "filename": stored_filename,
        },
    })


# ---------------------------------------------------------------------------
# GET /<int:org_id>/theme — Get theme settings
# ---------------------------------------------------------------------------


@identity_bp.route("/<int:org_id>/theme", methods=["GET"])
@login_required
def get_theme(org_id: int):
    """Get the current theme settings for an organization."""
    org = _get_org_or_404(org_id)
    theme = _get_or_create_theme(org)

    return jsonify({
        "success": True,
        "data": _theme_to_dict(theme),
    })


# ---------------------------------------------------------------------------
# PUT /<int:org_id>/theme — Update theme settings
# ---------------------------------------------------------------------------

# Fields that can be updated via the PUT endpoint
THEME_UPDATE_FIELDS = {
    "primary_color": str,
    "accent_color": str,
    "bg_color": str,
    "sidebar_bg": str,
    "font_family": str,
    "logo_style": str,
    "welcome_message": str,
    "company_motto": str,
    "custom_css": str,
}


@identity_bp.route("/<int:org_id>/theme", methods=["PUT"])
@login_required
def update_theme(org_id: int):
    """Update theme settings for an organization.

    Accepts JSON with any subset of theme fields:
        primary_color, accent_color, bg_color, sidebar_bg,
        font_family, logo_style, welcome_message, company_motto, custom_css
    """
    org = _get_org_or_404(org_id)

    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Request body must be valid JSON")

    theme = _get_or_create_theme(org)

    # Apply only the fields that are present and valid
    updated = {}
    for field, field_type in THEME_UPDATE_FIELDS.items():
        if field in data:
            value = data[field]
            if value is not None:
                value = field_type(value)
            setattr(theme, field, value)
            updated[field] = value

    # If logo_path is explicitly set to None or empty string, clear it
    if "logo_path" in data:
        if not data["logo_path"]:
            theme.logo_path = ""
            updated["logo_path"] = None
        else:
            # Setting logo_path via JSON is intentionally not supported;
            # use the POST /logo endpoint instead.
            raise BadRequest(
                "To set a logo, use POST /<org_id>/logo with a file upload. "
                "The logo_path field cannot be set directly via JSON."
            )

    db.session.commit()

    return jsonify({
        "success": True,
        "data": _theme_to_dict(theme),
        "updated": list(updated.keys()),
    })