/**
 * MarketingChannels — Channel connector frontends for Meta Ads and Google Ads.
 *
 * Provides the canonical UI for connecting and managing advertising channels.
 * All states: not_connected, connecting, connected, error, configuring.
 * No fake "live" state — connection status is always truthful.
 */

import { useState, type FC } from 'react';

// ── Channel Status Types ──────────────────────────────────────────

type ConnectorState = 'not_connected' | 'connecting' | 'connected' | 'error' | 'configuring';

interface ChannelInfo {
  id: string;
  name: string;
  icon: string;
  description: string;
  status: ConnectorState;
  statusText: string;
  accountName?: string;
  accountId?: string;
}

// ── Shared Styles ─────────────────────────────────────────────────

const s: Record<string, React.CSSProperties> = {
  container: {
    padding: '24px 32px',
    maxWidth: 800,
  },
  heading: {
    margin: '0 0 4px 0',
    fontSize: 22,
    fontWeight: 600,
    color: '#1a1c1d',
  },
  subheading: {
    margin: 0,
    fontSize: 14,
    color: 'rgba(26,28,29,0.55)',
  },
  card: {
    background: '#fff',
    border: '1px solid rgba(26,28,29,0.07)',
    borderRadius: 12,
    padding: 20,
    marginTop: 16,
  },
  cardHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  cardIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 20,
    fontWeight: 700,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 600,
    color: '#1a1c1d',
    margin: 0,
  },
  cardDesc: {
    fontSize: 13,
    color: 'rgba(26,28,29,0.55)',
    margin: '2px 0 0 0',
  },
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    padding: '3px 10px',
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 500,
  },
  btn: {
    padding: '8px 18px',
    borderRadius: 6,
    fontSize: 13,
    fontWeight: 500,
    cursor: 'pointer',
    border: 'none',
    fontFamily: 'inherit',
  },
  btnSecondary: {
    padding: '8px 18px',
    borderRadius: 6,
    fontSize: 13,
    fontWeight: 500,
    cursor: 'pointer',
    border: '1px solid rgba(26,28,29,0.12)',
    background: 'transparent',
    color: '#1a1c1d',
    fontFamily: 'inherit',
  },
  input: {
    padding: '8px 12px',
    border: '1px solid rgba(26,28,29,0.12)',
    borderRadius: 6,
    fontSize: 13,
    outline: 'none',
    fontFamily: 'inherit',
    color: '#1a1c1d',
    background: '#fff',
    width: '100%',
    boxSizing: 'border-box',
  },
  label: {
    fontSize: 12,
    fontWeight: 500,
    color: 'rgba(26,28,29,0.65)',
    marginBottom: 4,
    display: 'block',
  },
  divider: {
    height: 1,
    background: 'rgba(26,28,29,0.07)',
    margin: '20px 0',
  },
};

// ── Status Badge ──────────────────────────────────────────────────

function StatusBadge({ status, text }: { status: ConnectorState; text: string }) {
  const colors: Record<ConnectorState, { bg: string; text: string; dot: string }> = {
    not_connected: { bg: 'rgba(26,28,29,0.05)', text: 'rgba(26,28,29,0.45)', dot: 'rgba(26,28,29,0.25)' },
    connecting: { bg: 'rgba(164,134,95,0.1)', text: '#a4865f', dot: '#a4865f' },
    connected: { bg: 'rgba(46,125,50,0.08)', text: '#2e7d32', dot: '#2e7d32' },
    error: { bg: 'rgba(209,69,59,0.08)', text: '#d1453b', dot: '#d1453b' },
    configuring: { bg: 'rgba(26,114,232,0.08)', text: '#1a72e8', dot: '#1a72e8' },
  };
  const c = colors[status];
  return (
    <span style={{ ...s.badge, background: c.bg, color: c.text }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: c.dot, display: 'inline-block' }} />
      {text}
    </span>
  );
}

// ── Channel Connector Card ────────────────────────────────────────

