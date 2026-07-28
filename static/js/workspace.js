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
    insightData: null,
    selectedInsight: null,
    timelineData: null,
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
      var oid = f.object_id || f.space_id || '';
      var o = oid ? _navHandler(f.type || 'object', oid) : '';
      var icon = e.type === 'space_created' ? '\u25C8' : e.type === 'object_created' ? '\u25C7' : '\uD83D\uDCAC';
      return '<div class="eh-item" ' + o + '>' +
        '<span class="eh-item-dot eh-dot-info"></span>' +
        '<div class="eh-item-content"><div class="eh-item-title">' + icon + ' ' + _escapeHtml(e.title) + '</div>' +
        '<div class="eh-item-meta">' + _escapeHtml(e.detail || '') + ' \u00B7 ' + _timeAgo(e.timestamp) + '</div></div>' +
        (oid ? '<span class="eh-item-action">Open</span>' : '') + '</div>';
    }).join('');
  }

  function openInsight(insightId) {
    var allInsights = (state.insightData && state.insightData.insights) || [];
    var ins = allInsights.find(function(i) { return i.id === insightId; });
    if (!ins) {
      var aq = (state.insightData && state.insightData.attention_queue) || {};
      ['urgent','recommendations','information'].forEach(function(k) {
        (aq[k] || []).forEach(function(i) { if (i.id === insightId) ins = i; });
      });
    }
    state.selectedInsight = ins;
    if (!ins) return;

    var content = document.getElementById('ws-main-content');
    var title = document.getElementById('ws-main-title');
    var breadcrumb = document.getElementById('ws-breadcrumb');
    if (!content) return;

    breadcrumb.innerHTML = '<span onclick="WS.navigate(\'overview\')">SHUNYA</span><span class="sep">/</span><span>Insight</span>';
    title.textContent = ins.title;

    var ev = ins.evidence || {};
    var oid = ev.object_id || '';
    var oClick = oid ? _navHandler('object', oid) : '';
    var lifeBtns = ins.lifecycle === 'active'
      ? '<div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;">' +
        '<button class="ws-btn ws-btn-ghost ws-btn-sm" onclick="WS.updateInsightLifecycle(\'' + ins.id + '\',\'acknowledge\')">Acknowledge</button>' +
        '<button class="ws-btn ws-btn-ghost ws-btn-sm" onclick="WS.updateInsightLifecycle(\'' + ins.id + '\',\'resolve\')">Resolve</button>' +
        '<button class="ws-btn ws-btn-ghost ws-btn-sm" onclick="WS.updateInsightLifecycle(\'' + ins.id + '\',\'dismiss\')">Dismiss</button>' +
        (oid ? '<button class="ws-btn ws-btn-gold ws-btn-sm" ' + oClick + '>View Evidence</button>' : '') +
        '</div>'
      : '<div class="eh-health-assessment" style="margin-top:8px;">Lifecycle: ' + ins.lifecycle + '</div>';

    content.innerHTML = '<div class="eh-container">' +
      '<div class="eh-panel"><div class="eh-panel-header"><span>What happened</span></div>' +
      '<div class="eh-items"><div class="eh-item" style="cursor:default;"><div class="eh-item-content"><div class="eh-item-title">' + _escapeHtml(ins.what || ins.title) + '</div></div></div></div></div>' +
      '<div class="eh-panel"><div class="eh-panel-header"><span>Why this matters</span></div>' +
      '<div class="eh-items"><div class="eh-item" style="cursor:default;"><div class="eh-item-content"><div class="eh-item-meta" style="font-size:13px;color:var(--ws-text-secondary);">' + _escapeHtml(ins.why || '') + '</div></div></div></div></div>' +
      '<div class="eh-panel"><div class="eh-panel-header"><span>Evidence</span>' + (ev.object_name ? '<span class="ws-tiny ws-text-faint">' + _escapeHtml(ev.object_name) + '</span>' : '') + '</div>' +
      '<div class="eh-items"><div class="ws-small ws-p-sm ws-text-secondary"><pre style="font-family:var(--ws-font-mono);font-size:11px;white-space:pre-wrap;">' + _escapeHtml(JSON.stringify(ev, null, 2)) + '</pre></div></div></div>' +
      '<div class="eh-panel"><div class="eh-panel-header"><span>Next Steps</span></div>' +
      '<div class="eh-items">' + (ins.next_steps || []).map(function(ns) {
        return '<div class="eh-item" onclick="window.location.href=\'' + ns.target + '\'"><span class="eh-item-dot eh-dot-info"></span><div class="eh-item-content"><div class="eh-item-title">' + _escapeHtml(ns.label) + '</div></div><span class="eh-item-action">\u2192</span></div>';
      }).join('') + '</div></div>' +
      '<div class="eh-panel"><div class="eh-panel-header"><span>Details</span></div>' +
      '<div class="eh-items"><div class="ws-small ws-p-sm ws-text-secondary">' +
      '<div>Type: ' + ins.type + '</div><div>Priority: ' + ins.priority + ' (' + ins.priority_score + ')</div>' +
      '<div>Queue: ' + ins.queue + '</div><div>Lifecycle: ' + ins.lifecycle + '</div><div>ID: ' + ins.id + '</div>' +
      '</div></div>' + lifeBtns + '</div></div>';

    var ctx = document.getElementById('ws-context-body');
    if (ctx) ctx.innerHTML = '<div class="ws-panel"><div class="ws-panel-header"><span>Insight</span></div><div class="ws-small ws-text-secondary ws-p-sm">' +
      '<div class="ws-mb-sm"><strong>Type</strong><br>' + ins.type + '</div>' +
      '<div class="ws-mb-sm"><strong>Priority</strong><br>' + ins.priority + '</div>' +
      '<div class="ws-mb-sm"><strong>Queue</strong><br>' + ins.queue + '</div>' +
      '<div class="ws-mb-sm"><strong>Lifecycle</strong><br>' + ins.lifecycle + '</div></div></div>';
  }

  function updateInsightLifecycle(insightId, action) {
    apiFetch('/api/v1/founder/insights/' + insightId + '/lifecycle', {method:'POST', body:JSON.stringify({action:action})})
      .then(function() { navigate('overview'); });
  }

  // ─── Executive Home Overview Renderer ───
  registerRenderer('overview', function() {
    var eh = state.executiveHomeData;
    if (!eh) return '<div class="ws-loading"><div class="ws-loading-spinner"></div><span class="ws-small">Loading Executive Home...</span></div>';

    var brief = eh.morning_brief || {items:[], summary:{}};
    var recommendations = eh.recommendations || [];
    var health = eh.business_health || {assessment:'unknown'};
    var activity = eh.recent_activity || [];
    var cw = eh.continue_working || [];
    var s = brief.summary || {};
    var insightSummary = (state.insightData && state.insightData.summary) || {total_insights:0};

    function itemsPanel(title, items, subtitle) {
      if (!items.length) return '';
      return '<div class="eh-panel"><div class="eh-panel-header"><span>' + title + '</span>' +
        (subtitle ? '<span class="ws-tiny ws-text-faint">' + subtitle + '</span>' : '') + '</div><div class="eh-items">' + items + '</div></div>';
    }

    // ═══ Morning Brief ═══
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

    // ═══ Executive Intelligence ═══
    var insightPanel = '<div class="eh-panel"><div class="eh-panel-header"><span>Executive Intelligence</span>' +
      '<span class="ws-tiny ws-text-faint">' + insightSummary.total_insights + ' insight' + (insightSummary.total_insights !== 1 ? 's' : '') + '</span></div>' +
      '<div class="eh-items">' + (state.insightData ? _renderAttentionQueue(state.insightData.attention_queue) : '<div class="ws-loading"><div class="ws-loading-spinner"></div></div>') + '</div></div>';

    // ═══ Recommendations ═══
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
    var recPanel = recItems ? '<div class="eh-panel"><div class="eh-panel-header"><span>Recommendations</span>' +
      (recommendations.length ? '<span class="ws-tiny ws-text-faint">' + recommendations.length + ' item' + (recommendations.length !== 1 ? 's' : '') + '</span>' : '') + '</div><div class="eh-items">' + recItems + '</div></div>' : '';

    // ═══ Business Health ═══
    var healthPanel = '<div class="eh-panel"><div class="eh-panel-header"><span>Business Health</span><span class="ws-badge ' +
      (health.assessment === 'running' ? 'ws-badge-success' : health.assessment === 'attention_needed' ? 'ws-badge-warning' : 'ws-badge-default') + '">' + health.assessment + '</span></div>' +
      '<div class="eh-health-row">' +
      '<div class="eh-health-stat"><div class="eh-health-stat-value">' + (health.spaces || 0) + '</div><div class="eh-health-stat-label">Spaces</div></div>' +
      '<div class="eh-health-stat"><div class="eh-health-stat-value">' + (health.objects || 0) + '</div><div class="eh-health-stat-label">Objects</div></div>' +
      '<div class="eh-health-stat"><div class="eh-health-stat-value">' + (health.relationships || 0) + '</div><div class="eh-health-stat-label">Relationships</div></div>' +
      '<div class="eh-health-stat"><div class="eh-health-stat-value">' + (health.active_conversations || 0) + '</div><div class="eh-health-stat-label">Conversations</div></div>' +
      '<div class="eh-health-stat"><div class="eh-health-stat-value">' + (health.real_runtimes || 0) + '</div><div class="eh-health-stat-label">Real Runtimes</div></div>' +
      '</div>' +
      ((health.warnings || []).length ? '<div class="eh-health-warning">' + health.warnings.map(function(w) { return '<div>\u26A0 ' + _escapeHtml(w) + '</div>'; }).join('') + '</div>' : '') +
      '<div class="eh-health-assessment">Pipeline: ' + (health.pipeline_status || 'unknown') + (health.mock_runtimes ? ' \u00B7 ' + health.mock_runtimes + ' mock' : '') + '</div></div>';

    // ═══ Recent Activity ═══
    var actItems = activity.map(function(a) {
      var f = a.focus || {};
      var oid = f.object_id;
      var o = oid ? _navHandler('object', oid) : '';
      var icon = a.type === 'object_created' ? '\u25C7' : a.type === 'object_updated' ? '\u270E' : '\uD83D\uDCAC';
      return '<div class="eh-item" ' + o + '>' +
        '<span class="eh-item-dot eh-dot-info"></span>' +
        '<div class="eh-item-content"><div class="eh-item-title">' + icon + ' ' + _escapeHtml(a.title) + '</div>' +
        '<div class="eh-item-meta">' + _escapeHtml(a.subtitle || '') + '</div></div>' +
        (oid ? '<span class="eh-item-action">Open</span>' : '') + '</div>';
    }).join('');
    var actPanel = itemsPanel('Recent Activity', actItems, activity.length + ' item' + (activity.length !== 1 ? 's' : '')) ||
      '<div class="eh-panel"><div class="eh-panel-header"><span>Recent Activity</span></div><div class="eh-items"><div class="eh-empty"><div class="eh-empty-icon">\uD83D\uDCCB</div><div class="eh-empty-text">No recent activity.</div></div></div></div>';

    // ═══ Continue Working ═══
    var cwItems = cw.map(function(item) {
      var f = item.focus || {};
      var oid = f.object_id;
      var o = oid ? _navHandler('object', oid) : '';
      var icon = item.type === 'object' ? '\u25C7' : '\uD83D\uDCAC';
      return '<div class="eh-cw-card" ' + o + '>' +
        '<div class="eh-cw-icon">' + icon + '</div>' +
        '<div class="eh-cw-content"><div class="eh-cw-title">' + _escapeHtml(item.title) + '</div>' +
        '<div class="eh-cw-subtitle">' + _escapeHtml(item.subtitle || '') + '</div></div>' +
        (item.meta ? '<span class="eh-cw-meta">' + _escapeHtml(item.meta) + '</span>' : '') +
        '<span class="eh-item-action">Open</span></div>';
    }).join('');
    var cwPanel = itemsPanel('Continue Working', cwItems, cw.length + ' item' + (cw.length !== 1 ? 's' : '')) ||
      '<div class="eh-panel"><div class="eh-panel-header"><span>Continue Working</span></div><div class="eh-items"><div class="eh-empty"><div class="eh-empty-icon">\u25C8</div><div class="eh-empty-text">Nothing to resume.</div></div></div></div>';

    // ═══ Timeline ═══
    var timelineItems = state.timelineData ? _renderTimeline(state.timelineData) : '';
    var timelinePanel = timelineItems ? '<div class="eh-panel"><div class="eh-panel-header"><span>Timeline</span></div><div class="eh-items">' + timelineItems + '</div></div>' : '';

    return '<div class="eh-container">' + insightPanel + briefPanel + recPanel + healthPanel + actPanel + cwPanel + timelinePanel + '</div>';
  });

  // ─── Recent Activity Renderer ───
  registerRenderer('recent', function() {
    var eh = state.executiveHomeData;
    var activity = (eh && eh.recent_activity) || [];
    var html = '<div class="ws-h2 ws-mb-lg">Recent Activity</div>';
    if (activity.length) {
      html += activity.map(function(a) {
        var f = a.focus || {};
        var oid = f.object_id;
        var o = oid ? _navHandler('object', oid) : '';
        var icon = a.type === 'object_created' ? '\u25C7' : a.type === 'object_updated' ? '\u270E' : '\uD83D\uDCAC';
        return '<div class="ws-card ws-mb-sm" style="cursor:pointer;" ' + o + '>' +
          '<div class="ws-card-header"><span class="ws-card-title">' + icon + ' ' + _escapeHtml(a.title) + '</span>' +
          '<span class="ws-badge ws-badge-default">' + _escapeHtml(a.subtitle || '') + '</span></div></div>';
      }).join('');
    } else {
      html += '<div class="eh-empty"><div class="eh-empty-icon">\uD83D\uDCCB</div><div class="eh-empty-text">No recent activity.</div></div>';
    }
    return html;
  });

  // ─── Object Renderer ───
  registerRenderer('object', function(obj) {
    return (getRenderer(obj.entity_type || 'default'))(obj);
  });

  // ─── Context Panel ───
  const contextRenderers = {};

  function registerContextRenderer(type, fn) { contextRenderers[type] = fn; }

  function getContextRenderer(type) { return contextRenderers[type] || contextRenderers['default']; }

  registerContextRenderer('default', function(obj) {
    var o = obj.object || obj;
    return '<div class="ws-panel"><div class="ws-panel-header"><span>Details</span></div><div class="ws-small ws-text-secondary">' +
      (o.object_id ? '<div class="ws-mb-sm"><strong>ID</strong><br>' + o.object_id + '</div>' : '') +
      (o.name ? '<div class="ws-mb-sm"><strong>Name</strong><br>' + _escapeHtml(o.name) + '</div>' : '') +
      (o.object_type ? '<div class="ws-mb-sm"><strong>Type</strong><br>' + o.object_type + '</div>' : '') +
      (o.created_at ? '<div class="ws-mb-sm"><strong>Created</strong><br>' + new Date(o.created_at).toLocaleDateString() + '</div>' : '') +
      '</div></div>';
  });

  registerContextRenderer('overview', function() {
    var eh = state.executiveHomeData;
    var health = (eh && eh.business_health) || {};
    var brief = (eh && eh.morning_brief) || {summary:{}};
    var s = brief.summary || {};
    return '<div class="ws-panel"><div class="ws-panel-header"><span>SHUNYA Executive Home</span></div><div class="ws-small ws-text-secondary ws-mb-sm">' +
      '<div class="ws-mb-sm">\u00B7 ' + (s.active_spaces || 0) + ' spaces</div>' +
      '<div class="ws-mb-sm">\u00B7 ' + (s.active_objects || 0) + ' objects</div>' +
      '<div class="ws-mb-sm">\u00B7 ' + (s.pending_conversations || 0) + ' conversations</div>' +
      '<div class="ws-mb-sm">\u00B7 Pipeline: ' + (health.pipeline_status || 'unknown') + '</div>' +
      '<div class="ws-mb-sm">\u00B7 ' + (health.real_runtimes || 0) + ' real runtimes</div>' +
      '</div><div class="ws-small ws-text-secondary" style="border-top:1px solid var(--ws-border);padding-top:8px;margin-top:4px;">' +
      '<div class="ws-mb-sm"><strong>Health</strong></div>' +
      '<div class="ws-mb-xs">\u00B7 Assessment: ' + (health.assessment || 'unknown') + '</div>' +
      ((health.warnings || []).length ? health.warnings.map(function(w) { return '<div class="ws-mb-xs">\u00B7 \u26A0 ' + _escapeHtml(w) + '</div>'; }).join('') : '<div class="ws-mb-xs">\u00B7 All nominal</div>') +
      '</div></div>' +
      '<div class="ws-panel"><div class="ws-panel-header"><span>Quick Actions</span></div>' +
      '<div class="ws-flex ws-flex-col ws-gap-sm">' +
      '<button class="ws-btn ws-btn-ghost ws-btn-sm" onclick="WS.navigate(\'overview\')">Executive Home</button>' +
      '<button class="ws-btn ws-btn-ghost ws-btn-sm" onclick="WS.navigate(\'recent\')">Recent Activity</button>' +
      '</div></div>';
  });

  // ─── API ───
  async function apiFetch(path, options) {
    if (!options) options = {};
    try {
      var resp = await fetch(path, {headers:{'Content-Type':'application/json', ...options.headers}, ...options});
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
    document.querySelectorAll('.ws-rail-item').forEach(function(el) { el.classList.remove('active'); });
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
      var data = await apiFetch('/api/v1/founder/focus/' + id);
      if (data && data.success) {
        var obj = data.data;
        state.currentObject = obj;
        var o = obj.object || {};
        breadcrumb.innerHTML = '<span onclick="WS.navigate(\'overview\')">SHUNYA</span><span class="sep">/</span><span>' + _escapeHtml(o.name || 'Object') + '</span>';
        title.textContent = o.name || 'Object';
        content.innerHTML = _renderObjectView(obj);
        renderContextForObject(obj);
        addToRecent(o);
        closeMobilePanels();
      } else {
        content.innerHTML = '<div class="ws-empty"><div class="ws-empty-icon">\u25C8</div><div class="ws-empty-title">Object not found</div></div>';
      }
      return;
    }

    if (view === 'space' && id) {
      var data = await apiFetch('/api/v1/founder/spaces/' + id);
      if (data && data.success) {
        var space = data.data;
        var od = await apiFetch('/api/v1/founder/spaces/' + id + '/objects');
        var objects = (od && od.success) ? od.data : [];
        breadcrumb.innerHTML = '<span onclick="WS.navigate(\'overview\')">SHUNYA</span><span class="sep">/</span><span>' + _escapeHtml(space.name || 'Space') + '</span>';
        title.textContent = space.name || 'Space';
        content.innerHTML = _renderSpaceView(space, objects);
        renderContext('overview');
        closeMobilePanels();
      } else {
        content.innerHTML = '<div class="ws-empty"><div class="ws-empty-icon">\u25C8</div><div class="ws-empty-title">Space not found</div></div>';
      }
      return;
    }
  }

  function _renderObjectView(obj) {
    var o = obj.object || {};
    var messages = obj.messages || [];
    var space = obj.space || {};
    var ai = obj.ai_understanding || '';
    var html = '<div class="ws-h2 ws-mb-md">' + _escapeHtml(o.name || 'Object') + '</div>' +
      '<div class="ws-flex ws-gap-md ws-mb-md ws-small ws-text-secondary">' +
      '<span>Type: ' + _escapeHtml(o.object_type || 'unknown') + '</span>' +
      (space.name ? '<span>Space: ' + _escapeHtml(space.name) + '</span>' : '') +
      '<span>Created: ' + (o.created_at ? new Date(o.created_at).toLocaleDateString() : 'unknown') + '</span></div>' +
      (o.content ? '<div class="ws-panel ws-mb-md"><div class="ws-panel-header"><span>Content</span></div><div class="ws-body ws-small">' + _escapeHtml(o.content) + '</div></div>' : '') +
      (ai ? '<div class="ws-panel ws-mb-md"><div class="ws-panel-header"><span>SHUNYA Understanding</span></div><div class="ws-body ws-small ws-text-secondary">' + _escapeHtml(ai) + '</div></div>' : '');
    if (obj.relationships && obj.relationships.length) {
      html += '<div class="ws-panel ws-mb-md"><div class="ws-panel-header"><span>Related Objects</span></div><div class="ws-list">' +
        obj.relationships.map(function(r) {
          return '<div class="ws-list-item" onclick="WS.navigate(\'object\',\'' + r.object_id + '\')" style="cursor:pointer;">' +
            '<div class="ws-list-item-content"><div class="ws-list-item-title">' + _escapeHtml(r.name) + '</div>' +
            '<div class="ws-list-item-subtitle">' + _escapeHtml(r.type || '') + ' \u00B7 ' + _escapeHtml(r.relationship || '') + '</div></div></div>';
        }).join('') + '</div></div>';
    }
    html += '<div class="ws-panel"><div class="ws-panel-header"><span>Conversation</span></div><div class="ws-body ws-small">' +
      (messages.length ? messages.map(function(m) {
        return '<div class="ws-mb-sm"><strong>' + (m.role === 'human' ? 'You' : 'SHUNYA') + ':</strong> ' + _escapeHtml(m.content) + '</div>';
      }).join('') : '<div class="ws-text-tertiary">No conversation yet.</div>') + '</div></div>';
    return html;
  }

  function _renderSpaceView(space, objects) {
    var html = '<div class="ws-h2 ws-mb-md">' + _escapeHtml(space.name || 'Space') + '</div>' +
      '<div class="ws-flex ws-gap-md ws-mb-md ws-small ws-text-secondary">' +
      '<span>Type: ' + _escapeHtml(space.space_type || 'space') + '</span>' +
      '<span>Objects: ' + objects.length + '</span></div>';
    if (objects.length) {
      html += '<div class="ws-h3 ws-mb-sm">Objects</div><div class="ws-list">' +
        objects.map(function(o) {
          return '<div class="ws-list-item" onclick="WS.navigate(\'object\',\'' + o.object_id + '\')" style="cursor:pointer;">' +
            '<div class="ws-list-item-content"><div class="ws-list-item-title">' + _escapeHtml(o.name) + '</div>' +
            '<div class="ws-list-item-subtitle">' + _escapeHtml(o.object_type || 'Document') + '</div></div>' +
            '<div class="ws-list-item-meta">' + _timeAgo(o.updated_at) + '</div></div>';
        }).join('') + '</div>';
    } else {
      html += '<div class="ws-empty"><div class="ws-empty-icon">\u25C7</div><div class="ws-empty-text">No objects yet.</div></div>';
    }
    return html;
  }

  // ─── Context ───
  function renderContext(type) {
    var el = document.getElementById('ws-context-body');
    if (!el) return;
    el.innerHTML = getContextRenderer(type)(state.currentObject || {});
  }

  async function renderContextForObject(obj) {
    var el = document.getElementById('ws-context-body');
    if (!el) return;
    var o = obj.object || {};
    if (o.space_id) {
      var data = await apiFetch('/api/v1/founder/spaces/' + o.space_id);
      if (data && data.success) { el.innerHTML = getContextRenderer('default')(data.data); return; }
    }
    el.innerHTML = getContextRenderer('default')(o);
  }

  function addToRecent(obj) {
    var key = obj.object_id || obj.space_id;
    if (!key) return;
    state.recentObjects = state.recentObjects.filter(function(r) { return (r.object_id || r.space_id) !== key; });
    state.recentObjects.unshift(obj);
    if (state.recentObjects.length > 20) state.recentObjects.pop();
  }

  // ─── Search ───
  async function search(query) {
    var el = document.getElementById('ws-object-list');
    if (!query.trim()) { renderRail(); return; }
    var data = await apiFetch('/api/v1/founder/search?q=' + encodeURIComponent(query));
    if (!el || !data || !data.success || !data.data) { if (el) el.innerHTML = '<div class="ws-small ws-text-center ws-p-md">No results</div>'; return; }
    el.innerHTML = data.data.map(function(r) {
      return '<button class="ws-rail-item" data-view="object" data-id="' + (r.object_id || '') + '" onclick="WS.navigate(\'object\',\'' + (r.object_id || '') + '\')">' +
        '<span class="ws-rail-dot" style="background:var(--ws-gold);"></span>' + _escapeHtml(r.name) +
        '<span class="ws-rail-count">' + _escapeHtml(r.object_type || r._type || '') + '</span></button>';
    }).join('');
  }

  // ─── Mobile ───
  function toggleRail() {
    var rail = document.getElementById('ws-rail');
    if (!rail) return;
    var open = rail.classList.toggle('open');
    var overlay = document.getElementById('ws-rail-overlay');
    if (overlay) overlay.classList.toggle('open', open);
  }

  function toggleContext() {
    var ctx = document.getElementById('ws-context');
    if (!ctx) return;
    var open = ctx.classList.toggle('open');
    var overlay = document.getElementById('ws-context-overlay');
    if (overlay) overlay.classList.toggle('open', open);
  }

  function closeMobilePanels() {
    ['ws-rail','ws-context','ws-rail-overlay','ws-context-overlay'].forEach(function(id) {
      var el = document.getElementById(id);
      if (el) el.classList.remove('open');
    });
  }

  // ─── User Menu ───
  function toggleUserMenu() {
    var menu = document.getElementById('ws-user-menu');
    if (menu) { menu.remove(); return; }
    var div = document.createElement('div');
    div.id = 'ws-user-menu';
    div.style.cssText = 'position:fixed;top:52px;right:12px;background:var(--ws-surface);border:1px solid var(--ws-border);border-radius:var(--ws-radius-sm);padding:8px;z-index:50;box-shadow:var(--ws-shadow-md);min-width:160px;';
    div.innerHTML = '<div class="ws-small ws-p-md ws-text-secondary" style="border-bottom:1px solid var(--ws-border);margin-bottom:4px;">' + _escapeHtml(state.userName) + '</div>' +
      '<button class="ws-btn ws-btn-ghost ws-btn-sm" style="width:100%;justify-content:flex-start;" onclick="window.location.href=\'/founder/logout\'">Sign Out</button>';
    document.body.appendChild(div);
    document.addEventListener('click', function(e) {
      if (!div.contains(e.target) && e.target.id !== 'ws-avatar') div.remove();
    }, {once:true});
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
    openInsight,
    updateInsightLifecycle,
    state,
  };
})();