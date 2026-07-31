/**
 * Create Object Modal — Object creation form for customers and suppliers.
 *
 * Rendered on top of the workspace when the user clicks "New Object" in the
 * context panel. Supports two object types: customer and supplier.
 */
import { useState, useEffect, useRef } from 'react';
import { useWorkspaceStore } from '../../runtimes/workspace/store';

// ── Types ──────────────────────────────────────────────────

interface FieldDef {
  key: string;
  label: string;
  type?: 'text' | 'email' | 'tel' | 'number' | 'textarea' | 'select';
  required?: boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
}

interface ObjectTypeDef {
  type: string;
  label: string;
  apiUrl: string;
  fields: FieldDef[];
}

const OBJECT_TYPES: Record<string, ObjectTypeDef> = {
  customer: {
    type: 'customer',
    label: 'Customer',
    apiUrl: '/api/v1/objects/customer',
    fields: [
      { key: 'company_name', label: 'Company Name', required: true, placeholder: 'Acme Corp' },
      { key: 'contact_person', label: 'Contact Person', placeholder: 'Jane Doe' },
      { key: 'email', label: 'Email', type: 'email', placeholder: 'jane@acme.com' },
      { key: 'phone', label: 'Phone', type: 'tel', placeholder: '+1-555-0123' },
      { key: 'address', label: 'Address', type: 'textarea', placeholder: '123 Main St' },
      { key: 'gst_number', label: 'GST Number', placeholder: 'GSTIN1234' },
      {
        key: 'segment', label: 'Segment', type: 'select',
        options: [
          { value: '', label: '— Select —' },
          { value: 'enterprise', label: 'Enterprise' },
          { value: 'small_business', label: 'Small Business' },
          { value: 'startup', label: 'Startup' },
          { value: 'individual', label: 'Individual' },
        ],
      },
      {
        key: 'preferred_channel', label: 'Preferred Channel', type: 'select',
        options: [
          { value: '', label: '— Select —' },
          { value: 'email', label: 'Email' },
          { value: 'phone', label: 'Phone' },
          { value: 'whatsapp', label: 'WhatsApp' },
        ],
      },
    ],
  },
  supplier: {
    type: 'supplier',
    label: 'Supplier',
    apiUrl: '/api/v1/objects/supplier',
    fields: [
      { key: 'name', label: 'Supplier Name', required: true, placeholder: 'Grand Hyatt' },
      {
        key: 'category', label: 'Category', type: 'select',
        options: [
          { value: '', label: '— Select —' },
          { value: 'hotel', label: 'Hotel' },
          { value: 'flight', label: 'Flight' },
          { value: 'transport', label: 'Transport' },
          { value: 'activity', label: 'Activity' },
          { value: 'venue', label: 'Venue' },
        ],
      },
      { key: 'contact', label: 'Contact Person', placeholder: 'Reservations' },
      { key: 'email', label: 'Email', type: 'email', placeholder: 'reservations@example.com' },
      { key: 'phone', label: 'Phone', type: 'tel', placeholder: '+1-555-0199' },
      { key: 'city', label: 'City', placeholder: 'Mumbai' },
      { key: 'gstin', label: 'GST Number', placeholder: 'GSTIN5678' },
      { key: 'payment_terms', label: 'Payment Terms', placeholder: 'Net 30' },
      { key: 'rating', label: 'Rating', type: 'number', placeholder: '4' },
      { key: 'notes', label: 'Notes', type: 'textarea', placeholder: 'Preferred partner' },
    ],
  },
};

// ── Props ──────────────────────────────────────────────────

interface CreateObjectModalProps {
  open: boolean;
  onClose: () => void;
}

// ── Component ──────────────────────────────────────────────

