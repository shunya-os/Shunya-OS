"""EP-06A — Creative Intelligence Completion.

The Universal Creative Runtime models communication intent first.
Creative representations become render targets selected by the runtime.
One intent may generate multiple creative representations.
SHUNYA never thinks in terms of Canva, Photoshop, PowerPoint, or Figma.
SHUNYA thinks in terms of communication intent.
"""

import uuid
import logging
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ── Communication Intent ──────────────────────────────────────────
# Intent is the primary classification. Creative types are render targets.

COMMUNICATION_INTENTS = {
    "launch_campaign": {
        "label": "Launch Campaign",
        "description": "Introduce a product, service, or initiative to the market",
        "suggested_types": ["presentation", "social_post", "poster", "banner", "thumbnail"],
    },
    "explain": {
        "label": "Explain",
        "description": "Make a complex topic understandable",
        "suggested_types": ["infographic", "presentation", "storyboard"],
    },
    "educate": {
        "label": "Educate",
        "description": "Teach an audience about a subject",
        "suggested_types": ["presentation", "infographic", "storyboard", "reel"],
    },
    "sell": {
        "label": "Sell",
        "description": "Convince a prospect to purchase or commit",
        "suggested_types": ["presentation", "proposal", "banner", "social_post"],
    },
    "present": {
        "label": "Present",
        "description": "Share information with an audience in real time",
        "suggested_types": ["presentation", "storyboard"],
    },
    "recruit": {
        "label": "Recruit",
        "description": "Attract candidates to join an organization",
        "suggested_types": ["poster", "social_post", "banner", "reel"],
    },
    "inform": {
        "label": "Inform",
        "description": "Provide updates or announcements",
        "suggested_types": ["social_post", "infographic", "banner"],
    },
    "celebrate": {
        "label": "Celebrate",
        "description": "Mark an achievement or milestone",
        "suggested_types": ["poster", "social_post", "presentation"],
    },
    "build_trust": {
        "label": "Build Trust",
        "description": "Establish credibility and reliability",
        "suggested_types": ["presentation", "infographic", "social_post"],
    },
    "report_progress": {
        "label": "Report Progress",
        "description": "Show what has been accomplished",
        "suggested_types": ["presentation", "infographic", "dashboard"],
    },
}

# Creative types remain as render targets — metadata only, not implementations.
CREATIVE_TYPES = {
    "social_post": {"purpose": "Share a message with an audience", "formats": ["image", "svg"]},
    "infographic": {"purpose": "Explain complex information visually", "formats": ["svg", "image"]},
    "presentation": {"purpose": "Present information to an audience", "formats": ["svg", "html"]},
    "poster": {"purpose": "Promote or announce visually", "formats": ["image", "svg"]},
    "banner": {"purpose": "Advertise or promote digitally", "formats": ["image", "svg"]},
    "thumbnail": {"purpose": "Attract attention for video/content", "formats": ["image"]},
    "reel": {"purpose": "Short-form video storytelling", "formats": ["video"]},
    "storyboard": {"purpose": "Plan visual sequences", "formats": ["svg"]},
}

DEFAULT_CREATIVE_TYPE = "presentation"


# ── Creative Living Object ────────────────────────────────────────

@dataclass
class CreativeVersion:
    version_id: str
    content: str
    format: str
    author: str
    created_at: str
    preview_url: str = ""


@dataclass
class CreativeAsset:
    """A Creative Living Object.
    
    Identity never changes. Representations can change.
    The primary classification is communication intent.
    Creative types are render targets selected by the runtime.
    """
    asset_id: str
    title: str
    intent: str = "inform"            # communication intent (primary)
    creative_type: str = "presentation"  # render target (secondary)
    format: str = "svg"
    content: str = ""
    purpose: str = ""
    target_audience: str = ""
    brand_id: str = ""
    template_id: str = ""
    versions: list[CreativeVersion] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    status: str = "draft"
    ai_summary: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "title": self.title,
            "intent": self.intent,
            "creative_type": self.creative_type,
            "format": self.format,
            "purpose": self.purpose,
            "target_audience": self.target_audience,
            "brand_id": self.brand_id,
            "template_id": self.template_id,
            "version_count": len(self.versions),
            "relationships": self.relationships,
            "ai_summary": self.ai_summary,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── Brand Living Object ───────────────────────────────────────────

