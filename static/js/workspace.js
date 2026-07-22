/* SHUNYA — Workspace State Machine */

let state = {
  view: 'morning-zero',
  focus: null,       // current focused object
  space: null,       // current space
  identity: null,    // { name, id }
  convId: null,      // current conversation id
  morningData: null, // cached morning zero data
};

/* ─── State Transitions ─── */

function switchView(viewName, data) {
  // Hide all views
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  state.view = viewName;

  switch (viewName) {
    case 'morning-zero':
      showMorningZero(data);
      break;
    case 'ambient':
      showAmbient(data);
      break;
    case 'focused':
      showFocused(data);
      break;
    case 'deep':
      showDeep(data);
      break;
  }
}

/* ─── Identity ─── */

function setIdentity(name, id) {
  state.identity = { name, id };
  document.getElementById('identity-name').textContent = name;
}

/* ─── Relationships ─── */

async function loadRelationships() {
  setStatus('thinking');
  try {
    const resp = await fetch('/api/v1/founder/relationships');
    const data = await resp.json();
    if (data.success) {
      switchView('ambient', { relationships: data.data });
    }
  } catch(e) { console.error('Failed to load relationships', e); }
  setStatus('calm');
}

async function createRelationship() {
  const name = prompt('Name:');
  if (!name) return;
  const relType = prompt('Type (customer, supplier, partner, employee, vendor):', 'customer');
  if (!relType) return;
  try {
    const resp = await fetch('/api/v1/founder/relationships', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, rel_type: relType }),
    });
    const data = await resp.json();
    if (data.success) {
      loadRelationships();
    }
  } catch(e) { console.error('Failed to create relationship', e); }
}

async function focusRelationship(relId) {
  setStatus('thinking');
  try {
    const resp = await fetch(`/api/v1/founder/relationships/${relId}`);
    const data = await resp.json();
    if (data.success) {
      state.focus = relId;
      state.focusType = 'relationship';
      switchView('focused', { relationship: data.data });
    }
  } catch(e) { console.error('Failed to focus relationship', e); }
  setStatus('calm');
}

/* ─── Morning Zero ─── */

async function loadMorningZero() {
  setStatus('thinking');
  try {
    const resp = await fetch('/api/v1/founder/morning-zero');
    const data = await resp.json();
    if (data.success) {
      state.morningData = data;
      switchView('morning-zero', data);
    }
  } catch(e) {
    console.error('Failed to load morning zero', e);
  }
  setStatus('calm');
}

function showMorningZero(data) {
  const el = document.getElementById('view-morning-zero');
  el.innerHTML = renderMorningZero(data);
  el.classList.add('active');
}

function renderMorningZero(data) {
  const name = state.identity?.name || 'Founder';
  const items = data.data?.items || [];
  const hasItems = items.length > 0;

  let html = `<div class="greeting">Good morning, ${name}.</div>`;

  if (hasItems) {
    const attention = items.filter(i => i.priority === 'attention');
    const info = items.filter(i => i.priority === 'info');
    const opps = items.filter(i => i.priority === 'opportunity');

    if (attention.length > 0) {
      html += `<div class="subtitle">${attention.length} thing${attention.length > 1 ? 's' : ''} need${attention.length === 1 ? 's' : ''} your attention:</div>`;
      html += renderMZSection(attention);
    }

    if (info.length > 0) {
      html += `<div class="mz-section"><div class="mz-section-title">Updates</div>`;
      html += renderMZItems(info);
      html += `</div>`;
    }

    if (opps.length > 0) {
      html += `<div class="mz-section"><div class="mz-section-title">Opportunities</div>`;
      html += renderMZItems(opps);
      html += `</div>`;
    }
  } else {
    html += `<div class="subtitle">Everything is quiet.</div>`;
    const activeSpaces = state.morningData?.data?.summary?.active_spaces || 0;
    const activeObjects = state.morningData?.data?.summary?.active_objects || 0;
    html += `<div class="mz-quiet">You have ${activeObjects} active objects across ${activeSpaces} spaces.</div>`;
  }

  return html;
}

function renderMZSection(items) {
  return `<div class="mz-section">${renderMZItems(items)}</div>`;
}

function renderMZItems(items) {
  return items.map(item => {
    const dotClass = item.priority === 'attention' ? 'attention' : item.priority === 'opportunity' ? 'opportunity' : 'info';
    return `<div class="mz-item" data-focus='${JSON.stringify(item.focus || item)}'>
      <div class="mz-dot ${dotClass}"></div>
      <div class="mz-body">
        <div class="mz-title">${item.title}</div>
        ${item.meta ? `<div class="mz-meta">${item.meta}</div>` : ''}
      </div>
    </div>`;
  }).join('');
}

/* ─── Ambient (scanning) ─── */

