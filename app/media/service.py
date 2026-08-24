"""Media generation service — HF free inference + visual brief intelligence."""

import hashlib
import logging
import os
import re
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

from app import db
from app.media.models import MediaAsset

logger = logging.getLogger(__name__)

# ── Free image generation provider ──────────────────────────────
# Uses Hugging Face serverless Inference API (free tier, no token cost)
# with FLUX.1-schnell — fast, 4-step, 1024x1024 output.
HF_MODEL = "black-forest-labs/FLUX.1-schnell"
MEDIA_UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
MEDIA_UPLOAD_DIR.mkdir(exist_ok=True)

# ── Aspect ratio presets ──────────────────────────────────────
ASPECT_MAP = {
    "1:1": (1024, 1024),
    "4:5": (1024, 1280),
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "3:2": (1200, 800),
    "4:3": (1600, 1200),
}


def _get_hf_token() -> Optional[str]:
    return os.environ.get("HF_API_KEY") or os.environ.get("HF_TOKEN")


def _check_hf_available() -> bool:
    """Check whether Hugging Face inference is available.

    Uses a lightweight token validation by attempting to generate a tiny
    probe image (1x1) — avoids depending on model-status endpoints that
    may not exist on all InferenceClient versions.
    """
    token = _get_hf_token()
    if not token:
        return False
    try:
        from huggingface_hub import InferenceClient
        from io import BytesIO

        client = InferenceClient(token=token)
        # Probe with a minimal prompt — if the API returns an image the token works
        image = client.text_to_image("test", model=HF_MODEL)
        return image is not None
    except Exception:
        return False


def _generate_hf_image(prompt: str, aspect_ratio: str = "1:1") -> bytes:
    """Generate an image via Hugging Face free inference.

    Returns raw PNG bytes. Raises on failure.
    """
    token = _get_hf_token()
    if not token:
        raise RuntimeError("HF_API_KEY not configured")

    from huggingface_hub import InferenceClient

    client = InferenceClient(token=token)

    # Map aspect ratio to width/height
    w, h = ASPECT_MAP.get(aspect_ratio, (1024, 1024))
    # FLUX.1-schnell is fixed at 1024x1024, so we crop later
    # For now, generate at native and store the ratio info

    result = client.text_to_image(prompt, model=HF_MODEL)
    # result is PIL.Image

    buf = BytesIO()
    result.save(buf, format="PNG")
    return buf.getvalue()


def _save_image_file(raw_bytes: bytes, identity_id: str) -> str:
    """Save raw image bytes to disk and return the relative URL path.

    Naming: media/{identity_id}/{sha256[:16]}.png
    """
    digest = hashlib.sha256(raw_bytes).hexdigest()[:16]
    subdir = MEDIA_UPLOAD_DIR / identity_id
    subdir.mkdir(parents=True, exist_ok=True)
    filename = f"{digest}.png"
    path = subdir / filename
    if not path.exists():
        path.write_bytes(raw_bytes)
        logger.info("Saved media asset: %s (%d bytes)", path, len(raw_bytes))
    return f"/api/v1/media/uploads/{identity_id}/{filename}"


