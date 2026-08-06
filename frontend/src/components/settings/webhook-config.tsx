/**
 * Webhook Configuration — Free Integration
 *
 * Add webhook URLs for events (new_invoice, new_proposal, task_completed, etc.)
 * Test webhook button. Store in localStorage.
 * Warm glass-morphism design.
 */
import { useState, useEffect, useCallback } from 'react';

// ── Types ──
interface WebhookEntry {
  id: string;
  url: string;
  events: string[];
  label: string;
  enabled: boolean;
  createdAt: number;
}

const STORAGE_KEY = 'shunya_webhooks';
const AVAILABLE_EVENTS = [
  { id: 'new_invoice', label: 'New Invoice Created' },
  { id: 'invoice_paid', label: 'Invoice Paid' },
  { id: 'new_proposal', label: 'New Proposal Created' },
  { id: 'proposal_accepted', label: 'Proposal Accepted' },
  { id: 'task_completed', label: 'Task Completed' },
  { id: 'contact_added', label: 'Contact Added' },
  { id: 'email_sent', label: 'Email Sent' },
  { id: 'new_note', label: 'New Note Created' },
] as const;

function loadWebhooks(): WebhookEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveWebhooks(hooks: WebhookEntry[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(hooks));
}

export function WebhookConfig() {
  const [webhooks, setWebhooks] = useState<WebhookEntry[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [url, setUrl] = useState('');
  const [label, setLabel] = useState('');
  const [selectedEvents, setSelectedEvents] = useState<string[]>([]);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ id: string; ok: boolean; msg: string } | null>(null);

  useEffect(() => {
    setWebhooks(loadWebhooks());
  }, []);

  const resetForm = () => {
    setUrl('');
    setLabel('');
    setSelectedEvents([]);
    setEditingId(null);
    setShowForm(false);
    setTestResult(null);
  };

  const handleEdit = (hook: WebhookEntry) => {
    setUrl(hook.url);
    setLabel(hook.label);
    setSelectedEvents(hook.events);
    setEditingId(hook.id);
    setShowForm(true);
  };

  const handleSave = () => {
    if (!url.trim() || selectedEvents.length === 0) return;

    const hooks = loadWebhooks();
    if (editingId) {
      const idx = hooks.findIndex((h) => h.id === editingId);
      if (idx >= 0) {
        hooks[idx] = { ...hooks[idx], url: url.trim(), label: label.trim() || url.trim(), events: selectedEvents };
      }
    } else {
      const entry: WebhookEntry = {
        id: Date.now().toString(36) + Math.random().toString(36).substring(2, 6),
        url: url.trim(),
        events: selectedEvents,
        label: label.trim() || url.trim(),
        enabled: true,
        createdAt: Date.now(),
      };
      hooks.push(entry);
    }
    saveWebhooks(hooks);
    setWebhooks(hooks);
    resetForm();
  };

  const handleDelete = (id: string) => {
    const hooks = loadWebhooks().filter((h) => h.id !== id);
    saveWebhooks(hooks);
    setWebhooks(hooks);
    if (editingId === id) resetForm();
  };

  const toggleEnabled = (id: string) => {
    const hooks = loadWebhooks().map((h) => (h.id === id ? { ...h, enabled: !h.enabled } : h));
    saveWebhooks(hooks);
    setWebhooks(hooks);
  };

  const handleTest = useCallback(async (hook: WebhookEntry) => {
    setTestingId(hook.id);
    setTestResult(null);
    try {
      const payload = {
        event: 'test',
        timestamp: new Date().toISOString(),
        data: { message: 'This is a test webhook from SHUNYA OS' },
      };
      await fetch(hook.url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        mode: 'no-cors', // Allow cross-origin test
      });
      setTestResult({ id: hook.id, ok: true, msg: 'Webhook triggered (no-cors mode). Check your endpoint.' });
    } catch {
      setTestResult({ id: hook.id, ok: false, msg: 'Failed to reach endpoint. Check the URL.' });
    }
    setTestingId(null);
  }, []);

  const toggleEvent = (eventId: string) => {
    setSelectedEvents((prev) => (prev.includes(eventId) ? prev.filter((e) => e !== eventId) : [...prev, eventId]));
  };

  return (
    <div className="wh-container">
      {/* Header */}
      <div className="wh-header">
        <div className="wh-header-left">
          <span className="wh-title">
            <svg
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ marginRight: 6 }}
            >
              <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
            Webhooks
          </span>
        </div>
        <button
          className="wh-btn wh-btn-primary"
          onClick={() => {
            resetForm();
            setShowForm(true);
          }}
        >
          + Add Webhook
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <div className="wh-form">
          <div className="wh-form-field">
            <label className="wh-label">Label</label>
            <input
              className="wh-input"
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="My endpoint"
            />
          </div>
          <div className="wh-form-field">
            <label className="wh-label">Webhook URL</label>
            <input
              className="wh-input"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://hooks.example.com/shunya"
            />
          </div>
          <div className="wh-form-field">
            <label className="wh-label">Events to trigger on</label>
            <div className="wh-events-grid">
              {AVAILABLE_EVENTS.map((evt) => (
                <label key={evt.id} className="wh-event-chip">
                  <input
                    type="checkbox"
                    checked={selectedEvents.includes(evt.id)}
                    onChange={() => toggleEvent(evt.id)}
                  />
                  <span>{evt.label}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="wh-form-actions">
            <button
              className="wh-btn wh-btn-primary"
              onClick={handleSave}
              disabled={!url.trim() || selectedEvents.length === 0}
            >
              {editingId ? 'Update' : 'Save'}
            </button>
            <button className="wh-btn wh-btn-ghost" onClick={resetForm}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* List */}
      <div className="wh-list">
        {webhooks.length === 0 && !showForm && (
          <div className="wh-empty">
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ color: 'rgba(26,28,29,0.12)' }}
            >
              <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
            <span className="wh-empty-text">No webhooks configured yet.</span>
          </div>
        )}
        {webhooks.map((hook) => (
          <div key={hook.id} className={`wh-item ${!hook.enabled ? 'wh-item-disabled' : ''}`}>
            <div className="wh-item-info">
              <div className="wh-item-header">
                <span className="wh-item-label">{hook.label}</span>
                <span className={`wh-item-status ${hook.enabled ? 'wh-status-active' : 'wh-status-paused'}`}>
                  {hook.enabled ? 'Active' : 'Paused'}
                </span>
              </div>
              <div className="wh-item-url">{hook.url}</div>
              <div className="wh-item-events">
                {hook.events.map((e) => (
                  <span key={e} className="wh-event-tag">
                    {AVAILABLE_EVENTS.find((ev) => ev.id === e)?.label || e}
                  </span>
                ))}
              </div>
            </div>
            <div className="wh-item-actions">
              <button
                className="wh-btn wh-btn-ghost wh-btn-sm"
                onClick={() => handleTest(hook)}
                disabled={testingId === hook.id || !hook.enabled}
                title="Test webhook"
              >
                {testingId === hook.id ? '...' : 'Test'}
              </button>
              <button
                className="wh-btn wh-btn-ghost wh-btn-sm"
                onClick={() => toggleEnabled(hook.id)}
                title={hook.enabled ? 'Pause' : 'Activate'}
              >
                {hook.enabled ? '⏸' : '▶'}
              </button>
              <button className="wh-btn wh-btn-ghost wh-btn-sm" onClick={() => handleEdit(hook)} title="Edit">
                ✎
              </button>
              <button
                className="wh-btn wh-btn-ghost wh-btn-sm wh-btn-danger"
                onClick={() => handleDelete(hook.id)}
                title="Delete"
              >
                ✕
              </button>
            </div>
            {testResult && testResult.id === hook.id && (
              <div className={`wh-test-result ${testResult.ok ? 'wh-test-ok' : 'wh-test-fail'}`}>
                {testResult.ok ? '✓' : '✗'} {testResult.msg}
              </div>
            )}
          </div>
        ))}
      </div>

      <style>{whCss}</style>
    </div>
  );
}

