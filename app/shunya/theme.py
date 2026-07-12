"""Shunya OS — Theme Engine.

Three switchable design modes (modern, playful, elegant) + hybrid color extraction
from client logos for brand-matched theming.
"""
from __future__ import annotations
import json, os, math
from typing import Optional
from flask import g

THEMES = {
    "modern": {
        "label": "Modern",
        "icon": "💼",
        "description": "Clean, professional, business-first",
    },
    "playful": {
        "label": "Playful",
        "icon": "🎨",
        "description": "Vibrant, rounded, animated, warm",
    },
    "elegant": {
        "label": "Elegant",
        "icon": "✨",
        "description": "Minimal, monochrome, typography-first",
    },
    "brandverse": {
        "label": "Brandverse",
        "icon": "🌌",
        "description": "Auto-generated from your brand colors",
    },
}


def get_active_theme(tenant=None) -> str:
    """Get the active theme for the current tenant."""
    if tenant is None:
        tenant = getattr(g, "tenant", None)
    if not tenant:
        return "modern"
    config = tenant.ai_config or {}
    return config.get("theme", "modern")


def set_theme(tenant, theme: str) -> bool:
    """Set the active theme for a tenant."""
    if theme not in THEMES:
        return False
    config = dict(tenant.ai_config or {})
    config["theme"] = theme
    tenant.ai_config = config
    from app import db
    db.session.commit()
    return True


def get_brand_colors(tenant=None) -> dict:
    """Get brand colors extracted from logo or business type defaults."""
    if tenant is None:
        tenant = getattr(g, "tenant", None)
    if not tenant:
        return {"h": 0, "s": 0, "l": 40}

    config = tenant.ai_config or {}
    colors = config.get("brand_colors", {})

    if colors:
        return colors

    # Fallback: generate from business type
    return _colors_for_business(tenant.company_name or "", tenant.name if hasattr(tenant, 'name') else "")


def set_brand_colors(tenant, colors: dict) -> bool:
    """Store extracted brand colors for a tenant."""
    required = {"h", "s", "l"}
    if not all(k in colors for k in required):
        return False
    config = dict(tenant.ai_config or {})
    config["brand_colors"] = {k: colors[k] for k in required}
    tenant.ai_config = config
    from app import db
    db.session.commit()
    return True


# ---------------------------------------------------------------------------
# Color extraction from images
# ---------------------------------------------------------------------------

def extract_colors_from_image(image_path: str) -> dict:
    """Extract dominant HSL color from a logo/image file.
    
    Uses a simple pixel-sampling approach — extracts the most common hue
    from the image and returns HSL values suitable for CSS custom properties.
    """
    try:
        from PIL import Image
        img = Image.open(image_path).convert("RGB")
        # Resize for speed
        img = img.resize((64, 64))
        pixels = list(img.getdata())

        # Quantize to 36 hue bins
        hue_bins: dict[int, int] = {}
        for r, g, b in pixels:
            if r + g + b < 30:
                continue  # Skip near-black
            if r > 240 and g > 240 and b > 240:
                continue  # Skip near-white
            h, s, l = _rgb_to_hsl(r, g, b)
            hue_key = int(h / 10) * 10
            hue_bins[hue_key] = hue_bins.get(hue_key, 0) + 1

        if not hue_bins:
            return {"h": 220, "s": 60, "l": 45}  # Default blue

        # Find dominant hue
        dominant_hue = max(hue_bins, key=hue_bins.get)

        # Calculate average saturation and lightness for that hue
        total_s = total_l = count = 0
        for r, g, b in pixels:
            h, s, l = _rgb_to_hsl(r, g, b)
            if int(h / 10) * 10 == dominant_hue:
                total_s += s
                total_l += l
                count += 1

        avg_s = total_s / count if count > 0 else 50
        avg_l = total_l / count if count > 0 else 45

        return {"h": dominant_hue, "s": max(20, min(80, avg_s)), "l": max(30, min(60, avg_l))}

    except ImportError:
        return {"h": 220, "s": 60, "l": 45}  # Pillow not installed
    except Exception:
        return {"h": 220, "s": 60, "l": 45}


def _rgb_to_hsl(r: int, g: int, b: int) -> tuple:
    """Convert RGB to HSL (0-360, 0-100, 0-100)."""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    l = (mx + mn) / 2

    if mx == mn:
        h = s = 0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = ((g - b) / d + (6 if g < b else 0)) / 6
        elif mx == g:
            h = ((b - r) / d + 2) / 6
        else:
            h = ((r - g) / d + 4) / 6
        h *= 360

    return (h % 360, s * 100, l * 100)