export function CreateObjectModal({ open, onClose }: CreateObjectModalProps) {
  const [objectType, setObjectType] = useState<'customer' | 'supplier'>('customer');
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      setFormData({});
      setError(null);
      setSuccess(null);
      setSubmitting(false);
    }
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, onClose]);

  if (!open) return null;

  const def = OBJECT_TYPES[objectType];
  if (!def) return null;

  const handleFieldChange = (key: string, value: string) => {
    setFormData(prev => ({ ...prev, [key]: value }));
    setError(null);
  };

  const handleSubmit = async () => {
    // Validate required fields
    for (const f of def.fields) {
      if (f.required && !formData[f.key]?.trim()) {
        setError(`"${f.label}" is required`);
        return;
      }
    }

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await fetch(def.apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(formData),
      });

      const body = await res.json();

      if (!res.ok) {
        setError(body.detail || body.error || `Server error (${res.status})`);
        setSubmitting(false);
        return;
      }

      setSuccess(`${def.label} created successfully!`);
      setSubmitting(false);

      // Open the newly created object in the workspace
      const objId = body.data?.id;
      if (objId) {
        const { open: openWorkspace } = useWorkspaceStore.getState();
        openWorkspace(`${body.data?.name || body.data?.company_name || def.label}`, 'object', {
          objectType: def.type,
          objectId: String(objId),
        });
      }

      // Close after a brief delay
      setTimeout(onClose, 800);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error — please try again');
      setSubmitting(false);
    }
  };

  return (
    <div className="com-overlay" ref={overlayRef} onClick={e => { if (e.target === overlayRef.current) onClose(); }}>
      <div className="com-modal" role="dialog" aria-modal="true" aria-label="Create new object">
        {/* Header */}
        <div className="com-header">
          <h2 className="com-title">New Object</h2>
          <button className="com-close" onClick={onClose} aria-label="Close modal">✕</button>
        </div>

        {/* Type selector tabs */}
        <div className="com-tabs">
          <button
            className={`com-tab ${objectType === 'customer' ? 'com-tab-active' : ''}`}
            onClick={() => { setObjectType('customer'); setError(null); setSuccess(null); }}
          >
            Customer
          </button>
          <button
            className={`com-tab ${objectType === 'supplier' ? 'com-tab-active' : ''}`}
            onClick={() => { setObjectType('supplier'); setError(null); setSuccess(null); }}
          >
            Supplier
          </button>
        </div>

        {/* Form body */}
        <div className="com-body">
          {def.fields.map(f => {
            const value = formData[f.key] ?? '';
            const isTextarea = f.type === 'textarea';
            const isSelect = f.type === 'select';
            const isNumber = f.type === 'number';

            return (
              <div className="com-field" key={f.key}>
                <label className="com-label">
                  {f.label}
                  {f.required && <span className="com-required">*</span>}
                </label>

                {isSelect ? (
                  <select
                    className="com-input com-select"
                    value={value}
                    onChange={e => handleFieldChange(f.key, e.target.value)}
                  >
                    {f.options?.map(o => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                ) : isTextarea ? (
                  <textarea
                    className="com-input com-textarea"
                    placeholder={f.placeholder}
                    value={value}
                    onChange={e => handleFieldChange(f.key, e.target.value)}
                    rows={3}
                  />
                ) : (
                  <input
                    className="com-input"
                    type={isNumber ? 'number' : f.type || 'text'}
                    placeholder={f.placeholder}
                    value={value}
                    onChange={e => handleFieldChange(f.key, e.target.value)}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="com-footer">
          {error && <div className="com-error" role="alert">{error}</div>}
          {success && <div className="com-success" role="status">{success}</div>}
          <div className="com-actions">
            <button className="com-btn com-btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button className="com-btn com-btn-primary" onClick={handleSubmit} disabled={submitting}>
              {submitting ? 'Creating…' : `Create ${def.label}`}
            </button>
          </div>
        </div>
      </div>

      {/* Inline styles */}
      <style>{styles}</style>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────

const styles = `
.com-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}

.com-modal {
  background: var(--shunya-surface-2, #1a1a26);
  border: 1px solid var(--shunya-surface-1, #22222e);
  border-radius: var(--shunya-radius-md, 8px);
  width: 520px;
  max-width: 90vw;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4);
  animation: com-fade-in 0.15s ease-out;
}

@keyframes com-fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

.com-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--shunya-spacing-md, 12px) var(--shunya-spacing-md, 12px);
  border-bottom: 1px solid var(--shunya-surface-1, #22222e);
}

.com-title {
  font-size: var(--shunya-font-size-md, 16px);
  font-weight: 600;
  color: var(--shunya-text, #e0e0e0);
  margin: 0;
}

.com-close {
  background: transparent;
  border: none;
  color: var(--shunya-text-secondary, #666);
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  line-height: 1;
}
.com-close:hover { background: rgba(255,255,255,0.05); color: #e0e0e0; }

.com-tabs {
  display: flex;
  border-bottom: 1px solid var(--shunya-surface-1, #22222e);
}

.com-tab {
  flex: 1;
  padding: 10px 16px;
  background: transparent;
  border: none;
  color: var(--shunya-text-secondary, #888);
  font-size: var(--shunya-font-size-sm, 13px);
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}
.com-tab:hover { color: var(--shunya-text, #e0e0e0); }
.com-tab-active {
  color: var(--shunya-color-secondary, #D4A843);
  border-bottom-color: var(--shunya-color-secondary, #D4A843);
}

.com-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--shunya-spacing-md, 12px);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.com-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.com-label {
  font-size: var(--shunya-font-size-xs, 12px);
  font-weight: 500;
  color: var(--shunya-text, #e0e0e0);
}

.com-required {
  color: var(--shunya-color-danger, #f55);
  margin-left: 2px;
}

.com-input {
  padding: 8px 10px;
  border: 1px solid var(--shunya-surface-1, #2a2a3a);
  border-radius: var(--shunya-radius-sm, 4px);
  font-size: var(--shunya-font-size-sm, 13px);
  background: var(--shunya-surface-1, #16161e);
  color: var(--shunya-text, #e0e0e0);
  outline: none;
  transition: border-color 0.15s;
  font-family: inherit;
}
.com-input:focus { border-color: var(--shunya-color-secondary, #D4A843); }
.com-input::placeholder { color: var(--shunya-text-secondary, #555); }

.com-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%23888'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 28px;
  cursor: pointer;
}

.com-textarea {
  resize: vertical;
  min-height: 60px;
}

.com-footer {
  padding: var(--shunya-spacing-md, 12px);
  border-top: 1px solid var(--shunya-surface-1, #22222e);
}

.com-error {
  font-size: var(--shunya-font-size-xs, 12px);
  color: var(--shunya-color-danger, #f55);
  margin-bottom: 8px;
  padding: 6px 10px;
  background: rgba(255, 85, 85, 0.1);
  border-radius: var(--shunya-radius-sm, 4px);
}

.com-success {
  font-size: var(--shunya-font-size-xs, 12px);
  color: var(--shunya-color-success, #4caf50);
  margin-bottom: 8px;
  padding: 6px 10px;
  background: rgba(76, 175, 80, 0.1);
  border-radius: var(--shunya-radius-sm, 4px);
}

.com-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.com-btn {
  padding: 8px 16px;
  border-radius: var(--shunya-radius-sm, 4px);
  font-size: var(--shunya-font-size-sm, 13px);
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.15s;
}
.com-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.com-btn-primary {
  background: var(--shunya-color-primary, #555);
  color: #fff;
  border-color: var(--shunya-color-primary, #555);
}
.com-btn-primary:hover:not(:disabled) { filter: brightness(1.15); }

.com-btn-secondary {
  background: transparent;
  color: var(--shunya-text, #e0e0e0);
  border-color: var(--shunya-surface-1, #2a2a3a);
}
.com-btn-secondary:hover:not(:disabled) { background: rgba(255,255,255,0.05); }
`;

if (typeof document !== 'undefined') {
  const el = document.createElement('style');
  el.textContent = styles;
  document.head.appendChild(el);
}