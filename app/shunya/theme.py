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