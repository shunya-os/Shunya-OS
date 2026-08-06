/**
 * AI Business Insights — Mantine Edition
 *
 * Fetches all objects from the active workspace, sends a summary to
 * POST /api/v1/ai/chat with a prompt to analyze the data, and displays
 * the AI's response as a formatted insights card with key insights,
 * trends, and recommendations.
 *
 * Uses Mantine Paper, Timeline, Spoiler, Progress, Badge, Alert.
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import {
  Sparkles,
  Loader2,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus,
  Lightbulb,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Briefcase,
  Users,
  FileText,
  DollarSign,
  ClipboardList,
  Inbox,
} from 'lucide-react';
import {
  Paper,
  Group,
  Stack,
  Text,
  Alert,
  Badge,
  Spoiler,
  Progress,
  ActionIcon,
  Box,
} from '@mantine/core';
import { aiChat, type AIChatMessage } from '../../api/ai-chat';
import { fetchObjects, getStoredWorkspaceId } from '../../api/objects';

// ── Types ─────────────────────────────────────────────────────

export interface AIInsightsProps {
  workspaceId?: string;
  /** Auto-refresh interval in seconds (default: 0 = no auto-refresh). */
  autoRefresh?: number;
}

interface AIInsightData {
  summary: string;
  trend: 'up' | 'down' | 'stable' | 'mixed';
  insights: string[];
  recommendations: string[];
  metrics: { label: string; value: string; change?: string }[];
  categories: { type: string; count: number; icon: string }[];
}

// ── Helpers ───────────────────────────────────────────────────

function extractJson(raw: string): any | null {
  const cleaned = raw
    .replace(/```json\s*/gi, '')
    .replace(/```\s*/gi, '')
    .trim();
  try {
    return JSON.parse(cleaned);
  } catch {
    /* */
  }
  const start = cleaned.indexOf('{');
  const end = cleaned.lastIndexOf('}');
  if (start !== -1 && end > start) {
    try {
      return JSON.parse(cleaned.slice(start, end + 1));
    } catch {
      /* */
    }
  }
  return null;
}

function typeIcon(type: string) {
  switch (type) {
    case 'invoice':
      return <DollarSign size={13} />;
    case 'customer':
      return <Briefcase size={13} />;
    case 'contact':
      return <Users size={13} />;
    case 'proposal':
      return <FileText size={13} />;
    case 'task':
      return <ClipboardList size={13} />;
    case 'project':
      return <Briefcase size={13} />;
    case 'employee':
      return <Users size={13} />;
    case 'note':
      return <FileText size={13} />;
    default:
      return <Inbox size={13} />;
  }
}

function trendColor(trend: string): string {
  switch (trend) {
    case 'up':
      return '#2D6A4F';
    case 'down':
      return '#B91C1C';
    case 'mixed':
      return '#A4865F';
    default:
      return 'rgba(26,28,29,0.3)';
  }
}

function trendIcon(trend: string) {
  switch (trend) {
    case 'up':
      return <TrendingUp size={14} style={{ color: '#2D6A4F' }} />;
    case 'down':
      return <TrendingDown size={14} style={{ color: '#B91C1C' }} />;
    case 'mixed':
      return <Minus size={14} style={{ color: '#A4865F' }} />;
    default:
      return <Minus size={14} style={{ color: 'rgba(26,28,29,0.3)' }} />;
  }
}

// ── Main Component ────────────────────────────────────────────

