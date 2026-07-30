/** View Renderer — renders objects in different view modes (list, table, kanban, calendar, detail). */

import React, { useState, useEffect } from 'react';
import type { ObjectTypeDef, ObjectInstance, ViewDef, FieldDef } from './types';
import { listObjects, getViews, createObject } from './api';
import { FieldRenderer } from './field-renderer';

interface ViewRendererProps {
  objectType: ObjectTypeDef;
  moduleKey: string;
  initialView?: string;
}

export function ViewRenderer({ objectType, moduleKey: _moduleKey, initialView }: ViewRendererProps) {
  const [instances, setInstances] = useState<ObjectInstance[]>([]);
  const [views, setViews] = useState<ViewDef[]>([]);
  const [currentView, setCurrentView] = useState<string>(initialView || objectType.default_view || 'list');
  const [loading, setLoading] = useState(true);
  const [selectedInstance, setSelectedInstance] = useState<ObjectInstance | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadData();
  }, [objectType.key]);

  async function loadData() {
    setLoading(true);
    try {
      const [insts, vws] = await Promise.all([
        listObjects(objectType.key),
        getViews(objectType.key),
      ]);
      setInstances(insts);
      setViews(vws);
    } catch (err) {
      console.error('Failed to load view data:', err);
    }
    setLoading(false);
  }

  const filteredInstances = instances.filter((inst) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (inst.name?.toLowerCase().includes(q)) ||
      Object.values(inst.data || {}).some((v) =>
        String(v).toLowerCase().includes(q)
      )
    );
  });

  const fields = objectType.fields || [];
  const listFields = fields.filter((f) => f.display_in_list).slice(0, 8);

  if (loading) return <div className="ubme-loading">Loading...</div>;

  // ── Detail View ──
  if (selectedInstance) {
    return (
      <div className="ubme-detail">
        <button className="ubme-back-btn" onClick={() => setSelectedInstance(null)}>
          ← Back to {objectType.plural_name || objectType.name + 's'}
        </button>
        <h2 className="ubme-detail-title">{selectedInstance.name}</h2>
        <div className="ubme-detail-meta">
          <span className="ubme-badge">ID: {selectedInstance.id.slice(0, 12)}</span>
          <span className={`ubme-status status-${selectedInstance.status}`}>{selectedInstance.status}</span>
        </div>
        <div className="ubme-detail-fields">
          {fields.map((field) => (
            <FieldRenderer
              key={field.key}
              field={field}
              value={selectedInstance.data?.[field.key]}
              readOnly
            />
          ))}
        </div>
      </div>
    );
  }

  // ── Create Form ──
  if (showCreateForm) {
    return (
      <CreateForm
        objectType={objectType}
        onCreated={() => { setShowCreateForm(false); loadData(); }}
        onCancel={() => setShowCreateForm(false)}
      />
    );
  }

  // ── List View ──
  return (
    <div className="ubme-view">
      <div className="ubme-view-header">
        <div className="ubme-view-tabs">
          {views.map((v) => (
            <button
              key={v.key}
              className={`ubme-view-tab ${currentView === v.view_type ? 'active' : ''}`}
              onClick={() => setCurrentView(v.view_type)}
            >
              {getViewIcon(v.view_type)} {v.label}
            </button>
          ))}
        </div>
        <div className="ubme-view-actions">
          <input
            type="text"
            className="ubme-search-input"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button className="ubme-create-btn" onClick={() => setShowCreateForm(true)}>
            + New {objectType.name}
          </button>
        </div>
      </div>

      <div className="ubme-view-content">
        {filteredInstances.length === 0 ? (
          <div className="ubme-empty-state">
            <div className="ubme-empty-icon">{objectType.icon || '📦'}</div>
            <h3>No {objectType.plural_name || objectType.name + 's'} yet</h3>
            <p>Create your first {objectType.name.toLowerCase()} to get started.</p>
            <button className="ubme-create-btn" onClick={() => setShowCreateForm(true)}>
              + Create {objectType.name}
            </button>
          </div>
        ) : (
          renderView(currentView, filteredInstances, listFields, objectType, (inst) => setSelectedInstance(inst))
        )}
      </div>
    </div>
  );
}

function getViewIcon(viewType: string): string {
  const icons: Record<string, string> = {
    list: '📋',
    table: '📊',
    kanban: '📌',
    calendar: '📅',
    timeline: '⏱️',
    gallery: '🖼️',
    map: '🗺️',
    hierarchy: '🏗️',
    dashboard: '📈',
    detail: '🔍',
  };
  return icons[viewType] || '📋';
}

