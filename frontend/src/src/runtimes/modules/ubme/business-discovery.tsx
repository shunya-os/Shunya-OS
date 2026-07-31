/** Business Discovery — AI-assisted module generation from natural language. */

import { useState } from 'react';
import type { ModuleDef } from './types';

interface DiscoveryResult {
  status: string;
  module: ModuleDef;
  generated_type: string;
}

export function BusinessDiscovery({ onInstalled }: { onInstalled?: (module: ModuleDef) => void }) {
  const [step, setStep] = useState<'describe' | 'generating' | 'preview' | 'error'>('describe');
  const [description, setDescription] = useState('');
  const [businessName, setBusinessName] = useState('');
  const [result, setResult] = useState<DiscoveryResult | null>(null);
  const [errorMessage, setErrorMessage] = useState('');

  async function handleDiscover() {
    if (!description.trim()) return;
    setStep('generating');
    setErrorMessage('');

    try {
      const resp = await fetch('/api/ubme/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          description: description.trim(),
          business_name: businessName.trim(),
        }),
      });
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.error || `HTTP ${resp.status}`);
      }
      const data: DiscoveryResult = await resp.json();
      setResult(data);
      setStep('preview');
    } catch (err: any) {
      setErrorMessage(err.message || 'Discovery failed. Check console for details.');
      setStep('error');
    }
  }

  async function handleInstall() {
    if (!result) return;
    try {
      const resp = await fetch('/api/ubme/discover/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ module: result.module }),
      });
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.error || `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      onInstalled?.(data.module);
    } catch (err: any) {
      setErrorMessage('Installation failed: ' + err.message);
    }
  }

  // ── Describe step ──
  if (step === 'describe') {
    return (
      <div className="ubme-discovery">
        <div className="ubme-discovery-header">
          <span className="ubme-discovery-icon">🤖</span>
          <h2>Business Discovery Engine</h2>
          <p className="ubme-discovery-subtitle">
            Describe your business — SHUNYA will build your module automatically
          </p>
        </div>

        <div className="ubme-discovery-examples">
          <p className="ubme-discovery-examples-label">Try:</p>
          <div className="ubme-discovery-example-chips">
            {['I run a dental clinic', 'I manufacture furniture', "I'm starting a law firm", 'I own a retail store', 'I manage a restaurant'].map((ex) => (
              <button
                key={ex}
                className="ubme-discovery-chip"
                onClick={() => { setDescription(ex); setBusinessName(''); }}
              >
                {ex}
              </button>
            ))}
          </div>
        </div>

        <div className="ubme-discovery-form">
          <div className="ubme-form-row">
            <label>What is your business? Describe it in a sentence.</label>
            <textarea
              className="ubme-input ubme-textarea"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. I run a dental clinic with 3 dentists focusing on cosmetic dentistry"
              rows={3}
            />
          </div>
          <div className="ubme-form-row">
            <label>Business name (optional)</label>
            <input
              className="ubme-input"
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              placeholder="e.g. SmileCare Dental"
            />
          </div>
          <button
            className="ubme-btn-primary"
            onClick={handleDiscover}
            disabled={!description.trim()}
          >
            🪄 Generate Business Module
          </button>
        </div>
      </div>
    );
  }

  // ── Generating step ──
  if (step === 'generating') {
    return (
      <div className="ubme-discovery ubme-discovery-generating">
        <div className="ubme-discovery-spinner">⏳</div>
        <h3>Analyzing your business...</h3>
        <p>SHUNYA is determining the right object types, fields, workflows, and dashboards for your business.</p>
        <div className="ubme-discovery-progress">
          <div className="ubme-discovery-progress-dots">
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
        </div>
      </div>
    );
  }

  // ── Error step ──
  if (step === 'error') {
    return (
      <div className="ubme-discovery ubme-discovery-error">
        <div className="ubme-discovery-error-icon">😕</div>
        <h3>Discovery Failed</h3>
        <p>{errorMessage}</p>
        <button className="ubme-btn-secondary" onClick={() => setStep('describe')}>
          Try Again
        </button>
      </div>
    );
  }

  // ── Preview step ──
  if (!result) return null;
  const mod = result.module;
  const otCount = mod.object_types?.length || 0;
  const fieldCount = mod.object_types?.reduce((acc, ot) => acc + (ot.fields?.length || 0), 0) || 0;
  const actionCount = mod.object_types?.reduce((acc, ot) => acc + (ot.actions?.length || 0), 0) || 0;

  return (
    <div className="ubme-discovery ubme-discovery-preview">
      <div className="ubme-discovery-preview-header">
        <span style={{ fontSize: '2rem' }}>{mod.icon || '📦'}</span>
        <h2>{mod.name}</h2>
        <span className="ubme-discovery-badge">{result.generated_type === 'ai' ? 'AI Generated' : 'Rule Based'}</span>
      </div>
      <p className="ubme-discovery-preview-desc">{mod.description}</p>

      <div className="ubme-discovery-stats">
        <div className="ubme-discovery-stat">
          <span className="ubme-discovery-stat-value">{otCount}</span>
          <span className="ubme-discovery-stat-label">Object Types</span>
        </div>
        <div className="ubme-discovery-stat">
          <span className="ubme-discovery-stat-value">{fieldCount}</span>
          <span className="ubme-discovery-stat-label">Fields</span>
        </div>
        <div className="ubme-discovery-stat">
          <span className="ubme-discovery-stat-value">{actionCount}</span>
          <span className="ubme-discovery-stat-label">Actions</span>
        </div>
        <div className="ubme-discovery-stat">
          <span className="ubme-discovery-stat-value">{mod.dashboard_cards?.length || 0}</span>
          <span className="ubme-discovery-stat-label">Dashboard Cards</span>
        </div>
      </div>

      <div className="ubme-discovery-object-types">
        {mod.object_types?.map((ot) => (
          <div key={ot.key} className="ubme-discovery-ot">
            <div className="ubme-discovery-ot-header">
              <span>{ot.icon || '📦'}</span>
              <strong>{ot.name}</strong>
              <span className="ubme-badge">{ot.fields?.length || 0} fields</span>
              {ot.lifecycle && <span className="ubme-badge">{ot.lifecycle.length} stages</span>}
            </div>
            <div className="ubme-discovery-ot-fields">
              {ot.fields?.slice(0, 6).map((f) => (
                <span key={f.key} className="ubme-field-chip">
                  {f.label}{f.required ? '*' : ''}
                </span>
              ))}
              {(ot.fields?.length || 0) > 6 && (
                <span className="ubme-more-fields">+{(ot.fields?.length || 0) - 6} more</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="ubme-discovery-actions">
        <button className="ubme-btn-primary" onClick={handleInstall}>
          ✅ Install Module
        </button>
        <button className="ubme-btn-secondary" onClick={() => setStep('describe')}>
          ← Regenerate
        </button>
      </div>
    </div>
  );
}