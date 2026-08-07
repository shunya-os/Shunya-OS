/**
 * SHUNYA — Knowledge Browser Panel
 * 
 * Browses all entities SHUNYA knows about, grouped by object type.
 * Fetches types from GET /api/v1/founder/objects/types, then loads
 * objects for each type from GET /api/v1/objects/<type>.
 *
 * Mantine v7 card grid with search, detail view, loading/empty/error states.
 * Exported as `KnowledgeBrowserPanel`.
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  SimpleGrid,
  Card,
  Badge,
  TextInput,
  Text,
  Group,
  Stack,
  Paper,
  ScrollArea,
  Skeleton,
  ThemeIcon,
  ActionIcon,
  Divider,
  CloseButton,
} from '@mantine/core';
import {
  Search,
  ArrowLeft,
  Database,
  Calendar,
  FileText,
  Users,
  Receipt,
  Target,
  User,
  BookOpen,
  File,
  CheckCircle2,
  AlertCircle,
  MessageSquare,
} from 'lucide-react';

interface EntityRecord {
  id: number;
  object_id: string;
  object_type: string;
  name: string;
  status: string;
  data: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface EntityTypeEntry {
  type: string;
  count: number;
}

const TYPE_ICONS: Record<string, any> = {
  customer: Users,
  contact: User,
  invoice: Receipt,
  proposal: FileText,
  task: CheckCircle2,
  project: Target,
  employee: Users,
  document: File,
  note: BookOpen,
  conversation: MessageSquare,
};

const TYPE_COLORS: Record<string, string> = {
  customer: 'violet',
  contact: 'blue',
  invoice: 'teal',
  proposal: 'yellow',
  task: 'cyan',
  project: 'grape',
  employee: 'violet',
  document: 'orange',
  note: 'yellow',
  conversation: 'pink',
};

function humanize(key: string): string {
  if (!key) return '';
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function getIcon(type: string, size = 16) {
  const Icon = TYPE_ICONS[type] || Database;
  return <Icon size={size} />;
}

function getColor(type: string): string {
  return TYPE_COLORS[type] || 'gray';
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '\u2014';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

function getKeyFields(obj: EntityRecord): { label: string; value: string }[] {
  const data = obj.data || {};
  const fields: { label: string; value: string }[] = [];
  switch (obj.object_type) {
    case 'customer':
      if (data.contact_name) fields.push({ label: 'Contact', value: data.contact_name });
      if (data.email) fields.push({ label: 'Email', value: data.email });
      if (data.company) fields.push({ label: 'Company', value: data.company });
      break;
    case 'contact':
      if (data.email) fields.push({ label: 'Email', value: data.email });
      if (data.company) fields.push({ label: 'Company', value: data.company });
      if (data.phone) fields.push({ label: 'Phone', value: data.phone });
      break;
    case 'invoice':
      if (data.amount) fields.push({ label: 'Amount', value: `${data.currency || '$'}${data.amount}` });
      if (data.status) fields.push({ label: 'Status', value: data.status });
      break;
    case 'proposal':
      if (data.amount) fields.push({ label: 'Amount', value: `${data.currency || '$'}${data.amount}` });
      if (data.status) fields.push({ label: 'Status', value: data.status });
      break;
    case 'task':
      if (data.status) fields.push({ label: 'Status', value: data.status });
      if (data.priority) fields.push({ label: 'Priority', value: data.priority });
      if (data.assignee) fields.push({ label: 'Assignee', value: data.assignee });
      break;
    case 'project':
      if (data.status) fields.push({ label: 'Status', value: data.status });
      if (data.deadline) fields.push({ label: 'Deadline', value: data.deadline });
      break;
    case 'document':
      if (data.document_type) fields.push({ label: 'Type', value: data.document_type });
      if (data.status) fields.push({ label: 'Status', value: data.status });
      break;
    default:
      let count = 0;
      for (const [key, val] of Object.entries(data)) {
        if (count >= 2) break;
        if (val && typeof val !== 'object') {
          fields.push({ label: humanize(key), value: String(val).slice(0, 60) });
          count++;
        }
      }
      break;
  }
  return fields.slice(0, 3);
}

function EntityCard({ entity, onClick }: { entity: EntityRecord; onClick: () => void }) {
  const color = getColor(entity.object_type);
  const keyFields = getKeyFields(entity);
  return (
    <Card padding="md" radius="md" withBorder style={{ cursor: 'pointer' }} className="kb-card" onClick={onClick}>
      <Card.Section withBorder inheritPadding py="sm">
        <Group justify="space-between" wrap="nowrap">
          <Group gap="xs" wrap="nowrap" style={{ minWidth: 0 }}>
            <ThemeIcon size={28} radius="md" color={color} variant="light">
              {getIcon(entity.object_type, 14)}
            </ThemeIcon>
            <Text size="sm" fw={600} lineClamp={1} style={{ flex: 1 }}>
              {entity.name || 'Untitled'}
            </Text>
          </Group>
          <Badge variant="light" color={color} size="sm" styles={{ label: { textTransform: 'capitalize' } }}>
            {humanize(entity.object_type)}
          </Badge>
        </Group>
      </Card.Section>
      {keyFields.length > 0 && (
        <Stack gap={4} mt="xs">
          {keyFields.map((field) => (
            <Group key={field.label} gap={4} wrap="nowrap">
              <Text size="xs" c="dimmed" style={{ minWidth: 60, flexShrink: 0 }}>{field.label}:</Text>
              <Text size="xs" lineClamp={1}>{field.value}</Text>
            </Group>
          ))}
        </Stack>
      )}
      <Group gap={4} mt="xs">
        <Calendar size={10} />
        <Text size="xs" c="dimmed">{formatDate(entity.created_at)}</Text>
      </Group>
    </Card>
  );
}

function EntityDetail({ entity, onBack }: { entity: EntityRecord; onBack: () => void }) {
  const color = getColor(entity.object_type);
  const data = entity.data || {};
  const standardFields = [
    { label: 'Object ID', value: entity.object_id },
    { label: 'Status', value: entity.status || 'active' },
    { label: 'Created', value: formatDate(entity.created_at) },
    { label: 'Updated', value: formatDate(entity.updated_at) },
  ];
  const dataFields = Object.entries(data)
    .filter(([_, v]) => v !== null && v !== undefined && v !== '')
    .map(([k, v]) => ({ label: humanize(k), value: typeof v === 'object' ? JSON.stringify(v) : String(v) }));

  return (
    <Paper p="md" radius="md" withBorder>
      <Group justify="space-between" mb="md">
        <Group gap="xs">
          <ActionIcon variant="subtle" color="gray" onClick={onBack} aria-label="Back to list">
            <ArrowLeft size={16} />
          </ActionIcon>
          <ThemeIcon size={32} radius="md" color={color} variant="light">
            {getIcon(entity.object_type, 16)}
          </ThemeIcon>
          <div>
            <Text size="sm" fw={600}>{entity.name || 'Untitled'}</Text>
            <Badge variant="light" color={color} size="sm" styles={{ label: { textTransform: 'capitalize' } }}>
              {humanize(entity.object_type)}
            </Badge>
          </div>
        </Group>
      </Group>
      <Divider mb="md" />
      <ScrollArea h={400} type="auto">
        <Stack gap="md">
          <div>
            <Text size="xs" fw={600} c="dimmed" mb={4} tt="uppercase">Details</Text>
            <Stack gap={6}>
              {standardFields.map((f) => (
                <Group key={f.label} gap="xs" wrap="nowrap">
                  <Text size="xs" c="dimmed" style={{ minWidth: 80, flexShrink: 0 }}>{f.label}</Text>
                  <Text size="sm">{f.value}</Text>
                </Group>
              ))}
            </Stack>
          </div>
          {dataFields.length > 0 ? (
            <div>
              <Divider mb="sm" />
              <Text size="xs" fw={600} c="dimmed" mb={4} tt="uppercase">Data Fields</Text>
              <Stack gap={6}>
                {dataFields.map((f) => (
                  <Group key={f.label} gap="xs" wrap="nowrap">
                    <Text size="xs" c="dimmed" style={{ minWidth: 80, flexShrink: 0 }}>{f.label}</Text>
                    <Text size="sm">{f.value}</Text>
                  </Group>
                ))}
              </Stack>
            </div>
          ) : (
            <Text size="xs" c="dimmed" fs="italic">No additional data fields.</Text>
          )}
        </Stack>
      </ScrollArea>
    </Paper>
  );
}

export function KnowledgeBrowserPanel() {
  const [entityTypes, setEntityTypes] = useState<EntityTypeEntry[]>([]);
  const [entities, setEntities] = useState<EntityRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEntity, setSelectedEntity] = useState<EntityRecord | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const typesRes = await fetch('/api/v1/founder/objects/types', { credentials: 'include' });
      if (!typesRes.ok) throw new Error(`HTTP ${typesRes.status}`);
      const typesBody = await typesRes.json();
      if (!typesBody.success) throw new Error(typesBody.error || 'Failed to load types');
      const typeMap: Record<string, number> = typesBody.data || {};
      const typeEntries = Object.entries(typeMap).map(([type, count]) => ({ type, count }));
      if (typeEntries.length === 0) { setEntityTypes([]); setEntities([]); setLoading(false); return; }
      setEntityTypes(typeEntries);
      const allObjects: EntityRecord[] = [];
      const results = await Promise.allSettled(
        typeEntries.map(({ type }) =>
          fetch(`/api/v1/objects/${encodeURIComponent(type)}`, { credentials: 'include' })
            .then((r) => r.ok ? r.json() : null)
        )
      );
      for (const result of results) {
        if (result.status === 'fulfilled' && result.value?.success) {
          const body = result.value.data;
          const items = Array.isArray(body) ? body : (body?.objects || []);
          for (const item of items) {
            allObjects.push({
              id: item.id,
              object_id: item.object_id,
              object_type: item.object_type,
              name: item.name || '',
              status: item.status || 'active',
              data: item.data || {},
              created_at: item.created_at,
              updated_at: item.updated_at,
            });
          }
        }
      }
      allObjects.sort((a, b) => {
        const aTime = a.updated_at || a.created_at || '';
        const bTime = b.updated_at || b.created_at || '';
        return bTime.localeCompare(aTime);
      });
      setEntities(allObjects);
    } catch (err: any) {
      setError(err.message || 'Could not connect to server');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const filteredEntities = useMemo(() => {
    let result = entities;
    if (typeFilter) result = result.filter((e) => e.object_type === typeFilter);
    const q = searchQuery.trim().toLowerCase();
    if (q) {
      result = result.filter((e) => {
        if (e.name?.toLowerCase().includes(q)) return true;
        if (e.object_type?.toLowerCase().includes(q)) return true;
        if (e.data) {
          for (const val of Object.values(e.data)) {
            if (String(val).toLowerCase().includes(q)) return true;
          }
        }
        return false;
      });
    }
    return result;
  }, [entities, searchQuery, typeFilter]);

  const typeCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const e of entities) counts[e.object_type] = (counts[e.object_type] || 0) + 1;
    return counts;
  }, [entities]);

  if (selectedEntity) {
    return <Stack gap="md" style={{ width: '100%' }}>
      <EntityDetail entity={selectedEntity} onBack={() => setSelectedEntity(null)} />
    </Stack>;
  }

  if (loading) {
    return <Stack gap="md" style={{ width: '100%' }}>
      <Skeleton height={40} radius="md" />
      <Group gap="xs">
        {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} height={26} width={80} radius="xl" />)}
      </Group>
      <SimpleGrid cols={{ base: 2, sm: 3, md: 4 }} spacing="md">
        {Array.from({ length: 8 }).map((_, i) => (
          <Card key={i} padding="md" radius="md" withBorder>
            <Group gap="xs" mb="sm"><Skeleton height={28} circle /><Skeleton height={16} width="60%" /></Group>
            <Skeleton height={12} width="80%" mb={4} />
            <Skeleton height={12} width="50%" mb={4} />
            <Skeleton height={10} width="40%" />
          </Card>
        ))}
      </SimpleGrid>
    </Stack>;
  }

  if (error && entities.length === 0) {
    return <Paper p="xl" radius="md" withBorder style={{ textAlign: 'center' }}>
      <ThemeIcon size={48} radius="xl" color="red" variant="light" style={{ margin: '0 auto' }}>
        <AlertCircle size={24} />
      </ThemeIcon>
      <Text size="sm" fw={500} mt="md" c="red">{error}</Text>
      <Text size="xs" c="dimmed" mt={4}>Could not load knowledge entities.</Text>
      <ActionIcon variant="light" color="violet" size="sm" mt="md" onClick={loadData} aria-label="Retry">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="23 4 23 10 17 10" />
          <polyline points="1 20 1 14 7 14" />
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
        </svg>
      </ActionIcon>
    </Paper>;
  }

  if (!loading && entities.length === 0) {
    return <Stack gap="md" style={{ width: '100%' }}>
      <TextInput placeholder="Search entities..." leftSection={<Search size={14} />} value={searchQuery} onChange={(e) => setSearchQuery(e.currentTarget.value)} disabled />
      <Paper p="xl" radius="md" withBorder style={{ textAlign: 'center' }}>
        <ThemeIcon size={48} radius="xl" color="gray" variant="light" style={{ margin: '0 auto' }}><Database size={24} /></ThemeIcon>
        <Text size="sm" fw={500} mt="md">No knowledge entities found.</Text>
        <Text size="xs" c="dimmed" mt={4}>No entities have been created yet. Add customers, contacts, invoices, or other objects to populate the knowledge base.</Text>
      </Paper>
    </Stack>;
  }

  return <Stack gap="md" style={{ width: '100%' }}>
    <TextInput
      placeholder="Search entities by name, type, or field value..."
      leftSection={<Search size={14} />}
      rightSection={searchQuery ? <CloseButton size="sm" onClick={() => setSearchQuery('')} aria-label="Clear search" /> : undefined}
      value={searchQuery}
      onChange={(e) => setSearchQuery(e.currentTarget.value)}
      styles={{ input: { fontSize: 13 } }}
    />
    {entityTypes.length > 0 && (
      <ScrollArea h={36} type="never">
        <Group gap="xs" wrap="nowrap">
          <Badge variant={typeFilter === null ? 'filled' : 'light'} color="violet" size="lg"
            style={{ cursor: 'pointer', textTransform: 'capitalize' }}
            onClick={() => setTypeFilter(null)}>
            All ({entities.length})
          </Badge>
          {entityTypes.map(({ type }) => {
            const count = typeCounts[type] || 0;
            if (count === 0 && !typeFilter) return null;
            return <Badge key={type} variant={typeFilter === type ? 'filled' : 'light'} color={getColor(type)} size="lg"
              style={{ cursor: 'pointer', textTransform: 'capitalize' }}
              onClick={() => setTypeFilter(typeFilter === type ? null : type)}>
              {humanize(type)} ({count})
            </Badge>;
          })}
        </Group>
      </ScrollArea>
    )}
    {filteredEntities.length > 0 ? (
      <SimpleGrid cols={{ base: 2, sm: 3, md: 4 }} spacing="md">
        {filteredEntities.map((entity) => (
          <EntityCard key={entity.id} entity={entity} onClick={() => setSelectedEntity(entity)} />
        ))}
      </SimpleGrid>
    ) : (
      <Paper p="xl" radius="md" withBorder style={{ textAlign: 'center' }}>
        <ThemeIcon size={48} radius="xl" color="gray" variant="light" style={{ margin: '0 auto' }}><Search size={24} /></ThemeIcon>
        <Text size="sm" fw={500} mt="md">
          {searchQuery ? `No matches for "${searchQuery}"` : 'No entities match the current filter'}
        </Text>
        <Text size="xs" c="dimmed" mt={4}>
          {searchQuery ? 'Try a different search term or clear the filter.' : 'Try selecting a different type or clear the type filter.'}
        </Text>
      </Paper>
    )}
    <Text size="xs" c="dimmed" ta="right">
      {filteredEntities.length === entities.length
        ? `${entities.length} entit${entities.length === 1 ? 'y' : 'ies'}`
        : `${filteredEntities.length} of ${entities.length} entit${entities.length === 1 ? 'y' : 'ies'}`}
    </Text>
  </Stack>;
}
