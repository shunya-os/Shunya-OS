/**
 * SHUNYA — Global Notification System
 *
 * NotificationProvider wraps the app root and provides:
 *  - addNotification() for any component to fire a toast
 *  - dismissNotification() to manually close
 *  - clearAll() for the history panel
 *  - notification history (last 50 kept in memory)
 *
 * The <NotificationToast /> component is rendered automatically
 * inside the provider as a fixed-position stack overlay.
 */
import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from 'react';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message: string;
  timestamp: number;
  duration?: number; // auto-dismiss ms (0 = persistent)
}

interface NotificationContextType {
  notifications: Notification[];
  addNotification: (n: Omit<Notification, 'id' | 'timestamp'>) => void;
  dismissNotification: (id: string) => void;
  clearAll: () => void;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());

  const addNotification = useCallback(
    (n: Omit<Notification, 'id' | 'timestamp'>) => {
      const notif: Notification = {
        ...n,
        id: Date.now().toString() + Math.random().toString(36).slice(2, 8),
        timestamp: Date.now(),
      };
      setNotifications((prev) => [notif, ...prev].slice(0, 50));
      // Auto-dismiss unless duration is explicitly 0
      if (n.duration !== 0) {
        setTimeout(() => {
          setDismissedIds((prev) => new Set(prev).add(notif.id));
        }, n.duration || 5000);
      }
    },
    [],
  );

  const dismissNotification = useCallback((id: string) => {
    setDismissedIds((prev) => new Set(prev).add(id));
  }, []);

  const clearAll = useCallback(() => {
    const allIds = notifications.map((n) => n.id);
    setDismissedIds((prev) => {
      const next = new Set(prev);
      allIds.forEach((id) => next.add(id));
      return next;
    });
  }, [notifications]);

  const activeNotifications = notifications.filter(
    (n) => !dismissedIds.has(n.id),
  );

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        addNotification,
        dismissNotification,
        clearAll,
      }}
    >
      {children}
      <NotificationToast
        notifications={activeNotifications}
        onDismiss={dismissNotification}
      />
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const ctx = useContext(NotificationContext);
  if (!ctx) {
    throw new Error(
      'useNotifications must be used within a NotificationProvider',
    );
  }
  return ctx;
}

// ── Toast Overlay ──
function NotificationToast({
  notifications,
  onDismiss,
}: {
  notifications: Notification[];
  onDismiss: (id: string) => void;
}) {
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

// ── Inline styles (no external CSS dependency) ──

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

// Inject keyframe animation for slide-in
if (typeof document !== 'undefined') {
  const styleId = 'sh-notification-anim';
  // Only inject once
  if (!document.getElementById(styleId)) {
    const el = document.createElement('style');
    el.id = styleId;
    el.textContent = `
@keyframes sh-slide-in {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}`;
    document.head.appendChild(el);
  }
}