async function loadAmbient(spaceId) {
  setStatus('thinking');
  try {
    const url = spaceId ? `/api/v1/founder/spaces/${spaceId}/objects` : '/api/v1/founder/spaces';
    const resp = await fetch(url);
    const data = await resp.json();
    if (data.success) {
      if (spaceId) {
        state.space = spaceId;
        // Also get space info
        const spaceResp = await fetch(`/api/v1/founder/spaces/${spaceId}`);
        const spaceData = await spaceResp.json();
        switchView('ambient', { objects: data.data, space: spaceData.data || { name: 'Space' } });
      } else {
        switchView('ambient', { spaces: data.data });
      }
    }
  } catch(e) {
    console.error('Failed to load ambient', e);
  }
  setStatus('calm');
}

function showAmbient(data) {
  const el = document.getElementById('view-ambient');
  if (data.objects) {
    // Object grid for a specific space
    const space = data.space;
    el.innerHTML = `
      <div class="ambient-header">
        <h2>${space.name}</h2>
        <span class="space-name" onclick="loadAmbient()">All Spaces &rarr;</span>
      </div>
      <div class="ambient-grid">
        ${data.objects.map(o => `
          <div class="ambient-card" onclick="focusObject('${o.object_id}')">
            <div class="card-type">${o.object_type}</div>
            <div class="card-name">${o.name}</div>
            <div class="card-meta">${o.updated_at ? new Date(o.updated_at).toLocaleDateString() : ''}</div>
          </div>
        `).join('')}
      </div>
      <div class="ambient-header" style="margin-top:32px">
        <h2>Relationships</h2>
      </div>
      <div class="ambient-grid" id="rel-grid"></div>
    `;
    // Load relationships for this space
    fetch(`/api/v1/founder/relationships?q=${encodeURIComponent(space.name)}`)
      .then(r => r.json()).then(d => {
        if (d.success && d.data.length > 0) {
          document.getElementById('rel-grid').innerHTML = d.data.map(r => `
            <div class="ambient-card" onclick="focusRelationship('${r.rel_id}')">
              <div class="card-type">${r.rel_type}</div>
              <div class="card-name">${r.name}</div>
              <div class="card-meta">${r.company || r.email || ''}</div>
            </div>
          `).join('');
        } else {
          document.getElementById('rel-grid').innerHTML = '<div style="padding:16px;font-size:13px;color:rgba(26,26,26,0.25)">No relationships yet. <span style="cursor:pointer;color:rgba(26,26,26,0.5);text-decoration:underline" onclick="createRelationship()">Add one</span></div>';
        }
      });
  } else if (data.spaces) {
    // Space list
    el.innerHTML = `
      <div class="ambient-header"><h2>Your Spaces</h2></div>
      <div class="ambient-grid">
        ${data.spaces.map(s => `
          <div class="ambient-card" onclick="loadAmbient('${s.space_id}')">
            <div class="card-type">${s.space_type}</div>
            <div class="card-name">${s.name}</div>
            <div class="card-meta">${s.object_count} objects</div>
          </div>
        `).join('')}
      </div>
      <div class="ambient-header" style="margin-top:32px">
        <h2>Relationships</h2>
        <span class="space-name" onclick="loadRelationships()" style="cursor:pointer">View All &rarr;</span>
      </div>
      <div class="ambient-grid" id="rel-grid"></div>
    `;
    // Load recent relationships
    fetch('/api/v1/founder/relationships')
      .then(r => r.json()).then(d => {
        if (d.success && d.data.length > 0) {
          document.getElementById('rel-grid').innerHTML = d.data.slice(0,6).map(r => `
            <div class="ambient-card" onclick="focusRelationship('${r.rel_id}')">
              <div class="card-type">${r.rel_type}</div>
              <div class="card-name">${r.name}</div>
              <div class="card-meta">${r.company || r.email || ''}</div>
            </div>
          `).join('');
        } else {
          document.getElementById('rel-grid').innerHTML = '<div style="padding:16px;font-size:13px;color:rgba(26,26,26,0.25)">No relationships yet. <span style="cursor:pointer;color:rgba(26,26,26,0.5);text-decoration:underline" onclick="createRelationship()">Add one</span></div>';
        }
      });
  } else if (data.relationships) {
    // Relationship list
    el.innerHTML = `
      <div class="ambient-header">
        <h2>Relationships</h2>
        <span class="space-name" onclick="createRelationship()" style="cursor:pointer">+ Add</span>
      </div>
      <div class="ambient-grid">
        ${data.relationships.map(r => `
          <div class="ambient-card" onclick="focusRelationship('${r.rel_id}')">
            <div class="card-type">${r.rel_type}</div>
            <div class="card-name">${r.name}</div>
            <div class="card-meta">${r.company || r.email || r.phone || ''}</div>
          </div>
        `).join('')}
      </div>
    `;
  }
  el.classList.add('active');
}

