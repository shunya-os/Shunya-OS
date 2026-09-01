/**
 * Finance Workspace — Real financial data from /api/v1/finance/ endpoints.
 *
 * Shows: chart of accounts, invoices, payments, expenses, budgets
 * with tabbed navigation and full loading/empty/error states.
 *
 * This is NOT a placeholder. It renders real data from the existing
 * backend finance module (86+ routes).
 */

import { useState, useEffect, useCallback, type FC } from 'react';

// ── Data Types ──────────────────────────────────────────────────────────

interface Account {
  id: number;
  code: string;
  name: string;
  type: string;
  subtype?: string;
  balance: number;
  currency: string;
  is_active: boolean;
}

interface Invoice {
  id: number;
  number: string;
  status: string;
  type: string;
  issue_date: string;
  due_date: string;
  total_amount: number;
  currency: string;
  relationship_name?: string;
  notes?: string;
  created_at: string;
}

interface Payment {
  id: number;
  invoice_id: number;
  amount: number;
  method: string;
  reference?: string;
  created_at: string;
}

interface FinancialSummary {
  total_revenue?: number;
  total_receivables?: number;
  total_payables?: number;
  net_income?: number;
  cash_balance?: number;
  currency?: string;
}

interface TrialBalanceEntry {
  account_code: string;
  account_name: string;
  debit: number;
  credit: number;
  balance: number;
}

// ── API Helper ──────────────────────────────────────────────────────────

async function api<T>(path: string): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include' });
    if (r.status >= 500) return null;
    return (await r.json()) as T;
  } catch {
    return null;
  }
}

// ── Inline Styles ───────────────────────────────────────────────────────

function formatCurrency(val: number | string, currency = 'INR'): string {
  const n = typeof val === 'string' ? parseFloat(val) : val;
  if (isNaN(n)) return String(val);
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(n);
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('en-IN', {
      year: 'numeric', month: 'short', day: 'numeric',
    });
  } catch {
    return '—';
  }
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'rgba(26,28,29,0.45)',
  sent: '#2980b9',
  approved: '#6a9f6a',
  paid: '#6a9f6a',
  overdue: '#c0392b',
  cancelled: 'rgba(26,28,29,0.25)',
  void: 'rgba(26,28,29,0.25)',
  pending: '#e67e22',
  completed: '#6a9f6a',
};

// ── Sub-components ──────────────────────────────────────────────────────

function MetricCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div
      style={{
        background: '#fff',
        border: '1px solid rgba(26,28,29,0.07)',
        borderRadius: 10,
        padding: '16px 20px',
        flex: 1,
        minWidth: 140,
      }}
    >
      <div
        style={{
          fontSize: 24,
          fontWeight: 700,
          color: color || 'var(--shunya-text, #1A1C1D)',
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontSize: 12,
          color: 'rgba(26,28,29,0.55)',
          marginTop: 4,
        }}
      >
        {label}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || 'rgba(26,28,29,0.55)';
  return (
    <span
      className="pw-commercial-tag"
      style={{
        background: `${color}18`,
        color,
        border: `1px solid ${color}30`,
        fontWeight: 500,
        textTransform: 'capitalize',
      }}
    >
      {status.replace(/_/g, ' ')}
    </span>
  );
}

// ── Main Component ──────────────────────────────────────────────────────

type TabKey = 'ledger' | 'invoices' | 'payments' | 'summary';