function renderView(
  viewType: string,
  instances: ObjectInstance[],
  fields: FieldDef[],
  _objectType: ObjectTypeDef,
  onSelect: (inst: ObjectInstance) => void,
): React.ReactNode {
  switch (viewType) {
    case 'table':
      return <TableView instances={instances} fields={fields} onSelect={onSelect} />;
    case 'kanban':
      return <KanbanView instances={instances} fields={fields} onSelect={onSelect} />;
    default:
      return <ListView instances={instances} fields={fields} onSelect={onSelect} />;
  }
}

function ListView({ instances, fields, onSelect }: {
  instances: ObjectInstance[];
  fields: FieldDef[];
  onSelect: (inst: ObjectInstance) => void;
}) {
  return (
    <div className="ubme-list">
      {instances.map((inst) => (
        <div key={inst.id} className="ubme-list-item" onClick={() => onSelect(inst)}>
          <div className="ubme-list-item-header">
            <span className="ubme-list-item-name">{inst.name}</span>
            <span className={`ubme-status status-${inst.status}`}>{inst.status}</span>
          </div>
          <div className="ubme-list-item-details">
            {fields.slice(0, 4).map((f) => (
              <span key={f.key} className="ubme-list-item-field">
                <strong>{f.label}:</strong> {formatValue(f, inst.data?.[f.key])}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function TableView({ instances, fields, onSelect }: {
  instances: ObjectInstance[];
  fields: FieldDef[];
  onSelect: (inst: ObjectInstance) => void;
}) {
  return (
    <table className="ubme-table">
      <thead>
        <tr>
          <th>Name</th>
          {fields.slice(0, 6).map((f) => (
            <th key={f.key}>{f.label}</th>
          ))}
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {instances.map((inst) => (
          <tr key={inst.id} onClick={() => onSelect(inst)} className="ubme-table-row">
            <td className="ubme-table-name">{inst.name}</td>
            {fields.slice(0, 6).map((f) => (
              <td key={f.key}>{formatValue(f, inst.data?.[f.key])}</td>
            ))}
            <td><span className={`ubme-status status-${inst.status}`}>{inst.status}</span></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function KanbanView({ instances, fields, onSelect }: {
  instances: ObjectInstance[];
  fields: FieldDef[];
  onSelect: (inst: ObjectInstance) => void;
}) {
  const columns: Record<string, ObjectInstance[]> = {};
  for (const inst of instances) {
    const col = inst.status || 'unknown';
    if (!columns[col]) columns[col] = [];
    columns[col].push(inst);
  }

  const columnOrder = Object.keys(columns);

  return (
    <div className="ubme-kanban">
      {columnOrder.map((col) => (
        <div key={col} className="ubme-kanban-column">
          <div className="ubme-kanban-column-header">
            <span className={`ubme-kanban-dot status-${col}`}></span>
            <strong>{col}</strong>
            <span className="ubme-kanban-count">{columns[col].length}</span>
          </div>
          {columns[col].map((inst) => (
            <div key={inst.id} className="ubme-kanban-card" onClick={() => onSelect(inst)}>
              <div className="ubme-kanban-card-title">{inst.name}</div>
              {fields.slice(0, 3).map((f) => (
                f.key !== 'status' && (
                  <div key={f.key} className="ubme-kanban-card-field">
                    <span className="ubme-kanban-card-label">{f.label}:</span>
                    {' '}{formatValue(f, inst.data?.[f.key])}
                  </div>
                )
              ))}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

// ── Create Form ──

function CreateForm({ objectType, onCreated, onCancel }: {
  objectType: ObjectTypeDef;
  onCreated: () => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await createObject(objectType.key, formData);
      onCreated();
    } catch (err: any) {
      setError(err.message || 'Failed to create');
    }
    setSaving(false);
  }

  const fields = objectType.fields || [];

  return (
    <div className="ubme-create-form">
      <h2>New {objectType.name}</h2>
      <form onSubmit={handleSubmit}>
        {fields.map((field) => (
          <FieldRenderer
            key={field.key}
            field={field}
            value={formData[field.key]}
            onChange={(key, value) => setFormData((prev) => ({ ...prev, [key]: value }))}
          />
        ))}
        {error && <div className="ubme-error">{error}</div>}
        <div className="ubme-form-actions">
          <button type="submit" className="ubme-btn-primary" disabled={saving}>
            {saving ? 'Creating...' : `Create ${objectType.name}`}
          </button>
          <button type="button" className="ubme-btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

// ── Helpers ──

function formatValue(field: FieldDef, value: any): string {
  if (value === null || value === undefined) return '—';
  switch (field.field_type) {
    case 'currency':
      return `$${Number(value).toFixed(2)}`;
    case 'percentage':
      return `${value}%`;
    case 'date':
    case 'datetime':
      return new Date(value).toLocaleDateString();
    case 'boolean':
      return value ? 'Yes' : 'No';
    default:
      return String(value).length > 50 ? String(value).slice(0, 50) + '...' : String(value);
  }
}