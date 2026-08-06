/** Module Builder UI — create and manage business modules from the frontend. */

import React, { useState, useEffect } from 'react';
import type {
  ModuleDef,
  ObjectTypeDef,
  FieldDef,
  BusinessTemplate,
  WorkflowDef,
  WorkflowStateDef,
  WorkflowTransitionDef,
} from './types';
import * as api from './api';

// ── Field type options ──

const FIELD_TYPE_OPTIONS = [
  'text',
  'integer',
  'long_text',
  'rich_text',
  'number',
  'currency',
  'percentage',
  'boolean',
  'date',
  'datetime',
  'duration',
  'email',
  'phone',
  'url',
  'address',
  'location',
  'select',
  'json',
  'relationship',
  'collection',
  'attachment',
  'image',
];

const FIELD_TYPE_LABELS: Record<string, string> = {
  text: 'Text',
  integer: 'Integer',
  long_text: 'Long Text',
  rich_text: 'Rich Text',
  number: 'Number',
  currency: 'Currency',
  percentage: 'Percentage',
  boolean: 'Boolean',
  date: 'Date',
  datetime: 'Date & Time',
  duration: 'Duration',
  email: 'Email',
  phone: 'Phone',
  url: 'URL',
  address: 'Address',
  location: 'Location',
  select: 'Select/Dropdown',
  json: 'JSON',
  relationship: 'Relationship',
  collection: 'Collection',
  attachment: 'Attachment',
  image: 'Image',
};

const MODULE_ICONS = ['📦', '✈️', '🏥', '🏢', '🛒', '⚖️', '🎓', '🏨', '🏗️', '🏭', '💼', '📊', '🔧', '🎯', '💡'];
const MODULE_COLORS = [
  '#6366f1',
  '#0ea5e9',
  '#ec4899',
  '#10b981',
  '#f59e0b',
  '#ef4444',
  '#8b5cf6',
  '#14b8a6',
  '#f97316',
  '#78716c',
];

// ── Main Component ──

