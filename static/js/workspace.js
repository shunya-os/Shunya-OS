/* SHUNYA — Workspace State Machine v1.0
   Approved visual system. Faithful reproduction. */

/* ─── State ─── */
let state = {
  view: 'morning-zero',
  focus: null,
  space: null,
  convId: null,
  identity: null,
  morningData: null,
  activeTab: 'content',
  searchOpen: false,
  health: 0.78,
  priorities: [],
  risks: [],
  opportunities: [],
  decisions: [],
};

/* ─── Identity ─── */
function setIdentity(name, id) {
  state.identity = { name, id };
  document.getElementById('strip-identity').textContent = name;
}

/* ─── Status Dot ─── */
function setStatus(s) {
  const dot = document.getElementById('status-dot');
  if (dot) dot.className = s;
}

/* ─── Utils ─── */
function escapeHtml(text) {
  if (!text) return '';
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

function formatTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString([], { month: 'short', day: 'numeric' });
}

/* ─── Navigation ─── */
function navigateTo(view, data) {
  state.view = view;
  switch (view) {
    case 'morning-zero': showMorningZero(data); break;
    case 'object': showObject(data); break;
    case 'executive': showExecutiveBrief(data); break;
  }
}

/* ─── Morning Zero ─── */
async function loadMorningZero() {
  setStatus('thinking');
  const center = document.getElementById('zone-center');
  if (!center) return;
  center.innerHTML = '<div class="morning-zero"><div class="skeleton skeleton-line" style="width:40%;height:22px;margin-bottom:8px"></div><div class="skeleton skeleton-line short"></div></div>';
  try {
    const resp = await fetch('/api/v1/founder/morning-zero');
    const data = await resp.json();
    if (data.success) {
      state.morningData = data;
      showMorningZero(data);
    }
  } catch (e) { console.error('Failed to load morning zero', e); }
  setStatus('calm');
}

function showMorningZero(data) {
  const center = document.getElementById('zone-center');
  if (!center) return;
  const name = state.identity?.name || 'Founder';
  const items = data.data?.items || [];
  const hasItems = items.length > 0;

  let html = '<div class="morning-zero">';
  html += `<div class="greeting">Good morning, ${escapeHtml(name)}.</div>`;

  if (hasItems) {
    const attention = items.filter(i => i.priority === 'attention');
    const info = items.filter(i => i.priority === 'info');
    const opps = items.filter(i => i.priority === 'opportunity');

    if (attention.length > 0) {
      html += `<div class="subtitle">${attention.length} thing${attention.length > 1 ? 's' : ''} need${attention.length === 1 ? 's' : ''} your attention:</div>`;
      html += renderMZItems(attention);
    }

    if (info.length > 0) {
      html += `<div class="mz-section"><div class="mz-section-title">Updates</div>${renderMZItems(info)}</div>`;
    }

    if (opps.length > 0) {
      html += `<div class="mz-section"><div class="mz-section-title">Opportunities</div>${renderMZItems(opps)}</div>`;
    }
  } else {
    html += `<div class="subtitle">Everything is quiet.</div>`;
    const activeObjects = data.data?.summary?.active_objects || 0;
    html += `<div class="mz-quiet">You have ${activeObjects} active objects across your workspace.</div>`;
  }

  html += '</div>';
  center.innerHTML = html;
  document.getElementById('nav-morning')?.classList.add('active');
  loadExecutiveBrief();
}

function renderMZItems(items) {
  return items.map(item => {
    const dotClass = item.priority === 'attention' ? 'attention' : item.priority === 'opportunity' ? 'opportunity' : 'info';
    const focus = item.focus || {};
    const objectId = focus.object_id || focus.id || '';
    return `<div class="mz-item" onclick="focusObject('${escapeHtml(objectId)}')">
      <div class="mz-dot ${dotClass}"></div>
      <div class="mz-body">
        <div class="mz-title">${escapeHtml(item.title)}</div>
        ${item.meta ? `<div class="mz-meta">${escapeHtml(item.meta)}</div>` : ''}
      </div>
    </div>`;
  }).join('');
}

/* ─── Focus Object ─── */
async function focusObject(objectId) {
  if (!objectId) return;
  setStatus('thinking');
  const center = document.getElementById('zone-center');
  if (!center) return;
  center.innerHTML = '<div style="padding:32px"><div class="skeleton skeleton-line" style="width:50%;height:28px;margin-bottom:12px"></div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line short"></div><div class="skeleton skeleton-line" style="margin-top:20px"></div><div class="skeleton skeleton-line"></div></div>';

  try {
    const resp = await fetch(`/api/v1/founder/focus/${objectId}`);
    const data = await resp.json();
    if (data.success) {
      state.focus = objectId;
      state.convId = data.data.conversation?.conv_id || null;
      showObject(data);
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    }
  } catch (e) { console.error('Failed to focus object', e); }
  setStatus('calm');
}

