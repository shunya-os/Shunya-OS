"""Tests for Workspace Runtime."""

import json

import pytest

from core.workspace_runtime import (
    DockPosition,
    PanelType,
    WorkspaceRuntime,
)


@pytest.fixture
def runtime():
    r = WorkspaceRuntime()
    r.create_workspace("Main")
    return r


class TestWorkspaceLifecycle:
    def test_create(self, runtime):
        ws = runtime.create_workspace("Test")
        assert ws.name == "Test"
        assert len(ws.panels) == 1  # default center panel

    def test_get_workspace(self, runtime):
        ws = runtime.create_workspace("GetMe")
        fetched = runtime.get_workspace(ws.workspace_id)
        assert fetched.name == "GetMe"

    def test_list_workspaces(self, runtime):
        runtime.create_workspace("A")
        runtime.create_workspace("B")
        assert len(runtime.list_workspaces()) == 3  # Main + A + B

    def test_switch(self, runtime):
        ws = runtime.create_workspace("Other")
        switched = runtime.switch_workspace(ws.workspace_id)
        assert switched.name == "Other"

    def test_delete(self, runtime):
        ws = runtime.create_workspace("Temp")
        assert runtime.delete_workspace(ws.workspace_id) is True
        assert runtime.get_workspace(ws.workspace_id) is None


class TestPanelManagement:
    def test_add_panel(self, runtime):
        ws = runtime.active_workspace
        p = runtime.add_panel(ws.workspace_id, PanelType.SEARCH, DockPosition.RIGHT)
        assert p.panel_type == PanelType.SEARCH
        assert p.dock == DockPosition.RIGHT

    def test_remove_panel(self, runtime):
        ws = runtime.active_workspace
        p = runtime.add_panel(ws.workspace_id, PanelType.INSPECTOR)
        assert runtime.remove_panel(ws.workspace_id, p.panel_id) is True

    def test_dock_panel(self, runtime):
        ws = runtime.active_workspace
        p = runtime.add_panel(ws.workspace_id, PanelType.GRAPH)
        runtime.dock_panel(ws.workspace_id, p.panel_id, DockPosition.BOTTOM)
        assert p.dock == DockPosition.BOTTOM

    def test_split(self, runtime):
        ws = runtime.active_workspace
        p = runtime.add_panel(ws.workspace_id, PanelType.PROPERTIES)
        new_p = runtime.split_panel(ws.workspace_id, p.panel_id, "right")
        assert new_p is not None
        assert new_p.dock == p.dock


class TestTabManagement:
    def test_open_tab(self, runtime):
        ws = runtime.active_workspace
        tab = runtime.open_tab(ws.workspace_id, ws.active_panel_id, "obj:1", "Object 1")
        assert tab.label == "Object 1"
        assert tab.object_id == "obj:1"

    def test_switch_tab(self, runtime):
        ws = runtime.active_workspace
        t1 = runtime.open_tab(ws.workspace_id, ws.active_panel_id, "obj:a", "A")
        runtime.open_tab(ws.workspace_id, ws.active_panel_id, "obj:b", "B")
        assert runtime.switch_tab(ws.workspace_id, ws.active_panel_id, t1.tab_id) is True
        assert ws.focus_object_id == "obj:a"

    def test_close_tab(self, runtime):
        ws = runtime.active_workspace
        t = runtime.open_tab(ws.workspace_id, ws.active_panel_id, "obj:del")
        assert runtime.close_tab(ws.workspace_id, ws.active_panel_id, t.tab_id) is True


class TestUndoRedo:
    def test_push_command(self, runtime):
        ws = runtime.active_workspace
        runtime.add_panel(ws.workspace_id)
        history = runtime.get_history()
        assert len(history) == 1

    def test_undo(self, runtime):
        ws = runtime.active_workspace
        runtime.add_panel(ws.workspace_id)
        cmd = runtime.undo()
        assert cmd is not None
        assert cmd.command_type == "add_panel"

    def test_redo(self, runtime):
        ws = runtime.active_workspace
        runtime.add_panel(ws.workspace_id)
        runtime.undo()
        cmd = runtime.redo()
        assert cmd is not None

    def test_undo_empty(self, runtime):
        assert runtime.undo() is None


class TestNavigation:
    def test_navigate_to(self, runtime):
        ws = runtime.active_workspace
        runtime.navigate_to(ws.workspace_id, "obj:42")
        assert ws.focus_object_id == "obj:42"

    def test_back_forward(self, runtime):
        ws = runtime.active_workspace
        runtime.navigate_to(ws.workspace_id, "obj:1")
        runtime.navigate_to(ws.workspace_id, "obj:2")
        back = runtime.navigate_back(ws.workspace_id)
        assert back == "obj:1"
        fwd = runtime.navigate_forward(ws.workspace_id)
        assert fwd == "obj:2"

    def test_back_empty(self, runtime):
        assert runtime.navigate_back("nonexistent") is None


class TestDeepLinking:
    def test_resolve(self, runtime):
        result = runtime.resolve_deep_link("shunya://workspace/w1/panel/p1/tab/t1")
        assert result["workspace"] == "w1"
        assert result["panel"] == "p1"
        assert result["tab"] == "t1"


class TestCommandRouting:
    def test_register_and_execute(self, runtime):
        calls = []
        def my_handler(arg):
            calls.append(arg)
            return f"handled {arg}"
        runtime.register_command("test.cmd", my_handler, shortcut="ctrl+t", description="Test command")
        result = runtime.execute_command("test.cmd", "hello")
        assert result == "handled hello"
        assert "hello" in calls

    def test_unknown_command(self, runtime):
        with pytest.raises(ValueError, match="Unknown command"):
            runtime.execute_command("does_not_exist")

    def test_list_commands(self, runtime):
        runtime.register_command("cmd1", lambda: None)
        runtime.register_command("cmd2", lambda: None)
        cmds = runtime.list_commands()
        assert len(cmds) >= 2


class TestSessionPersistence:
    def test_save_and_restore(self, runtime):
        ws = runtime.active_workspace
        runtime.open_tab(ws.workspace_id, ws.active_panel_id, "obj:persist", "Persisted")
        ws.focus_object_id = "obj:persist"

        saved = runtime.save_session(ws.workspace_id)
        data = json.loads(saved)
        assert "workspace" in data

        restored = runtime.restore_session(saved)
        assert restored is not None
        assert len(restored.panels) >= 1

    def test_restore_invalid_json(self, runtime):
        restored = runtime.restore_session("{invalid}")
        assert restored is None


class TestFocus:
    def test_set_and_get_focus(self, runtime):
        ws = runtime.active_workspace
        runtime.set_focus(ws.workspace_id, "obj:focus")
        assert runtime.get_focus(ws.workspace_id) == "obj:focus"

    def test_get_focus_empty(self, runtime):
        assert runtime.get_focus("nonexistent") == ""


class TestPresence:
    def test_update_presence(self, runtime):
        ws = runtime.active_workspace
        info = runtime.update_presence("user:1", ws.workspace_id, "obj:1")
        assert info.user_id == "user:1"

    def test_get_presence(self, runtime):
        ws = runtime.active_workspace
        runtime.update_presence("user:a", ws.workspace_id, "obj:a")
        runtime.update_presence("user:b", ws.workspace_id, "obj:b")
        users = runtime.get_presence(ws.workspace_id)
        assert len(users) == 2


class TestHealth:
    def test_health(self, runtime):
        hc = runtime.health_check()
        assert hc["status"] == "healthy"
        assert hc["workspaces"] >= 1