/* ─── Focused (object-centered) ─── */

async function focusObject(objectId) {
  setStatus('thinking');
  try {
    const resp = await fetch(`/api/v1/founder/focus/${objectId}`);
    const data = await resp.json();
    if (data.success) {
      state.focus = objectId;
      state.convId = data.data.conversation?.conv_id || null;
      switchView('focused', data);
    }
  } catch(e) {
    console.error('Failed to focus object', e);
  }
  setStatus('calm');
}

function showFocused(data) {
  const el = document.getElementById('view-focused');

  // Handle relationship focus
  if (data.relationship) {
    const rel = data.relationship.relationship;
    const related = data.relationship.related_objects || [];
    el.innerHTML = `
      <div class="focus-back" onclick="backFromFocus()">&larr; Back</div>
      <div class="focus-header">
        <div class="focus-type">${rel.rel_type}</div>
        <div class="focus-name">${escapeHtml(rel.name)}</div>
      </div>
      <div class="focus-section">
        <div class="focus-section-title">Contact</div>
        <div style="font-size:13px;color:rgba(26,26,26,0.5);line-height:1.8">
          ${rel.email ? `<div>Email: ${rel.email}</div>` : ''}
          ${rel.phone ? `<div>Phone: ${rel.phone}</div>` : ''}
          ${rel.company ? `<div>Company: ${rel.company}</div>` : ''}
          ${rel.tags?.length ? `<div>Tags: ${rel.tags.join(', ')}</div>` : ''}
        </div>
      </div>
      ${rel.notes ? `<div class="focus-content">${escapeHtml(rel.notes)}</div>` : ''}
      <div class="focus-section">
        <div class="focus-section-title">AI Understanding</div>
        <div class="focus-ai">${rel.rel_type} relationship with ${rel.name}. ${rel.company ? 'Works at ' + rel.company + '. ' : ''}${rel.email ? 'Contact: ' + rel.email + '. ' : ''}Connected to ${related.length} object${related.length !== 1 ? 's' : ''} in the workspace.</div>
      </div>
      ${related.length > 0 ? `
      <div class="focus-section">
        <div class="focus-section-title">Related Objects</div>
        <div>${related.map(o => 
          `<span class="focus-rel-item" onclick="focusObject('${o.object_id}')">${escapeHtml(o.name)} <span style="color:rgba(26,26,26,0.25)">${o.object_type}</span></span>`
        ).join('')}</div>
      </div>` : ''}
      <div class="focus-section" style="margin-top:24px">
        <button onclick="focusRelationship('${rel.rel_id}');setTimeout(()=>document.getElementById('edit-rel-form')?.classList.toggle('hidden'),100)" style="padding:8px 20px;background:var(--accent);color:white;border:none;border-radius:var(--radius-sm);font-size:13px;cursor:pointer">Edit</button>
      </div>
    `;
    el.classList.add('active');
    return;
  }

  const obj = data.data.object;
  const conv = data.data.conversation;
  const messages = data.data.messages || [];
  const relationships = data.data.relationships || [];
  const ai = data.data.ai_understanding || '';

  const el = document.getElementById('view-focused');

  let html = `<div class="focus-back" onclick="backFromFocus()">&larr; Back</div>`;

  // Object header
  html += `<div class="focus-header">
    <div class="focus-type">${obj.object_type}</div>
    <div class="focus-name">${obj.name}</div>
  </div>`;

  // Content
  if (obj.content) {
    html += `<div class="focus-content">${escapeHtml(obj.content)}</div>`;
  }

  // AI Understanding
  if (ai) {
    html += `<div class="focus-section">
      <div class="focus-section-title">AI Understanding</div>
      <div class="focus-ai">${escapeHtml(ai)}</div>
    </div>`;
  }

  // Relationships
  if (relationships.length > 0) {
    html += `<div class="focus-section">
      <div class="focus-section-title">Relationships</div>
      <div>${relationships.map(r => 
        `<span class="focus-rel-item" onclick="focusObject('${r.object_id}')">${escapeHtml(r.name)} <span style="color:rgba(26,26,26,0.25)">${r.type}</span></span>`
      ).join('')}</div>
    </div>`;
  }

  // Conversations
  if (conv) {
    html += `<div class="focus-section">
      <div class="focus-section-title">Conversation</div>
      <div id="conv-messages">`;
    messages.forEach(m => {
      html += `<div class="focus-msg ${m.role}">
        ${escapeHtml(m.content)}
        <div class="msg-time">${m.created_at ? new Date(m.created_at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : ''}</div>
      </div>`;
    });
    html += `</div>
      <div class="focus-input-row">
        <input type="text" id="conv-input" placeholder="Type your message..." onkeydown="if(event.key==='Enter') sendMessage()">
        <button onclick="sendMessage()">Send</button>
      </div>`;
  } else {
    html += `<div class="focus-section" style="margin-top:24px">
      <button onclick="startConversation('${obj.object_id}')" style="padding:8px 20px;background:var(--accent);color:white;border:none;border-radius:var(--radius-sm);font-size:13px;cursor:pointer">Start Conversation</button>
    </div>`;
  }

  el.innerHTML = html;
  el.classList.add('active');

  // Scroll to bottom of messages
  const convMsgs = document.getElementById('conv-messages');
  if (convMsgs) convMsgs.scrollTop = convMsgs.scrollHeight;
}

