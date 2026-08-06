/**
 * SHUNYA — Notification History Panel (Mantine Edition)
 *
 * Displays all past notifications (up to the last 50 kept in memory)
 * with clear-all button and individual dismiss.
 * Uses Mantine Paper, Spoiler, Badge, ThemeIcon, Button.
 */
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

export function NotificationHistory() {
  const { notifications, dismissNotification, clearAll } = useNotifications();

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
                        onClick={() => dismissNotification(n.id)}
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