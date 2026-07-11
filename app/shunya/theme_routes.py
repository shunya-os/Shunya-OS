"""Shunya OS — Theme API routes."""
from flask import Blueprint, render_template, request, jsonify, g
from app import db
from app.routes.auth import login_required
from app.shunya.theme import THEMES, get_active_theme, set_theme, get_brand_colors, set_brand_colors

theme_bp = Blueprint("theme", __name__, url_prefix="/api/theme")


@theme_bp.route("", methods=["GET"])
@login_required
def get_theme():
    """Get current theme + brand colors + available themes."""
    return jsonify({
        "active_theme": get_active_theme(),
        "brand_colors": get_brand_colors(),
        "available_themes": THEMES,
        "tenant_name": g.tenant.company_name if g.tenant else "",
    })


@theme_bp.route("/set", methods=["POST"])
@login_required
def set():
    """Switch theme."""
    data = request.get_json(silent=True) or request.form
    theme = data.get("theme", "").strip()
    if not set_theme(g.tenant, theme):
        return jsonify({"error": f"Invalid theme: {theme}. Options: {', '.join(THEMES.keys())}"}), 400
    return jsonify({"success": True, "theme": theme, "brand_colors": get_brand_colors()})


@theme_bp.route("/brand-colors", methods=["POST"])
@login_required
def update_brand_colors():
    """Set brand colors (extracted from uploaded logo or manually)."""
    data = request.get_json(silent=True) or request.form
    colors = {
        "h": int(data.get("h", 220)),
        "s": int(data.get("s", 55)),
        "l": int(data.get("l", 42)),
    }
    if set_brand_colors(g.tenant, colors):
        return jsonify({"success": True, "brand_colors": colors})
    return jsonify({"error": "Invalid color data"}), 400


@theme_bp.route("/extract-colors", methods=["POST"])
@login_required
def extract_colors():
    """Extract brand colors from an uploaded logo image."""
    import os
    file = request.files.get("logo")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media", "logos")
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "logo.png")[1] or ".png"
    path = os.path.join(upload_dir, f"tenant_{g.tenant.id}_logo{ext}")
    file.save(path)

    from app.shunya.theme import extract_colors_from_image, set_brand_colors
    colors = extract_colors_from_image(path)

    # Save to tenant config
    set_brand_colors(g.tenant, colors)

    # Update logo_url
    g.tenant.logo_url = f"/media/logos/tenant_{g.tenant.id}_logo{ext}"
    from app import db
    db.session.commit()

    return jsonify({
        "success": True,
        "brand_colors": colors,
        "logo_url": g.tenant.logo_url,
    })


@theme_bp.route("/preview", methods=["POST"])
@login_required
def preview():
    """Preview a theme without saving."""
    data = request.get_json(silent=True) or {}
    theme = data.get("theme", "modern")
    colors = data.get("brand_colors", {})
    return jsonify({
        "theme": theme,
        "css_vars": _theme_to_css_vars(theme, colors),
    })


def _theme_to_css_vars(theme: str, brand_colors: dict) -> dict:
    """Convert theme + brand colors to CSS custom properties."""
    css = {"--theme": theme}
    if brand_colors:
        css["--brand-h"] = brand_colors.get("h", 0)
        css["--brand-s"] = f'{brand_colors.get("s", 0)}%'
        css["--brand-l"] = f'{brand_colors.get("l", 40)}%'
    return css