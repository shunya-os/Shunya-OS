/**
 * Operating Context Selector — Shows current operating context (Personal Space / Organization)
 * and allows switching between them.
 *
 * Visually and conceptually separate from object workspace tabs.
 * Answers: "Whose world am I currently operating in?"
 */
import { useState, useEffect, useRef, useCallback } from 'react';

interface OrgInfo {
  org: {
    id: number;
    name: string;
    slug: string;
    logo_url?: string;
    brand_color: string;
    business_type?: string;
  };
  role: string;
  name: string;
}

interface ContextSelectorProps {
  currentOrgId?: number | null;
  onSwitchContext: (orgId: number | null) => void;
}

export function OperatingContextSelector({ currentOrgId, onSwitchContext }: ContextSelectorProps) {
  const [open, setOpen] = useState(false);
  const [orgs, setOrgs] = useState<OrgInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const ref = useRef<HTMLDivElement>(null);

  const currentOrg = orgs.find(o => o.org.id === currentOrgId);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const loadOrgs = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch('/api/v1/for2/whoami', { credentials: 'include' });
      const data = await r.json();
      if (data.organizations) {
        setOrgs(data.organizations);
      }
    } catch {
      // Silently fail — context won't show orgs
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOrgs();
  }, [loadOrgs]);

  return (
    <div ref={ref} className="sh-context-selector">
      <button
        className="sh-context-trigger"
        onClick={() => setOpen(!open)}
        title="Switch operating context"
      >
        {currentOrg ? (
          <>
            <div
              className="sh-context-avatar"
              style={{ background: currentOrg.org.brand_color || '#6C4AE2' }}
            >
              {currentOrg.org.name[0]}
            </div>
            <span className="sh-context-name">{currentOrg.org.name}</span>
          </>
        ) : (
          <>
            <div className="sh-context-avatar sh-context-avatar-personal">S</div>
            <span className="sh-context-name">Personal Space</span>
          </>
        )}
        <span className="sh-context-chevron">▾</span>
      </button>

      {open && (
        <div className="sh-context-dropdown">
          <div className="sh-context-dropdown-header">
            Switch Operating Context
          </div>

          {/* Personal Space option */}
          <button
            className={`sh-context-item ${!currentOrgId ? 'active' : ''}`}
            onClick={() => {
              onSwitchContext(null);
              setOpen(false);
            }}
          >
            <div className="sh-context-item-avatar sh-context-avatar-personal">S</div>
            <div className="sh-context-item-info">
              <div className="sh-context-item-name">Personal Space</div>
              <div className="sh-context-item-meta">Your private workspace</div>
            </div>
            {!currentOrgId && <span className="sh-context-check">✓</span>}
          </button>

          {orgs.length > 0 && <div className="sh-context-divider" />}

          {/* Organization options */}
          {orgs.map(orgInfo => (
            <button
              key={orgInfo.org.id}
              className={`sh-context-item ${currentOrgId === orgInfo.org.id ? 'active' : ''}`}
              onClick={() => {
                onSwitchContext(orgInfo.org.id);
                setOpen(false);
              }}
            >
              <div
                className="sh-context-item-avatar"
                style={{ background: orgInfo.org.brand_color || '#6C4AE2' }}
              >
                {orgInfo.org.name[0]}
              </div>
              <div className="sh-context-item-info">
                <div className="sh-context-item-name">{orgInfo.org.name}</div>
                <div className="sh-context-item-meta">{orgInfo.role} · {orgInfo.org.business_type || 'General'}</div>
              </div>
              {currentOrgId === orgInfo.org.id && <span className="sh-context-check">✓</span>}
            </button>
          ))}

          {loading && (
            <div className="sh-context-loading">Loading...</div>
          )}
        </div>
      )}

      <style>{shContextStyles}</style>
    </div>
  );
}

const shContextStyles = `
.sh-context-selector {
  position: relative;
  flex-shrink: 0;
}
.sh-context-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  border: none;
  border-radius: 8px;
  background: rgba(108, 74, 226, 0.1);
  color: #b8a0ff;
  font-size: 0.8rem;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
}
.sh-context-trigger:hover {
  background: rgba(108, 74, 226, 0.2);
}
.sh-context-avatar {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 600;
  color: #fff;
  flex-shrink: 0;
}
.sh-context-avatar-personal {
  background: #444;
  font-size: 0.65rem;
}
.sh-context-name {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sh-context-chevron {
  font-size: 0.6rem;
  opacity: 0.6;
}
.sh-context-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  min-width: 240px;
  background: #15151f;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  z-index: 1000;
  padding: 6px;
}
.sh-context-dropdown-header {
  padding: 8px 10px;
  font-size: 0.7rem;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.sh-context-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #ccc;
  font-size: 0.85rem;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}
.sh-context-item:hover {
  background: rgba(255, 255, 255, 0.06);
}
.sh-context-item.active {
  background: rgba(108, 74, 226, 0.12);
  color: #b8a0ff;
}
.sh-context-item-avatar {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
  color: #fff;
  flex-shrink: 0;
}
.sh-context-item-info {
  flex: 1;
  min-width: 0;
}
.sh-context-item-name {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sh-context-item-meta {
  font-size: 0.7rem;
  color: #666;
}
.sh-context-check {
  font-size: 0.9rem;
  color: #6C4AE2;
  flex-shrink: 0;
}
.sh-context-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.06);
  margin: 4px 0;
}
.sh-context-loading {
  padding: 12px;
  text-align: center;
  font-size: 0.8rem;
  color: #666;
}
`;