/**
 * SHUNYA — AI File Assistant (Mantine Edition)
 *
 * Drag-drop file upload via Mantine Dropzone → AI extraction → Object creation.
 *
 * Users drop PDF, images, DOCX, or TXT files. The file is uploaded via
 * POST /api/v1/upload, then sent to POST /api/v1/ai/chat with a prompt to
 * extract structured data. The extracted data is shown for confirmation
 * before creating objects in the workspace.
 */
import { useState, useCallback } from 'react';
import {
  Upload,
  FileText,
  Loader2,
  CheckCircle2,
  XCircle,
  X,
  Sparkles,
  FileImage,
  File,
  AlertCircle,
} from 'lucide-react';
import {
  Paper,
  Group,
  Stack,
  Text,
  Button,
  Progress,
  Badge,
  ThemeIcon,
  Box,
} from '@mantine/core';
import { Dropzone, IMAGE_MIME_TYPE, PDF_MIME_TYPE } from '@mantine/dropzone';
import { aiChat, type AIChatMessage } from '../../api/ai-chat';
import { uploadFile, createObject, getStoredWorkspaceId } from '../../api/objects';

// ── Types ─────────────────────────────────────────────────────

export interface FileAssistantProps {
  workspaceId?: string;
  onCreated?: (type: string, result: any) => void;
}

interface ExtractionResult {
  object_type: string;
  fields: Record<string, string>;
  confidence: 'high' | 'medium' | 'low';
  summary: string;
}

const ALLOWED_TYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/webp',
  'image/gif',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
];

const ALLOWED_MIME_TYPES = [
  ...PDF_MIME_TYPE,
  ...IMAGE_MIME_TYPE,
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
];

// ── Helpers ───────────────────────────────────────────────────

