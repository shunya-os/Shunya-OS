"""SHUNYA Phase A1 — Space Renderer.
Phase A1A — Capability-driven rendering.

Replaces fixed panel rendering with:
Capability → Panel → Renderer → Widget

Applications register capabilities.
The Space runtime discovers them dynamically.
No application may modify the Space model directly.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.space.models import UniversalSpace, SpacePanel
from app.space.store import get_store
from app.space.capabilities import (
    Capability, get_registry, CapabilityRegistry,
)


# =========================================================================
# Widget
# =========================================================================


class Widget:
    """A rendered piece of panel content within a capability."""

    def __init__(self, widget_id: str, label: str, icon: str = "",
                 priority: int = 50):
        self.widget_id = widget_id
        self.label = label
        self.icon = icon
        self.priority = priority

    def render(self, space: UniversalSpace,
               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Render widget content."""
        return {
            "widget_id": self.widget_id,
            "label": self.label,
            "icon": self.icon,
            "content": {},
        }


# =========================================================================
# Panel Renderer
# =========================================================================


class PanelRenderer:
    """Renders a single panel for a capability.

    A panel is a container for widgets.
    """

    def __init__(self, panel: SpacePanel, label: str, icon: str,
                 widgets: Optional[List[Widget]] = None,
                 priority: int = 50):
        self.panel = panel
        self.label = label
        self.icon = icon
        self.widgets = widgets or []
        self.priority = priority

    def add_widget(self, widget: Widget) -> None:
        self.widgets.append(widget)
        self.widgets.sort(key=lambda w: w.priority)

    def render(self, space: UniversalSpace,
               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Render the panel with all its widgets."""
        widgets_data = {}
        for widget in self.widgets:
            wdata = widget.render(space, context)
            widgets_data[widget.widget_id] = wdata

        return {
            "panel": self.panel.value,
            "label": self.label,
            "icon": self.icon,
            "widgets": widgets_data,
        }


# =========================================================================
# Default Panel Renderers
# =========================================================================


def _build_context_renderer() -> PanelRenderer:
    r = PanelRenderer(SpacePanel.CONTEXT, "Context", "📋", priority=10)
    r.add_widget(Widget("position", "Position", "📍", 10))
    r.add_widget(Widget("sections", "Sections", "📑", 20))
    r.add_widget(Widget("pending", "Pending Work", "⏳", 30))
    r._orig_render = r.render
    r.render = lambda space, ctx=None: {
        "panel": "context",
        "label": "Context",
        "icon": "📋",
        "widgets": {
            "position": {
                "widget_id": "position", "label": "Position", "icon": "📍",
                "content": {
                    "last_position": space.context.last_position,
                    "collapsed_sections": space.context.collapsed_sections,
                },
            },
            "sections": {
                "widget_id": "sections", "label": "Sections", "icon": "📑",
                "content": {
                    "open_documents": space.context.open_documents,
                    "recent_conversations": space.context.recent_conversations,
                },
            },
            "pending": {
                "widget_id": "pending", "label": "Pending", "icon": "⏳",
                "content": {"items": space.context.pending_work},
            },
        },
    }
    return r


def _build_relationships_renderer() -> PanelRenderer:
    r = PanelRenderer(SpacePanel.RELATIONSHIPS, "Relationships", "🔗",
                      priority=20)
    r._orig_render = r.render
    r.render = lambda space, ctx=None: {
        "panel": "relationships", "label": "Relationships", "icon": "🔗",
        "widgets": {
            "graph": {
                "widget_id": "graph", "label": "Graph", "icon": "🔗",
                "content": {
                    "total": len(space.relationships),
                    "relationships": [r.to_dict() for r in space.relationships],
                },
            },
        },
    }
    return r


def _build_timeline_renderer() -> PanelRenderer:
    r = PanelRenderer(SpacePanel.TIMELINE, "Timeline", "📅", priority=30)
    r._orig_render = r.render
    r.render = lambda space, ctx=None: {
        "panel": "timeline", "label": "Timeline", "icon": "📅",
        "widgets": {
            "events": {
                "widget_id": "events", "label": "Events", "icon": "📅",
                "content": {
                    "total": len(space.timeline),
                    "events": [e.to_dict() for e in space.timeline[-20:]],
                },
            },
            "categories": {
                "widget_id": "categories", "label": "Categories", "icon": "🏷️",
                "content": {
                    "categories": list(set(
                        e.category for e in space.timeline if e.category
                    )),
                },
            },
        },
    }
    return r


def _build_knowledge_renderer() -> PanelRenderer:
    r = PanelRenderer(SpacePanel.KNOWLEDGE, "Knowledge", "🧠", priority=40)
    r._orig_render = r.render
    r.render = lambda space, ctx=None: {
        "panel": "knowledge", "label": "Knowledge", "icon": "🧠",
        "widgets": {
            "items": {
                "widget_id": "items", "label": "Items", "icon": "📄",
                "content": {
                    "total": len(space.knowledge),
                    "items": [k.to_dict() for k in space.knowledge[-20:]],
                },
            },
            "summary": {
                "widget_id": "summary", "label": "Summary", "icon": "📊",
                "content": {
                    "by_type": _count_by_type(space.knowledge, "item_type"),
                },
            },
        },
    }
    return r


def _build_plans_renderer() -> PanelRenderer:
    r = PanelRenderer(SpacePanel.PLANS, "Plans", "🎯", priority=50)
    r._orig_render = r.render
    r.render = lambda space, ctx=None: {
        "panel": "plans", "label": "Plans", "icon": "🎯",
        "widgets": {
            "plans": {
                "widget_id": "plans", "label": "Plans", "icon": "🎯",
                "content": {
                    "total": len(space.plans),
                    "plans": [p.to_dict() for p in space.plans],
                },
            },
        },
    }
    return r


def _build_execution_renderer() -> PanelRenderer:
    r = PanelRenderer(SpacePanel.EXECUTION, "Execution", "⚡", priority=60)
    r._orig_render = r.render
    r.render = lambda space, ctx=None: {
        "panel": "execution", "label": "Execution", "icon": "⚡",
        "widgets": {
            "executions": {
                "widget_id": "executions", "label": "Tasks", "icon": "⚡",
                "content": {
                    "total": len(space.executions),
                    "executions": [e.to_dict() for e in space.executions],
                },
            },
        },
    }
    return r


def _build_communications_renderer() -> PanelRenderer:
    r = PanelRenderer(SpacePanel.COMMUNICATIONS, "Communications", "💬",
                      priority=70)
    r._orig_render = r.render
    r.render = lambda space, ctx=None: {
        "panel": "communications", "label": "Communications", "icon": "💬",
        "widgets": {
            "messages": {
                "widget_id": "messages", "label": "Messages", "icon": "💬",
                "content": {
                    "total": len(space.communications),
                    "communications": [
                        c.to_dict() for c in reversed(space.communications)
                    ],
                },
            },
        },
    }
    return r


def _build_documents_renderer() -> PanelRenderer:
    r = PanelRenderer(SpacePanel.DOCUMENTS, "Documents", "📄", priority=80)
    r._orig_render = r.render
    r.render = lambda space, ctx=None: {
        "panel": "documents", "label": "Documents", "icon": "📄",
        "widgets": {
            "documents": {
                "widget_id": "documents", "label": "Files", "icon": "📄",
                "content": {
                    "total": len(space.documents),
                    "documents": [d.to_dict() for d in space.documents],
                },
            },
        },
    }
    return r


def _build_responsibilities_renderer() -> PanelRenderer:
    r = PanelRenderer(SpacePanel.RESPONSIBILITIES, "Responsibilities", "👤",
                      priority=90)
    r._orig_render = r.render
    r.render = lambda space, ctx=None: {
        "panel": "responsibilities", "label": "Responsibilities", "icon": "👤",
        "widgets": {
            "assignments": {
                "widget_id": "assignments", "label": "Assignments", "icon": "👤",
                "content": {
                    "total": len(space.responsibilities),
                    "responsibilities": [
                        r.to_dict() for r in space.responsibilities
                    ],
                },
            },
        },
    }
    return r


def _build_metrics_renderer() -> PanelRenderer:
    r = PanelRenderer(SpacePanel.METRICS, "Metrics", "📊", priority=100)
    r._orig_render = r.render
    r.render = lambda space, ctx=None: {
        "panel": "metrics", "label": "Metrics", "icon": "📊",
        "widgets": {
            "metrics": {
                "widget_id": "metrics", "label": "Values", "icon": "📊",
                "content": {
                    "total": len(space.metrics),
                    "metrics": [m.to_dict() for m in space.metrics],
                },
            },
            "trends": {
                "widget_id": "trends", "label": "Trends", "icon": "📈",
                "content": {
                    "improving": sum(1 for m in space.metrics if m.trend == "improving"),
                    "declining": sum(1 for m in space.metrics if m.trend == "declining"),
                    "stable": sum(1 for m in space.metrics if m.trend == "stable"),
                },
            },
        },
    }
    return r


def _build_ai_renderer() -> PanelRenderer:
    r = PanelRenderer(SpacePanel.AI_UNDERSTANDING, "AI Understanding", "🤖",
                      priority=110)
    r._orig_render = r.render
    r.render = lambda space, ctx=None: {
        "panel": "ai_understanding", "label": "AI Understanding", "icon": "🤖",
        "widgets": {
            "understanding": {
                "widget_id": "understanding", "label": "Understanding",
                "icon": "🧠",
                "content": {
                    "summary": space.ai_understanding.summary,
                    "goals": space.ai_understanding.goals,
                },
            },
            "resident": {
                "widget_id": "resident", "label": "AI Resident", "icon": "🤖",
                "content": space.ai_resident.to_dict(),
            },
        },
    }
    return r


# =========================================================================
# Panel Renderer Registry
# =========================================================================

PANEL_RENDERERS: Dict[str, PanelRenderer] = {
    "context": _build_context_renderer(),
    "relationships": _build_relationships_renderer(),
    "timeline": _build_timeline_renderer(),
    "knowledge": _build_knowledge_renderer(),
    "plans": _build_plans_renderer(),
    "execution": _build_execution_renderer(),
    "communications": _build_communications_renderer(),
    "documents": _build_documents_renderer(),
    "responsibilities": _build_responsibilities_renderer(),
    "metrics": _build_metrics_renderer(),
    "ai_understanding": _build_ai_renderer(),
}


# =========================================================================
# Capability-driven Space Renderer
# =========================================================================


class SpaceRenderer:
    """Capability-driven Space renderer.

    Rendering pipeline:
    1. Discover capabilities from CapabilityRegistry
    2. Resolve panels from capabilities
    3. Render each panel through its PanelRenderer
    4. Each panel renders its widgets

    No application may modify the Space model directly.
    """

    def __init__(self,
                 capability_registry: Optional[CapabilityRegistry] = None,
                 panel_renderers: Optional[Dict[str, PanelRenderer]] = None):
        self._cap_registry = capability_registry or get_registry()
        self._panel_renderers = panel_renderers or PANEL_RENDERERS

    def render(self, space: UniversalSpace,
               context: Optional[Dict[str, Any]] = None,
               panels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Render the full Space view based on its capabilities.

        Args:
            space: The UniversalSpace to render.
            context: Optional rendering context.
            panels: Optional list of panel names to include.
                    If None, derives from capabilities.

        Returns:
            A dict with identity, capabilities, panels, commands, composition.
        """
        # 1. Discover capabilities
        capabilities = self._cap_registry.discover_capabilities(space)
        cap_names = [c.name for c in capabilities]

        # 2. Resolve panels from capabilities
        if panels is None:
            panels = []
            for cap in capabilities:
                for p in cap.panels:
                    if p.value not in panels:
                        panels.append(p.value)

        # 3. Render each panel
        rendered_panels = {}
        for pname in panels:
            renderer = self._panel_renderers.get(pname)
            if renderer:
                rendered_panels[pname] = renderer.render(space, context)

        result = {
            "identity": space.identity.to_dict(),
            "summary": space.to_summary(),
            "capabilities": cap_names,
            "panels": rendered_panels,
            "commands": space.commands,
            "parent_space_id": space.parent_space_id,
            "child_space_ids": space.child_space_ids,
            "permissions": space.permissions,
            "lifecycle": space.lifecycle.to_dict(),
            "ai_resident": space.ai_resident.to_dict(),
        }
        return result

    def render_summary(self, space: UniversalSpace) -> Dict[str, Any]:
        return space.to_summary()

    def render_panel(self, space: UniversalSpace,
                     panel_name: str,
                     context: Optional[Dict[str, Any]] = None
                     ) -> Optional[Dict[str, Any]]:
        renderer = self._panel_renderers.get(panel_name)
        if renderer:
            return renderer.render(space, context)
        return None

    def get_visible_panels(self, space: UniversalSpace) -> List[str]:
        """Get which panels are visible based on capabilities."""
        capabilities = self._cap_registry.discover_capabilities(space)
        panels = []
        for cap in capabilities:
            for p in cap.panels:
                if p.value not in panels:
                    panels.append(p.value)
        return panels


# =========================================================================
# Helpers
# =========================================================================


def _count_by_type(items: list, attr: str) -> dict:
    counts = {}
    for item in items:
        val = getattr(item, attr, "unknown")
        counts[val] = counts.get(val, 0) + 1
    return counts


# =========================================================================
# Singleton
# =========================================================================

_renderer: Optional[SpaceRenderer] = None


def get_renderer() -> SpaceRenderer:
    global _renderer
    if _renderer is None:
        _renderer = SpaceRenderer()
    return _renderer


def reset_renderer() -> None:
    global _renderer
    _renderer = None


# Backward compatibility aliases
PanelProvider = PanelRenderer
DEFAULT_PANEL_PROVIDERS = list(PANEL_RENDERERS.values())