export function ModuleBuilder() {
  const [modules, setModules] = useState<ModuleDef[]>([]);
  const [templates, setTemplates] = useState<BusinessTemplate[]>([]);
  const [activeModule, setActiveModule] = useState<ModuleDef | null>(null);
  const [showNewModule, setShowNewModule] = useState(false);
  const [showTemplatePicker, setShowTemplatePicker] = useState(false);
  const [editingObjectType, setEditingObjectType] = useState<ObjectTypeDef | null>(null);
  const [tab, setTab] = useState<'modules' | 'objects' | 'workflows'>('modules');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [mods, tmpls] = await Promise.all([api.listModules(), api.listTemplates()]);
      setModules(mods);
      setTemplates(tmpls);
    } catch (err) {
      console.error('Failed to load modules:', err);
    }
    setLoading(false);
  }

  if (loading) return <div className="ubme-loading">Loading modules...</div>;

  // ── Template Picker ──
  if (showTemplatePicker) {
    return (
      <div className="ubme-builder">
        <div className="ubme-builder-header">
          <h2>📦 Install Business Template</h2>
          <button className="ubme-back-btn" onClick={() => setShowTemplatePicker(false)}>
            ← Back
          </button>
        </div>
        <div className="ubme-template-grid">
          {templates.map((t) => (
            <div
              key={t.id}
              className="ubme-template-card"
              onClick={async () => {
                try {
                  await api.installTemplate(t.id);
                  await loadData();
                  setShowTemplatePicker(false);
                } catch (err: any) {
                  alert('Failed: ' + err.message);
                }
              }}
            >
              <div className="ubme-template-icon">{t.icon}</div>
              <div className="ubme-template-info">
                <h3>{t.name}</h3>
                <p>{t.description}</p>
                <span className="ubme-template-badge">{t.industry}</span>
                <span className="ubme-template-count">{t.module.object_types?.length || 0} object types</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── Object Type Editor ──
  if (editingObjectType && activeModule) {
    return (
      <ObjectTypeEditor
        objectType={editingObjectType}
        onSave={async (updated) => {
          const idx = activeModule.object_types?.findIndex((ot) => ot.key === updated.key) ?? -1;
          if (idx >= 0 && activeModule.object_types) {
            activeModule.object_types[idx] = updated;
          } else {
            activeModule.object_types = [...(activeModule.object_types || []), updated];
          }
          await api.updateModule(activeModule.key, activeModule);
          setActiveModule({ ...activeModule });
          setEditingObjectType(null);
        }}
        onCancel={() => setEditingObjectType(null)}
        allObjectTypes={(activeModule.object_types || []).map((ot) => ot.key)}
      />
    );
  }

  // ── Module Detail ──
  if (activeModule) {
    return (
      <div className="ubme-builder">
        <div className="ubme-builder-header">
          <div className="ubme-builder-title-row">
            <span style={{ fontSize: '1.5rem' }}>{activeModule.icon || '📦'}</span>
            <h2>{activeModule.name}</h2>
            <button
              className="ubme-back-btn"
              onClick={async () => {
                setActiveModule(null);
                await loadData();
              }}
            >
              ← Back
            </button>
          </div>
          <input
            className="ubme-input"
            style={{ width: '200px' }}
            value={activeModule.key}
            placeholder="Module key"
            onChange={(e) => {
              const name = activeModule.name || e.target.value;
              setActiveModule({ ...activeModule, key: e.target.value, name });
            }}
          />
        </div>

        <div className="ubme-module-tabs">
          <button className={`ubme-tab ${tab === 'objects' ? 'active' : ''}`} onClick={() => setTab('objects')}>
            📋 Object Types ({activeModule.object_types?.length || 0})
          </button>
          <button className={`ubme-tab ${tab === 'workflows' ? 'active' : ''}`} onClick={() => setTab('workflows')}>
            🔄 Workflows ({activeModule.workflows?.length || 0})
          </button>
        </div>

        {tab === 'objects' && (
          <div className="ubme-object-types">
            {(activeModule.object_types || []).map((ot) => (
              <div key={ot.key} className="ubme-object-type-card">
                <div className="ubme-ot-header">
                  <span>{ot.icon || '📦'}</span>
                  <strong>{ot.name}</strong>
                  <span className="ubme-badge">{ot.plural_name || ot.name + 's'}</span>
                  <span className="ubme-field-count">{ot.fields?.length || 0} fields</span>
                  <button className="ubme-edit-btn" onClick={() => setEditingObjectType({ ...ot })}>
                    ✏️
                  </button>
                  <button
                    className="ubme-delete-btn"
                    onClick={async () => {
                      if (!confirm(`Delete object type "${ot.name}"?`)) return;
                      activeModule.object_types = (activeModule.object_types || []).filter((x) => x.key !== ot.key);
                      await api.updateModule(activeModule.key, activeModule);
                      setActiveModule({ ...activeModule });
                    }}
                  >
                    🗑️
                  </button>
                </div>
                <div className="ubme-ot-fields">
                  {(ot.fields || []).slice(0, 5).map((f) => (
                    <span key={f.key} className="ubme-field-chip">
                      {f.label}{' '}
                      <span className="ubme-field-type">({FIELD_TYPE_LABELS[f.field_type] || f.field_type})</span>
                    </span>
                  ))}
                  {(ot.fields?.length || 0) > 5 && (
                    <span className="ubme-more-fields">+{(ot.fields?.length || 0) - 5} more</span>
                  )}
                </div>
              </div>
            ))}
            <button
              className="ubme-add-ot-btn"
              onClick={() => {
                const newOt: ObjectTypeDef = {
                  key: `type_${Date.now()}`,
                  name: 'New Type',
                  plural_name: 'New Types',
                  icon: '📦',
                  color: '#6366f1',
                  fields: [],
                };
                setEditingObjectType(newOt);
              }}
            >
              + Add Object Type
            </button>
          </div>
        )}

        {tab === 'workflows' && (
          <WorkflowEditor
            module={activeModule}
            onSave={async (wf) => {
              activeModule.workflows = [wf];
              await api.updateModule(activeModule.key, activeModule);
              setActiveModule({ ...activeModule });
            }}
          />
        )}
      </div>
    );
  }

  // ── Module List ──
  return (
    <div className="ubme-builder">
      <div className="ubme-builder-header">
        <h2>📦 Universal Module Builder</h2>
        <div className="ubme-header-actions">
          <button className="ubme-btn-secondary" onClick={() => setShowTemplatePicker(true)}>
            Install Template
          </button>
          <button className="ubme-btn-primary" onClick={() => setShowNewModule(true)}>
            + New Module
          </button>
        </div>
      </div>

      {showNewModule && (
        <NewModuleForm
          onCreated={async (module) => {
            try {
              const created = await api.createModule(module);
              setModules([...modules, created]);
              setShowNewModule(false);
              setActiveModule(created);
            } catch (err: any) {
              alert('Failed: ' + err.message);
            }
          }}
          onCancel={() => setShowNewModule(false)}
        />
      )}

      {modules.length === 0 && !showNewModule ? (
        <div className="ubme-empty-state">
          <div className="ubme-empty-icon">📦</div>
          <h3>No modules yet</h3>
          <p>Install a template or create a new module to get started.</p>
        </div>
      ) : (
        <div className="ubme-module-grid">
          {modules.map((m) => (
            <div key={m.key} className="ubme-module-card" onClick={() => setActiveModule(m)}>
              <div className="ubme-module-icon" style={{ background: m.color || '#6366f1' }}>
                {m.icon || '📦'}
              </div>
              <div className="ubme-module-info">
                <h3>{m.name}</h3>
                <p>{m.description || 'No description'}</p>
                <div className="ubme-module-meta">
                  <span>{m.object_types?.length || 0} object types</span>
                  <span>{m.workflows?.length || 0} workflows</span>
                  {m.template_source && <span className="ubme-template-source">Template</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── New Module Form ──

function NewModuleForm({
  onCreated,
  onCancel,
}: {
  onCreated: (module: Partial<ModuleDef>) => void;
  onCancel: () => void;
}) {
  const [key, setKey] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [icon, setIcon] = useState('📦');
  const [color, setColor] = useState('#6366f1');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!key || !name) {
      alert('Key and name are required');
      return;
    }
    onCreated({ key, name, description, icon, color });
  }

  return (
    <form className="ubme-new-module-form" onSubmit={handleSubmit}>
      <h3>Create New Module</h3>
      <div className="ubme-form-row">
        <label>Key</label>
        <input
          className="ubme-input"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="e.g. my_business"
          required
        />
      </div>
      <div className="ubme-form-row">
        <label>Name</label>
        <input
          className="ubme-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. My Business"
          required
        />
      </div>
      <div className="ubme-form-row">
        <label>Description</label>
        <textarea
          className="ubme-input ubme-textarea"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>
      <div className="ubme-form-row">
        <label>Icon</label>
        <select className="ubme-select" value={icon} onChange={(e) => setIcon(e.target.value)}>
          {MODULE_ICONS.map((ic) => (
            <option key={ic} value={ic}>
              {ic}
            </option>
          ))}
        </select>
      </div>
      <div className="ubme-form-row">
        <label>Color</label>
        <select className="ubme-select" value={color} onChange={(e) => setColor(e.target.value)}>
          {MODULE_COLORS.map((c) => (
            <option key={c} value={c} style={{ background: c }}>
              {c}
            </option>
          ))}
        </select>
      </div>
      <div className="ubme-form-actions">
        <button type="submit" className="ubme-btn-primary">
          Create Module
        </button>
        <button type="button" className="ubme-btn-secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}

// ── Object Type Editor ──

function ObjectTypeEditor({
  objectType,
  onSave,
  onCancel,
  allObjectTypes,
}: {
  objectType: ObjectTypeDef;
  onSave: (ot: ObjectTypeDef) => Promise<void>;
  onCancel: () => void;
  allObjectTypes: string[];
}) {
  const [ot, setOt] = useState<ObjectTypeDef>(objectType);
  const [editingField, setEditingField] = useState<FieldDef | null>(null);

  async function handleSave() {
    await onSave(ot);
  }

  return (
    <div className="ubme-ot-editor">
      <div className="ubme-builder-header">
        <h2>
          <span>{ot.icon || '📦'}</span> {ot.name}
        </h2>
        <div className="ubme-header-actions">
          <button className="ubme-btn-primary" onClick={handleSave}>
            Save
          </button>
          <button className="ubme-btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </div>

      <div className="ubme-ot-settings">
        <div className="ubme-form-row">
          <label>Key</label>
          <input className="ubme-input" value={ot.key} onChange={(e) => setOt({ ...ot, key: e.target.value })} />
        </div>
        <div className="ubme-form-row">
          <label>Name</label>
          <input className="ubme-input" value={ot.name} onChange={(e) => setOt({ ...ot, name: e.target.value })} />
        </div>
        <div className="ubme-form-row">
          <label>Plural Name</label>
          <input
            className="ubme-input"
            value={ot.plural_name || ''}
            onChange={(e) => setOt({ ...ot, plural_name: e.target.value })}
          />
        </div>
        <div className="ubme-form-row">
          <label>Description</label>
          <textarea
            className="ubme-input ubme-textarea"
            value={ot.description || ''}
            onChange={(e) => setOt({ ...ot, description: e.target.value })}
          />
        </div>
      </div>

      <h3>Fields</h3>
      {(ot.fields || []).map((field) => (
        <div key={field.key} className="ubme-field-editor-row">
          <span className="ubme-field-editor-icon">{getFieldIcon(field.field_type)}</span>
          <strong>{field.label}</strong>
          <span className="ubme-field-editor-type">{FIELD_TYPE_LABELS[field.field_type] || field.field_type}</span>
          {field.required && <span className="ubme-badge">required</span>}
          {field.display_in_list && <span className="ubme-badge">list</span>}
          <button className="ubme-edit-btn" onClick={() => setEditingField({ ...field })}>
            ✏️
          </button>
          <button
            className="ubme-delete-btn"
            onClick={() => {
              setOt({ ...ot, fields: (ot.fields || []).filter((f) => f.key !== field.key) });
            }}
          >
            🗑️
          </button>
        </div>
      ))}

      {editingField && (
        <FieldEditor
          field={editingField}
          allObjectTypes={allObjectTypes}
          onSave={(f) => {
            const idx = ot.fields?.findIndex((x) => x.key === editingField.key) ?? -1;
            if (idx >= 0 && ot.fields) {
              ot.fields[idx] = f;
            } else {
              ot.fields = [...(ot.fields || []), f];
            }
            setOt({ ...ot });
            setEditingField(null);
          }}
          onCancel={() => setEditingField(null)}
        />
      )}

      <button
        className="ubme-add-field-btn"
        onClick={() => {
          setEditingField({
            key: `field_${Date.now()}`,
            label: 'New Field',
            field_type: 'text',
          });
        }}
      >
        + Add Field
      </button>
    </div>
  );
}

function getFieldIcon(type: string): string {
  const icons: Record<string, string> = {
    text: 'Aa',
    integer: '123',
    long_text: '📝',
    rich_text: '🖋️',
    number: '#',
    currency: '💰',
    percentage: '%',
    boolean: '☑️',
    date: '📅',
    datetime: '📅',
    email: '📧',
    phone: '📞',
    url: '🔗',
    address: '📍',
    select: '📋',
    json: '{ }',
    relationship: '🔗',
  };
  return icons[type] || '📋';
}

function FieldEditor({
  field,
  allObjectTypes,
  onSave,
  onCancel,
}: {
  field: FieldDef;
  allObjectTypes: string[];
  onSave: (f: FieldDef) => void;
  onCancel: () => void;
}) {
  const [f, setF] = useState<FieldDef>(field);
  const [optionsStr, setOptionsStr] = useState((field.options || []).join(', '));

  return (
    <div className="ubme-field-editor-modal">
      <div className="ubme-field-editor-form">
        <h4>Edit Field</h4>
        <div className="ubme-form-row">
          <label>Key</label>
          <input className="ubme-input" value={f.key} onChange={(e) => setF({ ...f, key: e.target.value })} />
        </div>
        <div className="ubme-form-row">
          <label>Label</label>
          <input className="ubme-input" value={f.label} onChange={(e) => setF({ ...f, label: e.target.value })} />
        </div>
        <div className="ubme-form-row">
          <label>Type</label>
          <select
            className="ubme-select"
            value={f.field_type}
            onChange={(e) => setF({ ...f, field_type: e.target.value })}
          >
            {FIELD_TYPE_OPTIONS.map((t) => (
              <option key={t} value={t}>
                {FIELD_TYPE_LABELS[t] || t}
              </option>
            ))}
          </select>
        </div>
        {f.field_type === 'select' && (
          <div className="ubme-form-row">
            <label>Options (comma-separated)</label>
            <input
              className="ubme-input"
              value={optionsStr}
              onChange={(e) => setOptionsStr(e.target.value)}
              placeholder="opt1, opt2, opt3"
            />
          </div>
        )}
        {f.field_type === 'relationship' && (
          <div className="ubme-form-row">
            <label>Target Object Type</label>
            <select
              className="ubme-select"
              value={f.target_object_type || ''}
              onChange={(e) => setF({ ...f, target_object_type: e.target.value })}
            >
              <option value="">Select...</option>
              {allObjectTypes.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="ubme-checkbox-row">
          <label>
            <input
              type="checkbox"
              checked={f.required || false}
              onChange={(e) => setF({ ...f, required: e.target.checked })}
            />
            Required
          </label>
          <label>
            <input
              type="checkbox"
              checked={f.display_in_list || false}
              onChange={(e) => setF({ ...f, display_in_list: e.target.checked })}
            />
            Show in List
          </label>
          <label>
            <input
              type="checkbox"
              checked={f.searchable || false}
              onChange={(e) => setF({ ...f, searchable: e.target.checked })}
            />
            Searchable
          </label>
        </div>
        <div className="ubme-form-actions">
          <button
            className="ubme-btn-primary"
            onClick={() => {
              if (f.field_type === 'select' && optionsStr) {
                f.options = optionsStr
                  .split(',')
                  .map((s: string) => s.trim())
                  .filter(Boolean);
              }
              onSave(f);
            }}
          >
            Save Field
          </button>
          <button className="ubme-btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Workflow Editor ──

function WorkflowEditor({ module, onSave }: { module: ModuleDef; onSave: (wf: WorkflowDef) => void }) {
  const objectTypes = module.object_types?.map((ot) => ot.key) || [];
  const existingWf = module.workflows?.[0];
  const [selectedType, setSelectedType] = useState(existingWf?.object_type || objectTypes[0] || '');
  const [states, setStates] = useState<WorkflowStateDef[]>(
    existingWf?.states || [
      { key: 'draft', label: 'Draft', state_type: 'initial' },
      { key: 'active', label: 'Active', state_type: 'intermediate' },
      { key: 'completed', label: 'Completed', state_type: 'final' },
    ],
  );
  const [transitions, setTransitions] = useState<WorkflowTransitionDef[]>(existingWf?.transitions || []);

  const wf: WorkflowDef = {
    key: `${selectedType}_lifecycle`,
    name: `${selectedType} Lifecycle`,
    object_type: selectedType,
    states,
    transitions,
    default_state: states.find((s) => s.state_type === 'initial')?.key || states[0]?.key || '',
  };

  return (
    <div className="ubme-workflow-editor">
      <h3>Workflow</h3>
      <div className="ubme-form-row">
        <label>For Object Type</label>
        <select className="ubme-select" value={selectedType} onChange={(e) => setSelectedType(e.target.value)}>
          {objectTypes.map((ot) => (
            <option key={ot} value={ot}>
              {ot}
            </option>
          ))}
        </select>
      </div>

      <h4>States</h4>
      {states.map((s, i) => (
        <div key={s.key} className="ubme-workflow-state-row">
          <input
            className="ubme-input"
            style={{ width: '150px' }}
            value={s.key}
            onChange={(e) => {
              const newStates = [...states];
              newStates[i] = { ...s, key: e.target.value };
              setStates(newStates);
            }}
          />
          <input
            className="ubme-input"
            style={{ width: '200px' }}
            value={s.label}
            onChange={(e) => {
              const newStates = [...states];
              newStates[i] = { ...s, label: e.target.value };
              setStates(newStates);
            }}
          />
          <select
            className="ubme-select"
            style={{ width: '150px' }}
            value={s.state_type}
            onChange={(e) => {
              const newStates = [...states];
              newStates[i] = { ...s, state_type: e.target.value };
              setStates(newStates);
            }}
          >
            <option value="initial">Initial</option>
            <option value="intermediate">Intermediate</option>
            <option value="final">Final</option>
          </select>
          <button className="ubme-delete-btn" onClick={() => setStates(states.filter((_, j) => j !== i))}>
            🗑️
          </button>
        </div>
      ))}
      <button
        className="ubme-add-btn"
        onClick={() => {
          setStates([
            ...states,
            { key: `state_${states.length + 1}`, label: `State ${states.length + 1}`, state_type: 'intermediate' },
          ]);
        }}
      >
        + Add State
      </button>

      <h4 style={{ marginTop: '1rem' }}>Transitions</h4>
      {transitions.map((t, i) => (
        <div key={`t${i}`} className="ubme-workflow-transition-row">
          <select
            className="ubme-select"
            style={{ width: '150px' }}
            value={t.from_state}
            onChange={(e) => {
              const nt = [...transitions];
              nt[i] = { ...t, from_state: e.target.value };
              setTransitions(nt);
            }}
          >
            {states.map((s) => (
              <option key={s.key} value={s.key}>
                {s.label}
              </option>
            ))}
          </select>
          <span>→</span>
          <select
            className="ubme-select"
            style={{ width: '150px' }}
            value={t.to_state}
            onChange={(e) => {
              const nt = [...transitions];
              nt[i] = { ...t, to_state: e.target.value };
              setTransitions(nt);
            }}
          >
            {states.map((s) => (
              <option key={s.key} value={s.key}>
                {s.label}
              </option>
            ))}
          </select>
          <input
            className="ubme-input"
            style={{ flex: 1 }}
            value={t.label}
            placeholder="Label"
            onChange={(e) => {
              const nt = [...transitions];
              nt[i] = { ...t, label: e.target.value };
              setTransitions(nt);
            }}
          />
          <label className="ubme-checkbox-label">
            <input
              type="checkbox"
              checked={t.requires_approval || false}
              onChange={(e) => {
                const nt = [...transitions];
                nt[i] = { ...t, requires_approval: e.target.checked };
                setTransitions(nt);
              }}
            />{' '}
            Approval
          </label>
          <button className="ubme-delete-btn" onClick={() => setTransitions(transitions.filter((_, j) => j !== i))}>
            🗑️
          </button>
        </div>
      ))}
      <button
        className="ubme-add-btn"
        onClick={() => {
          if (states.length < 2) return;
          setTransitions([
            ...transitions,
            { from_state: states[0].key, to_state: states[1].key, label: 'Transition', requires_approval: false },
          ]);
        }}
      >
        + Add Transition
      </button>

      <div className="ubme-form-actions" style={{ marginTop: '1rem' }}>
        <button className="ubme-btn-primary" onClick={() => onSave(wf)}>
          Save Workflow
        </button>
      </div>
    </div>
  );
}
