/**
 * EntityManager — Dynamic entity type system UI.
 *
 * Reads type schemas from /api/v1/entities/types and renders
 * a dynamic form for each type. Supports create, list, and edit.
 * Uses inline CSS — no external dependencies.
 */
import { useState, useEffect, useCallback, type FC } from 'react';

/* ── Types ──────────────────────────────────────────────────── */

interface FieldSchema {
  key: string;
  label: string;
  type: string;
  required?: boolean;
  options?: string[];
}

interface EntityType {
  id: string;
  name: string;
  fields: FieldSchema[];
}

interface EntityItem {
  id: number;
  type: string;
  data: Record<string, unknown>;
  status?: string;
  code?: string;
  state?: string;
}

/* ── API helpers ─────────────────────────────────────────────── */

async function api<T>(path: string, opts?: RequestInit): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...opts });
    return await r.json() as T;
  } catch { return null; }
}

/* ── Field Renderer ──────────────────────────────────────────── */

function DynamicField({
  field, value, onChange, error,
}: {
  field: FieldSchema;
  value: string;
  onChange: (key: string, val: string) => void;
  error?: string;
}) {
  const id = `ef-${field.key}`;
  const baseStyle: React.CSSProperties = {
    width: '100%', padding: '8px 12px',
    border: `1px solid ${error ? '#d1453b' : 'rgba(26,28,29,0.12)'}`,
    borderRadius: 6, fontSize: 13, outline: 'none',
    fontFamily: 'inherit', color: '#1A1C1D', background: '#fff',
    boxSizing: 'border-box',
  };

  if (field.type === 'textarea') {
    return (
      <div className="ef-field">
        <label htmlFor={id} className="ef-label">{field.label}{field.required && ' *'}</label>
        <textarea id={id} value={value} rows={3}
          onChange={e => onChange(field.key, e.target.value)}
          style={baseStyle} />
        {error && <span className="ef-error">{error}</span>}
      </div>
    );
  }
  if (field.type === 'select' && field.options) {
    return (
      <div className="ef-field">
        <label htmlFor={id} className="ef-label">{field.label}{field.required && ' *'}</label>
        <select id={id} value={value}
          onChange={e => onChange(field.key, e.target.value)}
          style={baseStyle}>
          <option value="">— Select —</option>
          {field.options.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
        {error && <span className="ef-error">{error}</span>}
      </div>
    );
  }
  if (field.type === 'boolean') {
    return (
      <div className="ef-field ef-field-row">
        <input type="checkbox" id={id} checked={value === 'true'}
          onChange={e => onChange(field.key, e.target.checked ? 'true' : 'false')}
          style={{ marginRight: 8 }} />
        <label htmlFor={id} className="ef-label">{field.label}</label>
      </div>
    );
  }
  if (field.type === 'number') {
    return (
      <div className="ef-field">
        <label htmlFor={id} className="ef-label">{field.label}{field.required && ' *'}</label>
        <input type="number" id={id} value={value}
          onChange={e => onChange(field.key, e.target.value)}
          style={baseStyle} />
        {error && <span className="ef-error">{error}</span>}
      </div>
    );
  }
  // Default: text/email/date
  return (
    <div className="ef-field">
      <label htmlFor={id} className="ef-label">{field.label}{field.required && ' *'}</label>
      <input type={field.type === 'email' ? 'email' : field.type === 'date' ? 'date' : 'text'}
        id={id} value={value}
        onChange={e => onChange(field.key, e.target.value)}
        style={baseStyle} />
      {error && <span className="ef-error">{error}</span>}
    </div>
  );
}

/* ── Entity Form ─────────────────────────────────────────────── */

function EntityCreateForm({
  type, fields, onCreated, onCancel,
}: {
  type: string;
  fields: FieldSchema[];
  onCreated: () => void;
  onCancel: () => void;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  const handleChange = (key: string, val: string) => {
    setValues(prev => ({ ...prev, [key]: val }));
    if (errors[key]) setErrors(prev => { const c = { ...prev }; delete c[key]; return c; });
  };

  const handleSubmit = async () => {
    // Validate required fields
    const newErrors: Record<string, string> = {};
    for (const f of fields) {
      if (f.required && !values[f.key]?.trim()) {
        newErrors[f.key] = `${f.label} is required`;
      }
    }
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    setSaving(true);
    const result = await api<{ id: number }>('/api/v1/entities/', {
      method: 'POST',
      body: JSON.stringify({ type, data: values }),
    });
    setSaving(false);
    if (result && result.id) {
      onCreated();
    } else {
      setErrors({ _form: 'Failed to create entity' });
    }
  };

  return (
    <div className="ef-form-container">
      <h3 className="ef-form-title">New {type}</h3>
      <div className="ef-fields">
        {fields.map(f => (
          <DynamicField
            key={f.key} field={f}
            value={values[f.key] ?? ''}
            onChange={handleChange}
            error={errors[f.key]}
          />
        ))}
      </div>
      {errors._form && <p className="ef-error">{errors._form}</p>}
      <div className="ef-actions">
        <button className="ef-btn ef-btn-primary" onClick={handleSubmit} disabled={saving}>
          {saving ? 'Creating…' : `Create ${type}`}
        </button>
        <button className="ef-btn ef-btn-secondary" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
}

/* ── Entity Card ─────────────────────────────────────────────── */

function EntityCard({ entity, fields }: { entity: EntityItem; fields: FieldSchema[] }) {
  const data = entity.data || {};
  const firstField = fields.find(f => f.type === 'text' || f.type === 'email');
  const title = firstField ? (data[firstField.key] as string || `#${entity.id}`) : `#${entity.id}`;
  const statusColor = entity.status === 'active' || entity.status === 'new' ? '#2e7d32'
    : entity.status === 'inactive' ? 'rgba(26,28,29,0.35)' : '#a4865f';

  return (
    <div className="ef-card">
      <div className="ef-card-header">
        <span className="ef-card-title">{String(title)}</span>
        <span className="ef-card-badge" style={{ color: statusColor }}>
          {entity.status || 'active'}
        </span>
      </div>
      <div className="ef-card-meta">
        <span>Type: {entity.type}</span>
        <span>ID: {entity.id}</span>
      </div>
      {fields.slice(0, 3).map(f => {
        const val = data[f.key];
        if (!val) return null;
        return (
          <div key={f.key} className="ef-card-field">
            <span className="ef-card-field-key">{f.label}:</span>
            <span className="ef-card-field-val">{String(val).slice(0, 60)}</span>
          </div>
        );
      })}
    </div>
  );
}

/* ── Main Component ──────────────────────────────────────────── */

export const EntityManager: FC = () => {
  const [types, setTypes] = useState<EntityType[]>([]);
  const [entities, setEntities] = useState<EntityItem[]>([]);
  const [selectedType, setSelectedType] = useState<string>('');
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const [typesResult, entitiesResult] = await Promise.all([
      api<{ types: EntityType[] }>('/api/v1/entities/types'),
      api<EntityItem[]>('/api/v1/entities/'),
    ]);
    if (typesResult?.types) {
      setTypes(typesResult.types);
      if (!selectedType && typesResult.types.length > 0) {
        setSelectedType(typesResult.types[0].id);
      }
    }
    if (Array.isArray(entitiesResult)) {
      setEntities(entitiesResult);
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const currentType = types.find(t => t.id === selectedType);
  const filteredEntities = selectedType
    ? entities.filter(e => e.type === selectedType)
    : [];

  const handleCreated = () => {
    setShowCreate(false);
    load();
  };

  return (
    <div className="ef-container">
      <div className="ef-header">
        <h2 className="ef-title">Entities</h2>
        <p className="ef-subtitle">Dynamic entity management</p>
      </div>

      {/* Type selector */}
      <div className="ef-toolbar">
        <div className="ef-type-selector">
          {types.map(t => (
            <button
              key={t.id}
              className={`ef-type-btn ${selectedType === t.id ? 'ef-type-active' : ''}`}
              onClick={() => { setSelectedType(t.id); setShowCreate(false); }}
            >
              {t.name}
            </button>
          ))}
        </div>
        {currentType && (
          <button
            className="ef-btn ef-btn-primary ef-create-btn"
            onClick={() => setShowCreate(!showCreate)}
          >
            {showCreate ? 'Cancel' : `+ New ${currentType.name}`}
          </button>
        )}
      </div>

      {/* Create form */}
      {showCreate && currentType && (
        <EntityCreateForm
          type={selectedType}
          fields={currentType.fields}
          onCreated={handleCreated}
          onCancel={() => setShowCreate(false)}
        />
      )}

      {/* Entity list */}
      <div className="ef-list">
        {loading && <div className="ef-loading">Loading entities…</div>}

        {!loading && filteredEntities.length === 0 && (
          <div className="ef-empty">
            <p>No {selectedType} entities found.</p>
            <p className="ef-empty-sub">Create one to get started.</p>
          </div>
        )}

        {!loading && filteredEntities.length > 0 && (
          <div className="ef-grid">
            {filteredEntities.map(e => (
              <EntityCard key={e.id} entity={e} fields={currentType?.fields || []} />
            ))}
          </div>
        )}
      </div>

      <style>{`
.ef-container {
  padding: clamp(16px, 3vw, 32px);
  max-width: 960px;
}
.ef-header { margin-bottom: 20px; }
.ef-title { margin: 0 0 4px; font-size: 22px; font-weight: 600; color: #1A1C1D; }
.ef-subtitle { margin: 0; font-size: 14px; color: rgba(26,28,29,0.55); }
.ef-toolbar {
  display: flex; gap: 12px; align-items: flex-start;
  margin-bottom: 16px; flex-wrap: wrap;
}
.ef-type-selector { display: flex; gap: 6px; flex-wrap: wrap; }
.ef-type-btn {
  padding: 6px 14px; border-radius: 6px;
  border: 1px solid rgba(26,28,29,0.06);
  background: transparent; color: rgba(26,28,29,0.55);
  font-size: 12px; font-weight: 500; cursor: pointer;
}
.ef-type-active {
  border-color: #a4865f; background: rgba(164,134,95,0.1); color: #a4865f;
}
.ef-create-btn { flex-shrink: 0; }
.ef-btn {
  padding: 8px 18px; border-radius: 6px;
  font-size: 13px; font-weight: 500; cursor: pointer; border: none;
}
.ef-btn-primary { background: #1A1C1D; color: #fff; }
.ef-btn-primary:disabled { opacity: 0.5; }
.ef-btn-secondary {
  background: transparent; border: 1px solid rgba(26,28,29,0.07); color: rgba(26,28,29,0.55);
}
.ef-form-container {
  background: #fff; border: 1px solid rgba(26,28,29,0.07);
  border-radius: 10px; padding: 20px; margin-bottom: 16px;
}
.ef-form-title { margin: 0 0 16px; font-size: 16px; font-weight: 600; }
.ef-fields { display: flex; flex-direction: column; gap: 12px; }
.ef-field { display: flex; flex-direction: column; gap: 4px; }
.ef-field-row { flex-direction: row; align-items: center; }
.ef-label { font-size: 12px; font-weight: 500; color: rgba(26,28,29,0.65); }
.ef-error { color: #d1453b; font-size: 11px; margin-top: 2px; }
.ef-actions { display: flex; gap: 8px; margin-top: 16px; }
.ef-loading { padding: 40px; text-align: center; color: rgba(26,28,29,0.55); }
.ef-empty { padding: 40px; text-align: center; }
.ef-empty-sub { font-size: 13px; color: rgba(26,28,29,0.45); }
.ef-grid { display: flex; flex-direction: column; gap: 8px; }
.ef-card {
  background: #fff; border: 1px solid rgba(26,28,29,0.07);
  border-radius: 10px; padding: 14px 16px;
}
.ef-card-header {
  display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;
}
.ef-card-title { font-size: 15px; font-weight: 600; color: #1A1C1D; }
.ef-card-badge { font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
.ef-card-meta { display: flex; gap: 16px; font-size: 11px; color: rgba(26,28,29,0.45); margin-bottom: 6px; }
.ef-card-field { font-size: 12px; color: rgba(26,28,29,0.55); display: flex; gap: 6px; }
.ef-card-field-key { font-weight: 500; color: rgba(26,28,29,0.65); min-width: 60px; }
.ef-card-field-val { color: #1A1C1D; }
      `}</style>
    </div>
  );
};

export default EntityManager;