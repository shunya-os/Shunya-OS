/**
 * Webhook Configuration — FDA26 Server-side Backed
 *
 * Add webhook URLs for events. Stored on the server, delivered with HMAC
 * signature, idempotency keys, and retry with backoff.
 */
import { useState, useEffect, useCallback } from 'react';
import {
  fetchWebhooks,
  createWebhook,
  updateWebhook,
  deleteWebhook,
  rotateWebhookSecret,
  testWebhook,
  fetchDeliveries,
  type WebhookEntry,
  type WebhookDelivery,
  AVAILABLE_EVENTS,
} from '../../api/webhooks';

export function WebhookConfig() {
  const [webhooks, setWebhooks] = useState<WebhookEntry[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [url, setUrl] = useState('');
  const [label, setLabel] = useState('');
  const [selectedEvents, setSelectedEvents] = useState<string[]>([]);
  const [testingId, setTestingId] = useState<number | null>(null);
  const [testResult, setTestResult] = useState<{ id: number; ok: boolean; msg: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deliveries, setDeliveries] = useState<Record<number, WebhookDelivery[]>>({});
  const [showDeliveries, setShowDeliveries] = useState<number | null>(null);

  useEffect(() => {
    loadWebhooks();
  }, []);

  const loadWebhooks = async () => {
    setLoading(true);
    setError('');
    try {
      const hooks = await fetchWebhooks();
      setWebhooks(hooks);
    } catch (e: any) {
      setError(e.message || 'Failed to load webhooks');
    } finally {
      setLoading(false);
    }
  };

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

  const handleSave = async () => {
    if (!url.trim() || selectedEvents.length === 0) return;
    setError('');
    try {
      if (editingId) {
        await updateWebhook(editingId, { url: url.trim(), label: label.trim() || url.trim(), events: selectedEvents });
      } else {
        await createWebhook({ url: url.trim(), label: label.trim() || url.trim(), events: selectedEvents });
      }
      resetForm();
      await loadWebhooks();
    } catch (e: any) {
      setError(e.message || 'Failed to save webhook');
    }
  };

  const handleDelete = async (id: number) => {
    setError('');
    try {
      await deleteWebhook(id);
      await loadWebhooks();
    } catch (e: any) {
      setError(e.message || 'Failed to delete webhook');
    }
  };

  const toggleEnabled = async (hook: WebhookEntry) => {
    setError('');
    try {
      await updateWebhook(hook.id, { is_active: !hook.is_active });
      await loadWebhooks();
    } catch (e: any) {
      setError(e.message || 'Failed to toggle webhook');
    }
  };

  const handleTest = useCallback(async (hook: WebhookEntry) => {
    setTestingId(hook.id);
    setTestResult(null);
    try {
      const delivery = await testWebhook(hook.id);
      const ok = delivery.status === 'delivered';
      setTestResult({
        id: hook.id,
        ok,
        msg: ok
          ? `Delivered (HTTP ${delivery.http_status}). Check your endpoint.`
          : `Failed: ${delivery.error || 'Delivery error'}`,
      });
    } catch (e: any) {
      setTestResult({ id: hook.id, ok: false, msg: e.message || 'Test failed' });
    }
    setTestingId(null);
  }, []);

  const handleShowDeliveries = async (hook: WebhookEntry) => {
    if (showDeliveries === hook.id) {
      setShowDeliveries(null);
      return;
    }
    try {
      const items = await fetchDeliveries(hook.id);
      setDeliveries((prev) => ({ ...prev, [hook.id]: items }));
      setShowDeliveries(hook.id);
    } catch {
      setShowDeliveries(hook.id);
    }
  };

  const toggleEvent = (eventId: string) => {
    setSelectedEvents((prev) => (prev.includes(eventId) ? prev.filter((e) => e !== eventId) : [...prev, eventId]));
  };

  const handleRotateSecret = async (hook: WebhookEntry) => {
    setError('');
    try {
      const updated = await rotateWebhookSecret(hook.id);
      if (updated.secret) {
        alert(`New secret: ${updated.secret}\n\nSave this — it will not be shown again.`);
      }
      await loadWebhooks();
    } catch (e: any) {
      setError(e.message || 'Failed to rotate secret');
    }
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

      {error && (
        <div className="wh-error" role="alert">
          {error}
        </div>
      )}

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
        {loading && <div className="wh-loading">Loading webhooks…</div>}
        {!loading && webhooks.length === 0 && !showForm && (
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
          <div key={hook.id} className={`wh-item ${!hook.is_active ? 'wh-item-disabled' : ''}`}>
            <div className="wh-item-info">
              <div className="wh-item-header">
                <span className="wh-item-label">{hook.label}</span>
                <span className={`wh-item-status ${hook.is_active ? 'wh-status-active' : 'wh-status-paused'}`}>
                  {hook.is_active ? 'Active' : 'Paused'}
                </span>
                {hook.last_delivery_status && hook.last_delivery_status !== 'never' && (
                  <span className={`wh-item-status ${hook.last_delivery_status === 'delivered' ? 'wh-status-ok' : 'wh-status-fail'}`}>
                    {hook.last_delivery_status}
                  </span>
                )}
              </div>
              <div className="wh-item-url">{hook.url}</div>
              <div className="wh-item-events">
                {hook.events.map((e) => (
                  <span key={e} className="wh-event-tag">
                    {AVAILABLE_EVENTS.find((ev) => ev.id === e)?.label || e}
                  </span>
                ))}
              </div>
              {hook.delivery_count > 0 && (
                <div className="wh-item-meta">
                  {hook.delivery_count} delivery{(hook.delivery_count || 0) !== 1 ? 'ies' : ''}
                  {hook.last_delivery_at ? ` · last ${new Date(hook.last_delivery_at).toLocaleDateString()}` : ''}
                </div>
              )}
            </div>
            <div className="wh-item-actions">
              <button
                className="wh-btn wh-btn-ghost wh-btn-sm"
                onClick={() => handleTest(hook)}
                disabled={testingId === hook.id || !hook.is_active}
                title="Test webhook"
              >
                {testingId === hook.id ? '...' : 'Test'}
              </button>
              <button
                className="wh-btn wh-btn-ghost wh-btn-sm"
                onClick={() => toggleEnabled(hook)}
                title={hook.is_active ? 'Pause' : 'Activate'}
              >
                {hook.is_active ? '⏸' : '▶'}
              </button>
              <button className="wh-btn wh-btn-ghost wh-btn-sm" onClick={() => handleEdit(hook)} title="Edit">
                ✎
              </button>
              <button
                className="wh-btn wh-btn-ghost wh-btn-sm"
                onClick={() => handleRotateSecret(hook)}
                title="Rotate secret"
              >
                🔑
              </button>
              <button
                className="wh-btn wh-btn-ghost wh-btn-sm wh-btn-danger"
                onClick={() => handleDelete(hook.id)}
                title="Delete"
              >
                ✕
              </button>
              <button
                className="wh-btn wh-btn-ghost wh-btn-sm"
                onClick={() => handleShowDeliveries(hook)}
                title="Delivery log"
              >
                📋
              </button>
            </div>
            {testResult && testResult.id === hook.id && (
              <div className={`wh-test-result ${testResult.ok ? 'wh-test-ok' : 'wh-test-fail'}`}>
                {testResult.ok ? '✓' : '✗'} {testResult.msg}
              </div>
            )}
            {showDeliveries === hook.id && (
              <div className="wh-deliveries">
                {(deliveries[hook.id] || []).length === 0 && (
                  <div className="wh-empty-text" style={{ padding: '8px 0' }}>No deliveries yet.</div>
                )}
                {(deliveries[hook.id] || []).slice(0, 10).map((d) => (
                  <div key={d.id} className="wh-delivery-row">
                    <span className={`wh-delivery-status wh-delivery-${d.status}`}>{d.status}</span>
                    <span className="wh-delivery-event">{d.event_name}</span>
                    <span className="wh-delivery-attempt">attempt {d.attempt}/{d.max_attempts}</span>
                    {d.http_status && <span className="wh-delivery-http">HTTP {d.http_status}</span>}
                    <span className="wh-delivery-time">{d.created_at ? new Date(d.created_at).toLocaleString() : ''}</span>
                  </div>
                ))}
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

.wh-error {
  padding: 8px 14px;
  background: rgba(185,28,28,0.08);
  color: #B91C1C;
  font-size: 12px;
  border-bottom: 1px solid rgba(185,28,28,0.1);
}

.wh-loading {
  padding: 32px 14px;
  text-align: center;
  font-size: 13px;
  color: rgba(26,28,29,0.3);
}

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
  background: rgba(148,115,71,0.1);
  color: #947347;
}

.wh-status-ok {
  background: rgba(45,106,79,0.08);
  color: #2D6A4F;
}

.wh-status-fail {
  background: rgba(185,28,28,0.08);
  color: #B91C1C;
}

.wh-item-url {
  font-size: 12px;
  color: rgba(26,28,29,0.35);
  word-break: break-all;
}

.wh-item-events {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.wh-event-tag {
  font-size: 10px;
  padding: 2px 8px;
  background: rgba(108,74,226,0.06);
  color: rgba(108,74,226,0.7);
  border-radius: 6px;
}

.wh-item-meta {
  font-size: 10px;
  color: rgba(26,28,29,0.3);
  margin-top: 2px;
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
}

.wh-test-ok {
  background: rgba(45,106,79,0.06);
  color: #2D6A4F;
}

.wh-test-fail {
  background: rgba(185,28,28,0.06);
  color: #B91C1C;
}

.wh-deliveries {
  margin-top: 8px;
  padding: 8px;
  background: rgba(26,28,29,0.02);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.wh-delivery-row {
  display: flex;
  gap: 8px;
  font-size: 11px;
  align-items: center;
}

.wh-delivery-status {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}

.wh-delivery-delivered { background: rgba(45,106,79,0.1); color: #2D6A4F; }
.wh-delivery-failed { background: rgba(185,28,28,0.1); color: #B91C1C; }
.wh-delivery-pending { background: rgba(148,115,71,0.1); color: #947347; }
.wh-delivery-exhausted { background: rgba(185,28,28,0.15); color: #B91C1C; }

.wh-delivery-event { color: rgba(26,28,29,0.6); }
.wh-delivery-attempt { color: rgba(26,28,29,0.35); }
.wh-delivery-http { color: rgba(26,28,29,0.35); }
.wh-delivery-time { color: rgba(26,28,29,0.25); margin-left: auto; }
`;