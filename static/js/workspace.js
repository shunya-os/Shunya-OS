/* =========================================================================
   SHUNYA Phase B1 — Universal Workspace Engine
   =========================================================================
   The workspace engine renders different object types without changing
   page architecture. The context engine dynamically updates the right
   panel based on the active object.
   ========================================================================= */

const WS = (function() {

  // ─── State ───
  let state = {
    userName: 'Founder',
    userId: 0,
    spaceApiUrl: '/api/v1/space',
    currentView: 'overview',
    currentObject: null,
    recentObjects: [],
    spaces: [],
    breadcrumb: [],
    contextPanel: 'overview',
    pipelineData: null,
    pipelineHealth: null,
    pipelineTraces: [],
    executiveHomeData: null,
  };

  // ─── Object Renderers ───
  const renderers = {};

  function registerRenderer(type, fn) {
    renderers[type] = fn;
  }

  function getRenderer(type) {
    return renderers[type] || renderers['default'];
  }

  // ─── Default Renderer ───
  registerRenderer('default', function(obj) {
    return `
      <div class="ws-card">
        <div class="ws-card-header">
          <span class="ws-card-title">${obj.name || 'Object'}</span>
          <span class="ws-badge ws-badge-gold">${obj.entity_type || 'unknown'}</span>
        </div>
        <div class="ws-body ws-text-secondary ws-mb-sm">
          ${obj.entity_id ? `<div>ID: ${obj.entity_id}</div>` : ''}
          ${obj.entity_type ? `<div>Type: ${obj.entity_type}</div>` : ''}
        </div>
        ${obj.relationship_count !== undefined ? `
        <div class="ws-flex ws-gap-md ws-text-secondary ws-small">
          <span>${obj.relationship_count} relationships</span>
          <span>${obj.timeline_count || 0} events</span>
          <span>${obj.knowledge_count || 0} items</span>
        </div>` : ''}
      </div>
    `;
  });

  // ─── Priority helpers ───
  function _priorityDot(p) {
    const map = {high: 'high', medium: 'medium', low: 'low', attention: 'attention', info: 'info', warning: 'warning'};
    return `eh-dot-${map[p] || 'info'}`;
  }

  function _priorityLabel(p) {
    return p ? p.charAt(0).toUpperCase() + p.slice(1) : 'Info';
  }

  function _timeAgo(ts) {
    if (!ts) return '';
    const now = Date.now();
    const d = new Date(ts).getTime();
    const diff = now - d;
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }

  function _navigateObject(objectId) {
    WS.navigate('object', objectId);
  }

  function _escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, function(m) {
      if (m === '&') return '&amp;';
      if (m === '<') return '&lt;';
      if (m === '>') return '&gt;';
      if (m === '"') return '&quot;';
      return '&#39;';
    });
  }

  // ─── Helper to create navigate onclick handlers ───
  function _navHandler(type, id) {
    return 'onclick="WS.navigate(\'' + type + '\', \'' + id + '\')"';
  }
  registerRenderer('overview', function() {
    const eh = state.executiveHomeData;
    if (!eh) {
      return `<div class="ws-loading"><div class="ws-loading-spinner"></div><span class="ws-small">Loading Executive Home...</span></div>`;
    }

    const brief = eh.morning_brief || {items: [], summary: {}};
    const recommendations = eh.recommendations || [];
    const health = eh.business_health || {assessment: 'unknown'};
    const activity = eh.recent_activity || [];
    const continueWorking = eh.continue_working || [];
    const summary = brief.summary || {};

    const html = `
      <div class="eh-container">

        <!-- ═══ Morning Brief ═══ -->
        <div class="eh-panel">
          <div class="eh-panel-header">
            <span>Morning Brief</span>
            ${summary.active_spaces > 0 ? `<span class="ws-tiny ws-text-faint">${summary.active_spaces} space${summary.active_spaces !== 1 ? 's' : ''}</span>` : ''}
          </div>
          ${summary.active_objects !== undefined ? `<div class="eh-panel-subtitle">${summary.active_objects} object${summary.active_objects !== 1 ? 's' : ''} · ${summary.pending_conversations} conversation${summary.pending_conversations !== 1 ? 's' : ''} · ${summary.recent_activity} recent</div>` : ''}
          <div class="eh-items">
            ${brief.items.length ? brief.items.map(function(item) {
              const dotClass = _priorityDot(item.priority);
              const label = _priorityLabel(item.priority);
              const focus = item.focus || {};
              const objectId = focus.object_id;
              const onclick = objectId ? _navHandler(focus.type || 'object', objectId) : '';
              return `
                <div class="eh-item" ${onclick}>
                  <span class="eh-item-dot ${dotClass}" title="${label}"></span>
                  <div class="eh-item-content">
                    <div class="eh-item-title">${_escapeHtml(item.title)}</div>
                    ${item.meta ? `<div class="eh-item-meta">${_escapeHtml(item.meta)}</div>` : ''}
                  </div>
                  ${objectId ? `<span class="eh-item-action">Open</span>` : ''}
                </div>
              `;
            }).join('') : `
              <div class="eh-empty">
                <div class="eh-empty-icon">☀</div>
                <div class="eh-empty-text">Everything is quiet. Start by creating a space or object.</div>
              </div>
            `}
          </div>
        </div>

        <!-- ═══ Recommendations ═══ -->
        <div class="eh-panel">
          <div class="eh-panel-header">
            <span>Recommendations</span>
            ${recommendations.length ? `<span class="ws-tiny ws-text-faint">${recommendations.length} item${recommendations.length !== 1 ? 's' : ''}</span>` : ''}
          </div>
          <div class="eh-items">
            ${recommendations.length ? recommendations.map(function(rec) {
              const prio = rec.priority || 'low';
              const action = rec.action || {};
              const target = action.target || '#';
              const label = action.label || 'Open';
              const onclick = target !== '#' ? 'onclick="window.location.href=\'' + target + '\'"' : '';
              return `
                <div class="eh-rec-card eh-priority-${prio}" ${onclick}>
                  <div class="eh-rec-title">${_escapeHtml(rec.title)}</div>
                  <div class="eh-rec-explanation">${_escapeHtml(rec.explanation)}</div>
                  <div class="eh-rec-why">${_escapeHtml(rec.why)}</div>
                  <div class="eh-rec-footer">
                    <span class="eh-rec-runtime">${_escapeHtml(rec.originating_runtime || 'kernel')}</span>
                    <span class="eh-rec-action">${label} →</span>
                  </div>
                </div>
              `;
            }).join('') : `
              <div class="eh-empty">
                <div class="eh-empty-icon">✦</div>
                <div class="eh-empty-text">No recommendations right now. SHUNYA will suggest actions as you work.</div>
              </div>
            `}
          </div>
        </div>

        <!-- ═══ Business Health ═══ -->
        <div class="eh-panel">
          <div class="eh-panel-header">
            <span>Business Health</span>
            <span class="ws-badge ${health.assessment === 'running' ? 'ws-badge-success' : health.assessment === 'attention_needed' ? 'ws-badge-warning' : 'ws-badge-default'}">${health.assessment || 'unknown'}</span>
          </div>
          <div class="eh-health-row">
            <div class="eh-health-stat">
              <div class="eh-health-stat-value">${health.spaces || 0}</div>
              <div class="eh-health-stat-label">Spaces</div>
            </div>
            <div class="eh-health-stat">
              <div class="eh-health-stat-value">${health.objects || 0}</div>
              <div class="eh-health-stat-label">Objects</div>
            </div>
            <div class="eh-health-stat">
              <div class="eh-health-stat-value">${health.relationships || 0}</div>
              <div class="eh-health-stat-label">Relationships</div>
            </div>
            <div class="eh-health-stat">
              <div class="eh-health-stat-value">${health.active_conversations || 0}</div>
              <div class="eh-health-stat-label">Conversations</div>
            </div>
            <div class="eh-health-stat">
              <div class="eh-health-stat-value">${health.real_runtimes || 0}</div>
              <div class="eh-health-stat-label">Real Runtimes</div>
            </div>
          </div>
          ${health.warnings && health.warnings.length ? `
            <div class="eh-health-warning">
              ${health.warnings.map(function(w) { return '<div>⚠ ' + _escapeHtml(w) + '</div>'; }).join('')}
            </div>
          ` : ''}
          <div class="eh-health-assessment">
            Pipeline: ${health.pipeline_status || 'unknown'}
            ${health.mock_runtimes ? ` · ${health.mock_runtimes} mock runtime${health.mock_runtimes !== 1 ? 's' : ''}` : ''}
          </div>
        </div>

        <!-- ═══ Recent Activity ═══ -->
        <div class="eh-panel">
          <div class="eh-panel-header">
            <span>Recent Activity</span>
            ${activity.length ? `<span class="ws-tiny ws-text-faint">${activity.length} item${activity.length !== 1 ? 's' : ''}</span>` : ''}
          </div>
          <div class="eh-items">
            ${activity.length ? activity.map(function(a) {
              const focus = a.focus || {};
              const objectId = focus.object_id;
              const icon = a.type === 'object_created' ? '◇' : a.type === 'object_updated' ? '✎' : '💬';
              const onclick = objectId ? 'onclick="WS.navigate(\'object\', \'' + objectId + '\')"' : '';
              return `
                <div class="eh-item" ${onclick}>
                  <span class="eh-item-dot eh-dot-info"></span>
                  <div class="eh-item-content">
                    <div class="eh-item-title">${icon} ${_escapeHtml(a.title)}</div>
                    <div class="eh-item-meta">${_escapeHtml(a.subtitle || '')}</div>
                  </div>
                  ${objectId ? `<span class="eh-item-action">Open</span>` : ''}
                </div>
              `;
            }).join('') : `
              <div class="eh-empty">
                <div class="eh-empty-icon">📋</div>
                <div class="eh-empty-text">No recent activity yet. Changes will appear here as you work.</div>
              </div>
            `}
          </div>
        </div>

        <!-- ═══ Continue Working ═══ -->
        <div class="eh-panel">
          <div class="eh-panel-header">
            <span>Continue Working</span>
            ${continueWorking.length ? `<span class="ws-tiny ws-text-faint">${continueWorking.length} item${continueWorking.length !== 1 ? 's' : ''}</span>` : ''}
          </div>
          <div class="eh-items">
            ${continueWorking.length ? continueWorking.map(function(cw) {
              const focus = cw.focus || {};
              const objectId = focus.object_id;
              const icon = cw.type === 'object' ? '◇' : '💬';
              const onclick = objectId ? 'onclick="WS.navigate(\'object\', \'' + objectId + '\')"' : '';
              return `
                <div class="eh-cw-card" ${onclick}>
                  <div class="eh-cw-icon">${icon}</div>
                  <div class="eh-cw-content">
                    <div class="eh-cw-title">${_escapeHtml(cw.title)}</div>
                    <div class="eh-cw-subtitle">${_escapeHtml(cw.subtitle || '')}</div>
                  </div>
                  ${cw.meta ? `<span class="eh-cw-meta">${_escapeHtml(cw.meta)}</span>` : ''}
                  <span class="eh-item-action">Open</span>
                </div>
              `;
            }).join('') : `
              <div class="eh-empty">
                <div class="eh-empty-icon">◈</div>
                <div class="eh-empty-text">Nothing to resume. Your previous work will appear here.</div>
              </div>
            `}
          </div>
        </div>

      </div>
    `;

    return html;
  });

  // ─── Recent Activity Renderer ───
    registerRenderer('recent', function() {
      const eh = state.executiveHomeData;
      const activity = (eh && eh.recent_activity) || [];

      var html = '<div class="ws-h2 ws-mb-lg">Recent Activity</div>';
      if (activity.length) {
        html += activity.map(function(a) {
          const focus = a.focus || {};
          const objectId = focus.object_id;
          const icon = a.type === 'object_created' ? '◇' : a.type === 'object_updated' ? '✎' : '💬';
          const onclick = objectId ? 'onclick="WS.navigate(\'object\', \'' + objectId + '\')"' : '';
          return '<div class="ws-card ws-mb-sm" style="cursor:pointer;" ' + onclick + '>' +
            '<div class="ws-card-header">' +
            '<span class="ws-card-title">' + icon + ' ' + _escapeHtml(a.title) + '</span>' +
            '<span class="ws-badge ws-badge-default">' + _escapeHtml(a.subtitle || '') + '</span>' +
            '</div></div>';
        }).join('');
      } else {
        html += '<div class="eh-empty"><div class="eh-empty-icon">📋</div><div class="eh-empty-text">No recent activity yet. Changes will appear here as you work.</div></div>';
      }
      return html;
    });
  // ─── Object Renderer (dispatches to type-specific renderer) ───
  registerRenderer('object', function(obj) {
    const type = obj.entity_type || 'default';
    const renderer = getRenderer(type);
    return renderer(obj);
  });

  // ─── Context Panel Renderers ───
  const contextRenderers = {};

  function registerContextRenderer(type, fn) {
    contextRenderers[type] = fn;
  }

  function getContextRenderer(type) {
    return contextRenderers[type] || contextRenderers['default'];
  }

  // Default context renderer
  registerContextRenderer('default', function(obj) {
    return `
      <div class="ws-panel">
        <div class="ws-panel-header"><span>Details</span></div>
        <div class="ws-small ws-text-secondary">
          ${obj.entity_id ? `<div class="ws-mb-sm"><strong>ID</strong><br>${obj.entity_id}</div>` : ''}
          ${obj.entity_type ? `<div class="ws-mb-sm"><strong>Type</strong><br>${obj.entity_type}</div>` : ''}
          ${obj.created_at ? `<div class="ws-mb-sm"><strong>Created</strong><br>${new Date(obj.created_at).toLocaleDateString()}</div>` : ''}
        </div>
      </div>
      ${obj.ai_understanding ? `
      <div class="ws-panel">
        <div class="ws-panel-header"><span>SHUNYA Understanding</span></div>
        <div class="ws-small ws-text-secondary">${obj.ai_understanding.summary || 'No understanding yet.'}</div>
      </div>` : ''}
    `;
  });

  // Overview context renderer (Executive Home aware)
  registerContextRenderer('overview', function() {
    const eh = state.executiveHomeData;
    const health = (eh && eh.business_health) || {};
    const brief = (eh && eh.morning_brief) || {summary: {}};
    const s = brief.summary || {};
    return `
      <div class="ws-panel">
        <div class="ws-panel-header"><span>SHUNYA Executive Home</span></div>
        <div class="ws-small ws-text-secondary ws-mb-sm">
          <div class="ws-mb-sm">· ${s.active_spaces || 0} spaces</div>
          <div class="ws-mb-sm">· ${s.active_objects || 0} objects</div>
          <div class="ws-mb-sm">· ${s.pending_conversations || 0} conversations</div>
          <div class="ws-mb-sm">· Pipeline: ${health.pipeline_status || 'unknown'}</div>
          <div class="ws-mb-sm">· ${health.real_runtimes || 0} real runtimes</div>
        </div>
        <div class="ws-small ws-text-secondary" style="border-top: 1px solid var(--ws-border); padding-top: 8px; margin-top: 4px;">
          <div class="ws-mb-sm"><strong>Health</strong></div>
          <div class="ws-mb-xs">· Assessment: ${health.assessment || 'unknown'}</div>
          ${health.warnings && health.warnings.length ? health.warnings.map(function(w) {
            return '<div class="ws-mb-xs">· ⚠ ' + _escapeHtml(w) + '</div>';
          }).join('') : '<div class="ws-mb-xs">· All nominal</div>'}
        </div>
      </div>
      <div class="ws-panel">
        <div class="ws-panel-header"><span>Quick Actions</span></div>
        <div class="ws-flex ws-flex-col ws-gap-sm">
          <button class="ws-btn ws-btn-ghost ws-btn-sm" onclick="WS.navigate('overview')">Executive Home</button>
          <button class="ws-btn ws-btn-ghost ws-btn-sm" onclick="WS.navigate('recent')">Recent Activity</button>
        </div>
      </div>
    `;
  });

  // ─── API ───
  async function apiFetch(path, options = {}) {
    try {
      const resp = await fetch(path, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
      });
      return await resp.json();
    } catch (e) {
      console.error('WS API error:', e);
      return { error: e.message };
    }
  }

  // ─── Load Executive Home Data (v2) ───
  async function loadExecutiveHome() {
    const data = await apiFetch('/api/v1/founder/executive-home-v2');
    if (data && data.success) {
      state.executiveHomeData = data.data;
    }
  }

  // ─── Load Pipeline Data (Legacy) ───
  async function loadPipelineData() {
    const homeData = await apiFetch('/api/v1/founder/executive-home');
    if (homeData && homeData.success) {
      state.pipelineData = homeData.data;
    }
    const healthData = await apiFetch('/api/v1/founder/pipeline/health');
    if (healthData && healthData.success) {
      state.pipelineHealth = healthData.data;
    }
    const tracesData = await apiFetch('/api/v1/founder/pipeline/traces');
    if (tracesData && tracesData.success) {
      state.pipelineTraces = tracesData.data || [];
    }
  }

  // ─── Load Spaces ───
  async function loadSpaces() {
    const data = await apiFetch('/api/v1/founder/spaces');
    if (data && data.success) {
      state.spaces = data.data || [];
      renderRail();
    }
  }

  // ─── Render Rail Items ───
  function renderRail() {
    const el = document.getElementById('ws-rail-items-objects');
    if (!el) {
      // Fallback to legacy rail
      const legacy = document.getElementById('ws-object-list');
      if (!legacy) return;
      _renderRailLegacy(legacy);
      return;
    }
    const types = {};
    state.spaces.forEach(s => {
      const t = s.space_type || 'space';
      if (!types[t]) types[t] = [];
      types[t].push(s);
    });
    let html = '';
    Object.keys(types).sort().forEach(type => {
      const label = type.charAt(0).toUpperCase() + type.slice(1) + 's';
      html += `<div class="ws-rail-section">${label}</div>`;
      types[type].forEach(s => {
        html += `<button class="ws-rail-item" data-view="space" data-id="${s.space_id}" onclick="WS.navigate('space', '${s.space_id}')">
          <span class="ws-rail-dot" style="background: var(--ws-gold);"></span>
          ${s.name}
          <span class="ws-rail-count">${s.object_count || 0}</span>
        </button>`;
      });
    });
    el.innerHTML = html;
  }

  function _renderRailLegacy(el) {
    const types = {};
    state.spaces.forEach(s => {
      const t = s.space_type || 'space';
      if (!types[t]) types[t] = [];
      types[t].push(s);
    });
    let html = '';
    Object.keys(types).sort().forEach(type => {
      const label = type.charAt(0).toUpperCase() + type.slice(1) + 's';
      html += `<div class="ws-rail-section">${label}</div>`;
      types[type].forEach(s => {
        html += `<button class="ws-rail-item" data-view="object" data-id="${s.space_id}" onclick="WS.navigate('object', '${s.space_id}')">
          <span class="ws-rail-dot" style="background: var(--ws-gold);"></span>
          ${s.name}
          <span class="ws-rail-count">${s.object_count || 0}</span>
        </button>`;
      });
    });
    el.innerHTML = html;
  }

  // ─── Navigation ───
  async function navigate(view, id) {
    state.currentView = view;

    // Update active rail item
    document.querySelectorAll('.ws-rail-item').forEach(el => el.classList.remove('active'));
    const target = document.querySelector(`.ws-rail-item[data-view="${view}"]${id ? `[data-id="${id}"]` : ''}`);
    if (target) target.classList.add('active');

    // Update breadcrumb
    const breadcrumb = document.getElementById('ws-breadcrumb');
    const title = document.getElementById('ws-main-title');
    const content = document.getElementById('ws-main-content');
    if (!content) return;

    // Show loading
    content.innerHTML = `<div class="ws-loading"><div class="ws-loading-spinner"></div><span class="ws-small">Loading...</span></div>`;

    if (view === 'overview') {
      breadcrumb.innerHTML = '<span>SHUNYA</span><span class="sep">/</span><span>Executive Home</span>';
      title.textContent = 'Executive Home';
      await Promise.all([loadSpaces(), loadExecutiveHome()]);
      content.innerHTML = renderers['overview']();
      renderContext('overview');
      closeMobilePanels();
      return;
    }

    if (view === 'recent') {
      breadcrumb.innerHTML = '<span>SHUNYA</span><span class="sep">/</span><span>Recent Activity</span>';
      title.textContent = 'Recent Activity';
      if (!state.executiveHomeData) {
        await loadExecutiveHome();
      }
      content.innerHTML = renderers['recent']();
      renderContext('overview');
      closeMobilePanels();
      return;
    }

    if (view === 'object' && id) {
      const data = await apiFetch('/api/v1/founder/focus/' + id);
      if (data && data.success) {
        const obj = data.data;
        state.currentObject = obj;
        breadcrumb.innerHTML = `<span onclick="WS.navigate('overview')">SHUNYA</span><span class="sep">/</span><span>${_escapeHtml(obj.object ? obj.object.name : 'Object')}</span>`;
        title.textContent = obj.object ? obj.object.name : 'Object';
        content.innerHTML = _renderObjectView(obj);
        renderContextForObject(obj);
        addToRecent(obj.object || obj);
        closeMobilePanels();
      } else {
        content.innerHTML = `<div class="ws-empty"><div class="ws-empty-icon">◈</div><div class="ws-empty-title">Object not found</div></div>`;
      }
      return;
    }

    if (view === 'space' && id) {
      const data = await apiFetch('/api/v1/founder/spaces/' + id);
      if (data && data.success) {
        const space = data.data;
        // Load objects in this space
        const objData = await apiFetch('/api/v1/founder/spaces/' + id + '/objects');
        const objects = (objData && objData.success) ? objData.data : [];
        breadcrumb.innerHTML = `<span onclick="WS.navigate('overview')">SHUNYA</span><span class="sep">/</span><span>${_escapeHtml(space.name || 'Space')}</span>`;
        title.textContent = space.name || 'Space';
        content.innerHTML = _renderSpaceView(space, objects);
        renderContext('overview');
        closeMobilePanels();
      } else {
        content.innerHTML = `<div class="ws-empty"><div class="ws-empty-icon">◈</div><div class="ws-empty-title">Space not found</div></div>`;
      }
      return;
    }
  }

  function _renderObjectView(obj) {
    const o = obj.object || {};
    const messages = obj.messages || [];
    const space = obj.space || {};
    const relationships = obj.relationships || [];
    const aiUnderstanding = obj.ai_understanding || '';

    let html = `
      <div class="ws-h2 ws-mb-md">${_escapeHtml(o.name || 'Object')}</div>
      <div class="ws-flex ws-gap-md ws-mb-md ws-small ws-text-secondary">
        <span>Type: ${_escapeHtml(o.object_type || 'unknown')}</span>
        ${space.name ? `<span>Space: ${_escapeHtml(space.name)}</span>` : ''}
        <span>Created: ${o.created_at ? new Date(o.created_at).toLocaleDateString() : 'unknown'}</span>
      </div>
      ${o.content ? `<div class="ws-panel ws-mb-md"><div class="ws-panel-header"><span>Content</span></div><div class="ws-body ws-small">${_escapeHtml(o.content)}</div></div>` : ''}
      ${aiUnderstanding ? `<div class="ws-panel ws-mb-md"><div class="ws-panel-header"><span>SHUNYA Understanding</span></div><div class="ws-body ws-small ws-text-secondary">${_escapeHtml(aiUnderstanding)}</div></div>` : ''}
      ${relationships.length ? `<div class="ws-panel ws-mb-md"><div class="ws-panel-header"><span>Related Objects</span></div><div class="ws-list">${relationships.map(function(r) {
        return `<div class="ws-list-item" onclick="WS.navigate('object', '${r.object_id}')" style="cursor:pointer;">
          <div class="ws-list-item-content">
            <div class="ws-list-item-title">${_escapeHtml(r.name)}</div>
            <div class="ws-list-item-subtitle">${_escapeHtml(r.type || '')} · ${_escapeHtml(r.relationship || '')}</div>
          </div>
        </div>`;
      }).join('')}</div></div>` : ''}
      <div class="ws-panel">
        <div class="ws-panel-header"><span>Conversation</span></div>
        <div class="ws-body ws-small">
          ${messages.length ? messages.map(function(m) {
            return `<div class="ws-mb-sm"><strong>${m.role === 'human' ? 'You' : 'SHUNYA'}:</strong> ${_escapeHtml(m.content)}</div>`;
          }).join('') : '<div class="ws-text-tertiary">No conversation yet. Start one by asking SHUNYA about this object.</div>'}
        </div>
      </div>
    `;
    return html;
  }

  function _renderSpaceView(space, objects) {
    let html = `
      <div class="ws-h2 ws-mb-md">${_escapeHtml(space.name || 'Space')}</div>
      <div class="ws-flex ws-gap-md ws-mb-md ws-small ws-text-secondary">
        <span>Type: ${_escapeHtml(space.space_type || 'space')}</span>
        <span>Objects: ${objects.length}</span>
      </div>
      ${objects.length ? `<div class="ws-h3 ws-mb-sm">Objects</div><div class="ws-list">${objects.map(function(o) {
        return `<div class="ws-list-item" onclick="WS.navigate('object', '${o.object_id}')" style="cursor:pointer;">
          <div class="ws-list-item-content">
            <div class="ws-list-item-title">${_escapeHtml(o.name)}</div>
            <div class="ws-list-item-subtitle">${_escapeHtml(o.object_type || 'Document')}</div>
          </div>
          <div class="ws-list-item-meta">${o.updated_at ? _timeAgo(o.updated_at) : ''}</div>
        </div>`;
      }).join('')}</div>` : '<div class="ws-empty"><div class="ws-empty-icon">◇</div><div class="ws-empty-text">No objects in this space yet.</div></div>'}
    `;
    return html;
  }

  // ─── Context Engine ───
  function renderContext(type) {
    const el = document.getElementById('ws-context-body');
    if (!el) return;
    const renderer = getContextRenderer(type);
    el.innerHTML = renderer(state.currentObject || {});
  }

  async function renderContextForObject(obj) {
    const el = document.getElementById('ws-context-body');
    if (!el) return;
    const o = obj.object || {};
    if (o.space_id) {
      const data = await apiFetch('/api/v1/founder/spaces/' + o.space_id);
      if (data && data.success) {
        el.innerHTML = getContextRenderer('default')(data.data);
        return;
      }
    }
    el.innerHTML = getContextRenderer('default')(o);
  }

  // ─── Recent Objects ───
  function addToRecent(obj) {
    const key = obj.object_id || obj.space_id;
    if (!key) return;
    state.recentObjects = state.recentObjects.filter(function(r) {
      return (r.object_id || r.space_id) !== key;
    });
    state.recentObjects.unshift(obj);
    if (state.recentObjects.length > 20) state.recentObjects.pop();
  }

  // ─── Search ───
  async function search(query) {
    const el = document.getElementById('ws-object-list');
    if (!query.trim()) {
      renderRail();
      return;
    }
    const data = await apiFetch('/api/v1/founder/search?q=' + encodeURIComponent(query));
    if (!el) return;
    if (data && data.success && data.data) {
      el.innerHTML = data.data.map(function(r) {
        const id = r.object_id || r.space_id || '';
        return `<button class="ws-rail-item" data-view="object" data-id="${id}" onclick="WS.navigate('object', '${id}')">
          <span class="ws-rail-dot" style="background: var(--ws-gold);"></span>
          ${_escapeHtml(r.name)}
          <span class="ws-rail-count">${_escapeHtml(r.object_type || r._type || '')}</span>
        </button>`;
      }).join('') || '<div class="ws-small ws-text-center ws-p-md">No results</div>';
    }
  }

  // ─── Mobile Toggle ───
  function toggleRail() {
    const rail = document.getElementById('ws-rail');
    const overlay = document.getElementById('ws-rail-overlay');
    if (!rail) return;
    const open = rail.classList.toggle('open');
    if (overlay) overlay.classList.toggle('open', open);
  }

  function toggleContext() {
    const ctx = document.getElementById('ws-context');
    const overlay = document.getElementById('ws-context-overlay');
    if (!ctx) return;
    const open = ctx.classList.toggle('open');
    if (overlay) overlay.classList.toggle('open', open);
  }

  function closeMobilePanels() {
    const rail = document.getElementById('ws-rail');
    const ctx = document.getElementById('ws-context');
    const railOverlay = document.getElementById('ws-rail-overlay');
    const ctxOverlay = document.getElementById('ws-context-overlay');
    if (rail) rail.classList.remove('open');
    if (ctx) ctx.classList.remove('open');
    if (railOverlay) railOverlay.classList.remove('open');
    if (ctxOverlay) ctxOverlay.classList.remove('open');
  }

  // ─── User Menu ───
  function toggleUserMenu() {
    const menu = document.getElementById('ws-user-menu');
    if (menu) {
      menu.remove();
    } else {
      const div = document.createElement('div');
      div.id = 'ws-user-menu';
      div.style.cssText = 'position:fixed;top:52px;right:12px;background:var(--ws-surface);border:1px solid var(--ws-border);border-radius:var(--ws-radius-sm);padding:8px;z-index:50;box-shadow:var(--ws-shadow-md);min-width:160px;';
      div.innerHTML = `
        <div class="ws-small ws-p-md ws-text-secondary" style="border-bottom:1px solid var(--ws-border);margin-bottom:4px;">${_escapeHtml(state.userName)}</div>
        <button class="ws-btn ws-btn-ghost ws-btn-sm" style="width:100%;justify-content:flex-start;" onclick="window.location.href='/founder/logout'">Sign Out</button>
      `;
      document.body.appendChild(div);
      document.addEventListener('click', function(e) {
        if (!div.contains(e.target) && e.target.id !== 'ws-avatar') {
          div.remove();
        }
      }, { once: true });
    }
  }

  // ─── Command Input ───
  function setupCommandInput() {
    const input = document.getElementById('ws-command');
    if (!input) return;
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        const val = this.value.trim().toLowerCase();
        if (!val) return;
        this.value = '';
        if (val === 'overview' || val === 'home') {
          navigate('overview');
        } else if (val === 'recent' || val === 'activity') {
          navigate('recent');
        } else {
          document.getElementById('ws-rail-search-input').value = val;
          search(val);
          toggleRail();
        }
      }
    });
    document.addEventListener('keydown', function(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        input.focus();
      }
    });
  }

  // ─── Init ───
  async function init(config) {
    Object.assign(state, config);
    setupCommandInput();
    await loadSpaces();
    navigate('overview');
  }

  // ─── Public API ───
  return {
    init,
    navigate,
    search,
    toggleRail,
    toggleContext,
    toggleUserMenu,
    registerRenderer,
    registerContextRenderer,
    state,
  };
})();