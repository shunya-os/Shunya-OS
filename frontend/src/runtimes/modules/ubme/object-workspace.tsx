/** Object Workspace — tabbed universal object workspace. */

import React, { useState, useEffect } from 'react';
import type { ObjectTypeDef, ObjectInstance, FieldDef } from './types';
import { getObject } from './api';

interface ObjectWorkspaceProps {
  objectType: ObjectTypeDef;
  objectId: string;
}

type TabId =
  | 'overview' | 'timeline' | 'activity' | 'relationships'
  | 'documents' | 'conversations' | 'ai' | 'history'
  | 'attachments' | 'tasks';

interface TabDef {
  id: TabId;
  label: string;
  icon: string;
}

const TABS: TabDef[] = [
  { id: 'overview', label: 'Overview', icon: '📋' },
  { id: 'timeline', label: 'Timeline', icon: '⏱️' },
  { id: 'activity', label: 'Activity', icon: '📊' },
  { id: 'relationships', label: 'Relationships', icon: '🔗' },
  { id: 'documents', label: 'Documents', icon: '📄' },
  { id: 'conversations', label: 'Conversations', icon: '💬' },
  { id: 'ai', label: 'AI', icon: '🤖' },
  { id: 'history', label: 'History', icon: '🕐' },
  { id: 'attachments', label: 'Attachments', icon: '📎' },
  { id: 'tasks', label: 'Tasks', icon: '✅' },
];

