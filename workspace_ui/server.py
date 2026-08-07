"""Universal Workspace — Flask server.

Serves the adaptive workspace UI and REST API.
Composes from frozen WorkspaceRuntime + PersonalOS.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

from workspace_ui.api import WorkspaceAPI

app = Flask(__name__, static_folder=None)
api = WorkspaceAPI()

STATIC_DIR = Path(__file__).parent / "static"


# ── API Routes ─────────────────────────────────────────────────────────

@app.route("/api/init", methods=["POST"])
def init():
    data = request.get_json(silent=True) or {}
    owner = data.get("owner_id", "default")
    result = api.initialize(owner)
    return jsonify(result)


@app.route("/api/context", methods=["GET"])
def context():
    objective = request.args.get("objective", "")
    return jsonify(api.get_context(objective))


@app.route("/api/workspace", methods=["GET"])
def get_workspace():
    ws_id = request.args.get("workspace_id", "")
    if not ws_id:
        return jsonify({"workspaces": api.list_workspaces()})
    return jsonify(api.get_workspace(ws_id))


@app.route("/api/open", methods=["POST"])
def open_object():
    data = request.get_json(silent=True) or {}
    return jsonify(api.open_object(
        data.get("workspace_id", ""),
        data.get("object_id", ""),
        data.get("label", ""),
        data.get("panel_type", "object"),
    ))


@app.route("/api/search", methods=["GET"])
def search():
    q = request.args.get("q", "")
    return jsonify({"results": api.search(q)})


@app.route("/api/memory", methods=["POST"])
def store_memory():
    data = request.get_json(silent=True) or {}
    return jsonify(api.store_memory(
        data.get("content", ""), data.get("source", ""), data.get("tags"),
    ))


@app.route("/api/memory", methods=["GET"])
def recall_memory():
    q = request.args.get("q", "")
    return jsonify({"results": api.recall_memory(q)})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify(api.health())


# ── Static File Serving ────────────────────────────────────────────────

@app.route("/")
def index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return "<h1>Workspace UI not found</h1><p>Run: python3 workspace_ui/build.py</p>"
    return index_path.read_text()


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(str(STATIC_DIR), filename)


# ── Startup ────────────────────────────────────────────────────────────

def main():
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 SHUNYA Universal Workspace — http://localhost:{port}")
    print(f"   API: http://localhost:{port}/api/health")
    print(f"   UI:  http://localhost:{port}/")
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    main()