@dataclass
class Brand:
    brand_id: str
    name: str
    primary_color: str = "#BFAC8B"
    secondary_color: str = "#2A2626"
    font_family: str = "-apple-system, 'Inter', sans-serif"
    logo_url: str = ""
    tone: str = "professional"
    voice: str = "confident, calm"
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "brand_id": self.brand_id,
            "name": self.name,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "font_family": self.font_family,
            "tone": self.tone,
            "voice": self.voice,
        }


# ── Template Living Object ────────────────────────────────────────

@dataclass
class Template:
    template_id: str
    name: str
    creative_type: str
    content: str = ""
    brand_id: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "creative_type": self.creative_type,
            "brand_id": self.brand_id,
        }


# ── Provider Adapter Interface ────────────────────────────────────

class CreativeProvider(ABC):
    """All creative providers implement one interface.
    No provider-specific logic in the workspace.
    """
    @abstractmethod
    def render(self, content: str, target_format: str) -> str: ...
    @abstractmethod
    def generate(self, prompt: str, creative_type: str, format: str) -> str: ...
    @abstractmethod
    def resize(self, content: str, width: int, height: int) -> str: ...
    @abstractmethod
    def preview(self, content: str, format: str) -> str: ...


class NativeSVGProvider(CreativeProvider):
    """Native SVG generation — no external engine needed."""
    def _svg_frame(self, title: str) -> str:
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <rect width="800" height="600" fill="#1A1818"/>
  <text x="400" y="280" text-anchor="middle" font-family="Inter,sans-serif" font-size="32" font-weight="300" fill="#BFAC8B">{title}</text>
  <text x="400" y="330" text-anchor="middle" font-family="Inter,sans-serif" font-size="14" fill="#8A8580">SHUNYA Creative Runtime</text>
</svg>'''

    def render(self, content: str, target_format: str) -> str:
        return self._svg_frame(content[:80]) if target_format == "svg" else content

    def generate(self, prompt: str, creative_type: str, format: str) -> str:
        return self._svg_frame(f"{creative_type}: {prompt[:60]}")

    def resize(self, content: str, width: int, height: int) -> str:
        return content  # In production, resample via ImageMagick

    def preview(self, content: str, format: str) -> str:
        return content


class EChartsProvider(CreativeProvider):
    """Apache ECharts integration for chart rendering.
    
    Free, open-source (Apache 2.0), self-hosted.
    Demonstrates a real provider integration through the abstraction.
    """
    def render(self, content: str, target_format: str) -> str:
        try:
            spec = json.loads(content) if content else {"type": "bar"}
            chart_type = spec.get("type", "bar")
            title = spec.get("title", "Chart")
            options = json.dumps(spec, indent=2)
            return f'''<html><body><div id="c" style="width:800px;height:600px;"></div>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<script>var c=echarts.init(document.getElementById('c'));