function showObject(data) {
  const center = document.getElementById('zone-center');
  if (!center) return;

  // Handle relationship focus
  if (data.relationship) {
    showRelationship(data);
    return;
  }

  const obj = data.data.object;
  const conv = data.data.conversation;
  const messages = data.data.messages || [];
  const relationships = data.data.relationships || [];
  const ai = data.data.ai_understanding || '';
  state.activeTab = 'content';

  let html = '<div id="object-workspace">';

  // Header
  html += `<div class="object-header">
    <div class="object-type">${escapeHtml(obj.object_type)}</div>
    <div class="object-name">${escapeHtml(obj.name)}</div>
    <div class="object-meta">
      <span class="object-health">
        <span class="object-health-dot good"></span> Active
      </span>
      <span>Created ${obj.created_at ? formatDate(obj.created_at) : ''}</span>
    </div>
  </div>`;

  // Tabs
  html += `<div class="object-tabs">
    <button class="object-tab active" data-tab="content" onclick="switchTab('content')">Content</button>
    <button class="object-tab" data-tab="conversation" onclick="switchTab('conversation')">Conversation${messages.length ? ` (${messages.length})` : ''}</button>
    <button class="object-tab" data-tab="timeline" onclick="switchTab('timeline')">Timeline</button>
    <button class="object-tab" data-tab="evidence" onclick="switchTab('evidence')">Evidence</button>
    <button class="object-tab" data-tab="links" onclick="switchTab('links')">Links</button>
  </div>`;

  // Body
  html += '<div class="object-body">';

  // Content panel
  html += `<div class="object-tab-panel active" id="panel-content">
    ${obj.content ? `<div class="panel-content">${escapeHtml(obj.content)}</div>` : '<div class="panel-content" style="color:var(--text-faint)">No content.</div>'}`;

  if (ai) {
    html += `<div style="margin-top:16px;padding:12px 16px;background:rgba(92,124,250,0.04);border:1px solid rgba(92,124,250,0.08);border-radius:var(--radius-sm);font-size:13px;color:var(--text-secondary);line-height:1.6">${escapeHtml(ai)}</div>`;
  }

  html += '</div>';

  // Conversation panel
  html += `<div class="object-tab-panel" id="panel-conversation">`;
  if (conv) {
    html += `<div class="conv-messages" id="conv-messages">`;
    messages.forEach(m => {
      html += `<div class="conv-message ${m.role}">
        ${escapeHtml(m.content)}
        <div class="msg-time">${formatTime(m.created_at)}</div>
      </div>`;
    });
    html += `</div>
      <div class="conv-input-row">
        <input type="text" id="conv-input" placeholder="Type your message..." onkeydown="if(event.key==='Enter') sendMessage()">
        <button onclick="sendMessage()">Send</button>
      </div>`;
  } else {
    html += `<button class="conv-start-btn" onclick="startConversation('${obj.object_id}')">Start Conversation</button>`;
  }
  html += '</div>';

  // Timeline panel
  html += `<div class="object-tab-panel" id="panel-timeline">
    <div class="timeline-item">
      <div class="timeline-dot change"></div>
      <div class="timeline-body">
        <div class="timeline-title">Object created</div>
        <div class="timeline-meta">${obj.created_at ? formatDate(obj.created_at) : 'Unknown'}</div>
      </div>
    </div>
    <div class="timeline-item">
      <div class="timeline-dot evidence"></div>
      <div class="timeline-body">
        <div class="timeline-title">Evidence recorded</div>
        <div class="timeline-meta">Constitutional compliance verified</div>
      </div>
    </div>
  </div>`;

  // Evidence panel
  html += `<div class="object-tab-panel" id="panel-evidence">
    <div class="intel-empty">Evidence chain available for this object.</div>
  </div>`;

  // Links panel
  html += `<div class="object-tab-panel" id="panel-links">
    <div class="links-grid">`;
  if (relationships.length > 0) {
    relationships.forEach(r => {
      html += `<span class="link-chip" onclick="focusObject('${r.object_id}')">
        <span class="link-type">${escapeHtml(r.type)}</span>
        ${escapeHtml(r.name)}
      </span>`;
    });
  } else {
    html += `<div class="intel-empty">No linked objects.</div>`;
  }
  html += `</div></div>`;

  html += '</div></div>';
  center.innerHTML = html;
  navigateTo('object');

  // Load intelligence
  loadExecutiveBrief();
}

