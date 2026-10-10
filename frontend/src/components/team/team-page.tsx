import { useState, useEffect, useCallback } from 'react';
import {
  IconUsers,
  IconUserPlus,
  IconTrash,
  IconSelector,
  IconMail,
  IconCheck,
  IconX,
} from '@tabler/icons-react';

// ── Types ──────────────────────────────────────────────────────────────

interface TeamMember {
  id: number;
  organization_id: number;
  identity_id: string;
  name: string;
  email: string;
  phone: string;
  role: string;
  designation: string;
  is_active: boolean;
  joined_at: string | null;
  roles: { id: number; name: string; display_name: string }[];
}

interface RoleOption {
  id: number;
  organization_id: number;
  name: string;
  display_name: string;
  description: string;
  permissions: string[];
  is_system: boolean;
}

interface ApiResponse<T> {
  success: boolean;
  data: T;
  total?: number;
  error?: string;
}

// ── Helpers ────────────────────────────────────────────────────────────

function timeAgo(ts: string | null): string {
  if (!ts) return '';
  const d = new Date(ts);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

// ── Main Component ─────────────────────────────────────────────────────

export function TeamPage() {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [roles, setRoles] = useState<RoleOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Invite modal state
  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteName, setInviteName] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState('');

  // Remove confirmation
  const [removing, setRemoving] = useState<number | null>(null);
  const [removingName, setRemovingName] = useState('');

  // Role change state
  const [changingRole, setChangingRole] = useState<number | null>(null);

  const fetchMembers = useCallback(async () => {
    try {
      const r = await fetch('/api/v1/team/members', { credentials: 'include' });
      const d: ApiResponse<TeamMember[]> = await r.json();
      if (d.success) setMembers(d.data || []);
      else setError(d.error || 'Failed to load members');
    } catch {
      setError('Network error loading members');
    }
  }, []);

  const fetchRoles = useCallback(async () => {
    try {
      const r = await fetch('/api/v1/team/roles', { credentials: 'include' });
      const d: ApiResponse<RoleOption[]> = await r.json();
      if (d.success) setRoles(d.data || []);
    } catch { /* roles are secondary */ }
  }, []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      await Promise.all([fetchMembers(), fetchRoles()]);
      setLoading(false);
    })();
  }, [fetchMembers, fetchRoles]);

  // ── Invite ────────────────────────────────────────────────────────────

  const handleInvite = async () => {
    setInviteError('');
    if (!inviteEmail.trim() || !inviteEmail.includes('@')) {
      setInviteError('A valid email is required');
      return;
    }
    setInviting(true);
    try {
      const r = await fetch('/api/v1/team/invite', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: inviteEmail.trim(),
          name: inviteName.trim(),
          role: inviteRole,
        }),
      });
      const d: ApiResponse<any> = await r.json();
      if (d.success) {
        setShowInvite(false);
        setInviteEmail('');
        setInviteName('');
        setInviteRole('member');
        await fetchMembers();
      } else {
        setInviteError(d.error || 'Invitation failed');
      }
    } catch {
      setInviteError('Network error sending invitation');
    }
    setInviting(false);
  };

  // ── Remove ────────────────────────────────────────────────────────────

  const handleRemove = async (memberId: number) => {
    try {
      const r = await fetch(`/api/v1/team/members/${memberId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      const d: ApiResponse<any> = await r.json();
      if (d.success) {
        setMembers((prev) => prev.filter((m) => m.id !== memberId));
      } else {
        setError(d.error || 'Failed to remove member');
      }
    } catch {
      setError('Network error removing member');
    }
    setRemoving(null);
  };

  // ── Change Role ───────────────────────────────────────────────────────

  const handleRoleChange = async (memberId: number, newRole: string) => {
    setChangingRole(memberId);
    try {
      const r = await fetch(`/api/v1/team/members/${memberId}/role`, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: newRole }),
      });
      const d: ApiResponse<any> = await r.json();
      if (d.success) {
        setMembers((prev) =>
          prev.map((m) => (m.id === memberId ? { ...m, role: newRole } : m))
        );
      } else {
        setError(d.error || 'Failed to change role');
      }
    } catch {
      setError('Network error changing role');
    }
    setChangingRole(null);
  };

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <div className="tm-page">
      <style>{teamStyles}</style>

      <div className="tm-header">
        <div className="tm-header-left">
          <IconUsers size={22} className="tm-header-icon" />
          <h1 className="tm-title">Team</h1>
        </div>
        <button className="tm-btn tm-btn-primary" onClick={() => setShowInvite(true)}>
          <IconUserPlus size={16} />
          <span>Invite member</span>
        </button>
      </div>

      {error && (
        <div className="tm-banner tm-banner-error" role="alert">
          <span>{error}</span>
          <button className="tm-banner-close" onClick={() => setError('')} aria-label="Dismiss">
            <IconX size={14} />
          </button>
        </div>
      )}

      {/* Invite Modal */}
      {showInvite && (
        <div className="tm-overlay" onClick={() => setShowInvite(false)}>
          <div className="tm-modal" onClick={(e) => e.stopPropagation()}>
            <div className="tm-modal-header">
              <h2 className="tm-modal-title">Invite team member</h2>
              <button className="tm-modal-close" onClick={() => setShowInvite(false)} aria-label="Close">
                <IconX size={18} />
              </button>
            </div>
            <div className="tm-modal-body">
              <div className="tm-field">
                <label className="tm-label">Email address</label>
                <input
                  type="email"
                  className="tm-input"
                  placeholder="colleague@example.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  autoFocus
                />
              </div>
              <div className="tm-field">
                <label className="tm-label">Name (optional)</label>
                <input
                  type="text"
                  className="tm-input"
                  placeholder="Full name"
                  value={inviteName}
                  onChange={(e) => setInviteName(e.target.value)}
                />
              </div>
              <div className="tm-field">
                <label className="tm-label">Role</label>
                <div className="tm-select-wrapper">
                  <select
                    className="tm-select"
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                  >
                    {roles.length === 0 && <option value="member">Member</option>}
                    {roles.map((r) => (
                      <option key={r.id} value={r.name}>
                        {r.display_name}
                      </option>
                    ))}
                  </select>
                  <IconSelector size={14} className="tm-select-icon" />
                </div>
              </div>
              {inviteError && <p className="tm-field-error">{inviteError}</p>}
            </div>
            <div className="tm-modal-footer">
              <button className="tm-btn" onClick={() => setShowInvite(false)}>
                Cancel
              </button>
              <button
                className="tm-btn tm-btn-primary"
                onClick={handleInvite}
                disabled={inviting}
              >
                {inviting ? 'Sending…' : 'Send invitation'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="tm-loading">
          <div className="tm-loading-shimmer" />
          <p className="tm-loading-text">Loading team members…</p>
        </div>
      )}

      {/* Empty state */}
      {!loading && members.length === 0 && (
        <div className="tm-empty">
          <IconUsers size={40} className="tm-empty-icon" />
          <p className="tm-empty-title">No team members yet</p>
          <p className="tm-empty-desc">
            Invite your first team member to collaborate together.
          </p>
          <button className="tm-btn tm-btn-primary" onClick={() => setShowInvite(true)}>
            <IconUserPlus size={16} />
            <span>Invite member</span>
          </button>
        </div>
      )}

      {/* Member table */}
      {!loading && members.length > 0 && (
        <div className="tm-table-wrap">
          <table className="tm-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Joined</th>
                <th className="tm-th-actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              {members.map((member) => (
                <tr key={member.id}>
                  <td className="tm-td-name">
                    <span className="tm-avatar">
                      {member.name
                        ? member.name.charAt(0).toUpperCase()
                        : (member.email || '?').charAt(0).toUpperCase()}
                    </span>
                    <span className="tm-name-text">{member.name || '—'}</span>
                  </td>
                  <td className="tm-td-email">
                    <IconMail size={13} className="tm-email-icon" />
                    {member.email}
                  </td>
                  <td>
                    <div className="tm-select-wrapper tm-select-small">
                      <select
                        className="tm-select"
                        value={member.role || 'member'}
                        onChange={(e) => handleRoleChange(member.id, e.target.value)}
                        disabled={changingRole === member.id}
                      >
                        {roles.map((r) => (
                          <option key={r.id} value={r.name}>
                            {r.display_name}
                          </option>
                        ))}
                      </select>
                      <IconSelector size={12} className="tm-select-icon" />
                    </div>
                  </td>
                  <td className="tm-td-date">{timeAgo(member.joined_at)}</td>
                  <td className="tm-td-actions">
                    {removing === member.id ? (
                      <div className="tm-confirm-remove">
                        <span className="tm-confirm-text">Remove {removingName}?</span>
                        <button
                          className="tm-btn-icon tm-btn-confirm"
                          onClick={() => handleRemove(member.id)}
                          title="Confirm remove"
                          aria-label="Confirm remove"
                        >
                          <IconCheck size={14} />
                        </button>
                        <button
                          className="tm-btn-icon tm-btn-cancel"
                          onClick={() => setRemoving(null)}
                          title="Cancel"
                          aria-label="Cancel"
                        >
                          <IconX size={14} />
                        </button>
                      </div>
                    ) : (
                      <button
                        className="tm-btn-icon tm-btn-remove"
                        onClick={() => {
                          setRemoving(member.id);
                          setRemovingName(member.name || member.email);
                        }}
                        title="Remove member"
                        aria-label="Remove member"
                      >
                        <IconTrash size={15} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────────────

const teamStyles = `
.tm-page {
  padding: 40px 48px;
  max-width: 960px;
  min-height: 100%;
  background: var(--shunya-bg, #FBF8F5);
  color: var(--shunya-text, #1A1C1D);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
}
.tm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28px;
}
.tm-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.tm-header-icon {
  opacity: 0.7;
  flex-shrink: 0;
}
.tm-title {
  font-size: 22px;
  font-weight: 500;
  margin: 0;
}
.tm-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 13px;
}
.tm-banner-error {
  background: rgba(192,57,43,0.06);
  border: 1px solid rgba(192,57,43,0.15);
  color: #c0392b;
}
.tm-banner-close {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 4px;
  min-height: 44px;
  min-width: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

/* ── Buttons ─────────────────────────────────────── */
.tm-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 8px;
  background: var(--shunya-surface, #ffffff);
  color: var(--shunya-text, #1A1C1D);
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
  min-height: 44px;
}
.tm-btn:hover {
  border-color: var(--shunya-gold, #a4865f);
}
.tm-btn-primary {
  background: var(--shunya-gold, #a4865f);
  color: #fff;
  border-color: var(--shunya-gold, #a4865f);
}
.tm-btn-primary:hover {
  opacity: 0.85;
}
.tm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Modal / Overlay ─────────────────────────────── */
.tm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.tm-modal {
  background: var(--shunya-surface, #ffffff);
  border-radius: 14px;
  width: 420px;
  max-width: calc(100vw - 32px);
  box-shadow: 0 16px 48px rgba(0,0,0,0.12);
}
.tm-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 0;
}
.tm-modal-title {
  font-size: 17px;
  font-weight: 500;
  margin: 0;
}
.tm-modal-close {
  background: none;
  border: none;
  color: rgba(26,28,29,0.55);
  cursor: pointer;
  padding: 4px;
  min-height: 44px;
  min-width: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}
.tm-modal-close:hover {
  color: var(--shunya-text, #1A1C1D);
}
.tm-modal-body {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.tm-modal-footer {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  padding: 0 24px 20px;
}

/* ── Form fields ─────────────────────────────────── */
.tm-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.tm-label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(26,28,29,0.55);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.tm-input {
  padding: 10px 12px;
  font-size: 14px;
  font-family: inherit;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.12));
  border-radius: 8px;
  background: var(--shunya-bg, #FBF8F5);
  color: var(--shunya-text, #1A1C1D);
  outline: none;
  transition: border-color 0.15s;
}
.tm-input:focus {
  border-color: var(--shunya-gold, #a4865f);
}
.tm-input::placeholder {
  color: rgba(26,28,29,0.35);
}
.tm-select-wrapper {
  position: relative;
}
.tm-select {
  width: 100%;
  padding: 10px 32px 10px 12px;
  font-size: 14px;
  font-family: inherit;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.12));
  border-radius: 8px;
  background: var(--shunya-bg, #FBF8F5);
  color: var(--shunya-text, #1A1C1D);
  outline: none;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  transition: border-color 0.15s;
}
.tm-select:focus {
  border-color: var(--shunya-gold, #a4865f);
}
.tm-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.tm-select-icon {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  color: rgba(26,28,29,0.35);
}
.tm-select-small .tm-select {
  padding: 6px 28px 6px 10px;
  font-size: 12px;
  border-radius: 6px;
}
.tm-select-small .tm-select-icon {
  right: 8px;
}
.tm-field-error {
  font-size: 12px;
  color: #c0392b;
  margin: 0;
}

/* ── Loading ─────────────────────────────────────── */
.tm-loading {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 40px 0;
}
.tm-loading-shimmer {
  height: 3px;
  background: linear-gradient(90deg, var(--shunya-border, rgba(26,28,29,0.07)) 0%, var(--shunya-gold, #a4865f) 50%, var(--shunya-border, rgba(26,28,29,0.07)) 100%);
  background-size: 200% 100%;
  animation: tm-shimmer 1.5s infinite;
  border-radius: 2px;
}
@keyframes tm-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
.tm-loading-text {
  font-size: 13px;
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.66));
  margin: 0;
}

/* ── Empty state ─────────────────────────────────── */
.tm-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 60px 40px;
  gap: 12px;
}
.tm-empty-icon {
  opacity: 0.25;
  margin-bottom: 8px;
}
.tm-empty-title {
  font-size: 17px;
  font-weight: 500;
  margin: 0;
}
.tm-empty-desc {
  font-size: 14px;
  color: rgba(26,28,29,0.55);
  max-width: 320px;
  margin: 0 0 8px;
  line-height: 1.5;
}

/* ── Table ───────────────────────────────────────── */
.tm-table-wrap {
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 10px;
  overflow: hidden;
}
.tm-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.tm-table th {
  text-align: left;
  padding: 10px 16px;
  font-size: 11px;
  font-weight: 600;
  color: rgba(26,28,29,0.55);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: var(--shunya-surface-subtle, #f8f7f4);
  border-bottom: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
}
.tm-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--shunya-border, rgba(26,28,29,0.04));
  vertical-align: middle;
}
.tm-table tbody tr:last-child td {
  border-bottom: none;
}
.tm-table tbody tr:hover {
  background: rgba(26,28,29,0.01);
}
.tm-th-actions {
  width: 100px;
  text-align: right;
}

/* ── Table cells ─────────────────────────────────── */
.tm-td-name {
  display: flex;
  align-items: center;
  gap: 10px;
}
.tm-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(164,134,95,0.12);
  color: var(--shunya-gold, #a4865f);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}
.tm-name-text {
  font-weight: 500;
}
.tm-td-email {
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(26,28,29,0.65);
}
.tm-email-icon {
  flex-shrink: 0;
  opacity: 0.4;
}
.tm-td-date {
  color: rgba(26,28,29,0.55);
  font-size: 12px;
  white-space: nowrap;
}
.tm-td-actions {
  text-align: right;
}

/* ── Action icons ────────────────────────────────── */
.tm-btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  background: transparent;
  color: rgba(26,28,29,0.45);
  transition: all 0.15s;
}
.tm-btn-icon:hover {
  background: rgba(26,28,29,0.04);
  color: var(--shunya-text, #1A1C1D);
}
.tm-btn-remove:hover {
  color: #c0392b;
  background: rgba(192,57,43,0.06);
}
.tm-btn-confirm {
  color: #6a9f6a;
}
.tm-btn-confirm:hover {
  background: rgba(106,159,106,0.08);
  color: #4a7f4a;
}
.tm-btn-cancel {
  color: rgba(26,28,29,0.55);
}

/* ── Confirmation inline ─────────────────────────── */
.tm-confirm-remove {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.tm-confirm-text {
  font-size: 11px;
  color: rgba(26,28,29,0.55);
  white-space: nowrap;
}

/* ── Responsive ──────────────────────────────────── */
@media (max-width: 768px) {
  .tm-page {
    padding: 24px 20px;
  }
  .tm-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .tm-table th:nth-child(4),
  .tm-table td:nth-child(4) {
    display: none;
  }
}
@media (max-width: 480px) {
  .tm-page {
    padding: 20px 14px;
  }
  .tm-table th:nth-child(3),
  .tm-table td:nth-child(3) {
    display: none;
  }
}
`;