var opts={options};
c.setOption({{title:{{text:'{title}'}},tooltip:{{}},
xAxis:{{data:['A','B','C','D','E']}},
yAxis:{{}},series:[{{type:'{chart_type}',data:[10,20,15,30,25]}}]}});</script></body></html>'''
        except Exception:
            return f"<p>Chart: {content[:100]}</p>"

    def generate(self, prompt: str, creative_type: str, format: str) -> str:
        return f"{{'title':'{prompt[:60]}','type':'bar'}}"

    def resize(self, content: str, width: int, height: int) -> str:
        return content

    def preview(self, content: str, format: str) -> str:
        return content


# ── Creative Runtime ──────────────────────────────────────────────

class CreativeRuntime:
    def __init__(self):
        self._assets: dict[str, CreativeAsset] = {}
        self._brands: dict[str, Brand] = {}
        self._templates: dict[str, Template] = {}
        self._providers: dict[str, CreativeProvider] = {}
        self._register_builtin()

    def _register_builtin(self):
        self.register_provider("svg", NativeSVGProvider())
        self.register_provider("echarts", EChartsProvider())
        # Seed default brands
        self._brands["shunya_default"] = Brand(
            brand_id="shunya_default", name="SHUNYA Default",
            primary_color="#BFAC8B", secondary_color="#2A2626",
            tone="professional", voice="confident, calm",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def register_provider(self, name: str, provider: CreativeProvider):
        self._providers[name] = provider

    def get_provider(self, name: str = "svg") -> Optional[CreativeProvider]:
        return self._providers.get(name, self._providers.get("svg"))

    # ── Creative Assets ──

    def create_asset(self, title: str, intent: str = "inform",
                     creative_type: str = "presentation",
                     purpose: str = "", content: str = "",
                     format: str = "svg") -> CreativeAsset:
        now = datetime.now(timezone.utc).isoformat()
        intent_info = COMMUNICATION_INTENTS.get(intent, {})
        type_info = CREATIVE_TYPES.get(creative_type, CREATIVE_TYPES.get("presentation", {}))
        asset = CreativeAsset(
            asset_id=f"cr_{uuid.uuid4().hex[:12]}",
            title=title,
            intent=intent,
            creative_type=creative_type,
            format=format or (type_info.get("formats", ["svg"])[0] if type_info else "svg"),
            content=content,
            purpose=purpose or intent_info.get("description", ""),
            created_at=now,
            updated_at=now,
        )
        self._assets[asset.asset_id] = asset
        self._emit_reality(asset, "creative_created")
        return asset

    def generate_representations(self, title: str, intent: str = "inform",
                                  content: str = "") -> list[CreativeAsset]:
        """Generate multiple creative representations from one intent.
        
        One intent → multiple render targets → all through the same runtime.
        Each representation is a separate CreativeAsset sharing the same intent.
        """
        intent_info = COMMUNICATION_INTENTS.get(intent, {})
        suggested_types = intent_info.get("suggested_types", ["presentation"])
        assets = []
        for i, ctype in enumerate(suggested_types):
            variant_title = f"{title} ({ctype.replace('_', ' ')})" if len(suggested_types) > 1 else title
            type_info = CREATIVE_TYPES.get(ctype, {})
            fmt = type_info.get("formats", ["svg"])[0] if type_info else "svg"
            asset = self.create_asset(
                title=variant_title,
                intent=intent,
                creative_type=ctype,
                purpose=intent_info.get("description", ""),
                content=content,
                format=fmt,
            )
            # Generate content via provider
            provider = self.get_provider("svg" if fmt == "svg" else "echarts")
            if provider:
                asset.content = provider.generate(title, ctype, fmt)
            assets.append(asset)
        return assets

    def get_asset(self, asset_id: str) -> Optional[CreativeAsset]:
        return self._assets.get(asset_id)

    def list_assets(self, creative_type: Optional[str] = None, limit: int = 50) -> list[CreativeAsset]:
        assets = list(self._assets.values())
        if creative_type:
            assets = [a for a in assets if a.creative_type == creative_type]
        assets.sort(key=lambda a: a.updated_at, reverse=True)
        return assets[:limit]

    def render_asset(self, asset_id: str, target_format: str = "svg") -> Optional[str]:
        asset = self._assets.get(asset_id)
        if not asset:
            return None
        provider = self.get_provider("svg" if target_format == "svg" else "echarts")
        if not provider:
            return asset.content
        return provider.render(asset.content, target_format)

    def generate_asset(self, prompt: str, creative_type: str = "presentation",
                       format: str = "svg") -> CreativeAsset:
        asset = self.create_asset(title=prompt[:80], creative_type=creative_type,
                                  purpose=f"Generated from: {prompt}", format=format)
        provider = self.get_provider("svg" if format == "svg" else "echarts")
        if provider:
            content = provider.generate(prompt, creative_type, format)
            asset.content = content
        return asset

    # ── Brands ──

    def create_brand(self, name: str, **kwargs) -> Brand:
        brand = Brand(
            brand_id=f"br_{uuid.uuid4().hex[:12]}",
            name=name,
            created_at=datetime.now(timezone.utc).isoformat(),
            **{k: v for k, v in kwargs.items() if hasattr(Brand, k)},
        )
        self._brands[brand.brand_id] = brand
        return brand

    def get_brand(self, brand_id: str) -> Optional[Brand]:
        return self._brands.get(brand_id)

    def list_brands(self) -> list[Brand]:
        return list(self._brands.values())

    # ── Templates ──

    def create_template(self, name: str, creative_type: str,
                        content: str = "", brand_id: str = "") -> Template:
        tpl = Template(
            template_id=f"tpl_{uuid.uuid4().hex[:12]}",
            name=name,
            creative_type=creative_type,
            content=content,
            brand_id=brand_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._templates[tpl.template_id] = tpl
        return tpl

    def get_template(self, template_id: str) -> Optional[Template]:
        return self._templates.get(template_id)

    def list_templates(self, creative_type: Optional[str] = None) -> list[Template]:
        templates = list(self._templates.values())
        if creative_type:
            templates = [t for t in templates if t.creative_type == creative_type]
        return templates

    # ── AI Intelligence ──

    def analyze_brand_consistency(self, asset_id: str) -> str:
        asset = self._assets.get(asset_id)
        if not asset:
            return ""
        if not asset.brand_id:
            return "No brand assigned — consistency not assessed"
        brand = self._brands.get(asset.brand_id)
        if not brand:
            return "Brand not found"
        return (f"Brand: {brand.name}. Tone: {brand.tone}. Voice: {brand.voice}. "
                f"Colors: {brand.primary_color}/{brand.secondary_color}. "
                f"Recommendation: Ensure visual matches brand guidelines.")

    def generate_summary(self, asset_id: str) -> str:
        asset = self._assets.get(asset_id)
        if not asset:
            return ""
        asset.ai_summary = (f"Creative: {asset.title} ({asset.creative_type}). "
                            f"Purpose: {asset.purpose}. Format: {asset.format}. "
                            f"Versions: {len(asset.versions)}.")
        return asset.ai_summary

    def suggest_variant(self, asset_id: str) -> str:
        asset = self._assets.get(asset_id)
        if not asset:
            return ""
        suggestions = {
            "social_post": "Consider creating a carousel variant for deeper storytelling.",
            "infographic": "Consider a video summary variant for social sharing.",
            "presentation": "Consider a handout PDF variant and a speaker notes variant.",
            "poster": "Consider digital banner and social media variants.",
            "banner": "Consider animated HTML5 and static image variants.",
            "thumbnail": "Consider a teaser video variant.",
            "reel": "Consider a vertical and horizontal aspect ratio variant.",
            "storyboard": "Consider an animatic preview variant.",
        }
        return suggestions.get(asset.creative_type, "Consider alternative format variants.")

    # ── Search ──

    def search(self, query: str) -> list[dict]:
        q = query.lower()
        results = []
        for a in self._assets.values():
            score = 0
            if q in a.title.lower(): score += 10
            if q in a.creative_type.lower(): score += 8
            if q in a.purpose.lower(): score += 5
            if q in a.ai_summary.lower(): score += 3
            if score > 0:
                results.append({"asset": a.to_dict(), "score": score})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:20]

    # ── Reality ──

    def _emit_reality(self, asset: CreativeAsset, event_type: str):
        try:
            from app.reality_engine.engine import get_reality_engine
            get_reality_engine().notify({
                "type": event_type, "identity_id": "system",
                "asset_id": asset.asset_id, "title": asset.title,
                "creative_type": asset.creative_type,
            })
        except Exception:
            pass


# ── Singleton ────────────────────────────────────────────────────

_RUNTIME_INSTANCE: Optional[CreativeRuntime] = None

def get_creative_runtime() -> CreativeRuntime:
    global _RUNTIME_INSTANCE
    if _RUNTIME_INSTANCE is None:
        _RUNTIME_INSTANCE = CreativeRuntime()
    return _RUNTIME_INSTANCE