/**
 * UniversalSearchBar — always-visible universal search for the primary
 * workspace header.
 *
 * Queries the real backend:
 *   - POST /api/v1/search/global  → canonical organization objects grouped by
 *     type (leads, people, commitments, documents, …)
 *   - GET  /api/v1/search?q=      → web results
 *
 * Results are grouped by type with click-through navigation: entity rows open
 * the object workspace; web rows open a new tab. A microphone button (wired to
 * the shared useVoiceInput hook) fills the query by speech.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { ActionIcon, Badge, Box, Group, Kbd, Loader, Text, TextInput } from '@mantine/core';
import { IconArrowRight, IconMicrophone, IconSearch, IconWorld } from '@tabler/icons-react';
import { useVoiceInput } from '../../hooks/use-voice-input';
import { useI18n, speechRecognitionLang } from '../../lib/i18n';
import { useOpenWorkspace } from '../../hooks/workspace-hooks';

interface EntityHit {
  id: string | number;
  type: string;
  name: string;
  summary?: string;
  status?: string;
  url?: string;
}

interface WebHit {
  title?: string;
  snippet?: string;
  url?: string;
}

export function UniversalSearchBar({ width }: { width?: number }) {
  const { t, lang } = useI18n();
  const openWorkspace = useOpenWorkspace();

  const [query, setQuery] = useState('');
  const [entities, setEntities] = useState<EntityHit[]>([]);
  const [webHits, setWebHits] = useState<WebHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [failed, setFailed] = useState(false);

  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const voice = useVoiceInput(speechRecognitionLang(lang), {
    continuous: false,
    onFinal: (text) => {
      setQuery(text);
      setOpen(true);
    },
  });

  // Keep the input in sync when speech produces a final transcript (also
  // re-syncs if the caller cleared the query after navigation).
  useEffect(() => {
    if (voice.transcript) setQuery(voice.transcript);
  }, [voice.transcript]);

  // Debounced search — canonical objects + web, in parallel.
  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setEntities([]);
      setWebHits([]);
      setOpen(false);
      setFailed(false);
      return;
    }
    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const [globalRes, webRes] = await Promise.all([
          fetch('/api/v1/search/global', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ query: q, limit: 6 }),
          })
            .then((r) => r.json())
            .catch(() => null),
          fetch(`/api/v1/search?q=${encodeURIComponent(q)}`, { credentials: 'include' })
            .then((r) => r.json())
            .catch(() => null),
        ]);
        setEntities(globalRes?.success ? (globalRes.data?.results ?? []) : []);
        setWebHits(webRes?.success ? (webRes.data ?? []) : []);
        setFailed(false);
        setOpen(true);
      } catch {
        setFailed(true);
      } finally {
        setLoading(false);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [query]);

  // Dismiss on outside click.
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener('mousedown', handler);
    return () => window.removeEventListener('mousedown', handler);
  }, []);

  const grouped = useMemo(() => {
    const map = new Map<string, EntityHit[]>();
    for (const e of entities) {
      const list = map.get(e.type) ?? [];
      list.push(e);
      map.set(e.type, list);
    }
    return [...map.entries()];
  }, [entities]);

  const hasResults = grouped.length > 0 || webHits.length > 0;
  const isEmpty = query.trim().length >= 2 && !loading && !hasResults && !failed;

  const goEntity = (hit: EntityHit) => {
    setOpen(false);
    setQuery('');
    openWorkspace(hit.name, 'object', { objectType: hit.type, objectId: String(hit.id) });
  };

  const toggleMic = () => {
    if (voice.listening) {
      voice.stop();
    } else {
      voice.reset();
      voice.start();
    }
  };

  return (
    <Box ref={rootRef} style={{ position: 'relative', width }} data-testid="universal-search-bar">
      <TextInput
        ref={inputRef}
        placeholder={t('searchPlaceholder')}
        value={query}
        leftSection={<IconSearch size={15} />}
        rightSection={
          <Group gap={4} wrap="nowrap">
            {loading ? (
              <Loader size="xs" />
            ) : (
              <ActionIcon
                variant={voice.listening ? 'filled' : 'subtle'}
                color={voice.listening ? 'red' : 'gray'}
                size="sm"
                onClick={toggleMic}
                aria-label={voice.listening ? t('stopRecording') : t('voiceInput')}
                title={voice.listening ? t('stopRecording') : t('voiceInput')}
              >
                <IconMicrophone size={14} />
              </ActionIcon>
            )}
          </Group>
        }
        onChange={(e) => {
          setQuery(e.currentTarget.value);
          if (e.currentTarget.value.trim().length >= 2) setOpen(true);
        }}
        onFocus={() => {
          if (query.trim().length >= 2) setOpen(true);
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && query.trim().length >= 2) setOpen(!open);
          if (e.key === 'Escape') setOpen(false);
        }}
        size="sm"
        aria-label={t('search')}
      />

      {voice.error && (
        <Text size="xs" c="red" mt={4} role="alert">
          {t(voice.error)}
        </Text>
      )}

      {open && (loading || hasResults || isEmpty || failed) && (
        <Box
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            left: 0,
            right: 0,
            zIndex: 400,
            background: 'var(--shunya-surface, #FFFFFF)',
            border: '1px solid var(--shunya-border, rgba(26,28,29,0.07))',
            borderRadius: 12,
            boxShadow: '0 12px 40px rgba(26,28,29,0.10)',
            maxHeight: 420,
            overflowY: 'auto',
            padding: 4,
          }}
        >
          {loading && !hasResults && (
            <Text size="sm" c="dimmed" p="md" ta="center">
              {t('loading')}
            </Text>
          )}

          {!loading && isEmpty && (
            <Text size="sm" c="dimmed" p="md" ta="center">
              {t('noResults')} “{query.trim()}”
            </Text>
          )}

          {!loading && failed && (
            <Text size="sm" c="red" p="md" ta="center" role="alert">
              {t('searchFailed')}
            </Text>
          )}

          {grouped.map(([type, hits]) => (
            <Box key={type} mb={2}>
              <Text
                size="10px"
                fw={700}
                tt="uppercase"
                c="dimmed"
                style={{ letterSpacing: '0.08em', padding: '8px 12px 4px' }}
              >
                {type}
              </Text>
              {hits.map((hit) => (
                <Box
                  key={`${type}-${hit.id}`}
                  role="option"
                  onClick={() => goEntity(hit)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '8px 12px',
                    borderRadius: 8,
                    cursor: 'pointer',
                  }}
                  onMouseDown={(e) => e.preventDefault()} // keep input focus
                  className="sh-search-row"
                >
                  <Text size="sm" fw={500} style={{ flex: 1, minWidth: 0 }} truncate>
                    {hit.name}
                  </Text>
                  {hit.status && (
                    <Badge size="xs" variant="light" color="gray" styles={{ label: { textTransform: 'none' } }}>
                      {hit.status}
                    </Badge>
                  )}
                  <IconArrowRight size={13} style={{ color: 'var(--shunya-text-tertiary, rgba(26,28,29,0.4))', flexShrink: 0 }} />
                </Box>
              ))}
            </Box>
          ))}

          {webHits.length > 0 && (
            <Box mb={2}>
              <Text size="10px" fw={700} tt="uppercase" c="dimmed" style={{ letterSpacing: '0.08em', padding: '8px 12px 4px' }}>
                <IconWorld size={11} style={{ verticalAlign: '-1px', marginRight: 4 }} />
                {t('web')}
              </Text>
              {webHits.slice(0, 4).map((hit, i) => (
                <Box
                  key={`web-${i}`}
                  role="option"
                  onClick={() => {
                    if (hit.url) window.open(hit.url, '_blank', 'noopener');
                  }}
                  onMouseDown={(e) => e.preventDefault()}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '8px 12px',
                    borderRadius: 8,
                    cursor: 'pointer',
                  }}
                  className="sh-search-row"
                >
                  <Text size="sm" style={{ flex: 1, minWidth: 0 }} truncate>
                    {hit.title}
                  </Text>
                  <Text size="xs" c="dimmed" truncate style={{ maxWidth: 140 }}>
                    {hit.snippet}
                  </Text>
                </Box>
              ))}
            </Box>
          )}

          <Group gap={6} p="xs">
            <Kbd size="xs">↵</Kbd>
            <Text size="10px" c="dimmed">
              {t('pressEnter')}
            </Text>
          </Group>
        </Box>
      )}
    </Box>
  );
}

// Row hover/active feedback for the results dropdown (dark theme friendly).
if (typeof document !== 'undefined') {
  const el = document.createElement('style');
  el.textContent = `
.sh-search-row:hover { background: rgba(164,134,95,0.10); }
.sh-search-row:active { background: rgba(164,134,95,0.16); }
`;
  el.id = 'shunya-universal-search-bar-styles';
  document.head.appendChild(el);
}