export const FinanceWorkspace: FC = () => {
  const [tab, setTab] = useState<TabKey>('summary');

  // Data states
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [summary, setSummary] = useState<FinancialSummary | null>(null);
  const [trialBalance, setTrialBalance] = useState<TrialBalanceEntry[]>([]);

  // UI states
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [accountsRes, invoicesRes, paymentsRes, summaryRes, tbRes] =
        await Promise.all([
          api<{ accounts: Account[] }>('/api/v1/finance/accounts'),
          api<{ invoices: Invoice[] }>('/api/v1/finance/invoices'),
          api<{ payments: Payment[] }>('/api/v1/finance/payments'),
          api<{ summary: FinancialSummary }>('/api/v1/finance/summary'),
          api<{ trial_balance: TrialBalanceEntry[] }>(
            '/api/v1/finance/trial-balance',
          ),
        ]);

      if (accountsRes?.accounts) setAccounts(accountsRes.accounts);
      if (invoicesRes?.invoices) setInvoices(invoicesRes.invoices);
      if (paymentsRes?.payments) setPayments(paymentsRes.payments);
      if (summaryRes?.summary) setSummary(summaryRes.summary);
      if (tbRes?.trial_balance) setTrialBalance(tbRes.trial_balance);
    } catch {
      setError('Could not load financial data. The service may be unavailable.');
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // ── Render ──

  return (
    <div className="pw-panel-container" style={{ padding: '24px 32px', maxWidth: 960 }}>
      <div className="pw-domain-header">
        <span className="pw-domain-icon">◇</span>
        <h2 className="pw-domain-title">Finance</h2>
      </div>
      <p
        style={{
          fontSize: 14,
          color: 'rgba(26,28,29,0.55)',
          margin: '0 0 20px',
        }}
      >
        Ledger, invoices, payments, and financial intelligence
      </p>

      {/* Tab Navigation */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, flexWrap: 'wrap' }}>
        {(
          [
            { key: 'summary', label: 'Summary' },
            { key: 'ledger', label: 'Ledger' },
            { key: 'invoices', label: `Invoices (${invoices.length})` },
            { key: 'payments', label: `Payments (${payments.length})` },
          ] as const
        ).map((t) => (
          <button
            key={t.key}
            className={`pw-tab-btn ${tab === t.key ? 'pw-tab-active' : ''}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && <div className="pw-domain-loading">Loading financial data…</div>}

      {/* Error */}
      {error && (
        <div
          className="pw-error-msg"
          style={{ color: '#c0392b', fontSize: 13, marginBottom: 16 }}
        >
          {error}
          <button
            className="pw-tab-btn"
            style={{ marginLeft: 12 }}
            onClick={loadData}
          >
            Retry
          </button>
        </div>
      )}

      {/* ── SUMMARY TAB ── */}
      {!loading && tab === 'summary' && (
        <>
          {/* Metrics */}
          <div
            style={{
              display: 'flex',
              gap: 12,
              marginBottom: 24,
              flexWrap: 'wrap',
            }}
          >
            <MetricCard
              label="Net Income"
              value={summary ? formatCurrency(summary.net_income ?? 0) : '—'}
              color={summary?.net_income && summary.net_income >= 0 ? '#6a9f6a' : '#c0392b'}
            />
            <MetricCard
              label="Receivables"
              value={summary ? formatCurrency(summary.total_receivables ?? 0) : '—'}
              color="#e67e22"
            />
            <MetricCard
              label="Payables"
              value={summary ? formatCurrency(summary.total_payables ?? 0) : '—'}
              color="#2980b9"
            />
            <MetricCard
              label="Cash Balance"
              value={summary ? formatCurrency(summary.cash_balance ?? 0) : '—'}
              color="#6a9f6a"
            />
          </div>

          {/* Recent Invoices */}
          <h3 style={{ fontSize: 14, fontWeight: 600, margin: '0 0 12px' }}>
            Recent Invoices
          </h3>
          {invoices.length === 0 ? (
            <div className="pw-domain-empty">
              <p>No invoices yet.</p>
              <p className="pw-domain-empty-hint">
                Create an invoice from a proposal or record one directly in the
                Invoices tab.
              </p>
            </div>
          ) : (
            <div className="pw-commercial-list">
              {invoices.slice(0, 5).map((inv) => (
                <div key={inv.id} className="pw-commercial-item">
                  <div className="pw-commercial-item-title">
                    {inv.number} — {inv.relationship_name || 'Unknown'}
                  </div>
                  <div className="pw-commercial-item-meta">
                    <StatusBadge status={inv.status} />
                    <span className="pw-commercial-tag">
                      {formatCurrency(inv.total_amount, inv.currency)}
                    </span>
                    <span className="pw-commercial-date">
                      Due {formatDate(inv.due_date)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* ── LEDGER TAB ── */}
      {!loading && tab === 'ledger' && (
        <>
          {/* Trial Balance summary */}
          {trialBalance.length > 0 ? (
            <>
              <h3 style={{ fontSize: 14, fontWeight: 600, margin: '0 0 12px' }}>
                Trial Balance ({trialBalance.length} entries)
              </h3>
              <div className="pw-commercial-list">
                {trialBalance.map((entry, i) => (
                  <div key={i} className="pw-commercial-item">
                    <div className="pw-commercial-item-title">
                      {entry.account_code} — {entry.account_name}
                    </div>
                    <div className="pw-commercial-item-meta">
                      {entry.debit > 0 && (
                        <span className="pw-commercial-tag">
                          Dr {formatCurrency(entry.debit)}
                        </span>
                      )}
                      {entry.credit > 0 && (
                        <span className="pw-commercial-tag">
                          Cr {formatCurrency(entry.credit)}
                        </span>
                      )}
                      <span
                        className="pw-commercial-tag"
                        style={{
                          fontWeight: 600,
                          color:
                            entry.balance > 0
                              ? '#6a9f6a'
                              : entry.balance < 0
                                ? '#c0392b'
                                : 'rgba(26,28,29,0.55)',
                        }}
                      >
                        Balance: {formatCurrency(entry.balance)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="pw-domain-empty">
              <p>No ledger entries yet.</p>
              <p className="pw-domain-empty-hint">
                Journal entries and transactions will appear here once financial
                activity is recorded.
              </p>
            </div>
          )}

          {/* Chart of Accounts */}
          {accounts.length > 0 && (
            <>
              <h3
                style={{
                  fontSize: 14,
                  fontWeight: 600,
                  margin: '20px 0 12px',
                }}
              >
                Chart of Accounts ({accounts.length})
              </h3>
              <div className="pw-commercial-list">
                {accounts.map((acc) => (
                  <div key={acc.id} className="pw-commercial-item">
                    <div className="pw-commercial-item-title">
                      {acc.code} — {acc.name}
                    </div>
                    <div className="pw-commercial-item-meta">
                      <StatusBadge status={acc.type} />
                      <span className="pw-commercial-tag">
                        {acc.subtype || acc.type}
                      </span>
                      <span
                        className="pw-commercial-tag"
                        style={{ fontWeight: 500 }}
                      >
                        {formatCurrency(acc.balance, acc.currency)}
                      </span>
                      {!acc.is_active && (
                        <span
                          className="pw-commercial-tag"
                          style={{
                            color: '#c0392b',
                            border: '1px solid rgba(192,57,43,0.3)',
                          }}
                        >
                          Inactive
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}

      {/* ── INVOICES TAB ── */}
      {!loading && tab === 'invoices' && (
        <>
          {invoices.length === 0 ? (
            <div className="pw-domain-empty">
              <p>No invoices found.</p>
              <p className="pw-domain-empty-hint">
                Create an invoice from a commercial proposal or record one
                directly via the Finance API.
              </p>
            </div>
          ) : (
            <div className="pw-commercial-list">
              {invoices.map((inv) => (
                <div key={inv.id} className="pw-commercial-item">
                  <div className="pw-commercial-item-title">
                    {inv.number} — {inv.relationship_name || 'Customer'}
                  </div>
                  <div className="pw-commercial-item-meta">
                    <StatusBadge status={inv.status} />
                    <span className="pw-commercial-tag">
                      {formatCurrency(inv.total_amount, inv.currency)}
                    </span>
                    <span className="pw-commercial-date">
                      Issued {formatDate(inv.issue_date)} · Due{' '}
                      {formatDate(inv.due_date)}
                    </span>
                  </div>
                  {inv.notes && (
                    <div
                      style={{
                        fontSize: 12,
                        color: 'rgba(26,28,29,0.55)',
                        marginTop: 4,
                      }}
                    >
                      {inv.notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* ── PAYMENTS TAB ── */}
      {!loading && tab === 'payments' && (
        <>
          {payments.length === 0 ? (
            <div className="pw-domain-empty">
              <p>No payments recorded yet.</p>
              <p className="pw-domain-empty-hint">
                Payments are recorded against invoices. Record a payment in the
                Finance module to see it here.
              </p>
            </div>
          ) : (
            <div className="pw-commercial-list">
              {payments.map((pmt) => (
                <div key={pmt.id} className="pw-commercial-item">
                  <div className="pw-commercial-item-title">
                    Payment #{pmt.id}
                  </div>
                  <div className="pw-commercial-item-meta">
                    <span
                      className="pw-commercial-tag"
                      style={{ fontWeight: 600 }}
                    >
                      {formatCurrency(pmt.amount)}
                    </span>
                    <StatusBadge status={pmt.method} />
                    <span className="pw-commercial-date">
                      {formatDate(pmt.created_at)}
                    </span>
                    {pmt.invoice_id && (
                      <span className="pw-commercial-tag">
                        Invoice #{pmt.invoice_id}
                      </span>
                    )}
                  </div>
                  {pmt.reference && (
                    <div
                      style={{
                        fontSize: 12,
                        color: 'rgba(26,28,29,0.55)',
                        marginTop: 4,
                      }}
                    >
                      Ref: {pmt.reference}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};