def _colors_for_business(company_name: str = "", business_type: str = "") -> dict:
    """Generate brand colors from company/business type name."""
    # Deterministic color from name hash
    name = (company_name or business_type or "shunya").lower()
    h = sum(ord(c) for c in name) % 360
    return {"h": h, "s": 55, "l": 42}


# ---------------------------------------------------------------------------
# Brandverse — Intelligent Palette Generator
# ---------------------------------------------------------------------------

def hex_to_hsl(hex_color: str) -> tuple:
    """Convert hex (#RRGGBB) to HSL (0-360, 0-100, 0-100)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return _rgb_to_hsl(r, g, b)


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert HSL to hex string (#RRGGBB)."""
    h, s, l = h % 360, max(0, min(100, s)), max(0, min(100, l))
    c = (1 - abs(2 * l / 100 - 1)) * (s / 100)
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l / 100 - c / 2

    if 0 <= h < 60:
        r, g, b = c, x, 0
    elif 60 <= h < 120:
        r, g, b = x, c, 0
    elif 120 <= h < 180:
        r, g, b = 0, c, x
    elif 180 <= h < 240:
        r, g, b = 0, x, c
    elif 240 <= h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    r, g, b = int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
    return f"#{r:02x}{g:02x}{b:02x}"


def is_light_color(hex_color: str) -> bool:
    """Determine if a color is perceived as light (uses relative luminance)."""
    h, s, l = hex_to_hsl(hex_color)
    return l > 55


def adjust_lightness(hex_color: str, delta: float) -> str:
    """Lighten (delta>0) or darken (delta<0) a hex color by delta percentage points."""
    h, s, l = hex_to_hsl(hex_color)
    return hsl_to_hex(h, s, max(0, min(100, l + delta)))


def adjust_saturation(hex_color: str, delta: float) -> str:
    """Increase (delta>0) or decrease (delta<0) saturation."""
    h, s, l = hex_to_hsl(hex_color)
    return hsl_to_hex(h, max(0, min(100, s + delta)), l)


def shift_hue(hex_color: str, degrees: float) -> str:
    """Shift hue by degrees."""
    h, s, l = hex_to_hsl(hex_color)
    return hsl_to_hex(h + degrees, s, l)


def blend_colors(c1: str, c2: str, ratio: float = 0.5) -> str:
    """Blend two hex colors. ratio=0 -> c1, ratio=1 -> c2."""
    h1, s1, l1 = hex_to_hsl(c1)
    h2, s2, l2 = hex_to_hsl(c2)
    # Shortest path around the hue wheel
    dh = h2 - h1
    if dh > 180:
        dh -= 360
    elif dh < -180:
        dh += 360
    h = (h1 + dh * ratio) % 360
    s = s1 + (s2 - s1) * ratio
    l = l1 + (l2 - l1) * ratio
    return hsl_to_hex(h, s, l)


