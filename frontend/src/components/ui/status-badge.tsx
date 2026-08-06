/**
 * StatusBadge — Standard status badge for every SHUNYA workspace space.
 * Every component uses this so all status badges have the same visual style.
 *
 * Inline CSS — no external stylesheet needed.
 */
interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
}

const STATUS_COLORS: Record<string, string> = {
  draft: '#A4865F',
  ai_generating: '#8B7BEE',
  review: '#6C4AE2',
  sent: '#3B82F6',
  paid: '#10B981',
  overdue: '#EF4444',
  active: '#10B981',
  pending: '#A4865F',
  completed: '#10B981',
  cancelled: '#EF4444',
  rejected: '#EF4444',
  booked: '#059669',
  in_progress: '#6C4AE2',
  accepted: '#10B981',
};

const STATUS_LABELS: Record<string, string> = {
  draft: 'Draft',
  ai_generating: 'AI Generating…',
  review: 'In Review',
  sent: 'Sent',
  paid: 'Paid',
  overdue: 'Overdue',
  active: 'Active',
  pending: 'Pending',
  completed: 'Completed',
  cancelled: 'Cancelled',
  rejected: 'Rejected',
  booked: 'Booked',
  in_progress: 'In Progress',
  accepted: 'Accepted',
};

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const color = STATUS_COLORS[status] || '#A4865F';
  const label = STATUS_LABELS[status] || status;
  return (
    <span className={`sh-badge sh-badge-${size}`} style={{ background: color }}>
      {label}
    </span>
  );
}
