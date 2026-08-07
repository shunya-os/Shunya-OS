/**
 * NotificationBell — Bell icon with unread count from the backend.
 * Polls /api/v1/integration/notifications/unread-count every 30s.
 */
import { useState, useEffect } from 'react';
import { ActionIcon, Badge, Group } from '@mantine/core';
import { Bell } from 'lucide-react';

export function NotificationBell() {
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const fetchCount = async () => {
      try {
        const resp = await fetch('/api/v1/integration/notifications/unread-count', {
          credentials: 'include',
        });
        if (!resp.ok) return;
        const body = await resp.json();
        if (!cancelled) setUnread(body?.data?.unread_count ?? 0);
      } catch { /* silent */ }
    };
    fetchCount();
    const interval = setInterval(fetchCount, 30000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  return (
    <Group gap={2} style={{ position: 'relative' }}>
      <ActionIcon variant="subtle" color="gray" aria-label="Notifications">
        <Bell size={14} />
      </ActionIcon>
      {unread > 0 && (
        <Badge
          size="xs"
          color="red"
          variant="filled"
          style={{
            position: 'absolute',
            top: -4,
            right: -4,
            minWidth: 14,
            height: 14,
            padding: '0 3px',
            fontSize: 9,
            lineHeight: '14px',
            pointerEvents: 'none',
          }}
        >
          {unread > 99 ? '99+' : unread}
        </Badge>
      )}
    </Group>
  );
}