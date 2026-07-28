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
  };

  // ─── Object Renderers ───
  // Extensible registry — add new renderers for any object type
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

  // ─── Overview Renderer ───
  registerRenderer('overview', function() {
    const recent = state.recentObjects.slice(0, 5);
    const spaces = state.spaces.slice(0, 8);
    return `
      <div class="ws-h2 ws-mb-lg">Overview</div>
      ${spaces.length ? `
      <div class="ws-panel">
        <div class="ws-panel-header"><span>Objects</span></div>
        <div class="ws-list">
          ${spaces.map(s => `
            <div class="ws-list-item" onclick="WS.navigate('object', '${s.space_id}')">
              <div class="ws-list-item-icon" style="background: var(--ws-gold-glow);">◈</div>
              <div class="ws-list-item-content">
                <div class="ws-list-item-title">${s.name}</div>
                <div class="ws-list-item-subtitle">${s.entity_type}</div>
              </div>
              <div class="ws-list-item-meta">${s.relationship_count || 0} rel</div>
            </div>
          `).join('')}
        </div>
      </div>` : `
      <div class="ws-empty">
        <div class="ws-empty-icon">◈</div>
        <div class="ws-empty-title">Welcome to SHUNYA</div>
        <div class="ws-empty-text">Your workspace is ready. Objects will appear here as you use SHUNYA.</div>
      </div>`}
      ${recent.length ? `
      <div class="ws-panel">
        <div class="ws-panel-header"><span>Recent Activity</span></div>
        <div class="ws-list">
          ${recent.map(r => `
            <div class="ws-list-item">
              <div class="ws-list-item-content">
                <div class="ws-list-item-title">${r.name}</div>
                <div class="ws-list-item-subtitle">${r.entity_type}</div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>` : ''}
    `;
  });

  // ─── Recent Activity Renderer ───
  registerRenderer('recent', function() {
    return `
      <div class="ws-h2 ws-mb-lg">Recent Activity</div>
      ${state.recentObjects.length ? state.recentObjects.map(r => `
        <div class="ws-card ws-mb-sm" style="cursor:pointer;" onclick="WS.navigate('object', '${r.space_id}')">
          <div class="ws-card-header">
            <span class="ws-card-title">${r.name}</span>
            <span class="ws-badge ws-badge-default">${r.entity_type}</span>
          </div>
        </div>
      `).join('') : `
      <div class="ws-empty">
        <div class="ws-empty-icon">📋</div>
        <div class="ws-empty-title">No recent activity</div>
        <div class="ws-empty-text">Activity will appear as you interact with SHUNYA.</div>
      </div>`}
    `;
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

  // Overview context renderer
  registerContextRenderer('overview', function() {
    return `
      <div class="ws-panel">
        <div class="ws-panel-header"><span>SHUNYA</span></div>
        <div class="ws-small ws-text-secondary ws-mb-sm">
          The workspace is ready. All systems nominal.
        </div>
        <div class="ws-small ws-text-secondary">
          <div class="ws-mb-sm">· ${state.spaces.length} objects available</div>
          <div class="ws-mb-sm">· ${state.recentObjects.length} recently viewed</div>
        </div>
      </div>
      <div class="ws-panel">
        <div class="ws-panel-header"><span>Quick Actions</span></div>
        <div class="ws-flex ws-flex-col ws-gap-sm">
          <button class="ws-btn ws-btn-ghost ws-btn-sm" onclick="WS.navigate('overview')">Overview</button>
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

  // ─── Load Spaces ───
  async function loadSpaces() {
    const data = await apiFetch(state.spaceApiUrl);
    if (data && data.spaces) {
      state.spaces = data.spaces;
      renderRail();
    }
  }

  // ─── Render Rail Items ───
  function renderRail() {
    const el = document.getElementById('ws-object-list');
    if (!el) return;
    const types = {};
    state.spaces.forEach(s => {
      if (!types[s.entity_type]) types[s.entity_type] = [];
      types[s.entity_type].push(s);
    });
    let html = '';
    Object.keys(types).sort().forEach(type => {
      html += `<div class="ws-rail-section">${type.charAt(0).toUpperCase() + type.slice(1)}s</div>`;
      types[type].forEach(s => {
        html += `<button class="ws-rail-item" data-view="object" data-id="${s.space_id}" onclick="WS.navigate('object', '${s.space_id}')">
          <span class="ws-rail-dot" style="background: var(--ws-gold);"></span>
          ${s.name}
          <span class="ws-rail-count">${s.relationship_count || 0}</span>
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
      breadcrumb.innerHTML = '<span>SHUNYA</span><span class="sep">/</span><span>Overview</span>';
      title.textContent = 'Welcome';
      await loadSpaces();
      content.innerHTML = renderers['overview']();
      renderContext('overview');
      closeMobilePanels();
      return;
    }

    if (view === 'recent') {
      breadcrumb.innerHTML = '<span>SHUNYA</span><span class="sep">/</span><span>Recent Activity</span>';
      title.textContent = 'Recent Activity';
      content.innerHTML = renderers['recent']();
      renderContext('overview');
      closeMobilePanels();
      return;
    }

    if (view === 'object' && id) {
      const data = await apiFetch(`${state.spaceApiUrl}/${id}/summary`);
      if (data && data.summary) {
        const obj = data.summary;
        state.currentObject = obj;
        breadcrumb.innerHTML = `<span onclick="WS.navigate('overview')">SHUNYA</span><span class="sep">/</span><span>${obj.name}</span>`;
        title.textContent = obj.name;
        content.innerHTML = renderers['object'](obj);
        renderContextForObject(obj);
        addToRecent(obj);
        closeMobilePanels();
      } else {
        content.innerHTML = `<div class="ws-empty"><div class="ws-empty-icon">◈</div><div class="ws-empty-title">Object not found</div></div>`;
      }
      return;
    }
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
    // Try to load full Space data for context panel
    const data = await apiFetch(`${state.spaceApiUrl}/${obj.space_id}`);
    if (data && data.space) {
      const full = data.space;
      el.innerHTML = getContextRenderer('default')(full);
    } else {
      el.innerHTML = getContextRenderer('default')(obj);
    }
  }

  // ─── Recent Objects ───
  function addToRecent(obj) {
    state.recentObjects = state.recentObjects.filter(r => r.space_id !== obj.space_id);
    state.recentObjects.unshift(obj);
    if (state.recentObjects.length > 20) state.recentObjects.pop();
  }

  // ─── Search ───
  async function search(query) {
    if (!query.trim()) {
      renderRail();
      return;
    }
    const data = await apiFetch(`${state.spaceApiUrl}/search?q=${encodeURIComponent(query)}`);
    const el = document.getElementById('ws-object-list');
    if (!el) return;
    if (data && data.results) {
      el.innerHTML = data.results.map(r => `
        <button class="ws-rail-item" data-view="object" data-id="${r.space_id}" onclick="WS.navigate('object', '${r.space_id}')">
          <span class="ws-rail-dot" style="background: var(--ws-gold);"></span>
          ${r.name}
          <span class="ws-rail-count">${r.entity_type}</span>
        </button>
      `).join('') || '<div class="ws-small ws-text-center ws-p-md">No results</div>';
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
    // Simple menu — could be extended
    const menu = document.getElementById('ws-user-menu');
    if (menu) {
      menu.remove();
    } else {
      const div = document.createElement('div');
      div.id = 'ws-user-menu';
      div.style.cssText = 'position:fixed;top:52px;right:12px;background:var(--ws-surface);border:1px solid var(--ws-border);border-radius:var(--ws-radius-sm);padding:8px;z-index:50;box-shadow:var(--ws-shadow-md);min-width:160px;';
      div.innerHTML = `
        <div class="ws-small ws-p-md ws-text-secondary" style="border-bottom:1px solid var(--ws-border);margin-bottom:4px;">${state.userName}</div>
        <button class="ws-btn ws-btn-ghost ws-btn-sm" style="width:100%;justify-content:flex-start;" onclick="window.location.href='/settings'">Settings</button>
        <button class="ws-btn ws-btn-ghost ws-btn-sm" style="width:100%;justify-content:flex-start;" onclick="window.location.href='/logout'">Logout</button>
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
          // Search for object
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