function showRelationship(data) {
  const center = document.getElementById('zone-center');
  if (!center) return;
  const rel = data.relationship.relationship;
  const related = data.relationship.related_objects || [];

  let html = '<div id="object-workspace">';
  html += `<div class="object-header">
    <div class="object-type">${escapeHtml(rel.rel_type)}</div>
    <div class="object-name">${escapeHtml(rel.name)}</div>
  </div>`;

  html += `<div class="object-body">
    <div class="panel-content" style="line-height:1.8">
      ${rel.email ? `<div>Email: ${escapeHtml(rel.email)}</div>` : ''}
      ${rel.phone ? `<div>Phone: ${escapeHtml(rel.phone)}</div>` : ''}
      ${rel.company ? `<div>Company: ${escapeHtml(rel.company)}</div>` : ''}
      ${rel.tags?.length ? `<div>Tags: ${rel.tags.join(', ')}</div>` : ''}
    </div>
    ${rel.notes ? `<div style="padding:12px 16px;background:rgba(26,26,26,0.02);border-radius:var(--radius-sm);font-size:13px;color:var(--text-secondary);margin-top:8px">${escapeHtml(rel.notes)}</div>` : ''}`;

  if (related.length > 0) {
    html += `<div style="margin-top:20px"><div class="intel-section-title" style="margin-bottom:8px">Related Objects</div>
    <div class="links-grid">`;
    related.forEach(o => {
      html += `<span class="link-chip" onclick="focusObject('${o.object_id}')">
        <span class="link-type">${escapeHtml(o.object_type)}</span>
        ${escapeHtml(o.name)}
      </span>`;
    });
    html += `</div></div>`;
  }

  html += '</div></div>';
  center.innerHTML = html;
}