def generate_brandverse_palette(primary: str = "#2563eb", secondary: str = "#7c3aed") -> dict:
    """Generate a complete, intelligent color palette from two brand colors.

    The primary and secondary colors are the mains. Every other color is
    auto-derived to create a harmonious, comfortable, and exciting UI.
    """
    p_h, p_s, p_l = hex_to_hsl(primary)
    s_h, s_s, s_l = hex_to_hsl(secondary)

    # Determine brand personality
    is_warm = 0 <= p_h <= 60 or 300 <= p_h <= 360
    is_cool = 180 <= p_h <= 270
    is_vibrant = p_s > 55
    is_muted = p_s < 35
    is_dark_brand = p_l < 40

    # ── Background System ──
    # Dark theme by default, but tinted with brand hue for depth
    bg_hue = p_h
    bg_sat = max(10, p_s * 0.3)  # Muted saturation for background
    bg_lum = 9  # Very dark
    bg = hsl_to_hex(bg_hue, bg_sat, bg_lum)

    # Card background — slightly lighter, hints of brand
    bg_card_lum = 16
    bg_card_sat = max(8, p_s * 0.25)
    bg_card = hsl_to_hex(bg_hue, bg_card_sat, bg_card_lum)

    # Hover state — between bg and bg_card
    bg_hover = hsl_to_hex(bg_hue, max(6, p_s * 0.2), 12)

    # Nav bar
    nav_bg = hsl_to_hex(bg_hue, bg_card_sat + 2, bg_card_lum - 2)
    nav_border = hsl_to_hex(p_h, max(15, p_s * 0.4), 22)

    # ── Text System ──
    text_primary = "#f1f5f9"
    text_muted = "#94a3b8"
    text_dim = "#64748b"

    # ── Border System ──
    border = hsl_to_hex(p_h, max(10, p_s * 0.35), 25)
    border_light = hsl_to_hex(p_h, max(6, p_s * 0.2), 18)

    # ── Semantic Colors (harmonized to brand) ──
    if is_warm:
        # Warm brands get warmer greens, softer reds
        success = hsl_to_hex(140, min(60, p_s * 1.1), 42)
        warning = hsl_to_hex(38, min(80, p_s * 1.2), 52)
        error = hsl_to_hex(358, min(65, p_s * 1.0), 55)
        info = hsl_to_hex(205, min(70, p_s * 1.0), 50)
    elif is_cool:
        # Cool brands get cooler, more professional sematics
        success = hsl_to_hex(155, min(55, p_s * 1.0), 40)
        warning = hsl_to_hex(42, min(70, p_s * 1.1), 48)
        error = hsl_to_hex(352, min(60, p_s * 0.9), 52)
        info = p_h > 200 and hsl_to_hex(p_h, p_s, 48) or hsl_to_hex(210, 60, 50)
    else:
        # Neutral/purple brands — balanced
        success = hsl_to_hex(148, 55, 40)
        warning = hsl_to_hex(40, 65, 48)
        error = hsl_to_hex(355, 60, 52)
        info = hsl_to_hex(210, 60, 50)

    # ── Accent (complementary to primary, for highlights) ──
    accent_hue = (p_h + 180) % 360  # Direct complement
    # Soften if too harsh
    accent_sat = max(40, min(65, p_s))
    accent = hsl_to_hex(accent_hue, accent_sat, 50)
    accent_light = hsl_to_hex(accent_hue, accent_sat * 0.6, 42)

    # ── Buttons ──
    btn_primary_bg = primary
    btn_primary_text = "#ffffff" if not is_light_color(primary) else "#0f172a"
    btn_primary_hover = adjust_lightness(primary, -8) if not is_light_color(primary) else adjust_lightness(primary, -12)

    btn_secondary_bg = adjust_lightness(bg_card, 5)
    btn_secondary_border = border
    btn_secondary_text = text_primary

    # ── Focus / Ring ──
    focus_ring = f"{primary}40"  # 25% opacity primary

    # ── Gradient ──
    gradient = f"linear-gradient(135deg, {primary}, {secondary})"

    # ── Status badges ──
    badge_success = hsl_to_hex(140, min(50, p_s * 0.8), 20)
    badge_warning = hsl_to_hex(38, min(60, p_s * 0.8), 25)
    badge_error = hsl_to_hex(358, min(50, p_s * 0.8), 25)

    return {
        # Mains
        "primary": primary,
        "secondary": secondary,
        "accent": accent,
        "accent_light": accent_light,

        # Backgrounds
        "bg": bg,
        "bg_card": bg_card,
        "bg_hover": bg_hover,
        "nav_bg": nav_bg,
        "nav_border": nav_border,
        "card_bg": bg_card,

        # Text
        "text": text_primary,
        "text_muted": text_muted,
        "text_dim": text_dim,

        # Borders
        "border": border,
        "border_light": border_light,

        # Semantics
        "success": success,
        "warning": warning,
        "error": error,
        "info": info,

        # Buttons
        "btn_primary_bg": btn_primary_bg,
        "btn_primary_text": btn_primary_text,
        "btn_primary_hover": btn_primary_hover,
        "btn_secondary_bg": btn_secondary_bg,
        "btn_secondary_border": btn_secondary_border,
        "btn_secondary_text": btn_secondary_text,

        # Status badge backgrounds
        "badge_success_bg": badge_success,
        "badge_warning_bg": badge_warning,
        "badge_error_bg": badge_error,

        # Effects
        "focus_ring": focus_ring,
        "gradient": gradient,

        # Metadata
        "_personality": {
            "is_warm": is_warm,
            "is_cool": is_cool,
            "is_vibrant": is_vibrant,
            "is_muted": is_muted,
            "is_dark_brand": is_dark_brand,
        },
    }