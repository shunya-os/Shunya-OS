/** Action Bar — renders context actions from metadata. */

import { useState, useEffect } from 'react';
import type { ActionDef } from './types';
import { getActions } from './api';

interface ActionBarProps {
  typeKey: string;
}

export function ActionBar({ typeKey }: ActionBarProps) {
  const [actions, setActions] = useState<ActionDef[]>([]);
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState<ActionDef | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    loadActions();
  }, [typeKey]);

  async function loadActions() {
    setLoading(true);
    setError('');
    try {
      const acts = await getActions(typeKey);
      setActions(acts);
    } catch (err: any) {
      setError(err.message || 'Failed to load actions');
    }
    setLoading(false);
  }

  async function executeAction(action: ActionDef) {
    setError('');
    try {
      const endpoint: string = action.endpoint || `/api/ubme/actions/${typeKey}/execute`;
      await fetch(endpoint, {
        method: action.method || 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });
      setConfirming(null);
    } catch (err: any) {
      setError(err.message || 'Action failed');
      setConfirming(null);
    }
  }

  function handleClick(action: ActionDef) {
    if (action.requires_confirmation) {
      setConfirming(action);
    } else {
      executeAction(action);
    }
  }

  if (loading) return <div className="ubme-loading">Loading actions...</div>;

  return (
    <div className="ubme-action-bar" style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
      {actions.map((action) => (
        <button
          key={action.key}
          className="ubme-btn-secondary"
          onClick={() => handleClick(action)}
          title={action.endpoint}
          style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}
        >
          <span>{action.icon}</span>
          <span>{action.label}</span>
        </button>
      ))}

      {actions.length === 0 && !error && (
        <span style={{ color: '#64748b', fontSize: '0.8rem' }}>No actions available</span>
      )}

      {error && <div className="ubme-error">{error}</div>}

      {/* Confirmation Dialog */}
      {confirming && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            style={{
              background: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '0.75rem',
              padding: '1.5rem',
              maxWidth: '400px',
              width: '90%',
            }}
          >
            <h4 style={{ margin: '0 0 0.75rem', color: '#fff' }}>
              {confirming.icon} {confirming.label}
            </h4>
            <p style={{ margin: '0 0 1.25rem', color: '#94a3b8', fontSize: '0.85rem' }}>
              Are you sure you want to perform this action?
            </p>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
              <button className="ubme-btn-secondary" onClick={() => setConfirming(null)}>
                Cancel
              </button>
              <button
                className="ubme-btn-primary"
                style={{ background: '#ef4444' }}
                onClick={() => executeAction(confirming)}
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