function backFromFocus() {
  if (state.space) {
    loadAmbient(state.space);
  } else {
    loadMorningZero();
  }
}

async function startConversation(objectId) {
  try {
    const resp = await fetch(`/api/v1/founder/objects/${objectId}/conversation`, { method: 'POST' });
    const data = await resp.json();
    if (data.success) {
      state.convId = data.data.conv_id;
      focusObject(objectId);
    }
  } catch(e) {
    console.error('Failed to start conversation', e);
  }
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
      // Reload focus to show new messages
      focusObject(state.focus);
    }
  } catch(e) {
    console.error('Failed to send message', e);
    input.disabled = false;
  }
}

/* ─── Deep (immersive) ─── */

function enterDeep() {
  if (!state.focus) return;
  setStatus('thinking');
  fetch(`/api/v1/founder/focus/${state.focus}`)
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        const obj = data.data.object;
        const el = document.getElementById('view-deep');
        el.innerHTML = `<div class="deep-content">
          <div style="margin-bottom:32px">
            <span class="focus-back" onclick="switchView('focused');setTimeout(()=>focusObject('${state.focus}'),50)" style="cursor:pointer;font-size:13px;color:rgba(26,26,26,0.3)">&larr; Back</span>
          </div>
          <div class="deep-name">${escapeHtml(obj.name)}</div>
          <div class="deep-body">${escapeHtml(obj.content || '')}</div>
        </div>`;
        el.classList.add('active');
        state.view = 'deep';
      }
    })
    .finally(() => setStatus('calm'));
}

/* ─── Search ─── */

function openSearch() {
  document.getElementById('search-overlay').classList.add('open');
  document.getElementById('search-input').value = '';
  document.getElementById('search-input').focus();
  document.getElementById('search-results-container').innerHTML = '';
}

function closeSearch() {
  document.getElementById('search-overlay').classList.remove('open');
}

document.addEventListener('keydown', function(e) {
  const searchOpen = document.getElementById('search-overlay').classList.contains('open');
  if (e.key === 'Escape') {
    if (searchOpen) closeSearch();
    else if (state.view === 'deep') switchView('focused');
    else if (state.view === 'focused') backFromFocus();
  }
  if (!searchOpen && e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey && document.activeElement?.tagName !== 'INPUT') {
    // Any keypress opens search
    openSearch();
    document.getElementById('search-input').value = e.key;
  }
});

let searchTimeout;
document.getElementById('search-input')?.addEventListener('input', function() {
  clearTimeout(searchTimeout);
  const q = this.value.trim();
  if (!q) {
    document.getElementById('search-results-container').innerHTML = '';
    return;
  }
  searchTimeout = setTimeout(async () => {
    try {
      const resp = await fetch('/api/v1/founder/search?q=' + encodeURIComponent(q));
      const data = await resp.json();
      const container = document.getElementById('search-results-container');
      if (data.success && data.data.length > 0) {
        container.innerHTML = data.data.map(r => `
          <div class="search-result-item" onclick="${r._type === 'relationship' ? `focusRelationship('${r.rel_id}')` : `selectSearchResult('${r.object_id}')`}">
            <div class="sr-name">${escapeHtml(r.name)}</div>
            <div class="sr-meta">${r._type === 'relationship' ? r.rel_type : r.object_type} &middot; ${r.company || r.space_id?.slice(0,8) || ''}</div>
          </div>
        `).join('');
      } else {
        container.innerHTML = '<div style="padding:16px 0;font-size:13px;color:rgba(26,26,26,0.25)">No results</div>';
      }
    } catch(e) {
      console.error('Search failed', e);
    }
  }, 200);
});

function selectSearchResult(objectId) {
  closeSearch();
  focusObject(objectId);
}

/* ─── Status Dot ─── */

function setStatus(s) {
  const dot = document.getElementById('status-dot');
  dot.className = s;
}

/* ─── Utils ─── */

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
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
  } catch(e) {}

  // Load morning zero
  loadMorningZero();
});