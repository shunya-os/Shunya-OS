/**
 * Invoice Detail Modal — clickable invoice view with actions and evidence.
 *
 * Displays full invoice info, related payments, and attached evidence files.
 * Actions vary by invoice status: edit draft, send, record payment, upload evidence.
 */
import { useState, useEffect, type FC } from 'react';

interface InvoiceDetailData {
  id: number;
  number: string;
  status: string;
  issue_date: string;
  due_date: string;
  total_amount: number;
  paid_amount: number;
  currency: string;
  relationship_name?: string;
  notes?: string;
  created_by?: string;
  created_at: string;
}

interface PaymentRecord {
  id: number;
  amount: number;
  method: string;
  reference_number?: string;
  status: string;
  payment_date: string;
  created_at: string;
}

interface EvidenceRecord {
  id: number;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  status: string;
  created_at: string;
  notes?: string;
}

interface Props {
  invoiceId: number;
  onClose: () => void;
  onRefresh: () => void;
}

function fmtCurrency(n: number | string, currency = 'INR'): string {
  const v = typeof n === 'string' ? parseFloat(n) : n;
  if (isNaN(v)) return String(n);
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v);
}

function fmtDate(s: string | null | undefined): string {
  if (!s) return '—';
  try { return new Date(s).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' }); }
  catch { return s; }
}

function statusColor(s: string): string {
  const m = new Map([
    ['draft', '#9575cd'], ['sent', '#42a5f5'], ['approved', '#66bb6a'],
    ['paid', '#2e7d32'], ['overdue', '#ef5350'], ['cancelled', '#9e9e9e'],
    ['refunded', '#ffa726'], ['void', '#78909c'],
  ]);
  return m.get(s) || '#9e9e9e';
}

export const InvoiceDetailModal: FC<Props> = ({ invoiceId, onClose, onRefresh }) => {
  const [inv, setInv] = useState<InvoiceDetailData | null>(null);
  const [payments, setPayments] = useState<PaymentRecord[]>([]);
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [payAmount, setPayAmount] = useState('');
  const [payBusy, setPayBusy] = useState(false);
  const [payMsg, setPayMsg] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [invRes, payRes, evRes] = await Promise.all([
          fetch('/api/v1/finance/invoices/' + invoiceId, { credentials: 'include' }),
          fetch('/api/v1/finance/payments?invoice_id=' + invoiceId + '&limit=20', { credentials: 'include' }),
          fetch('/api/v1/finance/invoices/' + invoiceId + '/evidence', { credentials: 'include' }),
        ]);
        const invBody = await invRes.json();
        if (invBody?.invoice) setInv(invBody.invoice);
        const payBody = await payRes.json();
        if (payBody?.payments) setPayments(payBody.payments);
        const evBody = await evRes.json();
        if (evBody?.evidence) setEvidence(evBody.evidence);
      } catch { setError('Could not load invoice details.'); }
      setLoading(false);
    })();
  }, [invoiceId]);

  const recordPayment = async () => {
    const amt = parseFloat(payAmount);
    if (!amt || amt <= 0) { setPayMsg('Enter a valid amount'); return; }
    setPayBusy(true); setPayMsg('');
    const r = await fetch('/api/v1/finance/payments', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ invoice_id: invoiceId, amount: amt, payment_date: new Date().toISOString().slice(0, 10) }),
    });
    const body = await r.json();
    if (body.payment) { setPayMsg('Payment recorded ✓'); setPayAmount(''); onRefresh(); }
    else { setPayMsg(body.error || 'Failed'); }
    setPayBusy(false);
  };

  const uploadEvidence = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true); setUploadMsg('');
    const fd = new FormData();
    fd.append('file', file);
    const r = await fetch('/api/v1/finance/invoices/' + invoiceId + '/evidence', {
      method: 'POST', credentials: 'include', body: fd,
    });
    const body = await r.json();
    if (body.success) { setUploadMsg('File attached ✓'); e.target.value = ''; onRefresh(); }
    else { setUploadMsg(body.error || 'Upload failed'); }
    setUploading(false);
  };

  if (loading) return <div className="pw-modal-overlay" onClick={onClose}><div className="pw-modal" onClick={e => e.stopPropagation()}>
    <div className="pw-modal-header"><h3>Invoice #{invoiceId}</h3><button onClick={onClose} aria-label="Close">×</button></div>
    <div className="pw-modal-body"><div className="pw-domain-loading">Loading…</div></div>
  </div></div>;

  if (error || !inv) return <div className="pw-modal-overlay" onClick={onClose}><div className="pw-modal" onClick={e => e.stopPropagation()}>
    <div className="pw-modal-header"><h3>Invoice</h3><button onClick={onClose} aria-label="Close">×</button></div>
    <div className="pw-modal-body"><p className="pw-error-msg">{error || 'Not found'}</p></div>
  </div></div>;

  const balance = inv.total_amount - inv.paid_amount;
  const isEditable = inv.status === 'draft' || inv.status === 'sent';

  return (
    <div className="pw-modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Invoice detail">
      <div className="pw-modal pw-modal-wide" onClick={e => e.stopPropagation()} style={{ maxWidth: 640 }}>
        <div className="pw-modal-header">
          <h3>{inv.number}</h3>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ background: statusColor(inv.status), color: '#fff', borderRadius: 6, padding: '2px 10px', fontSize: 11, fontWeight: 600, textTransform: 'capitalize' }}>{inv.status}</span>
            <button onClick={onClose} aria-label="Close" style={{ border: 'none', background: 'transparent', cursor: 'pointer', fontSize: 18, color: 'rgba(26,28,29,0.35)' }}>×</button>
          </div>
        </div>
        <div className="pw-modal-body">
          {/* Invoice fields */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
            <div><label style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)', fontWeight: 600, textTransform: 'uppercase' }}>Customer</label><p style={{ fontSize: 14, margin: '2px 0' }}>{inv.relationship_name || '—'}</p></div>
            <div><label style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)', fontWeight: 600, textTransform: 'uppercase' }}>Amount</label><p style={{ fontSize: 14, fontWeight: 600, margin: '2px 0' }}>{fmtCurrency(inv.total_amount, inv.currency)}</p></div>
            <div><label style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)', fontWeight: 600, textTransform: 'uppercase' }}>Issue Date</label><p style={{ fontSize: 14, margin: '2px 0' }}>{fmtDate(inv.issue_date)}</p></div>
            <div><label style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)', fontWeight: 600, textTransform: 'uppercase' }}>Due Date</label><p style={{ fontSize: 14, margin: '2px 0' }}>{fmtDate(inv.due_date)}</p></div>
            <div><label style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)', fontWeight: 600, textTransform: 'uppercase' }}>Paid</label><p style={{ fontSize: 14, margin: '2px 0', color: '#2e7d32' }}>{fmtCurrency(inv.paid_amount, inv.currency)}</p></div>
            <div><label style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)', fontWeight: 600, textTransform: 'uppercase' }}>Balance Due</label><p style={{ fontSize: 14, margin: '2px 0', color: balance > 0 ? '#e65100' : '#2e7d32' }}>{fmtCurrency(balance, inv.currency)}</p></div>
          </div>
          {inv.notes && <div style={{ fontSize: 13, color: 'rgba(26,28,29,0.55)', marginBottom: 16, padding: 8, background: 'rgba(26,28,29,0.03)', borderRadius: 8 }}>{inv.notes}</div>}

          {/* Actions */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
            {isEditable && (
              <button className="pw-tab-btn" onClick={() => {}} disabled>Edit</button>
            )}
            {inv.status === 'approved' && (
              <button className="pw-tab-btn pw-tab-active" onClick={() => {}} style={{ borderColor: '#2980b9' }}>Send</button>
            )}
            {balance > 0 && inv.status !== 'paid' && inv.status !== 'cancelled' && inv.status !== 'void' && (
              <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                <input
                  type="text" inputMode="decimal" value={payAmount} onChange={e => setPayAmount(e.target.value)}
                  placeholder="Amount" style={{ width: 100, padding: '4px 8px', border: '1px solid rgba(26,28,29,0.12)', borderRadius: 6, fontSize: 13 }}
                  aria-label="Payment amount"
                />
                <button className="pw-tab-btn" onClick={recordPayment} disabled={payBusy} style={{ borderColor: '#2e7d32' }}>
                  {payBusy ? '…' : 'Record payment'}
                </button>
              </div>
            )}
          </div>
          {payMsg && <p style={{ fontSize: 12, color: payMsg.includes('✓') ? '#2e7d32' : '#c0392b', marginBottom: 12 }}>{payMsg}</p>}

          {/* Payments */}
          {payments.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <h4 style={{ fontSize: 13, fontWeight: 600, margin: '0 0 8px', color: 'rgba(26,28,29,0.55)' }}>Payments</h4>
              {payments.map(p => (
                <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid rgba(26,28,29,0.04)', fontSize: 13 }}>
                  <span>{fmtDate(p.payment_date)} · {p.method || '—'}</span>
                  <span style={{ fontWeight: 600, color: '#2e7d32' }}>{fmtCurrency(p.amount)}</span>
                </div>
              ))}
            </div>
          )}

          {/* Evidence / Attachments */}
          <div style={{ marginBottom: 16 }}>
            <h4 style={{ fontSize: 13, fontWeight: 600, margin: '0 0 8px', color: 'rgba(26,28,29,0.55)' }}>
              Payment Evidence <span style={{ fontWeight: 400, color: 'rgba(26,28,29,0.35)' }}>(optional — recommended for payment records)</span>
            </h4>
            {evidence.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {evidence.map(ev => (
                  <div key={ev.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 8px', background: 'rgba(26,28,29,0.02)', borderRadius: 6, fontSize: 12 }}>
                    <span>
                      {ev.mime_type.startsWith('image/') ? '🖼️' : '📎'} {ev.original_filename}
                      <span style={{ color: 'rgba(26,28,29,0.35)', marginLeft: 8 }}>{ev.file_size_bytes ? Math.round(ev.file_size_bytes / 1024) + ' KB' : ''}</span>
                    </span>
                    <span style={{ fontSize: 11, color: 'rgba(26,28,29,0.35)' }}>{fmtDate(ev.created_at)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: 12, color: 'rgba(26,28,29,0.35)', fontStyle: 'italic' }}>No evidence attached yet. Upload a payment screenshot or receipt below.</p>
            )}
            {/* Upload button */}
            <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 8, padding: '6px 12px', border: '1px solid rgba(26,28,29,0.1)', borderRadius: 6, cursor: 'pointer', fontSize: 12, color: 'rgba(26,28,29,0.55)' }}>
              {uploading ? 'Uploading…' : '📎 Attach screenshot or receipt'}
              <input type="file" accept="image/jpeg,image/png,image/webp,image/gif,application/pdf" onChange={uploadEvidence} disabled={uploading} style={{ display: 'none' }} />
            </label>
            {uploadMsg && <p style={{ fontSize: 12, color: uploadMsg.includes('✓') ? '#2e7d32' : '#c0392b', marginTop: 4 }}>{uploadMsg}</p>}
          </div>
        </div>
      </div>
    </div>
  );
};