// ── Styles ──
const whCss = `
.wh-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
}

.wh-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(26,28,29,0.04);
  background: rgba(250,248,245,0.4);
}

.wh-header-left {
  display: flex;
  align-items: center;
}

.wh-title {
  font-size: 13px;
  font-weight: 600;
  color: #1A1C1D;
  display: flex;
  align-items: center;
}

.wh-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
  line-height: 1;
}

.wh-btn-primary {
  background: linear-gradient(135deg, #6C4AE2, #A4865F);
  color: #fff;
}
.wh-btn-primary:hover { opacity: 0.9; }
.wh-btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

.wh-btn-ghost {
  background: transparent;
  color: rgba(26,28,29,0.45);
}
.wh-btn-ghost:hover { background: rgba(255,255,255,0.5); color: #1A1C1D; }

.wh-btn-danger:hover { color: #B91C1C !important; }

.wh-btn-sm { padding: 4px 8px; font-size: 11px; }

/* ── Form ── */
.wh-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid rgba(26,28,29,0.04);
  background: rgba(255,255,255,0.3);
}

.wh-form-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.wh-label {
  font-size: 10px;
  font-weight: 600;
  color: rgba(26,28,29,0.45);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.wh-input {
  padding: 8px 10px;
  border: 1px solid rgba(26,28,29,0.08);
  border-radius: 8px;
  background: rgba(255,255,255,0.7);
  font-size: 13px;
  font-family: inherit;
  color: #1A1C1D;
  outline: none;
  transition: all 0.15s;
}
.wh-input:focus { border-color: #6C4AE2; }
.wh-input::placeholder { color: rgba(26,28,29,0.25); }

.wh-events-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.wh-event-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  background: rgba(255,255,255,0.5);
  border: 1px solid rgba(26,28,29,0.06);
  border-radius: 8px;
  font-size: 11px;
  color: rgba(26,28,29,0.55);
  cursor: pointer;
  transition: all 0.15s;
}
.wh-event-chip:hover { border-color: rgba(108,74,226,0.2); }
.wh-event-chip input { accent-color: #6C4AE2; }

.wh-form-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

/* ── List ── */
.wh-list {
  display: flex;
  flex-direction: column;
}

.wh-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 48px 20px;
}

.wh-empty-text {
  font-size: 13px;
  color: rgba(26,28,29,0.3);
}

.wh-item {
  display: flex;
  flex-direction: column;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(26,28,29,0.03);
  transition: all 0.15s;
}
.wh-item:hover { background: rgba(255,255,255,0.2); }
.wh-item-disabled { opacity: 0.5; }

.wh-item-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.wh-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.wh-item-label {
  font-size: 13px;
  font-weight: 600;
  color: #1A1C1D;
}

.wh-item-status {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.wh-status-active {
  background: rgba(45,106,79,0.1);
  color: #2D6A4F;
}

.wh-status-paused {
  background: rgba(164,134,95,0.1);
  color: #A4865F;
}

.wh-item-url {
  font-size: 12px;
  color: rgba(26,28,29,0.45);
  font-family: monospace;
  word-break: break-all;
}

.wh-item-events {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.wh-event-tag {
  padding: 2px 8px;
  background: rgba(108,74,226,0.06);
  border: 1px solid rgba(108,74,226,0.1);
  border-radius: 6px;
  font-size: 10px;
  color: #6C4AE2;
}

.wh-item-actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
}

.wh-test-result {
  margin-top: 6px;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 11px;
  line-height: 1.4;
}

.wh-test-ok {
  background: rgba(45,106,79,0.06);
  color: #2D6A4F;
}

.wh-test-fail {
  background: rgba(185,28,28,0.06);
  color: #B91C1C;
}

@media (max-width: 768px) {
  .wh-header { flex-direction: column; gap: 8px; align-items: stretch; }
  .wh-item-actions { flex-wrap: wrap; }
}
`;
