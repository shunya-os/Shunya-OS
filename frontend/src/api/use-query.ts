/**
 * useQuery — Universal data hydration hook.
 * Every component uses this. No more mock data, no more missing loading/error states.
 *
 * Usage:
 *   const { data, loading, error, refetch } = useQuery('/api/v1/objects/contact');
 *   if (loading) return <ListSkeleton />;
 *   if (error) return <ErrorFallback message={error} onRetry={refetch} />;
 *   return <ContactList data={data} />;
 */
import { useState, useEffect, useCallback } from 'react';
import { bus } from '../runtimes/event-bus';

interface QueryState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useQuery<T = any>(url: string, deps?: string[]) {
  const [state, setState] = useState<QueryState<T>>({ data: null, loading: true, error: null });

  const fetchData = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const body = await res.json();
      setState({ data: body.data || body, loading: false, error: null });
    } catch (e: any) {
      setState({ data: null, loading: false, error: e.message || 'Unknown error' });
    }
  }, [url]);

  useEffect(() => {
    fetchData();
    const unsub = bus.on('data:refresh', (e) => {
      if (e.type === 'data:refresh' && e.url === url) fetchData();
    });
    return () => { unsub(); };
  }, [fetchData, ...(deps || [])]);

  return { ...state, refetch: fetchData };
}

/**
 * useMutation — Universal action execution with progress tracking.
 *
 * Usage:
 *   const { execute, loading, progress, error, data } = useMutation('/api/v1/objects/invoice');
 *   execute('POST', { name: 'Tesla', amount: 12500 });
 */
export function useMutation(url: string) {
  const [state, setState] = useState<{
    loading: boolean;
    progress: number;
    error: string | null;
    data: any;
  }>({ loading: false, progress: 0, error: null, data: null });

  const execute = useCallback(
    async (method: string, body?: any, options?: { onProgress?: (pct: number) => void }) => {
      setState({ loading: true, progress: 0, error: null, data: null });
      try {
        let res: Response;
        if (body instanceof FormData) {
          // Upload with XHR for progress
          const xhr = new XMLHttpRequest();
          xhr.open(method, url);
          xhr.withCredentials = true;
          xhr.upload?.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
              const pct = Math.round((e.loaded / e.total) * 100);
              setState((s) => ({ ...s, progress: pct }));
              options?.onProgress?.(pct);
            }
          });
          const result = await new Promise<any>((resolve, reject) => {
            xhr.onload = () => {
              try {
                const d = JSON.parse(xhr.responseText);
                resolve(d);
              } catch {
                resolve(xhr.responseText);
              }
            };
            xhr.onerror = () => reject(new Error('Network error'));
            xhr.send(body);
          });
          setState({ loading: false, progress: 100, error: null, data: result });
          bus.emit({ type: 'data:refresh', url });
          bus.emit({ type: 'notification', kind: 'success', message: `${method} ${url} succeeded` });
          return result;
        } else {
          res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: body ? JSON.stringify(body) : undefined,
          });
          const json = await res.json();
          if (!res.ok) throw new Error(json.error || `HTTP ${res.status}`);
          setState({ loading: false, progress: 100, error: null, data: json });
          bus.emit({ type: 'data:refresh', url });
          bus.emit({ type: 'notification', kind: 'success', message: `${method} ${url} succeeded` });
          return json;
        }
      } catch (e: any) {
        const msg = e.message || 'Unknown error';
        setState({ loading: false, progress: 0, error: msg, data: null });
        bus.emit({ type: 'SystemError', source: url, error: msg });
        bus.emit({ type: 'notification', kind: 'error', message: msg });
        return null;
      }
    },
    [url],
  );

  return { ...state, execute };
}