export function ObjectWorkspace({ objectType, objectId }: ObjectWorkspaceProps) {
  const [object, setObject] = useState<ObjectInstance | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadObject();
  }, [objectType.key, objectId]);

  async function loadObject() {
    setLoading(true);
    setError('');
    try {
      const obj = await getObject(objectType.key, objectId);
      setObject(obj);
    } catch (err: any) {
      setError(err.message || 'Failed to load object');
    }
    setLoading(false);
  }

  if (loading) {
    return <div className="ubme-loading">Loading {objectType.name}...</div>;
  }

  if (error) {
    return <div className="ubme-error">{error}</div>;
  }

  if (!object) {
    return (
      <div className="ubme-empty-state">
        <div className="ubme-empty-icon">{objectType.icon || '📦'}</div>
        <h3>Object not found</h3>
        <p>The requested {objectType.name} could not be loaded.</p>
      </div>
    );
  }

  const fields = objectType.fields || [];
  const relationships = objectType.relationships || [];

  return (
    <div className="ubme-object-workspace" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div style={{
        padding: '1rem 1.5rem', borderBottom: '1px solid #334155',
        display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap',
      }}>
        <span style={{ fontSize: '1.5rem' }}>{objectType.icon || '📦'}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h2 style={{ margin: 0, fontSize: '1.25rem', color: '#fff' }}>{object.name}</h2>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
            <span className="ubme-badge">ID: {object.id.slice(0, 12)}</span>
            <span className={`ubme-status status-${object.status}`}>{object.status}</span>
            <span className="ubme-badge">{objectType.name}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="ubme-module-tabs" style={{ padding: '0.75rem 1.5rem 0', borderBottom: '1px solid #334155', overflowX: 'auto', flexWrap: 'nowrap' }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`ubme-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
            style={{ whiteSpace: 'nowrap' }}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem' }}>
        {activeTab === 'overview' && (
          <OverviewTab object={object} fields={fields} />
        )}
        {activeTab === 'timeline' && <GenericTab icon="⏱️" label="Timeline" />}
        {activeTab === 'activity' && <GenericTab icon="📊" label="Activity" />}
        {activeTab === 'relationships' && (
          <RelationshipsTab object={object} relationships={relationships} />
        )}
        {activeTab === 'documents' && <GenericTab icon="📄" label="Documents" />}
        {activeTab === 'conversations' && <GenericTab icon="💬" label="Conversations" />}
        {activeTab === 'ai' && <GenericTab icon="🤖" label="AI Insights" />}
        {activeTab === 'history' && <GenericTab icon="🕐" label="History" />}
        {activeTab === 'attachments' && <GenericTab icon="📎" label="Attachments" />}
        {activeTab === 'tasks' && <GenericTab icon="✅" label="Tasks" />}
      </div>
    </div>
  );
}

// ── Overview Tab ──

function OverviewTab({ object, fields }: { object: ObjectInstance; fields: FieldDef[] }) {
  return (
    <div style={{ maxWidth: '800px' }}>
      <div className="ubme-detail-fields">
        {fields.map((field) => (
          <div key={field.key} className="ubme-field ubme-field-readonly">
            <label className="ubme-field-label">{field.label}</label>
            <div className="ubme-field-value">
              {formatFieldValue(field, object.data?.[field.key])}
            </div>
          </div>
        ))}

        {/* System fields */}
        <div className="ubme-field ubme-field-readonly">
          <label className="ubme-field-label">Created At</label>
          <div className="ubme-field-value">
            {object.created_at ? new Date(object.created_at).toLocaleString() : '—'}
          </div>
        </div>
        <div className="ubme-field ubme-field-readonly">
          <label className="ubme-field-label">Updated At</label>
          <div className="ubme-field-value">
            {object.updated_at ? new Date(object.updated_at).toLocaleString() : '—'}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Relationships Tab ──

function RelationshipsTab({ relationships }: { object: ObjectInstance; relationships: Record<string, any>[] }) {
  if (!relationships || relationships.length === 0) {
    return (
      <GenericEmptyState icon="🔗" title="No relationships" message="This object type has no relationships configured." />
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '800px' }}>
      {relationships.map((rel, idx) => (
        <div key={idx} style={{
          background: '#1e293b', border: '1px solid #334155', borderRadius: '0.75rem',
          padding: '1rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span>🔗</span>
            <strong style={{ color: '#e2e8f0', fontSize: '0.9rem' }}>
              {rel.label || rel.type || rel.target_object_type || 'Relationship'}
            </strong>
            <span className="ubme-badge">{rel.type || rel.relationship_type || 'related'}</span>
          </div>
          <div style={{ color: '#64748b', fontSize: '0.8rem' }}>
            Target: <span style={{ color: '#94a3b8' }}>{rel.target_object_type || '—'}</span>
          </div>
          {/* Related objects would be loaded from the relationship endpoint here */}
        </div>
      ))}
    </div>
  );
}

// ── Generic Tab ──

function GenericTab({ icon, label }: { icon: string; label: string }) {
  return (
    <GenericEmptyState
      icon={icon}
      title={label}
      message={`${label} data will be available when the object has related ${label.toLowerCase()} entries.`}
    />
  );
}

function GenericEmptyState({ icon, title, message }: { icon: string; title: string; message: string }) {
  return (
    <div className="ubme-empty-state">
      <div className="ubme-empty-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}

// ── Helpers ──

function formatFieldValue(field: FieldDef, value: any): React.ReactNode {
  if (value === null || value === undefined) return <span style={{ color: '#64748b' }}>—</span>;

  switch (field.field_type) {
    case 'boolean':
      return value ? '✅ Yes' : '❌ No';
    case 'currency':
      return `$${Number(value).toFixed(2)}`;
    case 'percentage':
      return `${value}%`;
    case 'date':
    case 'datetime':
      return new Date(value).toLocaleString();
    case 'email':
      return <a href={`mailto:${value}`} style={{ color: '#6366f1' }}>{value}</a>;
    case 'phone':
      return <a href={`tel:${value}`} style={{ color: '#6366f1' }}>{value}</a>;
    case 'url':
      return <a href={value} target="_blank" rel="noopener noreferrer" style={{ color: '#6366f1' }}>{value}</a>;
    case 'json':
      return <pre style={{ background: '#0f172a', padding: '0.75rem', borderRadius: '0.5rem', overflow: 'auto', fontSize: '0.8rem' }}>{JSON.stringify(value, null, 2)}</pre>;
    case 'select':
    case 'text':
    case 'long_text':
    case 'rich_text':
    default:
      return String(value);
  }
}