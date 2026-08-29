/** FDA23 — People Panel: Members, Workload, Attendance, Training, Policy Acks, Persons */

import { useState, useEffect, type FC } from 'react';

interface PersonData {
  id: number;
  tenant_id: number | null;
  canonical_name: string;
  preferred_name: string;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  team_member: {
    id: number;
    email: string;
    role: string;
    is_active: boolean;
  } | null;
}

async function api<T>(path: string, opts?: RequestInit) {
  try {
    const r = await fetch(path, { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...opts });
    return r.json() as Promise<{ success: boolean; data?: T; error?: string }>;
  } catch { return { success: false, error: 'Network error' }; }
}

type Tab = 'members' | 'persons' | 'workload' | 'attendance' | 'training' | 'policies';

export const PeoplePanel: FC = () => {
  const [tab, setTab] = useState<Tab>('members');
  const [members, setMembers] = useState<any[]>([]);
  const [workload, setWorkload] = useState<any>(null);
  const [attendance, setAttendance] = useState<any[]>([]);
  const [trainings, setTrainings] = useState<any[]>([]);
  const [policies, setPolicies] = useState<any[]>([]);
  const [persons, setPersons] = useState<PersonData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    const [m, w, a, t, p, ps] = await Promise.all([
      api<any[]>('/api/v1/people/members'),
      api<any>('/api/v1/people/workload'),
      api<any[]>('/api/v1/people/attendance'),
      api<any[]>('/api/v1/people/training'),
      api<any[]>('/api/v1/people/policies'),
      api<PersonData[]>('/api/v1/people/persons'),
    ]);
    if (m.success) setMembers(m.data || []);
    if (w.success) setWorkload(w.data);
    if (a.success) setAttendance(a.data || []);
    if (t.success) setTrainings(t.data || []);
    if (p.success) setPolicies(p.data || []);
    if (ps.success) setPersons(ps.data || []);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const completeTraining = async (id: string) => {
    await api(`/api/v1/people/training/${id}/complete`, { method: 'POST' });
    load();
  };

  const acknowledgePolicy = async (id: string) => {
    await api(`/api/v1/people/policies/${id}/acknowledge`, { method: 'POST' });
    load();
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: 'members', label: 'Members' },
    { key: 'persons', label: 'Persons' },
    { key: 'workload', label: 'Workload' },
    { key: 'attendance', label: 'Attendance' },
    { key: 'training', label: 'Training' },
    { key: 'policies', label: 'Policies' },
  ];

  return (
    <div className="wksp-people">
      <div className="wksp-admin-tabs">
        {tabs.map(t => (
          <button key={t.key} className={`wksp-admin-tab ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>{t.label}</button>
        ))}
      </div>

      {loading && <div className="wksp-loading-text">Loading…</div>}
      {error && <div className="wksp-error-message">{error}</div>}

      {!loading && tab === 'members' && (
        <div className="wksp-admin-section">
          <h3>Team Members ({members.length})</h3>
          {members.map(m => (
            <div key={m.id} className="wksp-admin-row"><strong>{m.name}</strong> — {m.role} <span className="wksp-muted">{m.email}</span></div>
          ))}
        </div>
      )}

      {!loading && tab === 'persons' && (
        <div className="wksp-admin-section">
          <h3>Canonical Persons ({persons.length})</h3>
          {persons.length === 0 && <p className="wksp-muted">No Person records found for this tenant.</p>}
          <div className="wksp-persons-list">
            {persons.map(p => (
              <div key={p.id} className="wksp-admin-row">
                <strong>{p.preferred_name || p.canonical_name.split('@')[0]}</strong>
                {' '}&mdash; {p.canonical_name}
                <span className="wksp-muted"> | status: {p.status}</span>
                {p.team_member && (
                  <span className="wksp-muted"> | role: {p.team_member.role}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && tab === 'workload' && workload && (
        <div className="wksp-admin-section">
          <h3>Workload Overview</h3>
          <p className="wksp-muted">Total pending: {workload.total_pending_tasks} | Overdue: {workload.total_overdue}</p>
          {workload.members?.map((w: any) => (
            <div key={w.member_id} className="wksp-admin-row">
              <strong>{w.name}</strong> — {w.pending_tasks} pending, {w.overdue_tasks} overdue, {w.pending_approvals} approvals
            </div>
          ))}
        </div>
      )}

      {!loading && tab === 'attendance' && (
        <div className="wksp-admin-section">
          <h3>Attendance / Leave</h3>
          {attendance.length === 0 && <p className="wksp-muted">No attendance records.</p>}
          {attendance.map((a: any, i: number) => (
            <div key={i} className="wksp-admin-row">{a.member_name || a.type} — {a.status}</div>
          ))}
        </div>
      )}

      {!loading && tab === 'training' && (
        <div className="wksp-admin-section">
          <h3>Training Records</h3>
          {trainings.map((t: any) => (
            <div key={t.id} className="wksp-admin-row">
              <strong>{t.title}</strong> — {t.completed ? '✓ Completed' : '✗ Not completed'}
              {!t.completed && <button className="wksp-btn-sm" onClick={() => completeTraining(t.id)}>Mark Complete</button>}
            </div>
          ))}
          {trainings.length === 0 && <p className="wksp-muted">No training modules.</p>}
        </div>
      )}

      {!loading && tab === 'policies' && (
        <div className="wksp-admin-section">
          <h3>Policy Acknowledgement</h3>
          {policies.map((p: any) => (
            <div key={p.id} className="wksp-admin-row">
              <strong>{p.title}</strong> v{p.version} — {p.acknowledged ? '✓ Acknowledged' : '✗ Not acknowledged'}
              {!p.acknowledged && <button className="wksp-btn-sm" onClick={() => acknowledgePolicy(p.id)}>Acknowledge</button>}
            </div>
          ))}
          {policies.length === 0 && <p className="wksp-muted">No policies to acknowledge.</p>}
        </div>
      )}

      <style>{`
.wksp-people { padding: var(--shunya-spacing-md); }
.wksp-btn-sm { margin-left: 8px; padding: 2px 8px; background: var(--shunya-color-primary, #555); border: none; border-radius: 3px; color: #fff; cursor: pointer; font-size: 11px; }
      `}</style>
    </div>
  );
};