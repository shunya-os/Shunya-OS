"""Minimal SHUNYA interface — first visible brain."""

from flask import jsonify, request

from app import db
from app.objects.models import Object
from app.runtime.loop import run_cycle
from app.ui import ui_bp


@ui_bp.route("/app")
def shunya_app():
    """Serve the minimal workspace HTML."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SHUNYA</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #fff;
    color: #1a1a1a;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 100vh;
    padding: 60px 20px;
  }
  .container {
    width: 100%;
    max-width: 520px;
  }
  h1 {
    font-size: 28px;
    font-weight: 600;
    letter-spacing: -0.5px;
    margin-bottom: 32px;
    color: #000;
  }
  .input-row {
    display: flex;
    gap: 8px;
    margin-bottom: 24px;
  }
  input[type="text"] {
    flex: 1;
    padding: 12px 16px;
    border: 1px solid #d4d4d4;
    border-radius: 8px;
    font-size: 15px;
    outline: none;
    transition: border-color 0.2s;
  }
  input[type="text"]:focus {
    border-color: #000;
  }
  button {
    padding: 12px 20px;
    background: #000;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: opacity 0.2s;
  }
  button:hover { opacity: 0.85; }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  #output {
    background: #f5f5f5;
    border-radius: 8px;
    padding: 16px;
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 13px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
    min-height: 60px;
  }
  #output:empty { display: none; }
  .status { font-size: 13px; color: #888; margin-top: 8px; }
</style>
</head>
<body>
<div class="container">
  <h1>SHUNYA</h1>
  <div class="input-row">
    <input type="text" id="input" placeholder="Create or update anything..." autofocus />
    <button id="execute-btn">Execute</button>
  </div>
  <div id="output"></div>
  <div class="status" id="status"></div>
</div>
<script>
  const input = document.getElementById("input");
  const btn = document.getElementById("execute-btn");
  const output = document.getElementById("output");
  const status = document.getElementById("status");

  btn.addEventListener("click", async () => {
    const text = input.value.trim();
    if (!text) return;

    btn.disabled = true;
    status.textContent = "Processing...";

    try {
      const resp = await fetch("/app/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: text }),
      });
      const data = await resp.json();
      output.textContent = JSON.stringify(data, null, 2);
      status.textContent = "Done";
    } catch (err) {
      output.textContent = "Error: " + err.message;
      status.textContent = "Failed";
    } finally {
      btn.disabled = false;
    }
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") btn.click();
  });
</script>
</body>
</html>"""


@ui_bp.route("/app/execute", methods=["POST"])
def shunya_execute():
    """Accept user input, create/update entity, run loop, return result."""

    data = request.get_json(silent=True) or {}
    user_input = (data.get("input") or "").strip()
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    try:
        # Create entity
        entity = Object(
            object_type="lead",
            state={"stage": "new", "description": user_input},
            context={"description": user_input},
        )
        db.session.add(entity)
        db.session.commit()

        # 2. Update state — reassign to trigger SQLAlchemy JSON mutation tracking
        state = dict(entity.state or {})
        state["stage"] = "contacted"
        entity.state = state
        db.session.commit()

        # 3. Run decision loop
        actions = []
        try:
            loop_result = run_cycle()
            actions = loop_result.get("actions", [])
        except Exception as loop_err:
            db.session.rollback()
            actions = [{"note": f"Loop skipped: {loop_err}"}]

        return jsonify({
            "entity_id": entity.id,
            "state": entity.state,
            "actions": actions,
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500