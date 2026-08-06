/** Field Renderer — renders any field type based on metadata. */

import React from 'react';

interface FieldRendererProps {
  field: { key: string; label: string; field_type: string; options?: string[]; target_object_type?: string };
  value: any;
  onChange?: (key: string, value: any) => void;
  readOnly?: boolean;
}

export function FieldRenderer({ field, value, onChange, readOnly }: FieldRendererProps) {
  const handleChange = (newValue: any) => {
    if (onChange) onChange(field.key, newValue);
  };

  const { field_type, options, label } = field;

  if (readOnly) {
    return (
      <div className="ubme-field ubme-field-readonly">
        <label className="ubme-field-label">{label}</label>
        <div className="ubme-field-value">{renderReadOnlyValue(field_type, value, options)}</div>
      </div>
    );
  }

  return (
    <div className="ubme-field">
      <label className="ubme-field-label">{label}</label>
      {renderInput(field_type, field.key, value ?? '', options, handleChange)}
    </div>
  );
}

function renderReadOnlyValue(type: string, value: any, _options?: string[]): React.ReactNode {
  if (value === null || value === undefined) return <span className="ubme-empty">—</span>;

  switch (type) {
    case 'boolean':
      return value ? '✅ Yes' : '❌ No';
    case 'currency':
      return `$${Number(value).toFixed(2)}`;
    case 'percentage':
      return `${value}%`;
    case 'date':
    case 'datetime':
      return new Date(value).toLocaleDateString();
    case 'email':
      return <a href={`mailto:${value}`}>{value}</a>;
    case 'phone':
      return <a href={`tel:${value}`}>{value}</a>;
    case 'url':
      return (
        <a href={value} target="_blank" rel="noopener noreferrer">
          {value}
        </a>
      );
    case 'json':
      return <pre className="ubme-json">{JSON.stringify(value, null, 2)}</pre>;
    case 'select':
    case 'text':
    case 'long_text':
    default:
      return String(value);
  }
}

function renderInput(
  type: string,
  _key: string,
  value: any,
  options?: string[],
  onChange?: (v: any) => void,
): React.ReactNode {
  switch (type) {
    case 'long_text':
    case 'rich_text':
      return (
        <textarea
          className="ubme-input ubme-textarea"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          rows={4}
        />
      );

    case 'number':
    case 'integer':
    case 'currency':
    case 'percentage':
      return (
        <input
          type="number"
          className="ubme-input"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          step={type === 'integer' ? '1' : '0.01'}
        />
      );

    case 'boolean':
      return (
        <input
          type="checkbox"
          className="ubme-checkbox"
          checked={!!value}
          onChange={(e) => onChange?.(e.target.checked)}
        />
      );

    case 'date':
      return <input type="date" className="ubme-input" value={value} onChange={(e) => onChange?.(e.target.value)} />;

    case 'datetime':
      return (
        <input
          type="datetime-local"
          className="ubme-input"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
        />
      );

    case 'email':
      return (
        <input
          type="email"
          className="ubme-input"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          placeholder="email@example.com"
        />
      );

    case 'phone':
      return (
        <input
          type="tel"
          className="ubme-input"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          placeholder="+1 (555) 000-0000"
        />
      );

    case 'url':
      return (
        <input
          type="url"
          className="ubme-input"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          placeholder="https://"
        />
      );

    case 'select':
      return (
        <select className="ubme-select" value={value} onChange={(e) => onChange?.(e.target.value)}>
          <option value="">Select...</option>
          {(options || []).map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      );

    case 'text':
    default:
      return (
        <input
          type="text"
          className="ubme-input"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          placeholder="Enter value"
        />
      );
  }
}