def _transform_to_visual_brief(business_context: dict, raw_prompt: str) -> str:
    """Transform raw business facts + user prompt into a structured visual brief.

    Uses template-based composition (no AI call) to produce a
    meaningful creative brief from structured business data.
    """
    parts = []

    # Extract known fields
    destination = business_context.get("destination", "")
    duration = business_context.get("duration", "")
    price = business_context.get("price", "")
    positioning = business_context.get("positioning", "")
    audience = business_context.get("audience", "")
    platform = business_context.get("platform", "")

    # Build context summary
    context_items = []
    if destination:
        context_items.append(f"Destination: {destination}")
    if duration:
        context_items.append(f"Duration: {duration}")
    if price:
        context_items.append(f"Starting from: {price}")
    if positioning:
        context_items.append(f"Positioning: {positioning}")
    if audience:
        context_items.append(f"Target audience: {audience}")

    if context_items:
        parts.append("CONTEXT:\n" + "\n".join(context_items))

    # Build creative direction
    parts.append("\nCREATIVE BRIEF:")
    brief_lines = []

    if destination:
        brief_lines.append(f"Visual story centered on {destination}")
    if positioning:
        brief_lines.append(f"Tone and atmosphere reflecting {positioning} positioning")
    if audience:
        brief_lines.append(
            f"Composition and styling suited for {audience}"
        )
    if platform:
        brief_lines.append(
            f"Optimized framing for {platform} platform requirements"
        )

    if not brief_lines:
        brief_lines.append(raw_prompt)

    parts.append("\n".join(brief_lines))

    # Visual direction
    parts.append("\nVISUAL DIRECTION:")
    parts.append(
        "- Focal subject should be the hero element"
    )
    parts.append("- Environmental context supports the narrative")
    parts.append("- Emotional tone: aspirational, inviting, premium")
    parts.append("- Clean composition with clear visual hierarchy")
    parts.append("- Typography-safe zone maintained in lower third")
    parts.append("- Avoid generic stock-photo clichés")
    parts.append("- Color palette should feel warm and natural")

    return "\n".join(parts)


def generate_media(
    raw_prompt: str,
    identity_id: str,
    platform: Optional[str] = None,
    aspect_ratio: str = "1:1",
    visual_style: str = "realistic",
    business_context: Optional[dict] = None,
) -> dict:
    """Generate media through the full pipeline: visual brief -> generation -> persistence.

    Returns the canonical result contract.
    """
    # 1. Create initial record (IDLE -> PREPARING_BRIEF)
    asset = MediaAsset(
        identity_id=identity_id,
        runtime_state="preparing_brief",
        result_kind=None,
        raw_prompt=raw_prompt,
        visual_brief=None,
        platform=platform,
        aspect_ratio=aspect_ratio,
        visual_style=visual_style,
        business_context=business_context or {},
    )
    db.session.add(asset)
    db.session.commit()

    try:
        # 2. Transform into visual brief
        brief = _transform_to_visual_brief(
            business_context or {}, raw_prompt
        )
        asset.visual_brief = brief
        asset.runtime_state = "generating"
        db.session.commit()

        # 3. Check provider availability
        if not _get_hf_token():
            asset.runtime_state = "provider_unavailable"
            asset.result_kind = "provider_unavailable"
            asset.failure_reason = (
                "Hugging Face API token not configured. "
                "Set HF_API_KEY in environment to enable image generation."
            )
            db.session.commit()
            return asset.to_canonical()

        # 4. Generate image via HF free inference
        # Compose a detailed prompt from the visual brief + raw prompt
        generation_prompt = (
            f"{raw_prompt}. "
            f"Style: {visual_style}. "
            f"Aspect ratio: {aspect_ratio}. "
            f"{brief.split('VISUAL DIRECTION:')[0] if 'VISUAL DIRECTION:' in brief else ''}"
        )

        try:
            image_bytes = _generate_hf_image(
                generation_prompt.strip(), aspect_ratio
            )
        except Exception as gen_err:
            logger.warning("HF image generation failed: %s", gen_err)
            # Fallback: provider unavailable
            asset.runtime_state = "provider_unavailable"
            asset.result_kind = "provider_unavailable"
            asset.failure_reason = (
                f"Image generation service unavailable: {gen_err}. "
                "The visual brief was created — use description-only mode."
            )
            db.session.commit()

            # Also generate a description-only concept
            asset.runtime_state = "description_only"
            asset.result_kind = "visual_concept"
            asset.description = _generate_visual_concept(
                raw_prompt, brief, visual_style
            )
            db.session.commit()
            return asset.to_canonical()

        # 5. Save image to persistent storage
        asset_url = _save_image_file(image_bytes, identity_id)
        asset.asset_url = asset_url
        asset.provider = f"hf/{HF_MODEL}"
        asset.generation_job_id = hashlib.sha256(image_bytes).hexdigest()[:24]
        asset.runtime_state = "generated"
        asset.result_kind = "generated_image"
        db.session.commit()

        return asset.to_canonical()

    except Exception as exc:
        logger.error("Media generation failed: %s", exc)
        try:
            asset.runtime_state = "failed"
            asset.result_kind = "error"
            asset.failure_reason = str(exc)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return {
            "id": getattr(asset, "id", 0),
            "runtime_state": "failed",
            "result_kind": "error",
            "failure_reason": str(exc),
            "raw_prompt": raw_prompt,
        }


