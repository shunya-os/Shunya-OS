/**
 * SHUNYA LX-01 — Main Canonical Living Workspace
 *
 * There is exactly one SHUNYA Workspace.
 * There is exactly one set of production runtimes.
 *
 * Permanent Build Mode — implementing SCU-01 capabilities.
 */
import { useState, useEffect, useCallback, type FC } from 'react';
import { useLivingStore } from './living-store';
import { AIPresencePanel } from './ai-presence-panel';
import { RealityStream } from './reality-stream';
import { LivingObjectCard } from './living-object-card';
import { CommandSurface } from './command-surface';
import { ExecutiveBriefing } from './executive-briefing';
import { subscribeSSE } from '../../runtimes/sse-runtime';
import { UniversalObjectWorkspace } from './universal-object-workspace';

// ── Create Object Modal ────────────────────────────────────────────

const CreateObjectModal: FC<{ onClose: () => void }> = ({ onClose }) => {
  const [name, setName] = useState('');
  const [type, setType] = useState('proposal');
  const [creating, setCreating] = useState(false);
  const { fetchLivingObjects, fetchReality } = useLivingStore();

  const handleCreate = useCallback(async () => {
    if (!name.trim()) return;
    setCreating(true);
    try {
      const resp = await fetch('/api/v1/composer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          object_type: type,
          name: name.trim(),
          source: 'modal',
        }),
      });
      const json = await resp.json();
      if (json.success) {
        fetchLivingObjects();
        fetchReality();
        onClose();
      }
    } catch (e) {
      console.error('Create object failed:', e);
    } finally {
      setCreating(false);
    }
  }, [name, type, fetchLivingObjects, fetchReality, onClose]);

  return (
    <div className="lw-modal-overlay" onClick={onClose}>
      <div className="lw-modal" onClick={(e) => e.stopPropagation()}>
        <div className="lw-modal-header">
          <h3 className="lw-modal-title">Create New Object</h3>
          <button className="lw-modal-close" onClick={onClose}>×</button>
        </div>
        <div className="lw-modal-body">
          <div className="lw-modal-field">
            <label className="lw-modal-label">Type</label>
            <select className="lw-modal-select" value={type} onChange={(e) => setType(e.target.value)}>
              <option value="proposal">Proposal</option>
              <option value="invoice">Invoice</option>
              <option value="contact">Contact</option>
              <option value="task">Task</option>
              <option value="note">Note</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="lw-modal-field">
            <label className="lw-modal-label">Name</label>
            <input className="lw-modal-input" type="text" value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleCreate(); }}
              placeholder="e.g. Q4 Marketing Proposal" autoFocus />
          </div>
        </div>
        <div className="lw-modal-actions">
          <button className="lw-modal-btn lw-modal-btn-secondary" onClick={onClose}>Cancel</button>
          <button className="lw-modal-btn lw-modal-btn-primary" onClick={handleCreate} disabled={!name.trim() || creating}>
            {creating ? 'Creating...' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ── Session recognition ───────────────────────────────────────────

function markSeen() {
  if (typeof window !== 'undefined') localStorage.setItem('shunya_seen', String(Date.now()));
}

// ── Awakening ──────────────────────────────────────────────────────

const Invitation: FC<{ onAccept: () => void }> = ({ onAccept }) => {
  const [showInput, setShowInput] = useState(false);
  return (
    <div className="lw-invitation">
      {!showInput ? (
        <p className="lw-invitation-text" onClick={() => setShowInput(true)}>
          Would you like to make this yours?
        </p>
      ) : (
        <div className="lw-invitation-input-group">
          <input className="lw-invitation-input" type="email" placeholder="you@example.com" autoFocus
            onKeyDown={(e) => { if (e.key === 'Enter' && (e.target as HTMLInputElement).value) onAccept(); }} />
          <button className="lw-invitation-submit" onClick={onAccept}>Continue</button>
        </div>
      )}
    </div>
  );
};

const TopBar: FC<{ onSearch?: (q: string) => void; onCreateObject?: () => void }> = ({ onSearch, onCreateObject }) => {
  const { lastUpdated, observations, activeExecutions, sidebarCollapsed, toggleSidebar } = useLivingStore();
  const [searchQuery, setSearchQuery] = useState('');
  const fmt = (ts: string) => { try { return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); } catch { return ''; } };

  return (
    <div className="lw-topbar">
      <div className="lw-topbar-left">
        <div className="lw-brand">
          <span className="lw-brand-devanagari">शून्य</span>
          <span className="lw-brand-label">SHUNYA</span>
        </div>
        <div className="lw-topbar-divider" />
        {/* Search input — SCU-01 RM01 */}
        <div className="lw-search">
          <input
            className="lw-search-input"
            type="text"
            placeholder="Search objects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && onSearch) onSearch(searchQuery); }}
          />
        </div>
        <div className="lw-topbar-ai-status">
          <div className="lw-topbar-ai-dot" />
          <span className="lw-topbar-ai-label">
            {activeExecutions.length > 0 ? `Executing ${activeExecutions.length} action${activeExecutions.length !== 1 ? 's' : ''}` : observations.length > 0 ? `${observations.length} insight${observations.length !== 1 ? 's' : ''}` : 'Observing'}
          </span>
        </div>
      </div>
      <div className="lw-topbar-right">
        {/* Create button */}
        {onCreateObject && (
          <button className="lw-topbar-create" onClick={onCreateObject}>+ New</button>
        )}
        <span className="lw-topbar-updated">Updated {fmt(lastUpdated)}</span>
        <button className="lw-topbar-toggle" onClick={toggleSidebar}>
          <span style={{ display: 'inline-block', transform: `rotate(${sidebarCollapsed ? 0 : 180}deg)`, transition: 'transform 0.3s' }}>▸</span>
        </button>
      </div>
    </div>
  );
};

