/** Dashboard Generator — renders dashboard cards from metadata. */

import React, { useState, useEffect } from 'react';
import type { DashboardCard } from './types';
import { getDashboard } from './api';

interface DashboardGeneratorProps {
  moduleKey: string;
}

export function DashboardGenerator({ moduleKey }: DashboardGeneratorProps) {
  const [cards, setCards] = useState<DashboardCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadCards();
  }, [moduleKey]);

  async function loadCards() {
    setLoading(true);
    setError('');
    try {
      const data = await getDashboard(moduleKey);
      setCards(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    }
    setLoading(false);
  }

  if (loading) return <div className="ubme-loading">Loading dashboard...</div>;

  return (
    <div className="ubme-dashboard" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '1rem' }}>
      {cards.map((card) => (
        <DashboardCardView key={card.key} card={card} />
      ))}

      {cards.length === 0 && !error && (
        <div className="ubme-empty-state" style={{ gridColumn: '1 / -1' }}>
          <div className="ubme-empty-icon">📊</div>
          <h3>No dashboard cards</h3>
          <p>Add cards to the dashboard configuration.</p>
        </div>
      )}

      {error && <div className="ubme-error" style={{ gridColumn: '1 / -1' }}>{error}</div>}
    </div>
  );
}

function DashboardCardView({ card }: { card: DashboardCard }) {
  return (
    <div
      className="ubme-dashboard-card"
      style={{
        background: '#1e293b', border: '1px solid #334155', borderRadius: '0.75rem',
        padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem',
        transition: 'border-color 0.2s',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#6366f1'; }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#334155'; }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontSize: '1.5rem' }}>{card.icon || '📊'}</span>
        <span style={{ color: '#94a3b8', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {card.label}
        </span>
      </div>

      <div style={{ flex: 1 }}>
        {renderCardValue(card)}
      </div>
    </div>
  );
}

function renderCardValue(card: DashboardCard): React.ReactNode {
  switch (card.card_type) {
    case 'count':
      return (
        <div style={{ fontSize: '2rem', fontWeight: 700, color: '#fff' }}>
          {typeof card.value === 'number' ? card.value.toLocaleString() : card.value ?? 0}
        </div>
      );

    case 'sum':
      return (
        <div style={{ fontSize: '1.5rem', fontWeight: 600, color: '#10b981' }}>
          {typeof card.value === 'number' ? `$${card.value.toLocaleString()}` : card.value ?? '$0'}
        </div>
      );

    case 'alert':
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.25rem' }}>🔔</span>
          <span style={{ fontSize: '1.25rem', fontWeight: 600, color: '#fca5a5' }}>
            {typeof card.value === 'number' ? card.value : 0}
          </span>
          <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>alerts</span>
        </div>
      );

    case 'recent':
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
          {(Array.isArray(card.value) ? card.value : []).slice(0, 5).map((item: any) => (
            <div
              key={item.id}
              style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '0.25rem 0', borderBottom: '1px solid #1e293b', fontSize: '0.8rem',
              }}
            >
              <span style={{ color: '#e2e8f0' }}>{item.name || item.id}</span>
              {item.status && (
                <span className={`ubme-status status-${item.status}`}>{item.status}</span>
              )}
            </div>
          ))}
          {(!Array.isArray(card.value) || card.value.length === 0) && (
            <span style={{ color: '#64748b', fontSize: '0.8rem' }}>No recent items</span>
          )}
        </div>
      );

    default:
      return <span style={{ color: '#94a3b8' }}>{String(card.value ?? '—')}</span>;
  }
}