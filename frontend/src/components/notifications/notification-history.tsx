/**
 * SHUNYA — Notification History Panel (Mantine Edition)
 *
 * Hydrates from the canonical backend (GET /api/v1/notifications, polled
 * every 30s) so the panel shows persisted in-app notifications, not just
 * in-memory toasts. Context (toast) notifications are merged on top.
 * Dismiss / Clear All call POST /api/v1/notifications/mark-read.
 *
 * Uses Mantine Paper, Spoiler, Badge, ThemeIcon, Button.
 */
import { useEffect, useState, useCallback } from 'react';
import {
  Paper,
  Group,
  Stack,
  Text,
  Button,
  Badge,
  ThemeIcon,
  Spoiler,
  Box,
  ScrollArea,
} from '@mantine/core';
import { Bell, X, Trash2 } from 'lucide-react';
import { useNotifications, type Notification } from './notification-context';

interface ApiNotification {
  id: number;
  title: string;
  body?: string;
  notification_type?: string;
  is_read?: boolean;
  created_at?: string | null;
}

const POLL_MS = 30_000;

function mapType(nt: string | undefined): Notification['type'] {
  const t = (nt || '').toLowerCase();
  if (t.includes('fail') || t.includes('error')) return 'error';
  if (t.includes('due') || t.includes('reminder') || t.includes('warning')) return 'warning';
  if (t.includes('complete') || t.includes('success') || t.includes('status_change')) return 'success';
  return 'info';
}

function toLocalNotification(n: ApiNotification): Notification {
  const ts = n.created_at ? new Date(n.created_at).getTime() : Date.now();
  return {
    id: `api-${n.id}`,
    type: mapType(n.notification_type),
    title: n.title || 'Notification',
    message: n.body || '',
    timestamp: Number.isFinite(ts) ? ts : Date.now(),
    duration: 0, // persisted notifications do not auto-dismiss
  };
}

export function NotificationHistory() {
  const { notifications: toastNotifications, dismissNotification, clearAll: clearAllToasts } = useNotifications();
  const [apiNotifications, setApiNotifications] = useState<Notification[]>([]);

  const fetchApi = useCallback(async () => {
    try {
      const resp = await fetch('/api/v1/notifications?limit=50', { credentials: 'include' });
      if (!resp.ok) return;
      const body = await resp.json();
      const rows: ApiNotification[] = body?.notifications || [];
      setApiNotifications(rows.map(toLocalNotification));
    } catch { /* keep last known state */ }
  }, []);

  useEffect(() => {
    fetchApi();
    const interval = setInterval(fetchApi, POLL_MS);
    return () => clearInterval(interval);
  }, [fetchApi]);

  const markRead = async (ids?: number[]) => {
    try {
      await fetch('/api/v1/notifications/mark-read', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ids ? { ids } : {}),
      });
      await fetchApi();
    } catch { /* API unreachable — keep state */ }
  };

  const notifications = [...apiNotifications, ...toastNotifications];

  const dismiss = (n: Notification) => {
    if (n.id.startsWith('api-')) {
      const id = Number(n.id.replace('api-', ''));
      if (Number.isFinite(id)) markRead([id]);
      setApiNotifications((prev) => prev.filter((x) => x.id !== n.id));
    } else {
      dismissNotification(n.id);
    }
  };

  const clearAll = () => {
    markRead();
    setApiNotifications([]);
    clearAllToasts();
  };

  const typeConfig: Record<string, { color: string; label: string }> = {
    success: { color: 'green', label: 'Success' },
    error: { color: 'red', label: 'Error' },
    warning: { color: 'yellow', label: 'Warning' },
    info: { color: 'blue', label: 'Info' },
  };

  const formatTime = (ts: number) => {
    const diff = Date.now() - ts;
    if (diff < 60000) return 'just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return `${Math.floor(diff / 86400000)}d ago`;
  };

  return (
    <Box style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', overflow: 'hidden' }}>
      {/* Header */}
      <Group
        justify="space-between"
        p="md"
        style={{ borderBottom: '1px solid var(--mantine-color-gray-2)' }}
      >
        <Text size="sm" fw={600}>Notification History</Text>
        {notifications.length > 0 && (
          <Button
            variant="subtle"
            color="gray"
            size="compact-sm"
            onClick={clearAll}
            leftSection={<Trash2 size={12} />}
          >
            Clear All
          </Button>
        )}
      </Group>

      {notifications.length === 0 ? (
        <Box
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            padding: '48px 24px',
            color: 'var(--mantine-color-gray-5)',
          }}
        >
          <ThemeIcon size={48} radius="xl" color="gray" variant="light">
            <Bell size={24} />
          </ThemeIcon>
          <Text size="sm" c="dimmed">No notifications yet</Text>
        </Box>
      ) : (
        <ScrollArea style={{ flex: 1 }}>
          <Stack gap={4} p="sm">
            {notifications.map((n: Notification) => {
              const cfg = typeConfig[n.type] || typeConfig.info;
              return (
                <Paper
                  key={n.id}
                  p="sm"
                  radius="md"
                  withBorder
                  style={{
                    borderLeft: `3px solid var(--mantine-color-${cfg.color}-6)`,
                  }}
                >
                  <Group gap="sm" align="flex-start" wrap="nowrap">
                    <ThemeIcon
                      size={28}
                      radius="xl"
                      color={cfg.color}
                      variant="light"
                      style={{ flexShrink: 0, marginTop: 1 }}
                    >
                      <X size={12} />
                    </ThemeIcon>

                    <Box style={{ flex: 1, minWidth: 0 }}>
                      <Group gap="xs" align="center" mb={2}>
                        <Text size="sm" fw={500} lineClamp={1}>
                          {n.title}
                        </Text>
                        <Badge size="xs" color={cfg.color} variant="light">
                          {cfg.label}
                        </Badge>
                      </Group>

                      {n.message && (
                        <Spoiler
                          maxHeight={24}
                          showLabel="Show more"
                          hideLabel="Hide"
                          style={{ fontSize: 12 }}
                        >
                          <Text size="xs" c="dimmed" style={{ wordBreak: 'break-word' }}>
                            {n.message}
                          </Text>
                        </Spoiler>
                      )}
                    </Box>

                    <Stack gap={4} align="flex-end" style={{ flexShrink: 0 }}>
                      <Text size="xs" c="dimmed" style={{ whiteSpace: 'nowrap' }}>
                        {formatTime(n.timestamp)}
                      </Text>
                      <Button
                        variant="subtle"
                        color="gray"
                        size="compact-xs"
                        onClick={() => dismiss(n)}
                        aria-label="Dismiss"
                        style={{ opacity: 0.6 }}
                      >
                        <X size={12} />
                      </Button>
                    </Stack>
                  </Group>
                </Paper>
              );
            })}
          </Stack>
        </ScrollArea>
      )}
    </Box>
  );
}