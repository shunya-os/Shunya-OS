"""SHUNYA Workspace Runtime — Orchestrator."""

from __future__ import annotations

import json
import logging
from typing import Any

from core.workspace_runtime.models import (
    CommandBinding,
    DockPosition,
    Panel,
    PanelType,
    PresenceInfo,
    SessionState,
    Tab,
    Workspace,
    WorkspaceCommand,
    WorkspaceTrace,
    _generate_id,
)

logger = logging.getLogger(__name__)


class WorkspaceRuntime:
    """Makes SHUNYA feel like an OS. Manages workspaces, panels, tabs,
    docking, split views, undo/redo, session restore, command routing,
    keyboard navigation, focus, and presence."""

    def __init__(self):
        self._workspaces: dict[str, Workspace] = {}
        self._active_workspace_id: str = ""
        self._command_history: list[WorkspaceCommand] = []
        self._history_position: int = -1
        self._command_bindings: dict[str, CommandBinding] = {}
        self._presence: dict[str, PresenceInfo] = {}
        self._traces: list[WorkspaceTrace] = []
        self._max_history = 100

    # ── Workspace Management ─────────────────────────────────────────

    def create_workspace(self, name: str = "Default") -> Workspace:
        ws = Workspace(name=name)
        # Add default center panel
        center = Panel(panel_type=PanelType.OBJECT, dock=DockPosition.CENTER)
        ws.panels.append(center)
        ws.active_panel_id = center.panel_id
        self._workspaces[ws.workspace_id] = ws
        self._active_workspace_id = ws.workspace_id
        self._record_trace("create_workspace", ws.workspace_id)
        return ws

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        return self._workspaces.get(workspace_id)

    def list_workspaces(self) -> list[Workspace]:
        return list(self._workspaces.values())

    def switch_workspace(self, workspace_id: str) -> Workspace | None:
        ws = self._workspaces.get(workspace_id)
        if ws:
            self._active_workspace_id = workspace_id
            self._record_trace("switch_workspace", workspace_id)
        return ws

    def delete_workspace(self, workspace_id: str) -> bool:
        if workspace_id not in self._workspaces:
            return False
        del self._workspaces[workspace_id]
        if self._active_workspace_id == workspace_id:
            self._active_workspace_id = next(iter(self._workspaces), "")
        self._record_trace("delete_workspace", workspace_id)
        return True

    @property
    def active_workspace(self) -> Workspace | None:
        return self._workspaces.get(self._active_workspace_id)

    # ── Panel Management ─────────────────────────────────────────────

    def add_panel(self, workspace_id: str, panel_type: PanelType = PanelType.OBJECT,
                  dock: DockPosition = DockPosition.CENTER) -> Panel | None:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return None
        panel = Panel(panel_type=panel_type, dock=dock, order=len(ws.panels))
        ws.panels.append(panel)
        ws.active_panel_id = panel.panel_id
        self._push_command("add_panel", f"Add {panel_type.value} panel")
        self._record_trace("add_panel", workspace_id, panel.panel_id)
        return panel

    def remove_panel(self, workspace_id: str, panel_id: str) -> bool:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return False
        ws.panels = [p for p in ws.panels if p.panel_id != panel_id]
        if ws.active_panel_id == panel_id:
            ws.active_panel_id = ws.panels[0].panel_id if ws.panels else ""
        self._push_command("remove_panel", "Remove panel")
        self._record_trace("remove_panel", workspace_id, panel_id)
        return True

    def dock_panel(self, workspace_id: str, panel_id: str, dock: DockPosition) -> bool:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return False
        for p in ws.panels:
            if p.panel_id == panel_id:
                p.dock = dock
                self._push_command("dock_panel", f"Dock panel to {dock.value}")
                self._record_trace("dock_panel", workspace_id, panel_id)
                return True
        return False

    def split_panel(self, workspace_id: str, panel_id: str,
                    direction: str = "right") -> Panel | None:
        """Split a panel, creating a new panel alongside it."""
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return None
        for p in ws.panels:
            if p.panel_id == panel_id:
                new_panel = Panel(panel_type=p.panel_type, dock=p.dock,
                                  order=p.order + 1, width=p.width // 2)
                ws.panels.insert(ws.panels.index(p) + 1, new_panel)
                self._push_command("split_panel", f"Split {direction}")
                self._record_trace("split_panel", workspace_id, panel_id)
                return new_panel
        return None

    # ── Tab Management ───────────────────────────────────────────────

    def open_tab(self, workspace_id: str, panel_id: str, object_id: str,
                 label: str = "", panel_type: PanelType = PanelType.OBJECT) -> Tab | None:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return None
        for p in ws.panels:
            if p.panel_id == panel_id:
                tab = Tab(label=label or object_id, object_id=object_id, panel_type=panel_type)
                p.tabs.append(tab)
                p.active_tab_id = tab.tab_id
                self._push_command("open_tab", f"Open {label}")
                self._record_trace("open_tab", workspace_id, panel_id)
                # Navigation history
                ws.navigation_history.append(object_id)
                ws.history_index = len(ws.navigation_history) - 1
                return tab
        return None

    def close_tab(self, workspace_id: str, panel_id: str, tab_id: str) -> bool:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return False
        for p in ws.panels:
            if p.panel_id == panel_id:
                p.tabs = [t for t in p.tabs if t.tab_id != tab_id]
                if p.active_tab_id == tab_id:
                    p.active_tab_id = p.tabs[0].tab_id if p.tabs else ""
                self._record_trace("close_tab", workspace_id, panel_id)
                return True
        return False

    def switch_tab(self, workspace_id: str, panel_id: str, tab_id: str) -> bool:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return False
        for p in ws.panels:
            if p.panel_id == panel_id:
                for t in p.tabs:
                    if t.tab_id == tab_id:
                        p.active_tab_id = tab_id
                        ws.focus_object_id = t.object_id
                        self._record_trace("switch_tab", workspace_id, panel_id)
                        return True
        return False

    # ── Undo / Redo ──────────────────────────────────────────────────

    def _push_command(self, command_type: str, description: str,
                      data: dict | None = None) -> None:
        cmd = WorkspaceCommand(command_type=command_type, description=description, data=data or {})
        # Truncate history past current position
        self._command_history = self._command_history[:self._history_position + 1]
        self._command_history.append(cmd)
        self._history_position = len(self._command_history) - 1
        if len(self._command_history) > self._max_history:
            self._command_history.pop(0)
            self._history_position -= 1

    def undo(self) -> WorkspaceCommand | None:
        if self._history_position < 0:
            return None
        cmd = self._command_history[self._history_position]
        self._history_position -= 1
        self._record_trace("undo", "", "")
        return cmd

    def redo(self) -> WorkspaceCommand | None:
        if self._history_position >= len(self._command_history) - 1:
            return None
        self._history_position += 1
        cmd = self._command_history[self._history_position]
        self._record_trace("redo", "", "")
        return cmd

    def get_history(self) -> list[WorkspaceCommand]:
        return list(self._command_history)

    # ── Navigation ───────────────────────────────────────────────────

    def navigate_to(self, workspace_id: str, object_id: str) -> None:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return
        ws.navigation_history.append(object_id)
        ws.history_index = len(ws.navigation_history) - 1
        ws.focus_object_id = object_id
        self._record_trace("navigate", workspace_id)

    def navigate_back(self, workspace_id: str) -> str | None:
        ws = self._workspaces.get(workspace_id)
        if not ws or ws.history_index <= 0:
            return None
        ws.history_index -= 1
        obj_id = ws.navigation_history[ws.history_index]
        ws.focus_object_id = obj_id
        self._record_trace("navigate_back", workspace_id)
        return obj_id

    def navigate_forward(self, workspace_id: str) -> str | None:
        ws = self._workspaces.get(workspace_id)
        if not ws or ws.history_index >= len(ws.navigation_history) - 1:
            return None
        ws.history_index += 1
        obj_id = ws.navigation_history[ws.history_index]
        ws.focus_object_id = obj_id
        self._record_trace("navigate_forward", workspace_id)
        return obj_id

    # ── Deep Linking ─────────────────────────────────────────────────

    def resolve_deep_link(self, link: str) -> dict[str, Any]:
        """Parse a deep link like 'shunya://workspace/{id}/panel/{id}/tab/{id}'."""
        result: dict[str, Any] = {}
        parts = link.replace("shunya://", "").split("/")
        for i in range(0, len(parts) - 1, 2):
            key = parts[i]
            val = parts[i + 1]
            if key in ("workspace", "panel", "tab", "object"):
                result[key] = val
        return result

    # ── Command Routing ──────────────────────────────────────────────

    def register_command(self, command: str, handler: Any,
                         shortcut: str = "", description: str = "") -> None:
        self._command_bindings[command] = CommandBinding(
            command=command, shortcut=shortcut, description=description, handler=handler,
        )

    def execute_command(self, command: str, *args: Any, **kwargs: Any) -> Any:
        binding = self._command_bindings.get(command)
        if not binding or not binding.handler:
            raise ValueError(f"Unknown command: {command}")
        self._record_trace("command", "", "")
        return binding.handler(*args, **kwargs)

    def list_commands(self) -> list[CommandBinding]:
        return list(self._command_bindings.values())

    # ── Session Persistence ──────────────────────────────────────────

    def save_session(self, workspace_id: str) -> str:
        """Serialize a workspace to JSON for persistence."""
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return "{}"
        panels_data = []
        for p in ws.panels:
            panels_data.append({
                "panel_id": p.panel_id,
                "panel_type": p.panel_type.value,
                "dock": p.dock.value,
                "tabs": [{"tab_id": t.tab_id, "label": t.label, "object_id": t.object_id,
                          "panel_type": t.panel_type.value} for t in p.tabs],
                "active_tab_id": p.active_tab_id,
                "order": p.order,
                "width": p.width,
                "height": p.height,
                "minimized": p.minimized,
            })
        state = SessionState(
            workspace_id=ws.workspace_id,
            workspace_name=ws.name,
            panels=panels_data,
            focus_object_id=ws.focus_object_id,
            navigation_history=list(ws.navigation_history),
        )
        return json.dumps({"workspace": {
            "workspace_id": state.workspace_id,
            "workspace_name": state.workspace_name,
            "panels": state.panels,
            "focus_object_id": state.focus_object_id,
            "navigation_history": state.navigation_history,
            "saved_at": state.saved_at,
        }}, indent=2)

    def restore_session(self, json_data: str) -> Workspace | None:
        """Restore a workspace from JSON."""
        try:
            data = json.loads(json_data)
            ws_data = data.get("workspace", data)
            ws = Workspace(
                workspace_id=ws_data.get("workspace_id", _generate_id()),
                name=ws_data.get("workspace_name", "Restored"),
            )
            for p_data in ws_data.get("panels", []):
                panel = Panel(
                    panel_id=p_data.get("panel_id", _generate_id()),
                    panel_type=PanelType(p_data.get("panel_type", "object")),
                    dock=DockPosition(p_data.get("dock", "center")),
                    order=p_data.get("order", 0),
                    width=p_data.get("width", 400),
                    height=p_data.get("height", 300),
                    minimized=p_data.get("minimized", False),
                )
                for t_data in p_data.get("tabs", []):
                    tab = Tab(
                        tab_id=t_data.get("tab_id", _generate_id()),
                        label=t_data.get("label", ""),
                        object_id=t_data.get("object_id", ""),
                        panel_type=PanelType(t_data.get("panel_type", "object")),
                    )
                    panel.tabs.append(tab)
                panel.active_tab_id = p_data.get("active_tab_id", panel.tabs[0].tab_id if panel.tabs else "")
                ws.panels.append(panel)
            ws.active_panel_id = ws.panels[0].panel_id if ws.panels else ""
            ws.focus_object_id = ws_data.get("focus_object_id", "")
            ws.navigation_history = ws_data.get("navigation_history", [])
            ws.history_index = len(ws.navigation_history) - 1
            self._workspaces[ws.workspace_id] = ws
            self._active_workspace_id = ws.workspace_id
            self._record_trace("restore_session", ws.workspace_id)
            return ws
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("Failed to restore session: %s", exc)
            return None

    # ── Focus Orchestration ──────────────────────────────────────────

    def set_focus(self, workspace_id: str, object_id: str) -> None:
        ws = self._workspaces.get(workspace_id)
        if ws:
            ws.focus_object_id = object_id

    def get_focus(self, workspace_id: str) -> str:
        ws = self._workspaces.get(workspace_id)
        return ws.focus_object_id if ws else ""

    # ── Presence ──────────────────────────────────────────────────────

    def update_presence(self, user_id: str, workspace_id: str,
                        focus_object_id: str = "", online: bool = True) -> PresenceInfo:
        info = PresenceInfo(
            user_id=user_id, workspace_id=workspace_id,
            focus_object_id=focus_object_id, online=online,
        )
        self._presence[user_id] = info
        self._record_trace("presence", workspace_id)
        return info

    def get_presence(self, workspace_id: str) -> list[PresenceInfo]:
        return [p for p in self._presence.values()
                if p.workspace_id == workspace_id and p.online]

    # ── Observability ─────────────────────────────────────────────────

    def _record_trace(self, operation: str, workspace_id: str,
                      panel_id: str = "") -> None:
        self._traces.append(WorkspaceTrace(
            operation=operation, workspace_id=workspace_id, panel_id=panel_id,
            latency_ms=0.0,
        ))

    def get_traces(self, limit: int = 100) -> list[WorkspaceTrace]:
        return self._traces[-limit:]

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "runtime": "workspace_runtime",
            "workspaces": len(self._workspaces),
            "active_workspace": self._active_workspace_id,
            "total_commands": len(self._command_history),
            "history_position": self._history_position,
            "registered_commands": len(self._command_bindings),
            "online_users": len(self._presence),
        }