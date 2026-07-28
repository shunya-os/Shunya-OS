"""SHUNYA Workspace Runtime — data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _generate_id() -> str:
    from core.kernel.types import generate_uuid7
    return generate_uuid7()


class DockPosition(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    CENTER = "center"
    FLOAT = "float"


class PanelType(str, Enum):
    INSPECTOR = "inspector"
    PROPERTIES = "properties"
    TIMELINE = "timeline"
    GRAPH = "graph"
    SEARCH = "search"
    OBJECT = "object"
    COMMAND = "command"
    TERMINAL = "terminal"
    CUSTOM = "custom"


@dataclass
class Tab:
    tab_id: str = field(default_factory=_generate_id)
    label: str = ""
    object_id: str = ""
    panel_type: PanelType = PanelType.OBJECT
    icon: str = ""
    closable: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Panel:
    panel_id: str = field(default_factory=_generate_id)
    panel_type: PanelType = PanelType.OBJECT
    dock: DockPosition = DockPosition.CENTER
    tabs: list[Tab] = field(default_factory=list)
    active_tab_id: str = ""
    order: int = 0
    width: int = 400
    height: int = 300
    minimized: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def active_tab(self) -> Tab | None:
        for t in self.tabs:
            if t.tab_id == self.active_tab_id:
                return t
        return self.tabs[0] if self.tabs else None


@dataclass
class WorkspaceCommand:
    """A single undoable command."""

    command_id: str = field(default_factory=_generate_id)
    command_type: str = ""
    description: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now_iso)


@dataclass
class Workspace:
    """A named collection of panels, tabs, and state."""

    workspace_id: str = field(default_factory=_generate_id)
    name: str = "Default"
    panels: list[Panel] = field(default_factory=list)
    active_panel_id: str = ""
    focus_object_id: str = ""
    navigation_history: list[str] = field(default_factory=list)
    history_index: int = -1
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def active_panel(self) -> Panel | None:
        for p in self.panels:
            if p.panel_id == self.active_panel_id:
                return p
        return self.panels[0] if self.panels else None


@dataclass
class CommandBinding:
    command: str = ""
    shortcut: str = ""
    description: str = ""
    handler: Any = None


@dataclass
class PresenceInfo:
    user_id: str = ""
    workspace_id: str = ""
    focus_object_id: str = ""
    active_panel_id: str = ""
    online: bool = True
    last_seen: str = field(default_factory=_now_iso)


@dataclass
class SessionState:
    """Serializable workspace session for restore."""

    workspace_id: str = ""
    workspace_name: str = ""
    panels: list[dict[str, Any]] = field(default_factory=list)
    focus_object_id: str = ""
    navigation_history: list[str] = field(default_factory=list)
    saved_at: str = field(default_factory=_now_iso)


@dataclass
class WorkspaceTrace:
    operation: str = ""
    workspace_id: str = ""
    panel_id: str = ""
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=_now_iso)