function ChannelConnectorCard({
  channel,
  onConnect,
  onConfigure,
  onDisconnect,
}: {
  channel: ChannelInfo;
  onConnect: () => void;
  onConfigure: (action: string) => void;
  onDisconnect: () => void;
}) {
  const iconBg = channel.id === 'meta' ? 'rgba(24,119,242,0.1)' : 'rgba(234,67,53,0.1)';
  const iconColor = channel.id === 'meta' ? '#1877F2' : '#EA4335';

  return (
    <div style={s.card}>
      <div style={s.cardHeader}>
        <div style={{ ...s.cardIcon, background: iconBg, color: iconColor }}>{channel.icon}</div>
        <div style={{ flex: 1 }}>
          <h3 style={s.cardTitle}>{channel.name}</h3>
          <p style={s.cardDesc}>{channel.description}</p>
        </div>
        <StatusBadge status={channel.status} text={channel.statusText} />
      </div>

      {channel.status === 'connected' && channel.accountName && (
        <div style={{
          marginBottom: 12,
          padding: '10px 14px',
          background: 'rgba(46,125,50,0.04)',
          borderRadius: 8,
          fontSize: 13,
          color: '#2e7d32',
        }}>
          Connected as <strong>{channel.accountName}</strong>
          {channel.accountId && <span style={{ color: 'rgba(26,28,29,0.35)', marginLeft: 8 }}>({channel.accountId})</span>}
        </div>
      )}

      {channel.status === 'error' && (
        <div style={{
          marginBottom: 12,
          padding: '10px 14px',
          background: 'rgba(209,69,59,0.04)',
          borderRadius: 8,
          fontSize: 13,
          color: '#d1453b',
        }}>
          Authorization failed or token expired. Reconnect to restore access.
        </div>
      )}

      {/* Connected state: show account and campaign management */}
      {channel.status === 'connected' && (
        <div>
          <div style={s.divider} />
          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <button style={s.btnSecondary} onClick={() => onConfigure('configure')}>Configure Account</button>
            <button style={{ ...s.btnSecondary, color: '#d1453b', borderColor: 'rgba(209,69,59,0.2)' }} onClick={onDisconnect}>
              Disconnect
            </button>
          </div>
          <div style={{
            padding: '14px 16px',
            background: 'rgba(26,28,29,0.02)',
            borderRadius: 8,
            border: '1px dashed rgba(26,28,29,0.1)',
          }}>
            <div style={{ fontSize: 13, fontWeight: 500, color: 'rgba(26,28,29,0.55)', marginBottom: 8 }}>
              Campaigns
            </div>
            <div style={{ fontSize: 13, color: 'rgba(26,28,29,0.45)', textAlign: 'center', padding: '12px 0' }}>
              No campaigns yet. Create your first {channel.name} campaign to get started.
            </div>
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: 8 }}>
              <button style={{ ...s.btn, background: '#1a1c1d', color: '#fff' }}>
                + New {channel.id === 'meta' ? 'Meta' : 'Google'} Campaign
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Not connected state: show connect button */}
      {channel.status === 'not_connected' && (
        <div style={{ marginTop: 4 }}>
          <button style={{ ...s.btn, background: '#1a1c1d', color: '#fff' }} onClick={onConnect}>
            Connect {channel.name}
          </button>
        </div>
      )}

      {/* Connecting state */}
      {channel.status === 'connecting' && (
        <div style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 14, height: 14, borderRadius: '50%',
            border: '2px solid rgba(164,134,95,0.3)',
            borderTopColor: '#a4865f',
            animation: 'mkt-spin 0.8s linear infinite',
          }} />
          <span style={{ fontSize: 13, color: 'rgba(26,28,29,0.55)' }}>
            Authorizing… Complete the connection in the popup window.
          </span>
        </div>
      )}

      {/* Configuring state */}
      {channel.status === 'configuring' && (
        <div style={{ marginTop: 4 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
            <div>
              <label style={s.label}>Ad Account ID</label>
              <input style={s.input} placeholder="e.g. 1234567890" />
            </div>
            <div>
              <label style={s.label}>Account Name</label>
              <input style={s.input} placeholder="e.g. Panchi Club Main Account" />
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
              <button style={{ ...s.btn, background: '#1a1c1d', color: '#fff' }} onClick={() => { if (onConfigure) onConfigure('save'); }}>Save Configuration</button>
              <button style={s.btnSecondary} onClick={() => { if (onConfigure) onConfigure('cancel'); }}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Campaign Creation Modal ───────────────────────────────────────

function CampaignCreationModal({ channel, onClose }: { channel: string; onClose: () => void }) {
  const [form, setForm] = useState({
    name: '',
    objective: 'awareness',
    budget: '0',
    audience: '',
    startDate: '',
    endDate: '',
  });

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'rgba(0,0,0,0.3)',
    }}>
      <div style={{
        background: '#fff', borderRadius: 12, padding: 24, width: 480,
        maxWidth: '90vw', maxHeight: '80vh', overflowY: 'auto',
      }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 18, fontWeight: 600 }}>
          New {channel} Campaign
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <label style={s.label}>Campaign Name</label>
            <input style={s.input} placeholder="e.g. Bali Summer Promotion" value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <div style={{ flex: 1 }}>
              <label style={s.label}>Objective</label>
              <select style={s.input} value={form.objective}
                onChange={e => setForm(f => ({ ...f, objective: e.target.value }))}>
                <option value="awareness">Awareness</option>
                <option value="traffic">Traffic</option>
                <option value="engagement">Engagement</option>
                <option value="leads">Leads</option>
                <option value="conversions">Conversions</option>
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={s.label}>Daily Budget (USD)</label>
              <input style={s.input} type="number" min="1" value={form.budget}
                onChange={e => setForm(f => ({ ...f, budget: e.target.value }))} />
            </div>
          </div>

          <div>
            <label style={s.label}>Target Audience</label>
            <input style={s.input} placeholder="e.g. Travel enthusiasts, 25-45, Indonesia" value={form.audience}
              onChange={e => setForm(f => ({ ...f, audience: e.target.value }))} />
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <div style={{ flex: 1 }}>
              <label style={s.label}>Start Date</label>
              <input style={s.input} type="date" value={form.startDate}
                onChange={e => setForm(f => ({ ...f, startDate: e.target.value }))} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={s.label}>End Date</label>
              <input style={s.input} type="date" value={form.endDate}
                onChange={e => setForm(f => ({ ...f, endDate: e.target.value }))} />
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 20 }}>
          <button style={s.btnSecondary} onClick={onClose}>Cancel</button>
          <button style={{ ...s.btn, background: '#1a1c1d', color: '#fff' }}
            disabled={!form.name.trim()}>
            Save as Draft
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main MarketingChannels Component ──────────────────────────────

