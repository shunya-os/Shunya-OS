"""Minimal SHUNYA interface — first visible brain."""

from flask import jsonify, request

from app import db
from app.objects.models import Object
from app.runtime.loop import run_cycle
from app.ui import ui_bp


@ui_bp.route("/workspace")
def workspace_inbox():
    """Serve the UNIFIED workspace — single surface for all SHUNYA operations."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SHUNYA — Workspace</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    background:#f5f5f5;color:#1a1a1a;height:100vh;display:flex;flex-direction:column
  }
  /* ── Top bar ── */
  .topbar{
    display:flex;align-items:center;gap:16px;padding:10px 20px;
    background:#fff;border-bottom:1px solid #e5e7eb;flex-shrink:0
  }
  .topbar h1{font-size:17px;font-weight:600;letter-spacing:-0.3px}
  .topbar .badge{font-size:11px;color:#888;margin-left:auto}
  .top-actions{display:flex;gap:6px}
  .top-actions button{
    padding:6px 14px;border-radius:6px;border:1px solid #d4d4d4;
    background:#fff;cursor:pointer;font-size:12px;font-family:inherit
  }
  .top-actions button:hover{background:#f3f4f6}
  .top-actions .primary{background:#2563eb;color:#fff;border-color:#2563eb}
  .top-actions .primary:hover{background:#1d4ed8}

  /* ── Pipeline bar ── */
  .pipeline{
    display:flex;gap:0;padding:12px 20px;background:#fff;
    border-bottom:1px solid #e5e7eb;flex-shrink:0;
    overflow-x:auto
  }
  .pipe-stage{
    display:flex;align-items:center;gap:8px;flex-shrink:0
  }
  .pipe-stage .dot{
    width:10px;height:10px;border-radius:50%;
    background:#e5e7eb;flex-shrink:0
  }
  .pipe-stage .dot.active{background:#2563eb}
  .pipe-stage .dot.has{background:#22c55e}
  .pipe-label{font-size:11px;color:#6b7280;white-space:nowrap}
  .pipe-count{font-size:11px;font-weight:600;color:#374151}
  .pipe-arrow{color:#d4d4d4;font-size:12px;margin:0 6px}

  /* ── Main layout ── */
  .main{display:flex;flex:1;overflow:hidden}
  .left-panel{width:280px;min-width:260px;background:#fff;border-right:1px solid #e5e7eb;display:flex;flex-direction:column}
  .left-panel h2{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9ca3af;padding:14px 16px 6px}
  .entity-list{flex:1;overflow-y:auto}
  .entity-item{
    display:flex;align-items:center;gap:8px;padding:10px 16px;
    cursor:pointer;border-left:3px solid transparent;transition:all 0.1s;
    border-bottom:1px solid #f3f4f6
  }
  .entity-item:hover{background:#f9fafb}
  .entity-item.selected{border-left-color:#2563eb;background:#eff6ff}
  .entity-item .eid{font-size:10px;color:#9ca3af;font-weight:500;width:32px}
  .entity-item .ename{font-size:13px;font-weight:500;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .entity-item .estag{
    font-size:10px;padding:2px 6px;border-radius:4px;background:#f3f4f6;
    color:#6b7280;white-space:nowrap
  }
  .entity-item .estag.new{background:#dbeafe;color:#1d4ed8}
  .entity-item .estag.contacted{background:#fef3c7;color:#92400e}
  .entity-item .estag.quoted{background:#d1fae5;color:#065f46}
  .entity-item .estag.closed{background:#e5e7eb;color:#374151}

  .center-panel{flex:1;display:flex;flex-direction:column;overflow:hidden}
  .detail-header{
    padding:16px 20px 12px;background:#fff;border-bottom:1px solid #e5e7eb;
    flex-shrink:0
  }
  .detail-header h3{font-size:16px;font-weight:600;margin-bottom:2px}
  .detail-header .meta{font-size:12px;color:#888}
  .detail-body{flex:1;overflow-y:auto;padding:16px 20px}
  .detail-section{margin-bottom:20px}
  .detail-section h4{font-size:11px;font-weight:600;text-transform:uppercase;color:#9ca3af;margin-bottom:8px;letter-spacing:0.05em}
  .state-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px}
  .state-grid .kv{font-size:12px;padding:4px 8px;background:#f9fafb;border-radius:4px}
  .state-grid .kv .k{color:#6b7280}
  .state-grid .kv .v{font-weight:500}
  .timeline-item{
    font-size:12px;padding:6px 0;border-bottom:1px solid #f3f4f6;
    display:flex;gap:8px
  }
  .timeline-item .t{color:#9ca3af;white-space:nowrap}
  .timeline-item .d{color:#374151}

  .right-panel{width:360px;min-width:320px;background:#fff;border-left:1px solid #e5e7eb;display:flex;flex-direction:column}
  .right-panel h2{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9ca3af;padding:14px 16px 6px}
  .proposal-list{flex:1;overflow-y:auto}
  .prop-item{
    padding:12px 16px;border-bottom:1px solid #f3f4f6;cursor:pointer
  }
  .prop-item:hover{background:#f9fafb}
  .prop-item .phead{display:flex;gap:6px;align-items:center;margin-bottom:4px}
  .prop-item .pto{font-size:12px;font-weight:500;color:#374151}
  .prop-item .pstatus{font-size:10px;padding:2px 6px;border-radius:4px}
  .prop-item .pstatus.pending{background:#fef3c7;color:#92400e}
  .prop-item .pstatus.sent{background:#d1fae5;color:#065f46}
  .prop-item .pstatus.rejected{background:#fee2e2;color:#991b1b}
  .prop-item .pmsg{font-size:12px;color:#6b7280;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .prop-item .preason{font-size:11px;color:#9ca3af;margin-top:2px}
  .prop-actions{display:flex;gap:4px;margin-top:6px;flex-wrap:wrap}
  .prop-actions button{
    padding:4px 10px;border-radius:4px;border:1px solid #d4d4d4;
    background:#fff;cursor:pointer;font-size:11px;font-family:inherit
  }
  .prop-actions button:hover{background:#f3f4f6}
  .prop-actions .apr{background:#2563eb;color:#fff;border-color:#2563eb}
  .prop-actions .apr:hover{background:#1d4ed8}
  .prop-actions .rjt{color:#dc2626;border-color:#fca5a5}
  .prop-actions .rjt:hover{background:#fef2f2}
  .prop-actions .edt{color:#6b7280}
  .prop-actions button:disabled{opacity:0.4;cursor:not-allowed}
  .edit-box{margin:4px 0}
  .edit-box textarea{width:100%;padding:6px;border:1px solid #93c5fd;border-radius:4px;font-size:11px;font-family:inherit;min-height:48px;resize:vertical}
  .edit-box .ebtn{display:flex;gap:4px;margin-top:4px}
  .edit-box .ebtn button{padding:3px 8px;font-size:10px;border-radius:4px;border:1px solid #d4d4d4;background:#fff;cursor:pointer;font-family:inherit}
  .edit-box .ebtn .save{background:#2563eb;color:#fff;border-color:#2563eb}
  .pfeed{font-size:11px;color:#2563eb;margin-top:4px;font-weight:500}
  .empty-state{padding:32px 16px;text-align:center;color:#9ca3af;font-size:13px}
  .toast{position:fixed;bottom:20px;right:20px;background:#1a1a1a;color:#fff;padding:10px 16px;border-radius:6px;font-size:12px;z-index:999}
  @media (max-width:900px){
    .main{flex-direction:column}
    .left-panel,.right-panel{width:100%;min-width:0;border:none;border-bottom:1px solid #e5e7eb;max-height:300px}
  }
</style>
</head>
<body>

<div class="topbar">
  <h1>SHUNYA</h1>
  <span class="badge" id="entity-count">0 entities</span>
  <div class="top-actions">
    <button onclick="runLoop()" id="btn-loop">Run Loop</button>
    <button onclick="showCreateEntity()" class="primary" id="btn-create">+ Create Entity</button>
  </div>
</div>

<div class="pipeline" id="pipeline">
  <div class="pipe-stage"><span class="dot" id="pipe-new"></span><span class="pipe-label">New</span><span class="pipe-count" id="count-new">0</span></div>
  <span class="pipe-arrow">→</span>
  <div class="pipe-stage"><span class="dot" id="pipe-contacted"></span><span class="pipe-label">Contacted</span><span class="pipe-count" id="count-contacted">0</span></div>
  <span class="pipe-arrow">→</span>
  <div class="pipe-stage"><span class="dot" id="pipe-quoted"></span><span class="pipe-label">Quoted</span><span class="pipe-count" id="count-quoted">0</span></div>
  <span class="pipe-arrow">→</span>
  <div class="pipe-stage"><span class="dot" id="pipe-closed"></span><span class="pipe-label">Closed</span><span class="pipe-count" id="count-closed">0</span></div>
</div>

<div class="main">
  <div class="left-panel">
    <h2>Entities</h2>
    <div class="entity-list" id="entity-list"></div>
  </div>

  <div class="center-panel">
    <div class="detail-header">
      <h3 id="detail-name">Select an entity</h3>
      <div class="meta" id="detail-meta"></div>
    </div>
    <div class="detail-body" id="detail-body">
      <div class="empty-state">Click an entity from the left panel to see details.</div>
    </div>
  </div>

  <div class="right-panel">
    <h2>Proposals</h2>
    <div class="proposal-list" id="proposal-list"></div>
  </div>
</div>

<script>
let entities = [];
let proposals = [];
let selectedEntityId = null;
let editingProposalId = null;

async function api(url, method, body) {
  var opts = { method: method || 'GET', headers: {} };
  if (body) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
  var r = await fetch(url, opts);
  if (!r.ok) { var e = await r.json().catch(function(){return {} }); throw new Error(e.error || e.message || r.status); }
  return await r.json();
}

function toast(msg) {
  var t = document.createElement('div');
  t.className = 'toast';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(function(){ t.remove(); }, 2500);
}

async function loadAll() {
  await Promise.all([loadEntities(), loadProposals()]);
  renderEntityList();
  renderProposals();
  updatePipeline();
  document.getElementById('entity-count').textContent = entities.length + ' entities';
}

async function loadEntities() {
  try {
    var d = await api('/debug/entities');
    entities = d.entities || [];
  } catch(e) { console.error('load entities', e); entities = []; }
}

async function loadProposals() {
  try {
    var d = await api('/proposals');
    proposals = d.proposals || [];
  } catch(e) { console.error('load proposals', e); proposals = []; }
}

function getStage(st) {
  if (!st || typeof st !== 'object') return '—';
  var s = st.stage || '';
  if (s === 'new' || s === 'contacted' || s === 'quoted') return s;
  if (st.status === 'closed' || s === 'closed') return 'closed';
  return s || 'new';
}

function renderEntityList() {
  var el = document.getElementById('entity-list');
  if (!entities.length) { el.innerHTML = '<div class="empty-state">No entities. Create one to start.</div>'; return; }
  el.innerHTML = entities.map(function(e){
    var stage = getStage(e.state || {});
    var name = (e.state && (e.state.name || e.state.description || '')) || e.object_type || e.type || '#'+e.id;
    var cls = 'entity-item' + (selectedEntityId === e.id ? ' selected' : '');
    return '<div class="'+cls+'" onclick="selectEntity('+e.id+')">' +
      '<span class="eid">#'+e.id+'</span>' +
      '<span class="ename">'+esc(name)+'</span>' +
      '<span class="estag '+stage+'">'+stage+'</span>' +
    '</div>';
  }).join('');
}

function selectEntity(id) {
  selectedEntityId = id;
  renderEntityList();
  var e = entities.find(function(x){ return x.id === id; });
  if (!e) { return; }
  var state = e.state || {};
  var name = state.name || state.description || e.object_type || e.type || '#'+e.id;
  document.getElementById('detail-name').textContent = name;
  document.getElementById('detail-meta').textContent = '#'+e.id + ' · ' + (e.object_type || e.type || '?');

  var body = document.getElementById('detail-body');
  var shtml = '<div class="detail-section"><h4>Current State</h4><div class="state-grid">';
  for (var k in state) {
    shtml += '<div class="kv"><span class="k">'+k+'</span><span class="v">'+esc(String(state[k]))+'</span></div>';
  }
  shtml += '</div></div>';

  // Filter proposals for this entity
  var entityProps = proposals.filter(function(p){ return p.entity && p.entity.id === id; });
  if (entityProps.length) {
    shtml += '<div class="detail-section"><h4>Proposals</h4>';
    entityProps.forEach(function(p){
      shtml += '<div class="timeline-item"><span class="t">['+p.status+']</span><span class="d">'+esc(p.message.slice(0,80))+'</span></div>';
    });
    shtml += '</div>';
  }

  body.innerHTML = shtml || '<div class="empty-state">Entity has no state.</div>';
}

function renderProposals() {
  var pl = document.getElementById('proposal-list');
  if (!proposals.length) { pl.innerHTML = '<div class="empty-state">No proposals yet.</div>'; return; }
  pl.innerHTML = proposals.map(function(p){
    var entityName = (p.entity && (p.entity.name || '')) || p.to || '?';
    var cls = 'pstatus ' + (p.status === 'pending' ? 'pending' : p.status === 'sent' || p.status === 'approved' ? 'sent' : 'rejected');
    var showEdit = (editingProposalId === p.id);
    var ctx = p.context || {};

    var actionsHtml = '';
    if (p.status === 'pending') {
      actionsHtml = '<div class="prop-actions">' +
        '<button class="apr" onclick="approveProposal('+p.id+')" id="apr-'+p.id+'">Approve</button>' +
        '<button class="rjt" onclick="rejectProposal('+p.id+')" id="rjt-'+p.id+'">Reject</button>' +
        '<button class="edt" onclick="toggleEdit('+p.id+')">Edit</button>' +
      '</div>';
    }

    var editHtml = '';
    if (showEdit) {
      editHtml = '<div class="edit-box" id="ebox-'+p.id+'">' +
        '<textarea id="etext-'+p.id+'">'+esc(p.message)+'</textarea>' +
        '<div class="ebtn"><button class="save" onclick="saveEdit('+p.id+')">Save</button>' +
        '<button onclick="cancelEdit('+p.id+')">Cancel</button></div>' +
      '</div>';
    }

    return '<div class="prop-item" onclick="selectEntityFromProposal('+p.id+')">' +
      '<div class="phead">' +
        '<span class="pto">'+esc(entityName)+'</span>' +
        '<span class="'+cls+'">'+p.status+'</span>' +
      '</div>' +
      '<div class="pmsg">'+esc(p.message)+'</div>' +
      '<div class="preason">'+esc(ctx.reason || '')+'</div>' +
      editHtml +
      actionsHtml +
      '<div class="pfeed" id="pfeed-'+p.id+'"></div>' +
    '</div>';
  }).join('');
}

function selectEntityFromProposal(propId) {
  var p = proposals.find(function(x){ return x.id === propId; });
  if (p && p.entity && p.entity.id) { selectEntity(p.entity.id); }
}

function updatePipeline() {
  var counts = {new:0, contacted:0, quoted:0, closed:0};
  entities.forEach(function(e){
    var stage = getStage(e.state || {});
    if (counts[stage] !== undefined) counts[stage]++;
  });
  document.getElementById('count-new').textContent = counts.new;
  document.getElementById('count-contacted').textContent = counts.contacted;
  document.getElementById('count-quoted').textContent = counts.quoted;
  document.getElementById('count-closed').textContent = counts.closed;
  ['new','contacted','quoted','closed'].forEach(function(s){
    document.getElementById('pipe-'+s).className = 'dot' + (counts[s] > 0 ? ' has' : '');
  });
}

async function runLoop() {
  var btn = document.getElementById('btn-loop');
  btn.disabled = true;
  btn.textContent = 'Running...';
  try {
    var r = await api('/debug/run-cycle', 'POST');
    toast('Loop done: ' + (r.summary ? r.summary.actions_taken + ' actions' : 'ok'));
    await loadAll();
    if (selectedEntityId) selectEntity(selectedEntityId);
  } catch(e) { toast('Loop error: '+e.message); }
  btn.disabled = false;
  btn.textContent = 'Run Loop';
}

function showCreateEntity() {
  var name = prompt('Entity name:', 'Test Lead');
  if (!name) return;
  var phone = prompt('Phone:', '');
  var email = prompt('Email:', '');
  var data = { type:'lead', data:{ name: name, stage:'new' } };
  if (phone) data.data.phone = phone;
  if (email) data.data.email = email;
  api('/debug/entity', 'POST', data).then(function(){
    toast('Entity created');
    loadAll();
  }).catch(function(e){ toast('Error: '+e.message); });
}

async function approveProposal(id) {
  document.getElementById('pfeed-'+id).textContent = 'Approving...';
  var btn = document.getElementById('apr-'+id);
  if (btn) btn.disabled = true;
  try {
    await api('/proposals/'+id+'/approve', 'POST', { approved_by: 'human' });
    document.getElementById('pfeed-'+id).textContent = '✓ Sent';
    toast('Proposal approved and sent');
    await loadAll();
    if (selectedEntityId) selectEntity(selectedEntityId);
  } catch(e) { document.getElementById('pfeed-'+id).textContent = 'Error: '+e.message; if (btn) btn.disabled = false; }
}

async function rejectProposal(id) {
  document.getElementById('pfeed-'+id).textContent = 'Rejecting...';
  var btn = document.getElementById('rjt-'+id);
  if (btn) btn.disabled = true;
  try {
    await api('/proposals/'+id+'/reject', 'POST');
    document.getElementById('pfeed-'+id).textContent = '✗ Rejected';
    toast('Proposal rejected');
    await loadAll();
  } catch(e) { document.getElementById('pfeed-'+id).textContent = 'Error: '+e.message; if (btn) btn.disabled = false; }
}

function toggleEdit(id) {
  editingProposalId = (editingProposalId === id) ? null : id;
  renderProposals();
}

function cancelEdit(id) {
  editingProposalId = null;
  renderProposals();
}

async function saveEdit(id) {
  var ta = document.getElementById('etext-'+id);
  if (!ta) return;
  var newMsg = ta.value.trim();
  if (!newMsg) return;
  try {
    await api('/proposals/'+id+'/edit', 'POST', { message: newMsg });
    document.getElementById('pfeed-'+id).textContent = '✓ Saved';
    editingProposalId = null;
    toast('Proposal updated');
    await loadAll();
  } catch(e) { document.getElementById('pfeed-'+id).textContent = 'Error: '+e.message; }
}

function esc(s) { if (!s) return ''; var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

loadAll();
</script>
</body>
</html>"""


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