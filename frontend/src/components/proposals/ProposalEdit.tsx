/**
 * ProposalEdit — Create or edit a commercial proposal.
 *
 * Posts to /api/v1/commercial/proposals (create) or
 * updates via the PATCH route (not directly available for proposals,
 * so we rely on state transitions and recreate for version bumps).
 *
 * Full form with all CommercialProposal fields:
 * - Title, type, scope, assumptions, exclusions
 * - Pricing (line items), currency, total value
 * - Terms, conditions, validity, delivery timeline
 * - Source context, AI generation toggle
 */
import { useState } from 'react';
import type { FC } from 'react';
import type { ProposalData } from './ProposalList';

interface ProposalEditProps {
  editing?: ProposalData | null;  // null = create mode
  onSave: (proposal: ProposalData) => void;
  onCancel: () => void;
}

async function apiPost<T>(path: string, body: unknown): Promise<T | null> {
  try {
    const r = await fetch(path, {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return await r.json() as T;
  } catch { return null; }
}

export const ProposalEdit: FC<ProposalEditProps> = ({ editing, onSave, onCancel }) => {
  const isEdit = editing !== null;
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // Form state
  const [title, setTitle] = useState(editing?.title || '');
  const [propType, setPropType] = useState(editing?.proposal_type || 'proposal');
  const [opportunityId, setOpportunityId] = useState<number | ''>(editing?.opportunity_id || '');
  const [currency, setCurrency] = useState(editing?.currency || 'INR');
  const [totalValue, setTotalValue] = useState<number | ''>(editing?.total_value || '');
  const [scope, setScope] = useState(editing?.scope_description || '');
  const [assumptions, setAssumptions] = useState(editing?.assumptions || '');
  const [exclusions, setExclusions] = useState(editing?.exclusions || '');
  const [terms, setTerms] = useState(editing?.terms || '');
  const [conditions, setConditions] = useState(editing?.conditions || '');
  const [deliveryTimeline, setDeliveryTimeline] = useState(editing?.delivery_timeline || '');
  const [validFrom, setValidFrom] = useState(editing?.valid_from ? editing.valid_from.substring(0, 10) : '');
  const [validUntil, setValidUntil] = useState(editing?.valid_until ? editing.valid_until.substring(0, 10) : '');
  const [sourceContext, setSourceContext] = useState(editing?.source_context || '');
  const [decisionsRequired, setDecisionsRequired] = useState(
    editing?.decisions_required?.join('\n') || ''
  );
  const [aiGenerated, setAiGenerated] = useState(editing?.ai_generated || false);

  const handleSubmit = async () => {
    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setError('Title is required');
      return;
    }
    setSaving(true);
    setError('');

    const body: Record<string, any> = {
      title: trimmedTitle,
      proposal_type: propType,
      currency,
      total_value: totalValue || 0,
      scope_description: scope.trim(),
      assumptions: assumptions.trim(),
      exclusions: exclusions.trim(),
      terms: terms.trim(),
      conditions: conditions.trim(),
      delivery_timeline: deliveryTimeline.trim(),
      source_context: sourceContext.trim(),
      ai_generated: aiGenerated,
      decisions_required: JSON.stringify(
        decisionsRequired.split('\n').filter((d) => d.trim())
      ),
      created_by: editing?.created_by || 'Founder',
    };

    if (opportunityId) body.opportunity_id = Number(opportunityId);
    if (validFrom) body.valid_from = validFrom;
    if (validUntil) body.valid_until = validUntil;

    try {
      const result = await apiPost<any>('/api/v1/commercial/proposals', body);
      if (result && result.success && result.proposal) {
        onSave(result.proposal);
      } else {
        setError(result?.error || 'Failed to create proposal');
      }
    } catch {
      setError('Network error');
    }
    setSaving(false);
  };

  const inputStyle: React.CSSProperties = {
    padding: '6px 10px',
    border: '1px solid var(--shunya-border, rgba(26,28,29,0.12))',
    borderRadius: 6,
    fontFamily: 'inherit',
    fontSize: 13,
    background: 'var(--shunya-surface, #ffffff)',
    color: 'var(--shunya-text, #1A1C1D)',
    width: '100%',
    boxSizing: 'border-box',
  };

  const labelStyle: React.CSSProperties = {
    fontSize: 11,
    fontWeight: 500,
    color: 'rgba(26,28,29,0.55)',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  };

  return (
    <div className="proposal-edit">
      <div className="proposal-edit-top">
        <h3 className="proposal-edit-title">
          {isEdit ? `Edit: ${editing!.title}` : 'New Proposal'}
        </h3>
        <div className="proposal-edit-top-actions">
          <button className="pw-tab-btn" onClick={onCancel} disabled={saving}>Cancel</button>
          <button
            className="pw-tab-btn"
            style={{ background: 'var(--shunya-gold, #a4865f)', color: '#fff', borderColor: 'transparent' }}
            onClick={handleSubmit}
            disabled={saving}
          >
            {saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Proposal'}
          </button>
        </div>
      </div>

      {error && <div className="pw-error-msg" style={{ marginBottom: 12 }}>{error}</div>}

      <div className="proposal-edit-grid">
        {/* Left column */}
        <div className="proposal-edit-col">
          <div className="proposal-edit-field">
            <label style={labelStyle}>Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={inputStyle}
              placeholder="Proposal title"
              autoFocus
            />
          </div>

          <div className="proposal-edit-field">
            <label style={labelStyle}>Type</label>
            <select value={propType} onChange={(e) => setPropType(e.target.value)} style={inputStyle}>
              <option value="proposal">Proposal</option>
              <option value="offer">Offer</option>
              <option value="quote">Quote</option>
              <option value="estimate">Estimate</option>
            </select>
          </div>

          <div className="proposal-edit-field">
            <label style={labelStyle}>Opportunity ID (optional)</label>
            <input
              type="number"
              value={opportunityId}
              onChange={(e) => setOpportunityId(e.target.value ? Number(e.target.value) : '')}
              style={inputStyle}
              placeholder="Link to an opportunity"
            />
          </div>

          <div className="proposal-edit-row">
            <div className="proposal-edit-field" style={{ flex: 1 }}>
              <label style={labelStyle}>Currency</label>
              <select value={currency} onChange={(e) => setCurrency(e.target.value)} style={inputStyle}>
                <option value="INR">INR</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
              </select>
            </div>
            <div className="proposal-edit-field" style={{ flex: 2 }}>
              <label style={labelStyle}>Total Value</label>
              <input
                type="number"
                value={totalValue}
                onChange={(e) => setTotalValue(e.target.value ? Number(e.target.value) : '')}
                style={inputStyle}
                placeholder="0"
              />
            </div>
          </div>

          <div className="proposal-edit-row">
            <div className="proposal-edit-field" style={{ flex: 1 }}>
              <label style={labelStyle}>Valid From</label>
              <input
                type="date"
                value={validFrom}
                onChange={(e) => setValidFrom(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div className="proposal-edit-field" style={{ flex: 1 }}>
              <label style={labelStyle}>Valid Until</label>
              <input
                type="date"
                value={validUntil}
                onChange={(e) => setValidUntil(e.target.value)}
                style={inputStyle}
              />
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="proposal-edit-col">
          <div className="proposal-edit-field">
            <label style={labelStyle}>Scope Description</label>
            <textarea
              value={scope}
              onChange={(e) => setScope(e.target.value)}
              style={{ ...inputStyle, resize: 'vertical', minHeight: 60 }}
              rows={3}
              placeholder="What this proposal covers"
            />
          </div>

          <div className="proposal-edit-field">
            <label style={labelStyle}>Assumptions</label>
            <textarea
              value={assumptions}
              onChange={(e) => setAssumptions(e.target.value)}
              style={{ ...inputStyle, resize: 'vertical', minHeight: 50 }}
              rows={2}
              placeholder="Key assumptions"
            />
          </div>

          <div className="proposal-edit-field">
            <label style={labelStyle}>Exclusions</label>
            <textarea
              value={exclusions}
              onChange={(e) => setExclusions(e.target.value)}
              style={{ ...inputStyle, resize: 'vertical', minHeight: 50 }}
              rows={2}
              placeholder="What is NOT included"
            />
          </div>

          <div className="proposal-edit-field">
            <label style={labelStyle}>Terms</label>
            <textarea
              value={terms}
              onChange={(e) => setTerms(e.target.value)}
              style={{ ...inputStyle, resize: 'vertical', minHeight: 50 }}
              rows={2}
              placeholder="Payment terms, conditions"
            />
          </div>

          <div className="proposal-edit-field">
            <label style={labelStyle}>Conditions</label>
            <textarea
              value={conditions}
              onChange={(e) => setConditions(e.target.value)}
              style={{ ...inputStyle, resize: 'vertical', minHeight: 50 }}
              rows={2}
              placeholder="Any conditions or dependencies"
            />
          </div>
        </div>
      </div>

      {/* Bottom row fields */}
      <div className="proposal-edit-bottom">
        <div className="proposal-edit-field" style={{ flex: 1 }}>
          <label style={labelStyle}>Delivery Timeline</label>
          <input
            type="text"
            value={deliveryTimeline}
            onChange={(e) => setDeliveryTimeline(e.target.value)}
            style={inputStyle}
            placeholder="e.g. 2 weeks from acceptance"
          />
        </div>
        <div className="proposal-edit-field" style={{ flex: 1 }}>
          <label style={labelStyle}>Source Context</label>
          <input
            type="text"
            value={sourceContext}
            onChange={(e) => setSourceContext(e.target.value)}
            style={inputStyle}
            placeholder="What informed this proposal"
          />
        </div>
      </div>

      <div className="proposal-edit-bottom">
        <div className="proposal-edit-field" style={{ flex: 2 }}>
          <label style={labelStyle}>Decisions Required (one per line)</label>
          <textarea
            value={decisionsRequired}
            onChange={(e) => setDecisionsRequired(e.target.value)}
            style={{ ...inputStyle, resize: 'vertical', minHeight: 50 }}
            rows={2}
            placeholder="Decision 1&#10;Decision 2"
          />
        </div>
        <div className="proposal-edit-field" style={{ flex: 0, display: 'flex', alignItems: 'flex-end', paddingBottom: 8 }}>
          <label style={{ ...labelStyle, display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={aiGenerated}
              onChange={(e) => setAiGenerated(e.target.checked)}
            />
            AI Generated
          </label>
        </div>
      </div>

      <div className="proposal-edit-bottom-actions">
        <button className="pw-tab-btn" onClick={onCancel} disabled={saving}>Cancel</button>
        <button
          className="pw-tab-btn"
          style={{ background: 'var(--shunya-gold, #a4865f)', color: '#fff', borderColor: 'transparent' }}
          onClick={handleSubmit}
          disabled={saving}
        >
          {saving ? 'Saving…' : 'Create Proposal'}
        </button>
      </div>

      <style>{`
.proposal-edit { display: flex; flex-direction: column; }
.proposal-edit-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.proposal-edit-top-actions { display: flex; gap: 6px; }
.proposal-edit-title { font-size: 16px; font-weight: 500; margin: 0; color: var(--shunya-text, #1A1C1D); }
.proposal-edit-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 600px) { .proposal-edit-grid { grid-template-columns: 1fr; } }
.proposal-edit-col { display: flex; flex-direction: column; gap: 10px; }
.proposal-edit-row { display: flex; gap: 8px; }
.proposal-edit-field { display: flex; flex-direction: column; gap: 4px; }
.proposal-edit-bottom { display: flex; gap: 16px; margin-top: 12px; }
@media (max-width: 600px) { .proposal-edit-bottom { flex-direction: column; } }
.proposal-edit-bottom-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--shunya-border, rgba(26,28,29,0.07)); }
      `}</style>
    </div>
  );
};