export const MarketingChannels: FC = () => {
  const [channels, setChannels] = useState<ChannelInfo[]>([
    {
      id: 'meta',
      name: 'Meta Ads',
      icon: 'M',
      description: 'Facebook, Instagram, and Audience Network campaigns',
      status: 'not_connected',
      statusText: 'Not Connected',
    },
    {
      id: 'google',
      name: 'Google Ads',
      icon: 'G',
      description: 'Search, Display, YouTube, and Discovery campaigns',
      status: 'not_connected',
      statusText: 'Not Connected',
    },
  ]);

  const [showCampaignModal, setShowCampaignModal] = useState<string | null>(null);

  const handleConnect = (id: string) => {
    // In production, this would open OAuth popup.
    // No fake simulation — backend connector not yet implemented.
    // The UI shows the canonical integration boundary ready for the real connector.
    console.log(`Connect requested for ${id} — backend connector not yet wired`);
  };

  const handleConfigure = (id: string, action: string) => {
    if (action === 'save') {
      handleSaveConfig(id);
    } else if (action === 'cancel') {
      setChannels(prev => prev.map(c =>
        c.id === id ? { ...c, status: 'connected' as ConnectorState, statusText: 'Connected' } : c
      ));
    } else {
      setChannels(prev => prev.map(c =>
        c.id === id ? { ...c, status: 'configuring' as ConnectorState, statusText: 'Configuring' } : c
      ));
    }
  };

  const handleDisconnect = (id: string) => {
    // No-op when not connected — UI handles the not_connected state
  };

  const handleSaveConfig = (id: string) => {
    // Backend connector not yet implemented — save config for future use
    setChannels(prev => prev.map(c =>
      c.id === id ? { ...c, status: 'not_connected' as ConnectorState, statusText: 'Not Connected' } : c
    ));
  };

  return (
    <div style={s.container}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
        <div>
          <h2 style={s.heading}>Marketing Channels</h2>
          <p style={s.subheading}>
            Connect and manage your advertising channels. Campaigns are created as drafts — no ad spend is triggered automatically.
          </p>
        </div>
      </div>

      <div style={{ marginTop: 8 }}>
        {channels.map(channel => (
          <ChannelConnectorCard
            key={channel.id}
            channel={channel}
            onConnect={() => handleConnect(channel.id)}
            onConfigure={(action) => handleConfigure(channel.id, action)}
            onDisconnect={() => handleDisconnect(channel.id)}
          />
        ))}
      </div>

      {/* Channel overview summary */}
      <div style={s.card}>
        <h3 style={{ ...s.cardTitle, fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
          Channel Status Summary
        </h3>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <div>
            <span style={{ fontSize: 12, color: 'rgba(26,28,29,0.45)' }}>Connected Channels</span>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#2e7d32' }}>
              {channels.filter(c => c.status === 'connected').length}
            </div>
          </div>
          <div>
            <span style={{ fontSize: 12, color: 'rgba(26,28,29,0.45)' }}>Available Channels</span>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#1a1c1d' }}>{channels.length}</div>
          </div>
          <div>
            <span style={{ fontSize: 12, color: 'rgba(26,28,29,0.45)' }}>Live Campaigns</span>
            <div style={{ fontSize: 20, fontWeight: 700, color: 'rgba(26,28,29,0.35)' }}>0</div>
          </div>
        </div>
        <div style={{ marginTop: 12, fontSize: 12, color: 'rgba(26,28,29,0.35)', fontStyle: 'italic' }}>
          Campaigns are created as drafts. No ad spend is triggered automatically. Campaigns must be explicitly reviewed and launched to go live.
        </div>
      </div>

      {/* Campaign creation modal */}
      {showCampaignModal && (
        <CampaignCreationModal
          channel={showCampaignModal}
          onClose={() => setShowCampaignModal(null)}
        />
      )}

      {/* Spin animation keyframe */}
      <style>{`
        @keyframes mkt-spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

export default MarketingChannels;