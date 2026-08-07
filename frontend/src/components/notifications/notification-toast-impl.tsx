/**
 * SHUNYA — Standalone Notification Toast
 *
 * Exported for flexibility when you need a toast overlay
 * without the full NotificationProvider context.
 *
 * The provider already includes its own <NotificationToast />,
 * so you don't need to render this separately in most cases.
 */
import { type Notification } from './notification-context';

interface ToastProps {
  notifications: Notification[];
  onDismiss: (id: string) => void;
}

export function NotificationToast({
  notifications,
  onDismiss,
}: ToastProps) {
  if (notifications.length === 0) return null;

  const typeStyles: Record<string, { bg: string; icon: string }> = {
    success: { bg: '#065F46', icon: '✓' },
    error: { bg: '#991B1B', icon: '✕' },
    warning: { bg: '#92400E', icon: '⚠' },
    info: { bg: '#1E40AF', icon: '●' },
  };

  return (
    <div style={containerStyle}>
      {notifications.map((n) => {
        const style = typeStyles[n.type] || typeStyles.info;
        return (
          <div
            key={n.id}
            style={{
              ...toastStyle,
              background: style.bg,
              animation: 'sh-slide-in 0.25s ease-out',
            }}
          >
            <span style={iconStyle}>{style.icon}</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={titleStyle}>{n.title}</div>
              {n.message && <div style={msgStyle}>{n.message}</div>}
            </div>
            <button
              onClick={() => onDismiss(n.id)}
              style={closeBtnStyle}
              aria-label="Dismiss"
            >
              ✕
            </button>
          </div>
        );
      })}
    </div>
  );
}

const containerStyle: React.CSSProperties = {
  position: 'fixed',
  top: 16,
  right: 16,
  zIndex: 10000,
  display: 'flex',
  flexDirection: 'column',
  gap: 8,
  maxWidth: 380,
  pointerEvents: 'auto',
};

const toastStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'flex-start',
  gap: 10,
  padding: '10px 14px',
  borderRadius: 10,
  color: '#fff',
  fontSize: 13,
  lineHeight: 1.4,
  boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
  fontFamily: 'inherit',
};

const iconStyle: React.CSSProperties = {
  flexShrink: 0,
  width: 20,
  height: 20,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: '50%',
  background: 'rgba(255,255,255,0.2)',
  fontSize: 11,
  fontWeight: 700,
  marginTop: 1,
};

const titleStyle: React.CSSProperties = {
  fontWeight: 600,
  fontSize: 13,
  marginBottom: 2,
};

const msgStyle: React.CSSProperties = {
  fontSize: 12,
  opacity: 0.85,
  wordBreak: 'break-word',
};

const closeBtnStyle: React.CSSProperties = {
  flexShrink: 0,
  background: 'transparent',
  border: 'none',
  color: 'rgba(255,255,255,0.6)',
  cursor: 'pointer',
  fontSize: 12,
  padding: 2,
  lineHeight: 1,
  fontFamily: 'inherit',
};