export function AIBusinessInsights({ workspaceId, autoRefresh }: AIInsightsProps) {
  const [data, setData] = useState<AIInsightData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const fetchInsights = useCallback(async () => {
    setLoading(true);
    setError(null);
    const wsId = workspaceId || getStoredWorkspaceId() || undefined;

    try {
      // Fetch all object types in parallel
      const types = ['invoice', 'customer', 'contact', 'proposal', 'task', 'project', 'employee', 'note'];
      const results = await Promise.allSettled(types.map((type) => fetchObjects(type, wsId)));

      const objectCounts: Record<string, number> = {};
      let totalObjects = 0;
      let totalRevenue = 0;
      let overdueCount = 0;
      let openTasks = 0;
      let activeProjects = 0;

      results.forEach((r, i) => {
        const type = types[i];
        if (r.status === 'fulfilled' && r.value.success && r.value.data) {
          const list = r.value.data.objects || [];
          objectCounts[type] = list.length;
          totalObjects += list.length;

          if (type === 'invoice') {
            list.forEach((o: any) => {
              const amt = Number(o.data?.amount || o.data?.total || 0);
              totalRevenue += amt;
              if ((o.data?.status || o.status) === 'overdue') overdueCount++;
            });
          }
          if (type === 'task') {
            list.forEach((o: any) => {
              if ((o.data?.status || o.status) !== 'completed' && (o.data?.status || o.status) !== 'done') openTasks++;
            });
          }
          if (type === 'project') {
            list.forEach((o: any) => {
              if ((o.data?.status || o.status) === 'active') activeProjects++;
            });
          }
        } else {
          objectCounts[type] = 0;
        }
      });

      // Build a data summary prompt for the AI
      const dataPrompt = `Business data summary for the workspace:
- Total objects: ${totalObjects}
- Revenue across invoices: $${totalRevenue.toLocaleString()}
- Overdue invoices: ${overdueCount}
- Open tasks: ${openTasks}
- Active projects: ${activeProjects}
- Object counts: ${JSON.stringify(objectCounts)}

Analyze this business data and provide key insights, trends, and recommendations.`;

      const messages: AIChatMessage[] = [
        {
          role: 'system',
          content:
            "You are SHUNYA's business intelligence engine. Analyze the provided business data and return a JSON object only. " +
            'Structure: {\n' +
            '  "summary": "One-paragraph executive summary of the business state.",\n' +
            '  "trend": "up | down | stable | mixed",\n' +
            '  "insights": ["Key insight 1", "Key insight 2", ...],\n' +
            '  "recommendations": ["Actionable recommendation 1", ...],\n' +
            '  "metrics": [{"label": "Metric name", "value": "formatted value", "change": "+X% or -X% or null"}],\n' +
            '  "categories": [{"type": "invoice", "count": 5, "icon": "invoice"}]\n' +
            '}',
        },
        { role: 'user', content: dataPrompt },
      ];

      const resp = await aiChat(messages, { temperature: 0.3, max_tokens: 1024 });
      if (!resp.content || resp.error) throw new Error(resp.error || 'AI returned empty response.');

      const parsed = extractJson(resp.content);
      if (parsed && parsed.summary) {
        // Ensure categories are populated from actual data
        const categories = Object.entries(objectCounts)
          .filter(([_, count]) => (count as number) > 0)
          .map(([type, count]) => ({ type, count: count as number, icon: type }));
        if (!parsed.categories || parsed.categories.length === 0) {
          parsed.categories = categories;
        }
        setData(parsed as AIInsightData);
      } else {
        // Fallback: build a simple insight from the raw data
        setData({
          summary: `Your workspace has ${totalObjects} objects across ${Object.keys(objectCounts).filter((t) => objectCounts[t] > 0).length} types.`,
          trend: totalRevenue > 0 ? 'up' : 'stable',
          insights: [
            `${totalObjects} total objects in the workspace`,
            overdueCount > 0 ? `${overdueCount} overdue invoice(s) need attention` : 'No overdue invoices',
            `${openTasks} open task(s) pending`,
            activeProjects > 0 ? `${activeProjects} active project(s)` : 'No active projects',
          ],
          recommendations: [
            overdueCount > 0 ? 'Follow up on overdue invoices' : 'Keep up the good work on invoices',
            openTasks > 0 ? 'Review and prioritize open tasks' : 'No pending tasks',
            totalObjects === 0 ? 'Start adding objects to unlock AI insights' : 'Continue tracking business data',
          ],
          metrics: [
            { label: 'Total Objects', value: String(totalObjects) },
            ...(totalRevenue > 0
              ? [{ label: 'Revenue', value: `$${totalRevenue.toLocaleString()}`, change: 'tracked' }]
              : []),
            ...(overdueCount > 0 ? [{ label: 'Overdue', value: String(overdueCount), change: 'needs attention' }] : []),
          ],
          categories: Object.entries(objectCounts)
            .filter(([_, count]) => (count as number) > 0)
            .map(([type, count]) => ({ type, count: count as number, icon: type })),
        });
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch AI insights.');
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [workspaceId]);

  // Fetch on mount
  useEffect(() => {
    mountedRef.current = true;
    fetchInsights();
    return () => {
      mountedRef.current = false;
    };
  }, [fetchInsights]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh || autoRefresh <= 0) return;
    const interval = setInterval(fetchInsights, autoRefresh * 1000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchInsights]);

  return (
    <Stack gap="sm" w="100%">
      {/* Header */}
      <Group justify="space-between" align="center">
        <Group gap={6}>
          <Sparkles size={13} color="#6C4AE2" />
          <Text size="xs" fw={600} tt="uppercase" c="dimmed" style={{ letterSpacing: '0.08em' }}>
            AI Insights
          </Text>
        </Group>
        <ActionIcon
          variant="subtle"
          color="gray"
          onClick={fetchInsights}
          disabled={loading}
          aria-label="Refresh insights"
        >
          <RefreshCw size={13} className={loading ? 'aii-spin' : ''} />
        </ActionIcon>
      </Group>

      {loading && !data && (
        <Paper p="md" radius="md" withBorder>
          <Group gap="sm">
            <Loader2 size={16} className="aii-spin" color="#6C4AE2" />
            <Text size="sm" c="dimmed">Analyzing your business data…</Text>
          </Group>
        </Paper>
      )}

      {error && (
        <Alert variant="light" color="red" icon={<AlertTriangle size={13} />} p="sm">
          <Group gap="sm">
            <Text size="sm" style={{ flex: 1 }}>{error}</Text>
            <ActionIcon variant="subtle" color="red" onClick={fetchInsights} aria-label="Retry">
              <RefreshCw size={13} />
            </ActionIcon>
          </Group>
        </Alert>
      )}

      {data && (
        <Stack gap="sm">
          {/* Summary & Trend */}
          <Paper
            p="md"
            radius="md"
            withBorder
            style={{ borderLeft: `3px solid ${trendColor(data.trend)}` }}
          >
            <Group gap={6} mb="xs">
              {trendIcon(data.trend)}
              <Text size="xs" fw={600} tt="uppercase" c="dimmed" style={{ letterSpacing: '0.08em' }}>
                Executive Summary
              </Text>
            </Group>
            <Text size="sm" style={{ lineHeight: 1.6 }}>
              {data.summary}
            </Text>
          </Paper>

          {/* Metrics row */}
          {data.metrics && data.metrics.length > 0 && (
            <Group gap="sm" grow wrap="wrap">
              {data.metrics.map((m, i) => (
                <Paper key={i} p="sm" radius="md" withBorder style={{ minWidth: 110 }}>
                  <Stack gap={2}>
                    <Text size="xs" tt="uppercase" c="dimmed" style={{ letterSpacing: '0.06em' }}>
                      {m.label}
                    </Text>
                    <Text size="lg" fw={700}>{m.value}</Text>
                    {m.change && <Text size="xs" c="dimmed">{m.change}</Text>}
                  </Stack>
                </Paper>
              ))}
            </Group>
          )}

          {/* Categories */}
          {data.categories && data.categories.length > 0 && (
            <Group gap={6} wrap="wrap">
              {data.categories.map((c, i) => (
                <Badge
                  key={i}
                  variant="light"
                  color="violet"
                  size="lg"
                  leftSection={<Box style={{ color: '#6C4AE2', display: 'flex' }}>{typeIcon(c.type)}</Box>}
                >
                  {c.type} · {c.count}
                </Badge>
              ))}
            </Group>
          )}

          {/* Insights */}
          {data.insights && data.insights.length > 0 && (
            <Paper p="md" radius="md" withBorder>
              <Group gap={6} mb="xs">
                <Lightbulb size={12} color="#A4865F" />
                <Text size="xs" fw={600} tt="uppercase" c="dimmed" style={{ letterSpacing: '0.06em' }}>
                  Key Insights
                </Text>
              </Group>
              <Spoiler maxHeight={80} showLabel="Show more" hideLabel="Show less">
                <Stack gap={4}>
                  {data.insights.map((insight, i) => (
                    <Group key={i} gap="sm" align="flex-start" p={4}>
                      <CheckCircle2 size={12} color="#2D6A4F" style={{ flexShrink: 0, marginTop: 2 }} />
                      <Text size="sm" style={{ lineHeight: 1.5 }}>{insight}</Text>
                    </Group>
                  ))}
                </Stack>
              </Spoiler>
            </Paper>
          )}

          {/* Recommendations */}
          {data.recommendations && data.recommendations.length > 0 && (
            <Paper p="md" radius="md" withBorder style={{ borderLeft: '3px solid #6C4AE2' }}>
              <Group gap={6} mb="xs">
                <ArrowRight size={12} color="#6C4AE2" />
                <Text size="xs" fw={600} tt="uppercase" c="dimmed" style={{ letterSpacing: '0.06em' }}>
                  Recommendations
                </Text>
              </Group>
              <Spoiler maxHeight={80} showLabel="Show more" hideLabel="Show less">
                <Stack gap={4}>
                  {data.recommendations.map((rec, i) => (
                    <Group key={i} gap="sm" align="flex-start" p={4}>
                      <ArrowRight size={12} color="#6C4AE2" style={{ flexShrink: 0, marginTop: 2 }} />
                      <Text size="sm" style={{ lineHeight: 1.5 }}>{rec}</Text>
                    </Group>
                  ))}
                </Stack>
              </Spoiler>
            </Paper>
          )}

          {/* Confidence / loading indicator */}
          {loading && <Progress value={100} color="violet" size="xs" animated />}
        </Stack>
      )}

      {/* Timestamp */}
      {data && (
        <Text size="xs" c="dimmed" ta="center">
          AI-powered analysis · data from your workspace
        </Text>
      )}

      <style>{`
        .aii-spin { animation: aii-rotate 0.8s linear infinite; }
        @keyframes aii-rotate { to { transform: rotate(360deg); } }
      `}</style>
    </Stack>
  );
}