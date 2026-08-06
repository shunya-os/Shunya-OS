/**
 * PdfPreview — Mantine v7 component for previewing and downloading SHUNYA PDFs.
 *
 * Accepts {objectType: 'proposal' | 'invoice', objectId: number}
 * Fetches GET /api/v1/pdf/{type}/{id} as blob, displays via <iframe>, downloads via <a>.
 */
import { useState, useEffect, useRef } from 'react';
import {
  Paper,
  Button,
  Group,
  Text,
  Loader,
  Alert,
} from '@mantine/core';
import { Download, FileText, AlertCircle } from 'lucide-react';

interface PdfPreviewProps {
  objectType: 'proposal' | 'invoice';
  objectId: number;
}

export function PdfPreview({ objectType, objectId }: PdfPreviewProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [blob, setBlob] = useState<Blob | null>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const label = objectType === 'proposal' ? 'Proposal' : 'Invoice';

  useEffect(() => {
    let cancelled = false;

    async function fetchPdf() {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/v1/pdf/${objectType}/${objectId}`, {
          credentials: 'include',
        });

        if (!response.ok) {
          const text = await response.text();
          let detail = `HTTP ${response.status}`;
          try {
            const json = JSON.parse(text);
            detail = json.error || detail;
          } catch { /* not JSON, use raw text */ }
          throw new Error(detail);
        }

        const pdfBlob = await response.blob();
        if (cancelled) return;

        const url = URL.createObjectURL(pdfBlob);
        setPdfUrl(url);
        setBlob(pdfBlob);
      } catch (err: any) {
        if (!cancelled) {
          setError(err.message || 'Failed to load PDF');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchPdf();

    return () => {
      cancelled = true;
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [objectType, objectId]);

  const handleDownload = () => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${objectType}-${objectId}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Paper
      shadow="sm"
      radius="md"
      p="md"
      withBorder
      style={{
        background: 'rgba(255,255,255,0.6)',
        backdropFilter: 'blur(4px)',
        border: '1px solid rgba(26,28,29,0.06)',
      }}
    >
      <Group justify="space-between" mb="sm">
        <Group gap="xs">
          <FileText size={16} style={{ color: '#6C4AE2' }} />
          <Text size="sm" fw={600} c="#1A1C1D">
            {label} Preview
          </Text>
        </Group>
        {blob && (
          <Button
            size="xs"
            variant="light"
            color="violet"
            leftSection={<Download size={14} />}
            onClick={handleDownload}
          >
            Download PDF
          </Button>
        )}
      </Group>

      {loading && (
        <Group justify="center" py="xl">
          <Loader size="sm" color="violet" />
          <Text size="sm" c="dimmed">Loading {label} PDF...</Text>
        </Group>
      )}

      {error && (
        <Alert
          icon={<AlertCircle size={14} />}
          title="Failed to load PDF"
          color="red"
          variant="light"
        >
          <Text size="xs">{error}</Text>
        </Alert>
      )}

      {pdfUrl && !loading && !error && (
        <iframe
          ref={iframeRef}
          src={pdfUrl}
          title={`${label} PDF Preview`}
          style={{
            width: '100%',
            height: 500,
            border: '1px solid rgba(26,28,29,0.08)',
            borderRadius: 8,
            background: '#fff',
          }}
        />
      )}
    </Paper>
  );
}