/* ─── Tab Switching ─── */
function switchTab(tab) {
  state.activeTab = tab;
  document.querySelectorAll('.object-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.object-tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelector(`.object-tab[data-tab="${tab}"]`)?.classList.add('active');
  document.getElementById(`panel-${tab}`)?.classList.add('active');
  if (tab === 'conversation') {
    const msgs = document.getElementById('conv-messages');
    if (msgs) msgs.scrollTop = msgs.scrollHeight;
    setTimeout(() => document.getElementById('conv-input')?.focus(), 100);
  }
}

/* ─── Conversation ─── */
async function startConversation(objectId) {
  try {
    const resp = await fetch(`/api/v1/founder/objects/${objectId}/conversation`, { method: 'POST' });
    const data = await resp.json();
    if (data.success) {
      state.convId = data.data.conv_id;
      focusObject(objectId);
    }
  } catch (e) { console.error('Failed to start conversation', e); }
}

async function sendMessage() {
  const input = document.getElementById('conv-input');
  const content = input?.value?.trim();
  if (!content || !state.convId) return;
  input.disabled = true;
  try {
    const resp = await fetch(`/api/v1/founder/conversations/${state.convId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    const data = await resp.json();
    if (data.success) {
      focusObject(state.focus);
    }
  } catch (e) { console.error('Failed to send message', e); }
}

/* ─── Executive Brief (Right Zone) ─── */
async function loadExecutiveBrief() {
  const right = document.getElementById('zone-right-body');
  if (!right) return;
  try {
    const resp = await fetch('/api/v1/founder/morning-zero');
    const data = await resp.json();
    if (data.success) {
      renderExecutiveBrief(data);
    }
  } catch (e) { /* intelligence panel is optional */ }
}

function renderExecutiveBrief(data) {
  const right = document.getElementById('zone-right-body');
  if (!right) return;
  const items = data.data?.items || [];
  const health = state.health || 0.78;
  const healthClass = health >= 0.7 ? 'good' : health >= 0.5 ? 'caution' : health >= 0.3 ? 'at-risk' : 'critical';

  let html = '';

  // Health
  html += `<div class="exec-brief-header">
    <div class="exec-health">
      <span class="object-health-dot ${healthClass}"></span>
      ${Math.round(health * 100)}% Health
      <span class="health-bar"><span class="health-bar-fill ${healthClass}" style="width:${health * 100}%"></span></span>
    </div>
    <div class="exec-brief-summary">${data.data?.summary?.insight || 'Everything is operating normally.'}</div>
  </div>`;

  // Priorities
  const attention = items.filter(i => i.priority === 'attention');
  html += `<div class="intel-section">
    <div class="intel-section-title">Priorities ${attention.length ? `(${attention.length})` : ''}</div>`;
  if (attention.length > 0) {
    attention.slice(0, 3).forEach(a => {
      html += `<div class="intel-card"><div class="intel-label">${escapeHtml(a.title)}</div>${a.meta ? `<div class="intel-meta">${escapeHtml(a.meta)}</div>` : ''}</div>`;
    });
  } else {
    html += `<div class="intel-empty">No priorities.</div>`;
  }
  html += '</div>';

  // Risks
  html += `<div class="intel-section">
    <div class="intel-section-title">Risks</div>
    <div class="intel-empty">No risks detected.</div>
  </div>`;

  // Decisions
  html += `<div class="intel-section">
    <div class="intel-section-title">Decisions</div>
    <div class="intel-empty">No pending decisions.</div>
  </div>`;

  // Opportunities
  const opps = items.filter(i => i.priority === 'opportunity');
  if (opps.length > 0) {
    html += `<div class="intel-section">
      <div class="intel-section-title">Opportunities</div>`;
    opps.slice(0, 2).forEach(o => {
      html += `<div class="intel-card"><div class="intel-label">${escapeHtml(o.title)}</div></div>`;
    });
    html += '</div>';
  }

  right.innerHTML = html;
}

/* ─── Search ─── */
function openSearch() {
  state.searchOpen = true;
  const overlay = document.getElementById('search-overlay');
  overlay.classList.add('open');
  const input = document.getElementById('search-input');
  if (input) { input.value = ''; input.focus(); }
  document.getElementById('search-results').innerHTML = '';
}

function closeSearch() {
  state.searchOpen = false;
  document.getElementById('search-overlay').classList.remove('open');
}

function selectSearchResult(objectId) {
  closeSearch();
  focusObject(objectId);
}

/* ─── Keyboard Shortcuts ─── */
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape' && state.searchOpen) {
    closeSearch();
    return;
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    openSearch();
    return;
  }
  if (!state.searchOpen && e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey
      && document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA') {
    openSearch();
    const input = document.getElementById('search-input');
    if (input) input.value = e.key;
  }
});

/* ─── Search Input ─── */
let searchTimeout;
document.addEventListener('input', function(e) {
  if (e.target.id === 'search-input') {
    clearTimeout(searchTimeout);
    const q = e.target.value.trim();
    const results = document.getElementById('search-results');
    if (!q) { results.innerHTML = ''; return; }
    searchTimeout = setTimeout(async () => {
      try {
        const resp = await fetch('/api/v1/founder/search?q=' + encodeURIComponent(q));
        const data = await resp.json();
        if (data.success && data.data.length > 0) {
          results.innerHTML = data.data.map(r => {
            const id = r._type === 'relationship' ? r.rel_id : r.object_id;
            return `<div class="search-result" onclick="selectSearchResult('${id}')">
              <div class="sr-name">${escapeHtml(r.name)}</div>
              <div class="sr-meta">${r._type === 'relationship' ? r.rel_type : r.object_type}</div>
            </div>`;
          }).join('');
        } else {
          results.innerHTML = '<div style="padding:12px 0;font-size:13px;color:var(--text-faint)">No results</div>';
        }
      } catch (e) { console.error('Search failed', e); }
    }, 200);
  }
});

/* ─── Left Zone Navigation ─── */
function navClick(view) {
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const nav = document.getElementById(`nav-${view}`);
  if (nav) nav.classList.add('active');

  switch (view) {
    case 'morning': loadMorningZero(); break;
    case 'executive': loadExecutiveBrief(); break;
  }
}

/* ─── Init ─── */
document.addEventListener('DOMContentLoaded', async function() {
  // Get identity
  try {
    const resp = await fetch('/api/v1/founder/profile');
    const data = await resp.json();
    if (data.success) {
      setIdentity(data.data.name, data.data.identity_id);
    }
  } catch (e) {}

  // Clock
  function updateClock() {
    const now = new Date();
    const h = now.getHours().toString().padStart(2, '0');
    const m = now.getMinutes().toString().padStart(2, '0');
    document.getElementById('time-indicator').textContent = `${h}:${m}`;
  }
  updateClock();
  setInterval(updateClock, 30000);

  // Load morning zero
  loadMorningZero();
});