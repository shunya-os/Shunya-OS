/**
 * SHUNYA — AI Analysis Panel
 *
 * A Mantine v7 component that lets users ask a business analysis question
 * and get an answer combining company data context + web search results.
 *
 * Calls POST /api/v1/ai/analyze with {question: string}
 * Returns {answer, sources, data_used}
 */
import { useState } from 'react';
import {
  Paper,
  Textarea,
  Button,
  Text,
  Group,
  Loader,
  Stack,
  Badge,
  Alert,
} from '@mantine/core';
import { AlertCircle, Search, Send, Sparkles, Globe, Database } from 'lucide-react';

interface Source {
  title: string;
  url: string;
}

interface AnalyzeResponse {
  success: boolean;
  answer: string;
  sources: Source[];
  data_used?: {
    company_context_lines: number;
    web_results_count: number;
    sources: Source[];
  };
  error?: string;
}

export function AiAnalysisPanel() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [dataUsed, setDataUsed] = useState<AnalyzeResponse['data_used'] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    const q = question.trim();
    if (!q || q.length < 2) return;

    setLoading(true);
    setError(null);
    setAnswer(null);
    setSources([]);
    setDataUsed(null);

    try {
      const resp = await fetch('/api/v1/ai/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ question: q }),
      });

      const data: AnalyzeResponse = await resp.json();

      if (!resp.ok || !data.success) {
        throw new Error(data.error || `HTTP ${resp.status}`);
      }

      setAnswer(data.answer);
      setSources(data.sources || []);
      setDataUsed(data.data_used || undefined);
    } catch (err: any) {
      setError(err.message || 'Could not connect to server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper p="md" radius="md" withBorder>
      <Stack gap="md">
        {/* Header */}
        <Group gap="xs">
          <Sparkles size={18} />
          <Text size="sm" fw={600}>
            Analyze with AI
          </Text>
        </Group>

        <Text size="xs" c="dimmed">
          Ask a business question — SHUNYA will analyze your company data and
          supplement with web search results for a comprehensive answer.
        </Text>

        {/* Question input */}
        <Textarea
          placeholder="e.g., What's my current cash flow outlook? or Summarize my overdue invoices"
          value={question}
          onChange={(e) => setQuestion(e.currentTarget.value)}
          minRows={2}
          maxRows={4}
          autosize
          disabled={loading}
          rightSection={
            loading ? (
              <Loader size="sm" />
            ) : (
              <Send size={14} style={{ cursor: 'pointer', opacity: 0.5 }} onClick={handleAnalyze} />
            )
          }
          styles={{ input: { fontSize: 13 } }}
        />

        {/* Analyze button */}
        <Button
          onClick={handleAnalyze}
          loading={loading}
          disabled={!question.trim() || question.trim().length < 2}
          leftSection={loading ? undefined : <Search size={14} />}
          fullWidth
          size="sm"
          variant="light"
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </Button>

        {/* Error state */}
        {error && (
          <Alert
            icon={<AlertCircle size={14} />}
            color="red"
            variant="light"
            p="sm"
            styles={{ label: { fontSize: 12 } }}
          >
            {error}
          </Alert>
        )}

        {/* Loading state */}
        {loading && (
          <Paper p="md" radius="md" withBorder style={{ textAlign: 'center' }}>
            <Loader size="sm" mb="xs" />
            <Text size="xs" c="dimmed">
              Querying your business data and searching the web...
            </Text>
          </Paper>
        )}

        {/* Response */}
        {answer && !loading && (
          <Stack gap="sm">
            {/* Data usage badges */}
            {dataUsed && (
              <Group gap="xs">
                {dataUsed.company_context_lines > 0 && (
                  <Badge
                    variant="light"
                    color="violet"
                    size="sm"
                    leftSection={<Database size={10} />}
                  >
                    {dataUsed.company_context_lines} data records
                  </Badge>
                )}
                {dataUsed.web_results_count > 0 && (
                  <Badge
                    variant="light"
                    color="blue"
                    size="sm"
                    leftSection={<Globe size={10} />}
                  >
                    {dataUsed.web_results_count} web sources
                  </Badge>
                )}
              </Group>
            )}

            {/* AI answer */}
            <Paper p="sm" radius="sm" bg="gray.0" style={{ whiteSpace: 'pre-wrap' }}>
              <Text size="sm">{answer}</Text>
            </Paper>

            {/* Sources */}
            {sources.length > 0 && (
              <Stack gap={4}>
                <Text size="xs" fw={600} c="dimmed">
                  Sources ({sources.length}):
                </Text>
                <Group gap="xs" wrap="wrap">
                  {sources.map((src, i) => (
                    <Badge
                      key={i}
                      variant="outline"
                      color="gray"
                      size="sm"
                      style={{
                        cursor: src.url ? 'pointer' : undefined,
                        maxWidth: 300,
                      }}
                      component={src.url ? 'a' : 'span'}
                      href={src.url || undefined}
                      target={src.url ? '_blank' : undefined}
                      rel={src.url ? 'noopener noreferrer' : undefined}
                    >
                      {src.title || src.url || `Source ${i + 1}`}
                    </Badge>
                  ))}
                </Group>
              </Stack>
            )}
          </Stack>
        )}
      </Stack>
    </Paper>
  );
}