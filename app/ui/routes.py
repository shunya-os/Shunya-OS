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
  .topbar{
    display:flex;align-items:center;gap:16px;padding:10px 20px;
    background:#fff;border-bottom:1px solid #e5e7eb;flex-shrink:0
  }
  .topbar h1{font-size:17px;font-weight:600;letter-spacing:-0.3px}
  .topbar .badge{font-size:11px;color:#888;margin-left:auto;display:flex;align-items:center;gap:6px}
  .topbar .badge span{padding:2px 6px;border-radius:4px;font-size:10px}
  .topbar .badge .att-red{background:#fee2e2;color:#991b1b}
  .topbar .badge .att-amber{background:#fef3c7;color:#92400e}
  .top-actions{display:flex;gap:6px}
  .top-actions button{
    padding:6px 14px;border-radius:6px;border:1px solid #d4d4d4;
    background:#fff;cursor:pointer;font-size:12px;font-family:inherit
  }
  .top-actions button:hover{background:#f3f4f6}
  .top-actions .primary{background:#2563eb;color:#fff;border-color:#2563eb}
  .top-actions .primary:hover{background:#1d4ed8}

  .pipeline{
    display:flex;gap:0;padding:12px 20px;background:#fff;
    border-bottom:1px solid #e5e7eb;flex-shrink:0;overflow-x:auto
  }
  .pipe-stage{display:flex;align-items:center;gap:8px;flex-shrink:0}
  .pipe-stage .dot{width:10px;height:10px;border-radius:50%;background:#e5e7eb;flex-shrink:0}
  .pipe-stage .dot.has{background:#22c55e}
  .pipe-stage .dot.warn{background:#f59e0b}
  .pipe-label{font-size:11px;color:#6b7280;white-space:nowrap}
  .pipe-count{font-size:11px;font-weight:600;color:#374151}
  .pipe-arrow{color:#d4d4d4;font-size:12px;margin:0 6px}

  .main{display:flex;flex:1;overflow:hidden}

  .left-panel{width:260px;min-width:240px;background:#fff;border-right:1px solid #e5e7eb;display:flex;flex-direction:column}
  .left-panel h2{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9ca3af;padding:14px 16px 6px}
  .filter-bar{display:flex;gap:4px;padding:0 14px 8px;flex-wrap:wrap}
  .filter-btn{font-size:10px;padding:3px 8px;border-radius:12px;border:1px solid #d4d4d4;background:#fff;cursor:pointer;color:#6b7280;font-family:inherit;transition:all 0.1s}
  .filter-btn:hover{background:#f3f4f6}
  .filter-btn.active{background:#2563eb;color:#fff;border-color:#2563eb}
  .entity-list{flex:1;overflow-y:auto}
  .entity-item{
    display:flex;align-items:center;gap:6px;padding:10px 14px;
    cursor:pointer;border-left:3px solid #e5e7eb;
    border-bottom:1px solid #f3f4f6;font-size:13px;transition:all 0.1s
  }
  .entity-item:hover{background:#f9fafb}
  .entity-item.selected{border-left-color:#2563eb;background:#eff6ff}
  .entity-item.urgent{border-left-color:#dc2626}
  .entity-item.attention{border-left-color:#f59e0b}
  .entity-item .eid{font-size:10px;color:#9ca3af;font-weight:500;width:28px}
  .entity-item .ename{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .entity-item .ebadge{font-size:9px;padding:1px 5px;border-radius:3px;white-space:nowrap;display:none}
  .entity-item .ebadge.show{display:inline}
  .entity-item .ebadge.pending{background:#fef3c7;color:#92400e}
  .entity-item .ebadge.stale{background:#fee2e2;color:#991b1b}
  .entity-item .estag{font-size:10px;padding:2px 6px;border-radius:4px;background:#f3f4f6;color:#6b7280;white-space:nowrap}
  .entity-item .estag.new{background:#dbeafe;color:#1d4ed8}
  .entity-item .estag.contacted{background:#fef3c7;color:#92400e}
  .entity-item .estag.quoted{background:#d1fae5;color:#065f46}
  .entity-item .estag.closed{background:#d1fae5;color:#065f46}

  .center-panel{flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0}
  .detail-header{padding:14px 20px 10px;background:#fff;border-bottom:1px solid #e5e7eb;flex-shrink:0;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
  .detail-header .info{flex:1;min-width:0}
  .detail-header h3{font-size:15px;font-weight:600}
  .detail-header .meta{font-size:11px;color:#888}
  .detail-header .edit-btn{padding:4px 10px;border-radius:4px;border:1px solid #d4d4d4;background:#fff;cursor:pointer;font-size:11px;font-family:inherit}
  .detail-header .edit-btn:hover{background:#f3f4f6}
  .detail-body{flex:1;overflow-y:auto;padding:14px 20px}
  .tab-bar{display:flex;gap:4px;margin-bottom:12px;border-bottom:1px solid #e5e7eb}
  .tab-btn{padding:6px 14px;font-size:12px;border:none;background:none;cursor:pointer;color:#6b7280;font-family:inherit;border-bottom:2px solid transparent;margin-bottom:-1px}
  .tab-btn.active{color:#2563eb;border-bottom-color:#2563eb;font-weight:500}
  .tab-btn:hover:not(.active){color:#374151}
  .tab-btn .count{background:#e5e7eb;border-radius:8px;padding:0 5px;font-size:10px;margin-left:4px}
  .tab-btn.active .count{background:#dbeafe;color:#2563eb}
  .detail-section{margin-bottom:16px}
  .detail-section h4{font-size:11px;font-weight:600;text-transform:uppercase;color:#9ca3af;margin-bottom:8px;letter-spacing:0.05em}

  .edit-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
  .edit-field{display:flex;flex-direction:column;gap:3px}
  .edit-field label{font-size:11px;color:#6b7280;font-weight:500}
  .edit-field input,.edit-field select{padding:6px 8px;border:1px solid #d4d4d4;border-radius:4px;font-size:12px;font-family:inherit;outline:none}
  .edit-field input:focus,.edit-field select:focus{border-color:#93c5fd;box-shadow:0 0 0 2px rgba(37,99,235,0.1)}
  .edit-actions{display:flex;gap:6px;margin-top:10px}
  .edit-actions button{padding:5px 12px;border-radius:4px;border:1px solid #d4d4d4;background:#fff;cursor:pointer;font-size:11px;font-family:inherit}
  .edit-actions .save-btn{background:#2563eb;color:#fff;border-color:#2563eb}
  .edit-actions .save-btn:hover{background:#1d4ed8}
  .edit-actions .cancel-btn:hover{background:#f3f4f6}

  .state-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px}
  .state-grid .kv{font-size:12px;padding:4px 8px;background:#f9fafb;border-radius:4px;overflow:hidden;text-overflow:ellipsis}
  .state-grid .kv .k{color:#6b7280;font-weight:500}
  .state-grid .kv .v{font-weight:500}

  .tl-item{font-size:12px;padding:7px 0;border-bottom:1px solid #f3f4f6;display:flex;gap:8px;align-items:flex-start}
  .tl-item .tt{color:#9ca3af;white-space:nowrap;flex-shrink:0;font-size:10px;width:55px}
  .tl-item .ttype{font-size:10px;padding:2px 6px;border-radius:3px;background:#f3f4f6;color:#6b7280;flex-shrink:0;min-width:48px;text-align:center}
  .tl-item .ttype.cre{background:#dbeafe;color:#1d4ed8}
  .tl-item .ttype.upd{background:#fef3c7;color:#92400e}
  .tl-item .ttype.eff{background:#d1fae5;color:#065f46}
  .tl-item .ttype.pro{background:#ede9fe;color:#6d28d9}
  .tl-item .ttype.not{background:#e5e7eb;color:#374151}
  .tl-item .ttxt{color:#374151;line-height:1.4;flex:1}
  .tl-item .treason{font-size:10px;color:#9ca3af;margin-top:2px}

  .task-item{font-size:12px;padding:6px 0;border-bottom:1px solid #f3f4f6;display:flex;align-items:center;gap:8px}
  .task-item .ttitle{flex:1;color:#374151}
  .task-item .ttitle.done{text-decoration:line-through;color:#9ca3af}
  .task-item .tstatus{font-size:10px;padding:2px 6px;border-radius:4px}
  .task-item .tstatus.pending{background:#fef3c7;color:#92400e}
  .task-item .tstatus.completed{background:#d1fae5;color:#065f46}
  .task-item .tcomp{padding:2px 8px;border-radius:4px;border:1px solid #d4d4d4;background:#fff;cursor:pointer;font-size:10px;font-family:inherit}
  .task-item .tcomp:hover{background:#f3f4f6}
  .task-item .tcomp:disabled{opacity:0.3;cursor:default}

  .notes-area{width:100%;min-height:80px;padding:8px;border:1px solid #d4d4d4;border-radius:6px;font-size:12px;font-family:inherit;resize:vertical;outline:none;line-height:1.5}
  .notes-area:focus{border-color:#93c5fd}
  .notes-save{margin-top:6px;padding:4px 12px;border-radius:4px;border:1px solid #d4d4d4;background:#fff;cursor:pointer;font-size:11px;font-family:inherit}
  .notes-save:hover{background:#f3f4f6}
  .notes-status{font-size:11px;color:#22c55e;margin-top:4px;display:none}

  .right-panel{width:340px;min-width:300px;background:#fff;border-left:1px solid #e5e7eb;display:flex;flex-direction:column}
  .right-panel h2{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9ca3af;padding:14px 16px 6px}

  .attention-section{padding:0 16px 12px;border-bottom:1px solid #e5e7eb}
  .att-item{display:flex;align-items:center;gap:8px;padding:6px 0;font-size:12px;border-bottom:1px solid #f9fafb}
  .att-item:last-child{border:none}
  .att-icon{width:6px;height:6px;border-radius:50%;flex-shrink:0}
  .att-icon.red{background:#dc2626}
  .att-icon.amber{background:#f59e0b}
  .att-icon.green{background:#22c55e}
  .att-text{flex:1;color:#374151}
  .att-count{font-size:11px;font-weight:600;padding:1px 6px;border-radius:4px;background:#f3f4f6;color:#6b7280}
  .att-count.red{background:#fee2e2;color:#991b1b}
  .att-count.amber{background:#fef3c7;color:#92400e}

  .proposal-list{flex:1;overflow-y:auto}
  .prop-item{padding:10px 16px;border-bottom:1px solid #f3f4f6;cursor:pointer}
  .prop-item:hover{background:#f9fafb}
  .prop-item .phead{display:flex;gap:6px;align-items:center;margin-bottom:3px;flex-wrap:wrap}
  .prop-item .pto{font-size:12px;font-weight:500;color:#374151}
  .prop-item .pstatus{font-size:10px;padding:2px 6px;border-radius:4px}
  .prop-item .pstatus.pending{background:#fef3c7;color:#92400e}
  .prop-item .pstatus.sent{background:#d1fae5;color:#065f46}
  .prop-item .pstatus.rejected{background:#fee2e2;color:#991b1b}
  .prop-item .pmsg{font-size:11px;color:#6b7280;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .prop-item .preason{font-size:10px;color:#2563eb;margin-top:2px}
  .prop-actions{display:flex;gap:4px;margin-top:5px;flex-wrap:wrap}
  .prop-actions button{padding:3px 8px;border-radius:4px;border:1px solid #d4d4d4;background:#fff;cursor:pointer;font-size:10px;font-family:inherit}
  .prop-actions .apr{background:#2563eb;color:#fff;border-color:#2563eb}
  .prop-actions .apr:hover{background:#1d4ed8}
  .prop-actions .rjt{color:#dc2626;border-color:#fca5a5}
  .prop-actions .rjt:hover{background:#fef2f2}
  .prop-actions .edt{color:#6b7280}
  .prop-actions button:disabled{opacity:0.4;cursor:not-allowed}
  .edit-box{margin:4px 0}
  .edit-box textarea{width:100%;padding:5px;border:1px solid #93c5fd;border-radius:4px;font-size:11px;font-family:inherit;min-height:40px;resize:vertical}
  .edit-box .ebtn{display:flex;gap:4px;margin-top:4px}
  .edit-box .ebtn button{padding:3px 8px;font-size:10px;border-radius:4px;border:1px solid #d4d4d4;background:#fff;cursor:pointer;font-family:inherit}
  .edit-box .ebtn .save{background:#2563eb;color:#fff;border-color:#2563eb}
  .pfeed{font-size:10px;color:#2563eb;margin-top:3px;font-weight:500}
  .empty-state{padding:32px 16px;text-align:center;color:#9ca3af;font-size:13px;line-height:1.6}
  .empty-state strong{color:#6b7280}
  .toast{position:fixed;bottom:20px;right:20px;background:#1a1a1a;color:#fff;padding:10px 16px;border-radius:6px;font-size:12px;z-index:999;max-width:300px}
</style>
</head>
<body>

<div class="topbar">
  <h1>SHUNYA</h1>
  <div class="badge" id="entity-count">
    <span>0 entities</span>
  </div>
  <div class="top-actions">
    <button onclick="runLoop()" id="btn-loop">Run Loop</button>
    <button onclick="showCreateEntity()" class="primary">+ Create Entity</button>
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
    <div class="filter-bar" id="filter-bar"></div>
    <div class="entity-list" id="entity-list"></div>
  </div>

  <div class="center-panel">
    <div class="detail-header" id="detail-header">
      <div class="info">
        <h3 id="detail-name">Select an entity</h3>
        <div class="meta" id="detail-meta"></div>
      </div>
      <button class="edit-btn" id="btn-toggle-edit" onclick="toggleEditMode()" style="display:none">Edit</button>
    </div>
    <div class="detail-body" id="detail-body">
      <div class="empty-state" id="empty-state">
        <strong>Welcome to SHUNYA Workspace</strong><br><br>
        Get started:<br>
        • Click <strong>"+ Create Entity"</strong> above to add a lead<br>
        • Then click <strong>"Run Loop"</strong> to process it<br>
        • Approve proposals in the right panel<br><br>
        Each entity goes through:<br>
        <strong>New → Contacted → Quoted → Closed</strong>
      </div>
    </div>
  </div>

  <div class="right-panel">
    <h2>Attention</h2>
    <div class="attention-section" id="attention-section"></div>
    <h2>Proposals</h2>
    <div class="proposal-list" id="proposal-list"></div>
  </div>
</div>

<script>
var entities = [], proposals = [], tasks = [];
var selectedEntityId = null, editingProposalId = null, editMode = false;
var currentTimeline = [], currentTasks = [];
var activeTab = 'state';
var STALE_HOURS = 1;
var activeFilter = 'all';

var EVENT_LABELS = {'CREATED':'Created','UPDATED':'Updated','EFFECT':'Effect',
  'PROPOSAL_CREATED':'Proposal','NOTES_SAVED':'Notes','NOOP':'NoOp',
  'DECISION':'Decision','ACTION':'Action','ENTITY_SEEN':'Scan',
  'NOTES_SAVED':'Notes'};

async function api(u,m,b) {
  var o={method:m||'GET',headers:{}}; if(b){o.headers['Content-Type']='application/json';o.body=JSON.stringify(b)}
  var r=await fetch(u,o); if(!r.ok){var e=await r.json().catch(function(){return{}});throw new Error(e.error||e.message||r.status)}
  return await r.json();
}
function toast(m){var t=document.createElement('div');t.className='toast';t.textContent=m;document.body.appendChild(t);setTimeout(function(){t.remove()},2500);}
function esc(s){if(!s)return'';var d=document.createElement('div');d.textContent=s;return d.innerHTML;}
function ago(i){if(!i)return'';var m=Math.floor((new Date()-new Date(i))/60000);if(m<1)return'now';if(m<60)return m+'m';return Math.floor(m/60)+'h';}

async function loadAll(){
  try{var d=await api('/debug/entities');entities=d.entities||[]}catch(e){entities=[]}
  try{var d=await api('/proposals');proposals=d.proposals||[]}catch(e){proposals=[]}
  try{var d=await api('/debug/tasks');tasks=(d.tasks||[]).filter(function(t){return t.entity_id})}catch(e){tasks=[]}
  renderAttention();renderEntityList();renderProposals();updatePipeline();
  document.getElementById('entity-count').innerHTML='<span>'+entities.length+' entities</span>';
  if(selectedEntityId)loadEntityDetail(selectedEntityId);
}

function getStage(st){
  if(!st||typeof st!=='object')return'new';var s=st.stage||'';
  if(s==='new'||s==='contacted'||s==='quoted')return s;
  if(st.status==='closed'||s==='closed')return'closed';return s||'new';
}

function renderAttention(){
  var pp=proposals.filter(function(p){return p.status==='pending'});
  var ot=tasks.filter(function(t){return t.status==='pending'});
  var se=entities.filter(function(e){
    var s=getStage(e.state||{});if(s==='closed')return false;
    if(!e.updated_at)return false;return(new Date()-new Date(e.updated_at))/3600000>STALE_HOURS&&(s==='new'||s==='contacted');
  });
  var due=tasks.filter(function(t){return t.status==='pending'&&t.due_date&&new Date(t.due_date)<new Date();});
  var h='';
  if(!pp.length&&!ot.length&&!se.length&&!due.length){
    h='<div class="att-item"><span class="att-icon green"></span><span class="att-text">All clear</span></div>';
  }else{
    if(pp.length)h+='<div class="att-item"><span class="att-icon amber"></span><span class="att-text">Proposals to review</span><span class="att-count amber">'+pp.length+'</span></div>';
    if(due.length)h+='<div class="att-item"><span class="att-icon red"></span><span class="att-text">Overdue tasks</span><span class="att-count red">'+due.length+'</span></div>';
    else if(ot.length)h+='<div class="att-item"><span class="att-icon amber"></span><span class="att-text">Pending tasks</span><span class="att-count amber">'+ot.length+'</span></div>';
    if(se.length)h+='<div class="att-item"><span class="att-icon red"></span><span class="att-text">Stale leads</span><span class="att-count red">'+se.length+'</span></div>';
  }
  document.getElementById('attention-section').innerHTML=h;
}

function renderEntityList(){
  renderFilters();
  var el=document.getElementById('entity-list');
  if(!entities.length){el.innerHTML='<div class="empty-state">No entities yet.<br>Click <strong>+ Create Entity</strong> above.</div>';return;}
  var epp={};proposals.filter(function(p){return p.status==='pending'&&p.entity;}).forEach(function(p){epp[p.entity.id]=(epp[p.entity.id]||0)+1;});
  var sei={},oei={};
  entities.forEach(function(e){
    var s=getStage(e.state||{});if(s==='closed')return;
    if(!e.updated_at)return;
    var hr=(new Date()-new Date(e.updated_at))/3600000;
    if(hr>STALE_HOURS&&(s==='new'||s==='contacted'))sei[e.id]=true;
    // Overdue: tasks past due
    tasks.filter(function(t){return t.entity_id===e.id&&t.status==='pending'&&t.due_date&&new Date(t.due_date)<new Date();}).forEach(function(){oei[e.id]=true;});
  });
  var filtered=entities.slice();
  if(activeFilter==='priority')filtered=filtered.filter(function(e){return epp[e.id]||sei[e.id]||oei[e.id];});
  else if(activeFilter==='stale')filtered=filtered.filter(function(e){return sei[e.id];});
  else if(activeFilter==='proposals')filtered=filtered.filter(function(e){return epp[e.id];});
  else if(activeFilter==='tasks')filtered=filtered.filter(function(e){return oei[e.id];});
  var sorted=filtered.slice().sort(function(a,b){return((epp[b.id]?2:0)+(sei[b.id]?1:0))-((epp[a.id]?2:0)+(sei[a.id]?1:0));});
  el.innerHTML=sorted.map(function(e){
    var st=e.state||{};var stage=getStage(st);var name=st.name||st.description||e.object_type||e.type||'#'+e.id;
    var owner=st.assigned_to||'';var val=st.deal_value?st.currency+' '+st.deal_value:'';
    var cls='entity-item'+(selectedEntityId===e.id?' selected':'');
    if(epp[e.id])cls+=' urgent';else if(sei[e.id]||oei[e.id])cls+=' attention';
    var b='';
    if(epp[e.id])b='<span class="ebadge pending show">prop</span>';
    else if(sei[e.id])b='<span class="ebadge stale show">stale</span>';
    else if(oei[e.id])b='<span class="ebadge stale show">overdue</span>';
    return '<div class="'+cls+'" onclick="selectEntity('+e.id+')"><span class="eid">#'+e.id+'</span><span class="ename">'+esc(name)+'</span>'+b+'<span class="estag '+stage+'">'+stage+'</span></div>';
  }).join('');
}
function renderFilters(){
  var fb=document.getElementById('filter-bar');
  var filters=[{k:'all',l:'All'},{k:'priority',l:'Priority'},{k:'stale',l:'Stale'},{k:'proposals',l:'Proposals'},{k:'tasks',l:'Tasks'}];
  fb.innerHTML=filters.map(function(f){return '<button class="filter-btn'+(activeFilter===f.k?' active':'')+'" onclick="activeFilter=\''+f.k+'\';renderEntityList()">'+f.l+'</button>';}).join('');
}

function selectEntity(id){
  selectedEntityId=id;editMode=false;renderEntityList();
  document.getElementById('btn-toggle-edit').style.display='';loadEntityDetail(id);
}

async function loadEntityDetail(id){
  var e=entities.find(function(x){return x.id===id;});if(!e)return;
  var state=e.state||{};var name=state.name||state.description||e.object_type||e.type||'#'+e.id;
  document.getElementById('detail-name').textContent=name;
  document.getElementById('detail-meta').textContent='#'+e.id+' · '+(e.object_type||e.type||'?')+(e.updated_at?' · '+ago(e.updated_at):'');
  try{var d=await api('/debug/execution/'+id);currentTimeline=d.timeline||[]}catch(e){currentTimeline=[]}
  try{var d=await api('/debug/tasks?entity_id='+id);currentTasks=d.tasks||[]}catch(e){currentTasks=[]}
  renderDetail();
}

function renderDetail(){
  if(editMode){renderEditForm();return}
  renderDetailTabs(activeTab);
}

function renderDetailTabs(tab){
  activeTab=tab||activeTab;
  var e=entities.find(function(x){return x.id===selectedEntityId;});if(!e)return;
  var state=e.state||{};
  var pc=currentTasks.filter(function(t){return t.status==='pending';}).length;
  var th='<div class="tab-bar">'+
    '<button class="tab-btn'+(activeTab==='state'?' active':'')+'" onclick="renderDetailTabs(\'state\')">State</button>'+
    '<button class="tab-btn'+(activeTab==='timeline'?' active':'')+'" onclick="renderDetailTabs(\'timeline\')">Timeline'+(currentTimeline.length?'<span class="count">'+currentTimeline.length+'</span>':'')+'</button>'+
    '<button class="tab-btn'+(activeTab==='tasks'?' active':'')+'" onclick="renderDetailTabs(\'tasks\')">Tasks'+(pc?'<span class="count">'+pc+'</span>':'')+'</button>'+
    '<button class="tab-btn'+(activeTab==='notes'?' active':'')+'" onclick="renderDetailTabs(\'notes\')">Notes</button></div>';
  var ch='';
  if(activeTab==='state'){
    ch='<div class="detail-section"><h4>Current State</h4><div class="state-grid">';
    var pk=['name','phone','email','stage','status','task'];var ok=Object.keys(state).filter(function(k){return pk.indexOf(k)===-1;});
    pk.concat(ok).forEach(function(k){if(state[k]!==undefined)ch+='<div class="kv"><span class="k">'+k+'</span><span class="v">'+esc(String(state[k]))+'</span></div>';});
    ch+='</div></div>';
    var ep=proposals.filter(function(p){return p.entity&&p.entity.id===selectedEntityId;});
    if(ep.length){ch+='<div class="detail-section"><h4>Proposals</h4>';
      ep.slice(-5).reverse().forEach(function(p){ch+='<div class="tl-item"><span class="ttype '+(p.status==='pending'?'pro':'upd')+'">'+p.status+'</span><span class="ttxt">'+esc(p.message.slice(0,60))+'</span><div class="treason">'+esc((p.context||{}).reason||'')+'</div></div>';});
      ch+='</div>';}
  }else if(activeTab==='timeline'){
    if(!currentTimeline.length){ch='<div class="empty-state">No events yet. Run the loop.</div>';}
    else{ch='<div class="detail-section"><h4>Events</h4>';
      currentTimeline.slice().reverse().forEach(function(l){
        var tp=l.event_type||l.type||'-',lb=EVENT_LABELS[tp]||tp;
        var ic='ttype';if(tp==='CREATED'||tp==='PROPOSAL_CREATED')ic+=' pro';else if(tp==='UPDATED'||tp==='NOTES_SAVED')ic+=' upd';else if(tp.indexOf('EFFECT')>=0)ic+=' eff';else ic+=' cre';
        var ts=l.timestamp?(l.timestamp.slice(11,19)||''):'';var pl=l.payload||{};var txt='';
        if(tp==='PROPOSAL_CREATED')txt='Proposal: '+esc((pl.message_preview||pl.message||'').slice(0,60));
        else if(tp==='EFFECT')txt='Effect: '+esc(pl.type||pl.effect_type||'')+' — '+esc((pl.result||{}).status||'');
        else if(tp==='UPDATED'){var up=pl.state_updates||{};txt='Updated: '+Object.keys(up).map(function(k){return k+'='+up[k];}).join(', ');}
        else if(tp==='CREATED')txt='Entity created';
        else if(tp==='NOTES_SAVED')txt='Notes updated';
        else if(tp==='DECISION')txt='Decision → '+esc(JSON.stringify(pl.payload||{}).slice(0,40));
        else if(tp==='ACTION')txt='Action: '+esc(JSON.stringify(pl.action||{}).slice(0,40));
        else txt=esc(JSON.stringify(pl).slice(0,60));
        ch+='<div class="tl-item"><span class="tt">'+ts+'</span><span class="'+ic+'">'+esc(lb)+'</span><span class="ttxt">'+txt+'</span></div>';
      });ch+='</div>';}
  }else if(activeTab==='tasks'){
    if(!currentTasks.length){ch='<div class="empty-state">No tasks. Run the loop.</div>';}
    else{ch='<div class="detail-section"><h4>Tasks</h4>';
      currentTasks.forEach(function(t){
        var d=t.status==='completed';var pri=t.priority||'medium';
        var due=t.due_date?new Date(t.due_date):null;var overdue=due&&due<new Date()&&t.status==='pending';
        ch+='<div class="task-item"><span class="ttitle'+(d?' done':'')+'">'+esc(t.title)+'</span>'+
          (t.due_date?'<span style="font-size:10px;color:'+(overdue?'#dc2626':'#9ca3af')+'">'+t.due_date.slice(0,10)+'</span>':'')+
          '<span class="tstatus '+(t.status)+'">'+t.status+'</span>'+
          (t.status==='pending'?'<button class="tcomp" onclick="completeTask('+t.id+')">Done</button>':'')+'</div>';});
      ch+='</div>';}
  }else if(activeTab==='notes'){
    ch='<div class="detail-section"><h4>Notes</h4><textarea class="notes-area" id="notes-text" placeholder="Add notes..."></textarea><button class="notes-save" onclick="saveNotes()">Save</button><div class="notes-status" id="notes-status">Saved</div></div>';
    api('/debug/entity/'+selectedEntityId+'/notes').then(function(d){document.getElementById('notes-text').value=d.notes||'';}).catch(function(){});
  }
  document.getElementById('detail-body').innerHTML=th+ch;
}

function renderEditForm(){
  var e=entities.find(function(x){return x.id===selectedEntityId;});if(!e)return;var st=e.state||{};
  var h='<div class="edit-grid">'+
    '<div class="edit-field"><label>Name</label><input id="ef-name" value="'+esc(st.name||'')+'"></div>'+
    '<div class="edit-field"><label>Phone</label><input id="ef-phone" value="'+esc(st.phone||'')+'"></div>'+
    '<div class="edit-field"><label>Email</label><input id="ef-email" value="'+esc(st.email||'')+'"></div>'+
    '<div class="edit-field"><label>Company</label><input id="ef-company" value="'+esc(st.company||'')+'" placeholder="Company name"></div>'+
    '<div class="edit-field"><label>Contact Person</label><input id="ef-contact" value="'+esc(st.contact_person||'')+'" placeholder="Contact name"></div>'+
    '<div class="edit-field"><label>Deal Value</label><input id="ef-value" value="'+esc(st.deal_value||'')+'" placeholder="0.00"></div>'+
    '<div class="edit-field"><label>Currency</label><select id="ef-currency"><option value="USD"'+(st.currency==='USD'?' selected':'')+'>USD</option><option value="INR"'+(st.currency==='INR'?' selected':'')+'>INR</option><option value="EUR"'+(st.currency==='EUR'?' selected':'')+'>EUR</option></select></div>'+
    '<div class="edit-field"><label>Assigned To</label><input id="ef-owner" value="'+esc(st.assigned_to||'')+'" placeholder="Owner name"></div>'+
    '<div class="edit-field"><label>Stage</label><select id="ef-stage">'+
    '<option value="new"'+(st.stage==='new'?' selected':'')+'>New</option>'+
    '<option value="contacted"'+(st.stage==='contacted'?' selected':'')+'>Contacted</option>'+
    '<option value="quoted"'+(st.stage==='quoted'?' selected':'')+'>Quoted</option>'+
    '<option value="closed"'+(st.stage==='closed'?' selected':'')+'>Closed</option></select></div></div>'+
    '<div class="edit-actions"><button class="save-btn" onclick="saveEntityEdit()">Save Changes</button><button class="cancel-btn" onclick="toggleEditMode()">Cancel</button></div>';
  document.getElementById('detail-body').innerHTML='<div class="detail-section"><h4>Edit Entity</h4>'+h+'</div>';
}
function toggleEditMode(){editMode=!editMode;document.getElementById('btn-toggle-edit').textContent=editMode?'View':'Edit';if(editMode)renderEditForm();else renderDetail();}

async function saveEntityEdit(){
  var updates={name:document.getElementById('ef-name').value,phone:document.getElementById('ef-phone').value,email:document.getElementById('ef-email').value,company:document.getElementById('ef-company').value,contact_person:document.getElementById('ef-contact').value,deal_value:document.getElementById('ef-value').value,currency:document.getElementById('ef-currency').value,assigned_to:document.getElementById('ef-owner').value,stage:document.getElementById('ef-stage').value};
  try{await api('/debug/entity/'+selectedEntityId,'PUT',{state:updates});toast('Updated');editMode=false;document.getElementById('btn-toggle-edit').textContent='Edit';await loadAll();selectEntity(selectedEntityId);}catch(e){toast('Error: '+e.message);}
}
async function saveNotes(){var t=document.getElementById('notes-text').value;try{await api('/debug/entity/'+selectedEntityId+'/notes','POST',{notes:t});var s=document.getElementById('notes-status');s.style.display='block';setTimeout(function(){s.style.display='none';},2000);}catch(e){toast('Error: '+e.message);}}
async function completeTask(id){try{await api('/debug/tasks/'+id+'/complete','POST');toast('Done');await loadAll();selectEntity(selectedEntityId);}catch(e){toast('Error: '+e.message);}}

function renderProposals(){
  var pl=document.getElementById('proposal-list');
  if(!proposals.length){pl.innerHTML='<div class="empty-state">No proposals yet.<br>Create entity, run loop.</div>';return;}
  pl.innerHTML=proposals.map(function(p){
    var en=(p.entity&&(p.entity.name||''))||p.to||'?',cs='pstatus '+(p.status==='pending'?'pending':(p.status==='sent'||p.status==='approved'?'sent':'rejected'));
    var se=(editingProposalId===p.id),ctx=p.context||{},ah='';
    if(p.status==='pending')ah='<div class="prop-actions"><button class="apr" onclick="approveProposal('+p.id+')" id="apr-'+p.id+'">Approve</button><button class="rjt" onclick="rejectProposal('+p.id+')" id="rjt-'+p.id+'">Reject</button><button class="edt" onclick="toggleEdit('+p.id+')">Edit</button></div>';
    var eh='';if(se)eh='<div class="edit-box"><textarea id="etext-'+p.id+'">'+esc(p.message)+'</textarea><div class="ebtn"><button class="save" onclick="saveEdit('+p.id+')">Save</button><button onclick="toggleEdit('+p.id+')">Cancel</button></div></div>';
    return '<div class="prop-item" onclick="selectEntityFromProposal('+p.id+')"><div class="phead"><span class="pto">'+esc(en)+'</span><span class="'+cs+'">'+p.status+'</span></div><div class="pmsg">'+esc(p.message)+'</div><div class="preason">Why: '+esc(ctx.reason||'AI')+'</div>'+eh+ah+'<div class="pfeed" id="pfeed-'+p.id+'"></div></div>';
  }).join('');
}
function selectEntityFromProposal(i){var p=proposals.find(function(x){return x.id===i;});if(p&&p.entity&&p.entity.id)selectEntity(p.entity.id);}

function updatePipeline(){
  var c={new:0,contacted:0,quoted:0,closed:0},val={new:0,contacted:0,quoted:0,closed:0};
  entities.forEach(function(e){
    var s=getStage(e.state||{});if(c[s]!==undefined)c[s]++;
    var st=e.state||{};if(st.deal_value){var v=parseFloat(st.deal_value)||0;if(val[s]!==undefined)val[s]+=v;}
  });
  for(var s in c){
    document.getElementById('count-'+s).textContent=c[s]+(val[s]?' $'+val[s].toFixed(0):'');
    var d=document.getElementById('pipe-'+s);d.className='dot'+(c[s]>0?(s==='new'||s==='contacted'?' warn':' has'):'');
  }
}

async function runLoop(){var b=document.getElementById('btn-loop');b.disabled=true;b.textContent='Running...';try{var r=await api('/debug/run-cycle','POST');toast('Done: '+(r.summary?r.summary.actions_taken+' actions':'ok'));await loadAll();}catch(e){toast('Error: '+e.message);}b.disabled=false;b.textContent='Run Loop';}
function showCreateEntity(){var n=prompt('Name:','Test Lead');if(!n)return;var p=prompt('Phone:',''),e=prompt('Email:',''),d={type:'lead',data:{name:n,stage:'new'}};if(p)d.data.phone=p;if(e)d.data.email=e;api('/debug/entity','POST',d).then(function(){toast('Created');loadAll();}).catch(function(e){toast('Error: '+e.message);});}
async function approveProposal(id){document.getElementById('pfeed-'+id).textContent='Approving...';var b=document.getElementById('apr-'+id);if(b)b.disabled=true;try{await api('/proposals/'+id+'/approve','POST',{approved_by:'human'});document.getElementById('pfeed-'+id).textContent='✓ Sent';toast('Approved');await loadAll();}catch(e){document.getElementById('pfeed-'+id).textContent='Error: '+e.message;if(b)b.disabled=false;}}
async function rejectProposal(id){document.getElementById('pfeed-'+id).textContent='Rejecting...';var b=document.getElementById('rjt-'+id);if(b)b.disabled=true;try{await api('/proposals/'+id+'/reject','POST');document.getElementById('pfeed-'+id).textContent='✗ Rejected';toast('Rejected');await loadAll();}catch(e){document.getElementById('pfeed-'+id).textContent='Error: '+e.message;if(b)b.disabled=false;}}
function toggleEdit(id){editingProposalId=(editingProposalId===id)?null:id;renderProposals();}
async function saveEdit(id){var t=document.getElementById('etext-'+id);if(!t)return;var m=t.value.trim();if(!m)return;try{await api('/proposals/'+id+'/edit','POST',{message:m});document.getElementById('pfeed-'+id).textContent='✓ Saved';editingProposalId=null;toast('Updated');await loadAll();}catch(e){document.getElementById('pfeed-'+id).textContent='Error: '+e.message;}}
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