function extractJson(raw: string): any | null {
  const cleaned = raw
    .replace(/```json\s*/gi, '')
    .replace(/```\s*/gi, '')
    .trim();
  try {
    return JSON.parse(cleaned);
  } catch {
    /* fall through */
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

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIconComponent(type: string, size: number = 32) {
  if (type.startsWith('image/')) return <FileImage size={size} />;
  if (type === 'application/pdf') return <FileText size={size} />;
  if (type.includes('wordprocessingml')) return <FileText size={size} />;
  return <File size={size} />;
}

// ── Confidence badge color ──

function confidenceColor(c: string): string {
  switch (c) {
    case 'high': return 'green';
    case 'medium': return 'yellow';
    case 'low': return 'red';
    default: return 'gray';
  }
}

// ── Main Component ────────────────────────────────────────────

export function AIFileAssistant({ workspaceId, onCreated }: FileAssistantProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [extracting, setExtracting] = useState(false);
  const [extraction, setExtraction] = useState<ExtractionResult | null>(null);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const reset = useCallback(() => {
    setFile(null);
    setExtraction(null);
    setError(null);
    setDone(false);
    setUploadProgress(0);
  }, []);

  const handleFile = useCallback(
    async (f: File) => {
      if (!ALLOWED_TYPES.includes(f.type)) {
        setError(`Unsupported file type: ${f.type || 'unknown'}. Accepted: PDF, PNG, JPG, WebP, GIF, DOCX, TXT.`);
        return;
      }
      if (f.size > 10 * 1024 * 1024) {
        setError('File too large. Maximum size is 10 MB.');
        return;
      }
      setFile(f);
      setError(null);
      setExtraction(null);
      setDone(false);

      // Step 1: Upload
      setUploading(true);
      setUploadProgress(0);

      // Simulate progress steps
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 15, 85));
      }, 300);

      try {
        const wsId = workspaceId || getStoredWorkspaceId() || undefined;
        const uploadResp = await uploadFile(f, wsId);
        clearInterval(progressInterval);
        setUploadProgress(100);
        if (!uploadResp.success) throw new Error(uploadResp.error || 'Upload failed.');
      } catch (err: any) {
        clearInterval(progressInterval);
        setError(err?.message || 'Upload failed. Please try again.');
        setUploading(false);
        setFile(null);
        setUploadProgress(0);
        return;
      } finally {
        setUploading(false);
      }

      // Step 2: AI extraction
      setExtracting(true);
      try {
        const messages: AIChatMessage[] = [
          {
            role: 'system',
            content:
              "You are SHUNYA's document intelligence engine. Extract structured business data from file content. " +
              'Return ONLY valid JSON with this structure: {\n' +
              '  "object_type": "customer | contact | invoice | proposal | task | project | note",\n' +
              '  "fields": { "key": "value", ... },\n' +
              '  "confidence": "high | medium | low",\n' +
              '  "summary": "One-sentence description of what you extracted."\n' +
              '}\n' +
              'Map field keys to standard names: company_name, email, phone, amount, due_date, status, name, description, notes, address, etc.',
          },
          {
            role: 'user',
            content: `Extract data from this uploaded file: "${f.name}" (${f.type}, ${formatFileSize(f.size)}). Return the JSON object only.`,
          },
        ];
        const resp = await aiChat(messages, { temperature: 0.2, max_tokens: 1024 });
        if (!resp.content || resp.error) throw new Error(resp.error || 'AI returned empty response.');

        const parsed = extractJson(resp.content);
        if (!parsed || !parsed.object_type || !parsed.fields) {
          setExtraction({
            object_type: 'note',
            fields: { name: `File: ${f.name}`, description: resp.content.slice(0, 500), notes: resp.content },
            confidence: 'low',
            summary: `Extracted content from ${f.name} as a note.`,
          });
        } else {
          setExtraction({
            object_type: parsed.object_type,
            fields: parsed.fields,
            confidence: parsed.confidence || 'medium',
            summary: parsed.summary || `Extracted data from ${f.name}`,
          });
        }
      } catch (err: any) {
        setError(err?.message || 'AI extraction failed. Try again.');
        setExtracting(false);
        return;
      } finally {
        setExtracting(false);
      }
    },
    [workspaceId],
  );

  const handleCreate = useCallback(async () => {
    if (!extraction) return;
    setCreating(true);
    setError(null);
    try {
      const wsId = workspaceId || getStoredWorkspaceId() || undefined;
      const resp = await createObject(extraction.object_type, extraction.fields, wsId);
      if (!resp.success) throw new Error(resp.error || 'Failed to create object.');
      setDone(true);
      onCreated?.(extraction.object_type, resp.data);
    } catch (err: any) {
      setError(err?.message || 'Failed to create object.');
    } finally {
      setCreating(false);
    }
  }, [extraction, workspaceId, onCreated]);

  return (
    <Stack gap="sm" w="100%">
      {!done && (
        <>
          {/* Dropzone */}
          {!file && (
            <Dropzone
              onDrop={(files) => {
                const f = files[0];
                if (f) handleFile(f);
              }}
              onReject={(rejections) => {
                const err = rejections[0]?.errors[0]?.message;
                setError(err || 'File rejected. Accepted: PDF, PNG, JPG, WebP, GIF, DOCX, TXT · up to 10 MB');
              }}
              maxSize={10 * 1024 * 1024}
              accept={ALLOWED_MIME_TYPES}
              loading={uploading}
              radius="md"
              p="xl"
            >
              <Group justify="center" gap="xs" style={{ pointerEvents: 'none' }}>
                <Dropzone.Accept>
                  <Upload size={28} color="var(--mantine-color-violet-6)" />
                </Dropzone.Accept>
                <Dropzone.Reject>
                  <X size={28} color="var(--mantine-color-red-6)" />
                </Dropzone.Reject>
                <Dropzone.Idle>
                  <Upload size={28} color="var(--mantine-color-gray-5)" />
                </Dropzone.Idle>
                <div>
                  <Text size="sm" fw={500} ta="center">
                    <Dropzone.Accept>Drop file to upload</Dropzone.Accept>
                    <Dropzone.Reject>File type not accepted</Dropzone.Reject>
                    <Dropzone.Idle>Drop a file or click to upload</Dropzone.Idle>
                  </Text>
                  <Text size="xs" c="dimmed" ta="center" mt={4}>
                    PDF, PNG, JPG, WebP, DOCX, TXT · up to 10 MB
                  </Text>
                </div>
              </Group>
            </Dropzone>
          )}

          {/* Upload Progress */}
          {uploading && (
            <Paper p="md" radius="md" withBorder>
              <Group gap="sm" mb="xs">
                <Loader2 size={14} className="aifa-spin" color="var(--mantine-color-violet-6)" />
                <Text size="sm" fw={500}>Uploading {file?.name}…</Text>
              </Group>
              <Progress value={uploadProgress} color="violet" size="sm" animated />
              <Text size="xs" c="dimmed" mt={4}>{uploadProgress}%</Text>
            </Paper>
          )}

          {/* Selected file (before extraction) */}
          {file && !uploading && !extracting && !extraction && (
            <Paper p="md" radius="md" withBorder style={{ borderStyle: 'solid', borderColor: 'var(--mantine-color-violet-2)' }}>
              <Group gap="md" align="center">
                <ThemeIcon size={40} radius="md" color="violet" variant="light">
                  {getFileIconComponent(file.type, 20)}
                </ThemeIcon>
                <Box style={{ flex: 1 }}>
                  <Text size="sm" fw={500}>{file.name}</Text>
                  <Text size="xs" c="dimmed">{formatFileSize(file.size)}</Text>
                </Box>
                <Button
                  variant="subtle"
                  color="gray"
                  size="compact-sm"
                  onClick={reset}
                  leftSection={<X size={14} />}
                >
                  Remove
                </Button>
              </Group>
            </Paper>
          )}

          {/* Extracting spinner */}
          {extracting && (
            <Paper p="md" radius="md" withBorder>
              <Group gap="sm">
                <Loader2 size={16} className="aifa-spin" color="var(--mantine-color-violet-6)" />
                <Text size="sm" c="dimmed">AI is extracting data from your file…</Text>
              </Group>
            </Paper>
          )}

          {/* Extraction result */}
          {!extracting && extraction && (
            <Paper p="md" radius="md" withBorder style={{ borderLeft: '3px solid var(--mantine-color-violet-6)' }}>
              <Stack gap="sm">
                <Group gap={6}>
                  <Sparkles size={13} color="var(--mantine-color-violet-6)" />
                  <Text size="xs" fw={600} tt="uppercase" c="dimmed">AI Extraction</Text>
                  <Badge
                    size="sm"
                    color={confidenceColor(extraction.confidence)}
                    variant="light"
                    style={{ marginLeft: 'auto' }}
                  >
                    {extraction.confidence} confidence
                  </Badge>
                </Group>

                <Text size="sm">{extraction.summary}</Text>

                <Badge
                  size="lg"
                  color="violet"
                  variant="light"
                  leftSection={<FileText size={11} />}
                  style={{ alignSelf: 'flex-start' }}
                >
                  {extraction.object_type}
                </Badge>

                <Paper p="xs" radius="sm" withBorder>
                  <Stack gap={2}>
                    {Object.entries(extraction.fields).map(([k, v]) => (
                      <Group key={k} justify="space-between" gap="md" p={4}>
                        <Text size="xs" c="dimmed" style={{ textTransform: 'capitalize' }}>
                          {k.replace(/_/g, ' ')}
                        </Text>
                        <Text size="xs" fw={500}>{v || '—'}</Text>
                      </Group>
                    ))}
                  </Stack>
                </Paper>

                <Group justify="flex-end" gap="sm">
                  <Button
                    variant="subtle"
                    color="gray"
                    size="sm"
                    onClick={reset}
                    disabled={creating}
                    leftSection={<XCircle size={13} />}
                  >
                    Discard
                  </Button>
                  <Button
                    color="violet"
                    size="sm"
                    onClick={handleCreate}
                    loading={creating}
                    leftSection={creating ? undefined : <CheckCircle2 size={13} />}
                  >
                    {creating ? 'Creating…' : `Create ${extraction.object_type}`}
                  </Button>
                </Group>
              </Stack>
            </Paper>
          )}

          {/* Error */}
          {error && (
            <Paper p="sm" radius="md" style={{ background: 'rgba(185,28,28,0.06)', border: '1px solid rgba(185,28,28,0.10)' }}>
              <Group gap="sm">
                <AlertCircle size={13} color="#B91C1C" />
                <Text size="sm" c="red" style={{ flex: 1 }}>{error}</Text>
                <Button variant="subtle" color="gray" size="compact-sm" onClick={reset} leftSection={<X size={13} />}>
                  Dismiss
                </Button>
              </Group>
            </Paper>
          )}
        </>
      )}

      {/* Done state */}
      {done && (
        <Paper p="lg" radius="md" style={{ background: 'rgba(45,106,79,0.06)', border: '1px solid rgba(45,106,79,0.12)' }}>
          <Group gap="md">
            <CheckCircle2 size={24} color="#2D6A4F" />
            <Box style={{ flex: 1 }}>
              <Text size="sm" fw={600}>Object created successfully</Text>
              <Text size="xs" c="dimmed">
                {extraction?.object_type} with data from "{file?.name}" is ready.
              </Text>
            </Box>
            <Button color="violet" onClick={reset}>
              Upload another
            </Button>
          </Group>
        </Paper>
      )}

      <style>{`
        .aifa-spin { animation: aifa-rotate 0.8s linear infinite; }
        @keyframes aifa-rotate { to { transform: rotate(360deg); } }
      `}</style>
    </Stack>
  );
}