const LivingObjectsSection: FC<{ onCreateObject?: () => void; onOpenWorkspace?: (id: string, type: string, name: string) => void }> = ({ onCreateObject, onOpenWorkspace }) => {
  const { livingObjects, objectsLoading } = useLivingStore();
  return (
    <div className="lw-objects-section">
      <div className="lw-objects-header">
        <h3 className="lw-objects-title">Living Objects</h3>
        <div className="lw-objects-header-right">
          <span className="lw-objects-count">{livingObjects.length} type{livingObjects.length !== 1 ? 's' : ''}</span>
          {onCreateObject && (
            <button className="lw-create-obj-btn" onClick={onCreateObject}>+ Create</button>
          )}
        </div>
      </div>
      <div className="lw-objects-grid">
        {livingObjects.slice(0, 6).map((obj) => <LivingObjectCard key={obj.id} object={obj} onOpenWorkspace={onOpenWorkspace} />)}
      </div>
      {livingObjects.length === 0 && !objectsLoading && (
        <div className="lw-objects-empty">
          <p>No object types detected yet.</p>
          <p className="lw-objects-empty-sub">Create your first object to see it here as a living entity.</p>
          {onCreateObject && (
            <button className="lw-create-obj-btn lw-create-obj-btn-empty" onClick={onCreateObject}>+ Create your first object</button>
          )}
        </div>
      )}
    </div>
  );
};

// ── Main Workspace ─────────────────────────────────────────────────

export const LivingWorkspace: FC = () => {
  const { startPolling, setCommandOpen } = useLivingStore();
  const [arrivalComplete, setArrivalComplete] = useState(false);
  const [searchResults, setSearchResults] = useState<any[] | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [workspaceObject, setWorkspaceObject] = useState<{id: string; type: string; name: string} | null>(null);

  // Mark visit and start production runtimes
  useEffect(() => {
    markSeen();
    const stop = startPolling();
    const sse = subscribeSSE('reality');
    // Transition to arrival complete after a brief moment for returning users
    const t = setTimeout(() => setArrivalComplete(true), 500);
    return () => { stop(); sse.close(); clearTimeout(t); };
  }, [startPolling]);

  // Search handler
  const handleSearch = useCallback(async (q: string) => {
    if (!q.trim()) { setSearchResults(null); return; }
    try {
      const resp = await fetch(`/api/v1/objects?q=${encodeURIComponent(q.trim())}`, { credentials: 'include' });
      const json = await resp.json();
      setSearchResults(json.success ? json.data || [] : []);
    } catch {
      setSearchResults([]);
    }
  }, []);

  // Keyboard shortcut
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); setCommandOpen(true); } };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [setCommandOpen]);

  return (
    <div className="lw-workspace">
      {/* Search results overlay */}
      {searchResults !== null && (
        <div className="lw-search-overlay" onClick={() => setSearchResults(null)}>
          <div className="lw-search-panel" onClick={(e) => e.stopPropagation()}>
            <div className="lw-search-panel-header">
              <span>Search results ({searchResults.length})</span>
              <button onClick={() => setSearchResults(null)}>×</button>
            </div>
            <div className="lw-search-panel-body">
              {searchResults.length === 0 ? (
                <p className="lw-search-empty">No results found.</p>
              ) : (
                searchResults.map((r: any, i: number) => (
                  <div key={r.id || i} className="lw-search-item" onClick={() => setSearchResults(null)}>
                    <span className="lw-search-item-name">{r.name}</span>
                    <span className="lw-search-item-type">{r.object_type}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Create object modal */}
      {showCreateModal && <CreateObjectModal onClose={() => setShowCreateModal(false)} />}

      {/* Universal Object Workspace — same component for all object types */}
      {workspaceObject && (
        <UniversalObjectWorkspace
          objectId={workspaceObject.id}
          objectType={workspaceObject.type}
          objectName={workspaceObject.name}
          onClose={() => setWorkspaceObject(null)}
        />
      )}

      {/* Shunya wordmark — settles to signature */}
      {!arrivalComplete && (
        <div className="lw-wordmark-container">
          <div className="lw-wordmark">
            <span className="lw-wordmark-text" data-text="शून्य">शून्य</span>
          </div>
        </div>
      )}

      {/* TopBar with search and create */ }
      <TopBar onSearch={handleSearch} onCreateObject={() => setShowCreateModal(true)} />

      {/* Main workspace body */}
      <div className="lw-workspace-body">
        <div className="lw-workspace-main">
          <ExecutiveBriefing />
          <RealityStream />
          <LivingObjectsSection onCreateObject={() => setShowCreateModal(true)} onOpenWorkspace={(id, type, name) => setWorkspaceObject({id, type, name})} />
        </div>
        <aside className="lw-workspace-sidebar">
          <AIPresencePanel />
        </aside>
      </div>

      <CommandSurface />
      {arrivalComplete && <Invitation onAccept={() => {}} />}
    </div>
  );
};