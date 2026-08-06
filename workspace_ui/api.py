"""Universal Workspace — API Server.

Composes from frozen WorkspaceRuntime + PersonalOSOrchestrator.
No new Runtime. No new Living Object. Pure composition.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from core.personal_os import PersonalOSOrchestrator
from core.workspace_runtime import WorkspaceRuntime

logger = logging.getLogger(__name__)


class WorkspaceAPI:
    """Server-side workspace logic — bridges Personal OS and Workspace Runtime."""

    def __init__(self) -> None:
        self._os = PersonalOSOrchestrator()
        self._ws = WorkspaceRuntime()
        self._owner_id: str = ""
        self._initialized = False

    def initialize(self, owner_id: str = "default") -> dict[str, Any]:
        self._owner_id = owner_id
        init_result = self._os.initialize()
        self._os.set_owner(owner_id)
        ws = self._ws.create_workspace(f"{owner_id}'s Workspace")
        self._initialized = True
        return {
            "status": "ok",
            "owner_id": owner_id,
            "workspace_id": ws.workspace_id,
            "ucps": init_result,
        }

    # ── Context ────────────────────────────────────────────────────────

    def get_context(self, objective: str = "") -> dict[str, Any]:
        if not self._initialized:
            return {"error": "Not initialized"}
        context = self._os.build_context(objective)
        signals = self._os.assess_attention()
        return {
            "context": context.to_dict() if context else {},
            "signals": [s.to_dict() for s in signals],
            "time": context.timestamp if context else "",
        }

    # ── Workspace ──────────────────────────────────────────────────────

    def get_workspace(self, workspace_id: str) -> dict[str, Any]:
        ws = self._ws.get_workspace(workspace_id)
        if not ws:
            return {"error": "Workspace not found"}
        return self._workspace_to_dict(ws)

    def list_workspaces(self) -> list[dict[str, Any]]:
        return [self._workspace_to_dict(w) for w in self._ws.list_workspaces()]

    def _workspace_to_dict(self, ws) -> dict[str, Any]:
        return {
            "workspace_id": ws.workspace_id,
            "name": ws.name,
            "panels": [{
                "panel_id": p.panel_id,
                "panel_type": p.panel_type.value,
                "dock": p.dock.value,
                "tabs": [{"tab_id": t.tab_id, "label": t.label,
                          "object_id": t.object_id, "panel_type": t.panel_type.value}
                         for t in p.tabs],
                "active_tab_id": p.active_tab_id,
                "order": p.order, "width": p.width, "height": p.height,
                "minimized": p.minimized,
            } for p in ws.panels],
            "active_panel_id": ws.active_panel_id,
            "focus_object_id": ws.focus_object_id,
            "created_at": ws.created_at, "updated_at": ws.updated_at,
        }

    def open_object(self, workspace_id: str, object_id: str,
                    label: str = "", panel_type: str = "object") -> dict[str, Any]:
        from core.workspace_runtime.models import PanelType as PT
        ws = self._ws.get_workspace(workspace_id)
        if not ws:
            return {"error": "Workspace not found"}
        # Find or create center panel
        center = next((p for p in ws.panels if p.dock.value == "center"), None)
        if not center:
            from core.workspace_runtime.models import Panel, DockPosition
            center = Panel(panel_type=PT.OBJECT, dock=DockPosition.CENTER)
            ws.panels.append(center)
        tab = self._ws.open_tab(workspace_id, center.panel_id, object_id,
                                 label=label, panel_type=PT(object_id.split(":")[0] if ":" in object_id else "object"))
        self._ws.navigate_to(workspace_id, object_id)
        return {"tab": {"tab_id": tab.tab_id, "label": tab.label, "object_id": tab.object_id} if tab else None,
                "workspace": self._workspace_to_dict(ws)}

    # ── Search ─────────────────────────────────────────────────────────

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        if not query or not self._initialized:
            return []
        results = []

        # Search across knowledge UCP
        ucps = self._os._composed_runtimes
        if "knowledge" in ucps:
            try:
                kp = ucps["knowledge"]._resolve(self._owner_id)
                if kp:
                    for k in getattr(kp, 'knowledge_list', []):
                        if query.lower() in getattr(k, 'statement', '').lower():
                            results.append({
                                "type": "knowledge", "id": getattr(k, 'knowledge_id', ''),
                                "title": getattr(k, 'statement', '')[:100],
                            })
            except Exception:
                pass

        # Search memory
        mem_results = self._os.recall(query, limit // 2)
        for m in mem_results:
            results.append({
                "type": "memory", "id": m.memory_id,
                "title": m.content[:100], "importance": m.importance,
            })

        return results[:limit]

    # ── Memory ─────────────────────────────────────────────────────────

    def store_memory(self, content: str, source: str = "",
                     tags: list[str] | None = None) -> dict[str, Any]:
        rec = self._os.store(content, source, tags)
        return {"memory_id": rec.memory_id, "type": rec.memory_type}

    def recall_memory(self, query: str) -> list[dict[str, Any]]:
        return [{"id": m.memory_id, "content": m.content[:100],
                 "type": m.memory_type, "importance": m.importance}
                for m in self._os.recall(query)]

    # ── Health ─────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        if not self._initialized:
            return {"status": "not_initialized"}
        os_health = self._os.health_check()
        ws_health = self._ws.health_check()
        return {"os": os_health, "workspace": ws_health, "owner_id": self._owner_id}

    def shutdown(self) -> None:
        self._os.shutdown()
        self._initialized = False