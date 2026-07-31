/* =========================================================================
   SHUNYA Phase B1 — Universal Workspace Engine
   =========================================================================
   The workspace engine renders different object types without changing
   page architecture. The context engine dynamically updates the right
   panel based on the active object.
   ========================================================================= */
(function() {

  'use strict';

  console.log('WS: IIFE executing...');

  // ─── State ───
  var state = {
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
    insightData: null,
    selectedInsight: null,
    timelineData: null,
  };

  // ─── Object Renderers ───
  var renderers = {};

  function registerRenderer(type, fn) {
    renderers[type] = fn;
  }

  function getRenderer(type) {
    return renderers[type] || renderers['default'];
  }

  // ─── Default Renderer ───
  registerRenderer('default', function(obj) {
    return '<div class="ws-card"><div class="ws-card-header"><span class="ws-card-title">' + (obj.name || 'Object') + '</span><span class="ws-badge ws-badge-gold">' + (obj.entity_type || 'unknown') + '</span></div>' +
      '<div class="ws-body ws-text-secondary ws-mb-sm">' +
      (obj.entity_id ? '<div>ID: ' + obj.entity_id + '</div>' : '') +
      (obj.entity_type ? '<div>Type: ' + obj.entity_type + '</div>' : '') +
      '</div></div>';
  });

  // ─── Helpers ───
  function _escapeHtml(s) { if (!s) return ''; return String(s).replace(/[&<>"']/g, function(c) { return '&#' + c.charCodeAt(0) + ';'; }); }

  function _timeAgo(ts) {
    if (!ts) return '';
    var diff = Date.now() - new Date(ts).getTime();
    var mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return mins + 'm ago';
    var hours = Math.floor(mins / 60);
    if (hours < 24) return hours + 'h ago';
    return Math.floor(hours / 24) + 'd ago';
  }

  function _prioDot(p) { var m = {urgent:'high',high:'high',medium:'medium',low:'low',info:'info',warning:'warning'}; return 'eh-dot-' + (m[p] || 'info'); }

  function _navHandler(type, id) { return 'onclick="WS.navigate(\'' + type + '\',\'' + id + '\')"'; }

  // ─── Insight renderers ───
  function _renderAttentionQueue(aq) {
    if (!aq) return '<div class="eh-empty"><div class="eh-empty-text">No insights yet.</div></div>';
    var html = '';
    var sections = [
      {key:'urgent', label:'Urgent', icon:'❗'},
      {key:'recommendations', label:'Recommendations', icon:'✦'},
      {key:'information', label:'Information', icon:'ℹ'},
    ];
    sections.forEach(function(s) {
      var items = aq[s.key] || [];
      if (!items.length) return;
      html += '<div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:var(--ws-text-tertiary);padding:8px 0 2px;">' + s.icon + ' ' + s.label + ' (' + items.length + ')</div>';
      items.slice(0, 3).forEach(function(ins) {
        var oid = (ins.evidence || {}).object_id || '';
        var onclick = oid ? 'onclick="WS.openInsight(\'' + ins.id + '\')"' : '';
        html += '<div class="eh-item" ' + onclick + '>' +
          '<span class="eh-item-dot ' + _prioDot(ins.priority) + '"></span>' +
          '<div class="eh-item-content"><div class="eh-item-title">' + _escapeHtml(ins.title) + '</div>' +
          '<div class="eh-item-meta">' + _escapeHtml((ins.why || '').slice(0, 80)) + '</div></div>' +
          '<span class="eh-item-action">Explain</span></div>';
      });
      if (items.length > 3) html += '<div class="ws-tiny ws-text-faint ws-p-sm" style="text-align:center;">+' + (items.length - 3) + ' more</div>';
    });
    if (!html) html = '<div class="eh-empty"><div class="eh-empty-icon">\uD83E\uDDE0</div><div class="eh-empty-text">SHUNYA is analyzing your business. Insights will appear as patterns emerge.</div></div>';
    return html;
  }

  function _renderTimeline(tl) {
    if (!tl || !tl.length) return '<div class="eh-empty"><div class="eh-empty-icon">\uD83D\uDCC5</div><div class="eh-empty-text">Timeline will populate as you work.</div></div>';
    return tl.map(function(e) {
      var f = e.focus || {};
      var oid = f.object_id;
      var o = oid ? _navHandler(f.type || 'object', oid) : '';
      return '<div class="eh-item" ' + o + '>' +
        '<span class="eh-item-dot ' + _prioDot(e.priority) + '"></span>' +
        '<div class="eh-item-content"><div class="eh-item-title">' + _escapeHtml(e.title) + '</div>' +
        (e.detail ? '<div class="eh-item-meta">' + _escapeHtml(e.detail) + '</div>' : '') + '</div>' +
        '<span class="eh-item-time">' + _timeAgo(e.occurred_at) + '</span></div>';
    }).join('');
  }

  // ─── Overview renderer ───
  registerRenderer('overview', function() {
    var eh = state.executiveHomeData;
    if (!eh) return '<div class="ws-loading"><div class="ws-loading-spinner"></div><span class="ws-small">Loading Executive Home...</span></div>';

    var org = eh.organization || {};
    var brief = eh.morning_brief || {items:[], summary:{}};
    var recommendations = eh.recommendations || [];
    var health = eh.business_health || {assessment:'unknown'};
    var activity = eh.recent_activity || [];
    var cw = eh.continue_working || [];
    var s = brief.summary || {};
    var insightSummary = (state.insightData && state.insightData.summary) || {total_insights:0};

    // Organization greeting
    var orgGreeting = '';
    if (org.org_name) {
      orgGreeting = '<div style="padding: var(--ws-space-md) 0; border-bottom: 1px solid var(--ws-border); margin-bottom: var(--ws-space-md);">' +
        '<div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--ws-gold);">' + _escapeHtml(org.org_name) + '</div>' +
        (org.org_tagline ? '<div style="font-size: 13px; color: var(--ws-text-tertiary); margin-top: 2px;">' + _escapeHtml(org.org_tagline) + '</div>' : '') +
        '</div>';
    }

    function itemsPanel(title, items, subtitle) {
      if (!items.length) return '';
      return '<div class="eh-panel"><div class="eh-panel-header"><span>' + title + '</span>' +
        (subtitle ? '<span class="ws-tiny ws-text-faint">' + subtitle + '</span>' : '') + '</div><div class="eh-items">' + items + '</div></div>';
    }

    // Morning Brief
    var briefItems = brief.items.map(function(item) {
      var focus = item.focus || {};
      var oid = focus.object_id;
      var o = oid ? _navHandler(focus.type || 'object', oid) : '';
      return '<div class="eh-item" ' + o + '>' +
        '<span class="eh-item-dot ' + _prioDot(item.priority) + '"></span>' +
        '<div class="eh-item-content"><div class="eh-item-title">' + _escapeHtml(item.title) + '</div>' +
        (item.meta ? '<div class="eh-item-meta">' + _escapeHtml(item.meta) + '</div>' : '') + '</div>' +
        (oid ? '<span class="eh-item-action">Open</span>' : '') + '</div>';
    }).join('');

    var briefPanel = '<div class="eh-panel"><div class="eh-panel-header"><span>Morning Brief</span>' +
      (s.active_spaces > 0 ? '<span class="ws-tiny ws-text-faint">' + s.active_spaces + ' space' + (s.active_spaces !== 1 ? 's' : '') + '</span>' : '') + '</div>' +
      (s.active_objects !== undefined ? '<div class="eh-panel-subtitle">' + s.active_objects + ' object' + (s.active_objects !== 1 ? 's' : '') + ' \u00B7 ' + s.pending_conversations + ' conversation' + (s.pending_conversations !== 1 ? 's' : '') + ' \u00B7 ' + s.recent_activity + ' recent</div>' : '') +
      '<div class="eh-items">' + (briefItems || '<div class="eh-empty"><div class="eh-empty-icon">\u2600</div><div class="eh-empty-text">Everything is quiet.</div></div>') + '</div></div>';

    // Executive Intelligence
    var insightPanel = '<div class="eh-panel"><div class="eh-panel-header"><span>Executive Intelligence</span>' +
      '<span class="ws-tiny ws-text-faint">' + insightSummary.total_insights + ' insight' + (insightSummary.total_insights !== 1 ? 's' : '') + '</span></div>' +
      '<div class="eh-items">' + (state.insightData ? _renderAttentionQueue(state.insightData.attention_queue) : '<div class="ws-loading"><div class="ws-loading-spinner"></div></div>') + '</div></div>';

    // Recommendations
    var recItems = recommendations.map(function(rec) {
      var target = (rec.action || {}).target || '#';
      var label = (rec.action || {}).label || 'Open';
      var o = target !== '#' ? 'onclick="window.location.href=\'' + target + '\'"' : '';
      return '<div class="eh-rec-card eh-priority-' + rec.priority + '" ' + o + '>' +
        '<div class="eh-rec-title">' + _escapeHtml(rec.title) + '</div>' +
        '<div class="eh-rec-explanation">' + _escapeHtml(rec.explanation) + '</div>' +
        '<div class="eh-rec-why">' + _escapeHtml(rec.why) + '</div>' +
        '<div class="eh-rec-footer"><span class="eh-rec-runtime">' + _escapeHtml(rec.originating_runtime || 'kernel') + '</span><span class="eh-rec-action">' + label + ' \u2192</span></div></div>';
    }).join('');

    // Continue Working
    var cwItems = cw.map(function(item) {
      var target = (item.action || {}).target || (item.focus ? '/' + item.focus.type + '/' + item.focus.id : '#');
      return '<div class="eh-item" onclick="window.location.href=\'' + target + '\'">' +
        '<span class="eh-item-dot ' + _prioDot(item.priority) + '"></span>' +
        '<div class="eh-item-content"><div class="eh-item-title">' + _escapeHtml(item.title) + '</div>' +
        (item.meta ? '<div class="eh-item-meta">' + _escapeHtml(item.meta) + '</div>' : '') + '</div>' +
        '<span class="eh-item-action">Continue</span></div>';
    }).join('');

    // Business Health
    var healthBadge = health.assessment === 'cold_start' ? 'ws-badge-info' : health.assessment === 'healthy' ? 'ws-badge-success' : 'ws-badge-warning';
    var healthPanel = '<div class="eh-panel"><div class="eh-panel-header"><span>Business Health</span>' +
      '<span class="ws-badge ' + healthBadge + '">' + health.assessment + '</span></div>' +
      (health.warnings && health.warnings.length ? '<div class="eh-items">' + health.warnings.map(function(w) {
        return '<div class="eh-item"><span class="eh-item-dot eh-dot-warning"></span><div class="eh-item-content"><div class="eh-item-title">' + _escapeHtml(w) + '</div></div></div>';
      }).join('') + '</div>' : '<div class="eh-items"><div class="eh-empty"><div class="eh-empty-icon">\u2705</div><div class="eh-empty-text">All systems nominal.</div></div></div>') + '</div>';

    // Assemble
    return orgGreeting + briefPanel + recItems + cwItems + insightPanel + healthPanel;
  });

  // ─── Recent Activity ───
  registerRenderer('recent', function() {
    var eh = state.executiveHomeData;
    if (!eh) return '';
    var activity = eh.recent_activity || [];
    var timeline = state.timelineData || [];
    if (!activity.length && !timeline.length) return '<div class="eh-empty"><div class="eh-empty-icon">\uD83D\uDD0D</div><div class="eh-empty-text">No activity yet. Start working with SHUNYA to see your timeline.</div></div>';

    var html = '<div class="eh-panel"><div class="eh-panel-header"><span>Recent Activity</span></div><div class="eh-items">';
    if (activity.length) {
      activity.forEach(function(a) {
        html += '<div class="eh-item">' +
          '<span class="eh-item-dot ' + _prioDot(a.priority) + '"></span>' +
          '<div class="eh-item-content"><div class="eh-item-title">' + _escapeHtml(a.title) + '</div>' +
          (a.detail ? '<div class="eh-item-meta">' + _escapeHtml(a.detail) + '</div>' : '') + '</div>' +
          '<span class="eh-item-time">' + _timeAgo(a.occurred_at) + '</span></div>';
      });
    }
    html += '</div></div>';
    return html;
  });

  // ─── Context Renderers ───
  var contextRenderers = {};

  function registerContextRenderer(type, fn) {
    contextRenderers[type] = fn;
  }

  function renderContext(type) {
    var el = document.getElementById('ws-context-content');
    if (!el) return;
    var fn = contextRenderers[type] || contextRenderers['default'];
    if (fn) el.innerHTML = fn();
    state.contextPanel = type;
  }

  registerContextRenderer('overview', function() {
    var eh = state.executiveHomeData;
    if (!eh) return '<div class="ws-loading"><div class="ws-loading-spinner"></div></div>';
    var health = eh.business_health || {};

    return '<div class="ws-context-section"><div class="ws-context-section-title">Pipeline Health</div>' +
      (health.pipeline_status ? '<div class="ws-context-stat"><span class="ws-context-stat-label">Status</span><span class="ws-context-stat-value ws-status-' + health.pipeline_status + '">' + health.pipeline_status + '</span></div>' : '') +
      (health.real_runtimes !== undefined ? '<div class="ws-context-stat"><span class="ws-context-stat-label">Real runtimes</span><span class="ws-context-stat-value">' + health.real_runtimes + '</span></div>' : '') +
      (health.mock_runtimes !== undefined ? '<div class="ws-context-stat"><span class="ws-context-stat-label">Mock runtimes</span><span class="ws-context-stat-value">' + health.mock_runtimes + '</span></div>' : '') +
      (health.objects !== undefined ? '<div class="ws-context-stat"><span class="ws-context-stat-label">Objects</span><span class="ws-context-stat-value">' + health.objects + '</span></div>' : '') +
      (health.spaces !== undefined ? '<div class="ws-context-stat"><span class="ws-context-stat-label">Spaces</span><span class="ws-context-stat-value">' + health.spaces + '</span></div>' : '') +
      (health.relationships !== undefined ? '<div class="ws-context-stat"><span class="ws-context-stat-label">Relationships</span><span class="ws-context-stat-value">' + health.relationships + '</span></div>' : '') +
      '</div>' +
      '<div class="ws-context-section"><div class="ws-context-section-title">Quick Actions</div>' +
      '<button class="ws-btn ws-btn-ghost ws-btn-sm" onclick="WS.navigate(\'overview\')">Executive Home</button>' +
      '<button class="ws-btn ws-btn-ghost ws-btn-sm" onclick="WS.navigate(\'recent\')">Recent Activity</button></div>';
  });

  // ─── API ───
  async function apiFetch(path, options) {
    try {
      var opts = options || {};
      var headers = {'Content-Type':'application/json'};
      if (opts.headers) {
        for (var k in opts.headers) { headers[k] = opts.headers[k]; }
      }
      opts.headers = headers;
      var resp = await fetch(path, opts);
      return await resp.json();
    } catch(e) { console.error('WS API error:', e); return {error:e.message}; }
  }

  // ─── Data Loaders ───
  async function loadExecutiveHome() {
    var data = await apiFetch('/api/v1/founder/executive-home-v2');
    if (data && data.success) state.executiveHomeData = data.data;
    var ins = await apiFetch('/api/v1/founder/insights');
    if (ins && ins.success) state.insightData = ins.data;
    var tl = await apiFetch('/api/v1/founder/timeline');
    if (tl && tl.success) state.timelineData = tl.data;
  }

  async function loadPipelineData() {
    var hd = await apiFetch('/api/v1/founder/executive-home');
    if (hd && hd.success) state.pipelineData = hd.data;
    var hl = await apiFetch('/api/v1/founder/pipeline/health');
    if (hl && hl.success) state.pipelineHealth = hl.data;
    var tr = await apiFetch('/api/v1/founder/pipeline/traces');
    if (tr && tr.success) state.pipelineTraces = tr.data || [];
  }

  async function loadSpaces() {
    var data = await apiFetch('/api/v1/founder/spaces');
    if (data && data.success) { state.spaces = data.data || []; renderRail(); }
  }

  // ─── Rail ───
  function renderRail() {
    var el = document.getElementById('ws-rail-items-objects') || document.getElementById('ws-object-list');
    if (!el) return;
    if (!state.spaces.length) { el.innerHTML = ''; return; }
    var types = {};
    state.spaces.forEach(function(s) {
      var t = s.space_type || 'space';
      if (!types[t]) types[t] = [];
      types[t].push(s);
    });
    el.innerHTML = Object.keys(types).sort().map(function(type) {
      var label = type.charAt(0).toUpperCase() + type.slice(1) + 's';
      return '<div class="ws-rail-section">' + label + '</div>' + types[type].map(function(s) {
        return '<button class="ws-rail-item" data-view="space" data-id="' + s.space_id + '" onclick="WS.navigate(\'space\',\'' + s.space_id + '\')">' +
          '<span class="ws-rail-dot" style="background:var(--ws-gold);"></span>' + _escapeHtml(s.name) +
          '<span class="ws-rail-count">' + (s.object_count || 0) + '</span></button>';
      }).join('');
    }).join('');
  }

  // ─── Navigation ───
  async function navigate(view, id) {
    state.currentView = view;
    var railItems = document.querySelectorAll('.ws-rail-item');
    for (var i = 0; i < railItems.length; i++) { railItems[i].classList.remove('active'); }
    var target = document.querySelector('.ws-rail-item[data-view="' + view + '"]' + (id ? '[data-id="' + id + '"]' : ''));
    if (target) target.classList.add('active');

    var breadcrumb = document.getElementById('ws-breadcrumb');
    var title = document.getElementById('ws-main-title');
    var content = document.getElementById('ws-main-content');
    if (!content) return;
    content.innerHTML = '<div class="ws-loading"><div class="ws-loading-spinner"></div><span class="ws-small">Loading...</span></div>';

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
      if (!state.executiveHomeData) await loadExecutiveHome();
      content.innerHTML = renderers['recent']();
      renderContext('overview');
      closeMobilePanels();
      return;
    }

    if (view === 'object' && id) {
      var data = await apiFetch('/api/v1/founder/workspace/' + id);
      if (data && data.success) {
        var wsData = data.data;
        state.currentObject = wsData;
        var summary = wsData.summary || {};
        breadcrumb.innerHTML = '<span onclick="WS.navigate(\'overview\')">SHUNYA</span><span class="sep">/</span><span class="ws-breadcrumb-obj">' + _escapeHtml(summary.name || 'Object') + '</span>';
        title.textContent = summary.name || 'Object';
        content.innerHTML = _renderM4Workspace(wsData);
        _renderM4Context(wsData);
        addToRecent(summary);
        closeMobilePanels();
      } else {
        content.innerHTML = '<div class="ws-empty"><div class="ws-empty-icon">\u25C8</div><div class="ws-empty-title">Object not found</div></div>';
      }
      return;
    }

    if (view === 'space' && id) {
      var data = await apiFetch('/api/v1/founder/spaces/' + id);
      if (data && data.success) {
        var sp = data.data;
        state.currentObject = sp;
        breadcrumb.innerHTML = '<span onclick="WS.navigate(\'overview\')">SHUNYA</span><span class="sep">/</span><span>' + _escapeHtml(sp.name || 'Space') + '</span>';
        title.textContent = sp.name || 'Space';
        content.innerHTML = _renderSpace(sp);
        renderContext('overview');
        closeMobilePanels();
      } else {
        content.innerHTML = '<div class="ws-empty"><div class="ws-empty-icon">\u25C8</div><div class="ws-empty-title">Space not found</div></div>';
      }
      return;
    }

    // Fallback
    breadcrumb.innerHTML = '<span>SHUNYA</span><span class="sep">/</span><span>Unknown</span>';
    title.textContent = 'Not Found';
    content.innerHTML = '<div class="ws-empty"><div class="ws-empty-icon">\u2753</div><div class="ws-empty-text">Page not found.</div></div>';
  }

  function closeMobilePanels() {
    var els = document.querySelectorAll('.ws-rail-open, .ws-context-open');
    for (var i = 0; i < els.length; i++) { els[i].classList.remove('ws-rail-open', 'ws-context-open'); }
  }

  // ─── Command Input ───
  function setupCommandInput() {
    var input = document.getElementById('ws-command');
    if (!input) return;
    input.addEventListener('keydown', function(e) {
      if (e.key !== 'Enter') return;
      var val = this.value.trim().toLowerCase();
      this.value = '';
      if (!val) return;
      if (val === 'overview' || val === 'home') { navigate('overview'); }
      else if (val === 'recent' || val === 'activity') { navigate('recent'); }
      else { var si = document.getElementById('ws-rail-search-input'); if (si) si.value = val; search(val); toggleRail(); }
    });
    document.addEventListener('keydown', function(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); if (input) input.focus(); }
    });
  }

  // ─── Init ───
  async function init(config) {
    if (config) {
      for (var k in config) { state[k] = config[k]; }
    }
    setupCommandInput();
    await loadSpaces();
    navigate('overview');
  }

  // ─── Stub functions (to be replaced by app.js) ───
  function search(q) { console.log('WS.search:', q); }
  function toggleRail() { document.querySelector('.ws-app')?.classList.toggle('ws-rail-hidden'); }
  function toggleContext() { document.querySelector('.ws-app')?.classList.toggle('ws-context-hidden'); }
  function toggleUserMenu() { /* stub */ }
  function openInsight(id) { console.log('WS.openInsight:', id); }
  function updateInsightLifecycle(id, status) { console.log('WS.updateInsightLifecycle:', id, status); }
  function addToRecent(obj) { /* stub */ }
  function _renderM4Workspace(data) { return '<div class="ws-empty"><div class="ws-empty-icon">\u25C8</div><div class="ws-empty-text">Workspace view coming soon</div></div>'; }
  function _renderM4Context(data) { /* stub */ }
  function _renderSpace(sp) { return '<div class="ws-empty"><div class="ws-empty-text">' + _escapeHtml(sp.name || 'Space') + '</div></div>'; }

  // ─── Public API ───
  window.WS = {
    init: init,
    navigate: navigate,
    search: search,
    toggleRail: toggleRail,
    toggleContext: toggleContext,
    toggleUserMenu: toggleUserMenu,
    registerRenderer: registerRenderer,
    registerContextRenderer: registerContextRenderer,
    openInsight: openInsight,
    updateInsightLifecycle: updateInsightLifecycle,
    state: state,
  };

  console.log('WS: initialized successfully');
})();