def _generate_visual_concept(
    raw_prompt: str, brief: str, visual_style: str
) -> str:
    """Generate a textual visual concept when image generation is unavailable.

    This is a valid result — but it is FUNDAMENTALLY DIFFERENT from
    generated media and must be presented as such.
    """
    style_guides = {
        "realistic": "photorealistic, natural lighting, authentic textures",
        "illustration": "hand-drawn or digital illustration, stylized, artistic",
        "cinematic": "cinematic framing, dramatic lighting, film-grade composition",
        "minimalist": "clean, minimal, generous whitespace, simple forms",
        "corporate": "professional, polished, brand-consistent, structured",
        "artistic": "creative, experimental, avant-garde, expressive",
    }
    style_desc = style_guides.get(visual_style, "professional")

    return (
        f"Visual Concept — {visual_style.title()} Style\n\n"
        f"Scene: {raw_prompt}\n\n"
        f"Art Direction:\n"
        f"- Approach: {style_desc}\n"
        f"- Composition: The focal subject dominates the frame, "
        f"with environmental context supporting the narrative\n"
        f"- Color Palette: Warm, natural tones with strategic accent colors "
        f"for visual interest\n"
        f"- Lighting: Soft, directional lighting that creates depth "
        f"and draws attention to the subject\n"
        f"- Atmosphere: Aspirational yet approachable, inviting the "
        f"viewer into the scene\n\n"
        f"Typography Safe Zone:\n"
        f"- Lower third of frame preserved for text overlay\n"
        f"- Ample negative space around key focal points\n\n"
        f"Prohibited Elements:\n"
        f"- Generic stock photography clichés\n"
        f"- Overly saturated or artificial color grading\n"
        f"- Cluttered compositions that compete with the focal subject"
    )


def get_asset(asset_id: int, identity_id: str) -> Optional[dict]:
    """Get a single media asset by ID (scoped to identity)."""
    asset = MediaAsset.query.filter_by(
        id=asset_id, identity_id=identity_id
    ).first()
    if not asset:
        return None
    return asset.to_canonical()


def list_assets(
    identity_id: str, limit: int = 50, offset: int = 0
) -> tuple[list[dict], int]:
    """List media assets for an identity, newest first."""
    q = (
        MediaAsset.query.filter_by(identity_id=identity_id)
        .order_by(MediaAsset.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = q.all()
    total = MediaAsset.query.filter_by(identity_id=identity_id).count()
    return [a.to_canonical() for a in items], total


def attach_to_campaign(
    asset_id: int, campaign_id: int, identity_id: str
) -> Optional[dict]:
    """Attach a media asset to a campaign."""
    asset = MediaAsset.query.filter_by(
        id=asset_id, identity_id=identity_id
    ).first()
    if not asset:
        return None
    # Verify campaign exists and belongs to user
    from app.integration.models import AdCampaign

    campaign = AdCampaign.query.filter_by(
        id=campaign_id, identity_id=identity_id
    ).first()
    if not campaign:
        return None

    asset.campaign_id = campaign_id
    db.session.commit()
    return asset.to_canonical()


def get_hf_status() -> dict:
    """Check HF free inference availability. Returns status dict."""
    token_ok = bool(_get_hf_token())
    if not token_ok:
        return {
            "available": False,
            "provider": "huggingface",
            "model": HF_MODEL,
            "error": "HF_API_KEY not configured",
        }
    try:
        available = _check_hf_available()
        return {
            "available": available,
            "provider": "huggingface",
            "model": HF_MODEL,
            "cost": "free",
            "token_cost": 0,
        }
    except Exception as e:
        return {
            "available": False,
            "provider": "huggingface",
            "model": HF_MODEL,
            "error": str(e),
        }