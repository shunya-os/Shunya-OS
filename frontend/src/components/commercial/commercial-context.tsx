/**
 * CommercialContext — contextual commercial panel for a relationship.
 *
 * Displays what matters about this relationship right now:
 * - Active opportunity/need
 * - Proposals/offers
 * - Next action
 * - Commercial context summary
 *
 * Uses the real G4 API. Shows loading/error states gracefully.
 */
import { useState, useEffect } from 'react';
import type { ComponentProps } from '../executive/index';
import { Badge, Panel } from '../executive/index';

interface CommercialContextProps {
  relationshipId?: number | string;
  organizationId?: number;
}

interface Opportunity {
  id: number;
  title: string;
  lifecycle_state: string;
  estimated_value?: number;
  currency?: string;
  confidence?: number;
  next_action?: string;
  next_action_due_at?: string;
}

interface ContextData {
  context: {
    summary?: string;
    active_opportunity?: Opportunity | null;
    engagement_level?: number;
    relationship_health?: number;
    lifetime_value_estimate?: number;
    retention_risk?: number;
    suggested_next_action?: string;
    suggested_action_reason?: string;
  } | null;
  opportunities: Opportunity[];
}

const STATE_LABELS: Record<string, string> = {
  discovered: 'Identified',
  being_understood: 'Learning',
  active: 'Active',
  waiting: 'Waiting',
  proposal_pending: 'Proposal Sent',
  accepted: 'Accepted',
  declined: 'Declined',
  committed: 'Committed',
  executing: 'Executing',
  completed: 'Completed',
  lost: 'Lost',
};

const STATE_COLORS: Record<string, string> = {
  discovered: 'info',
  being_understood: 'info',
  active: 'success',
  waiting: 'warning',
  proposal_pending: 'info',
  accepted: 'success',
  declined: 'danger',
  committed: 'success',
  executing: 'success',
  completed: 'neutral',
  lost: 'danger',
};

function fetchContext(
  relationshipId: number | string,
): Promise<ContextData | null> {
  return fetch(`/api/v1/commercial/context/${relationshipId}`, {
    credentials: 'include',
  })
    .then((r) => (r.ok ? r.json() : null))
    .catch(() => null);
}

export function CommercialContext({
  state,
  loading: panelLoading,
  error: panelError,
  label,
}: ComponentProps<CommercialContextProps>) {
  const relationshipId = state.relationshipId;
  const [data, setData] = useState<ContextData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!relationshipId) {
      setLoading(false);
      setError('No relationship selected');
      return;
    }
    setLoading(true);
    setError(null);
    fetchContext(relationshipId)
      .then((result) => {
        if (result) {
          setData(result);
        } else {
          setData(null);
          setError('No commercial context available');
        }
      })
      .catch((e) => {
        setError(e.message || 'Failed to load commercial context');
      })
      .finally(() => setLoading(false));
  }, [relationshipId]);

  if (panelError)
    return (
      <Panel id="commercial-context" name={label ?? 'Commercial Context'} error={panelError} />
    );
  if (loading || panelLoading)
    return (
      <Panel id="commercial-context" name={label ?? 'Commercial Context'} loading>
        <div className="sh-comp-skeleton" aria-busy="true">
          <div className="sh-skel-line w-3/4" />
          <div className="sh-skel-line w-full" />
          <div className="sh-skel-line w-1/2" />
        </div>
      </Panel>
    );

  if (error || !data || !data.context) {
    return (
      <Panel id="commercial-context" name={label ?? 'Commercial Context'}>
        <div style={{ padding: '8px 0', fontSize: 'var(--sh-text-sm)', color: 'var(--sh-text-secondary)' }}>
          {error || 'No commercial context for this relationship'}
        </div>
        {data?.opportunities && data.opportunities.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div style={{ fontSize: 10, textTransform: 'uppercase', color: 'var(--sh-text-secondary)', letterSpacing: '0.08em', marginBottom: 6 }}>
              Opportunities ({data.opportunities.length})
            </div>
            {data.opportunities.slice(0, 3).map((opp) => (
              <div
                key={opp.id}
                style={{
                  padding: '6px 0',
                  borderBottom: '1px solid var(--sh-border)',
                  fontSize: 'var(--sh-text-sm)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                  <Badge
                    state={{
                      text: STATE_LABELS[opp.lifecycle_state] ?? opp.lifecycle_state,
                      variant: (STATE_COLORS[opp.lifecycle_state] ?? 'neutral') as any,
                    }}
                  />
                  <span style={{ fontWeight: 500 }}>{opp.title}</span>
                </div>
                {opp.estimated_value != null && opp.estimated_value > 0 && (
                  <div style={{ fontSize: 'var(--sh-text-xs)', color: 'var(--sh-text-secondary)' }}>
                    {opp.currency ?? ''} {opp.estimated_value.toLocaleString()}
                    {opp.confidence != null ? ` · ${opp.confidence}% conf` : ''}
                  </div>
                )}
                {opp.next_action && (
                  <div style={{ fontSize: 'var(--sh-text-xs)', color: 'var(--sh-warning)', marginTop: 2 }}>
                    Next: {opp.next_action}
                    {opp.next_action_due_at ? ` (due ${new Date(opp.next_action_due_at).toLocaleDateString()})` : ''}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Panel>
    );
  }

  const ctx = data.context;
  const activeOpp = ctx.active_opportunity;
  const opportunities = data.opportunities;

  return (
    <Panel id="commercial-context" name={label ?? 'Commercial Context'}>
      {/* Summary */}
      {ctx.summary && (
        <div
          style={{
            padding: '8px 0',
            fontSize: 'var(--sh-text-sm)',
            lineHeight: 1.5,
            color: 'var(--sh-text-primary)',
            borderBottom: '1px solid var(--sh-border)',
            marginBottom: 8,
          }}
        >
          {ctx.summary}
        </div>
      )}

      {/* Active opportunity */}
      {activeOpp && (
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', color: 'var(--sh-text-secondary)', letterSpacing: '0.08em', marginBottom: 4 }}>
            Active Opportunity
          </div>
          <div style={{ padding: '6px 0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
              <Badge
                state={{
                  text: STATE_LABELS[activeOpp.lifecycle_state] ?? activeOpp.lifecycle_state,
                  variant: (STATE_COLORS[activeOpp.lifecycle_state] ?? 'neutral') as any,
                }}
              />
              <span style={{ fontWeight: 500, fontSize: 'var(--sh-text-sm)' }}>{activeOpp.title}</span>
            </div>
            {activeOpp.estimated_value != null && activeOpp.estimated_value > 0 && (
              <div style={{ fontSize: 'var(--sh-text-xs)', color: 'var(--sh-text-secondary)', marginTop: 2 }}>
                {activeOpp.currency ?? ''} {activeOpp.estimated_value.toLocaleString()}
                {activeOpp.confidence != null ? ` · ${activeOpp.confidence}% confidence` : ''}
              </div>
            )}
            {activeOpp.next_action && (
              <div style={{ fontSize: 'var(--sh-text-xs)', color: 'var(--sh-warning)', marginTop: 2 }}>
                Next: {activeOpp.next_action}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Suggested next action */}
      {ctx.suggested_next_action && (
        <div style={{ marginBottom: 8, padding: '6px 8px', border: '1px solid var(--sh-gold)', borderRadius: 6 }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', color: 'var(--sh-text-secondary)', letterSpacing: '0.08em', marginBottom: 2 }}>
            Suggested Next Action
          </div>
          <div style={{ fontSize: 'var(--sh-text-sm)', fontWeight: 500 }}>{ctx.suggested_next_action}</div>
          {ctx.suggested_action_reason && (
            <div style={{ fontSize: 'var(--sh-text-xs)', color: 'var(--sh-text-secondary)', marginTop: 2 }}>
              {ctx.suggested_action_reason}
            </div>
          )}
        </div>
      )}

      {/* Health indicators */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 8,
          padding: '4px 0',
          fontSize: 'var(--sh-text-xs)',
          color: 'var(--sh-text-secondary)',
        }}
      >
        {ctx.engagement_level != null && (
          <div>
            <div>Engagement</div>
            <div style={{ fontWeight: 500, color: 'var(--sh-text-primary)' }}>{ctx.engagement_level}/100</div>
          </div>
        )}
        {ctx.relationship_health != null && (
          <div>
            <div>Health</div>
            <div style={{ fontWeight: 500, color: 'var(--sh-text-primary)' }}>{ctx.relationship_health}/100</div>
          </div>
        )}
        {ctx.retention_risk != null && (
          <div>
            <div>Retention Risk</div>
            <div style={{ fontWeight: 500, color: 'var(--sh-text-primary)' }}>{ctx.retention_risk}/100</div>
          </div>
        )}
        {ctx.lifetime_value_estimate != null && ctx.lifetime_value_estimate > 0 && (
          <div>
            <div>LTV Estimate</div>
            <div style={{ fontWeight: 500, color: 'var(--sh-text-primary)' }}>{ctx.lifetime_value_estimate.toLocaleString()}</div>
          </div>
        )}
      </div>

      {/* Other opportunities */}
      {opportunities.length > 1 && (
        <div style={{ marginTop: 8 }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', color: 'var(--sh-text-secondary)', letterSpacing: '0.08em', marginBottom: 4 }}>
            Other Opportunities ({opportunities.length - (activeOpp ? 1 : 0)})
          </div>
          {opportunities
            .filter((o) => !activeOpp || o.id !== activeOpp.id)
            .slice(0, 3)
            .map((opp) => (
              <div
                key={opp.id}
                style={{
                  padding: '4px 0',
                  borderBottom: '1px solid var(--sh-border)',
                  fontSize: 'var(--sh-text-xs)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Badge
                    state={{
                      text: STATE_LABELS[opp.lifecycle_state] ?? opp.lifecycle_state,
                      variant: (STATE_COLORS[opp.lifecycle_state] ?? 'neutral') as any,
                    }}
                  />
                  <span style={{ fontWeight: 500 }}>{opp.title}</span>
                </div>
              </div>
            ))}
        </div>
      )}
    </Panel>
  );
}
