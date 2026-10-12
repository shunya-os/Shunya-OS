/**
 * Vitest global setup.
 *
 * Node ≥22 defines an experimental `localStorage` global (webstorage) that is
 * `undefined` unless the process runs with `--localstorage-file`. In these
 * environments vitest's jsdom populate step cannot overwrite that global, so
 * tests touching `localStorage` (e.g. onboarding-url-truth) crash with
 * "Cannot read properties of undefined (reading 'clear')".
 *
 * This shim force-installs an in-memory Storage on globalThis when the host
 * global is missing, so storage-dependent tests run in both node and jsdom
 * environments. It does not touch a working jsdom storage.
 */

function installMemoryStorage(key: 'localStorage' | 'sessionStorage') {
  try {
    const g = globalThis as any;
    // Property missing entirely → define it. Accessor returning undefined
    // (Node's experimental global) or undefined value → replace it via
    // defineProperty so the assignment can't be silently dropped.
    const current =
      key in g ? (() => { try { return g[key]; } catch { return undefined; } })() : undefined;
    if (current !== undefined && current !== null) return;

    let data: Record<string, string> = {};
    const storage = {
      get length() {
        return Object.keys(data).length;
      },
      clear() {
        data = {};
      },
      getItem(k: string) {
        return Object.prototype.hasOwnProperty.call(data, k) ? data[k] : null;
      },
      key(i: number) {
        return Object.keys(data)[i] ?? null;
      },
      removeItem(k: string) {
        delete data[k];
      },
      setItem(k: string, v: unknown) {
        data[k] = String(v);
      },
    };
    Object.defineProperty(g, key, {
      value: storage,
      configurable: true,
      writable: true,
      enumerable: true,
    });
  } catch {
    /* Storage host globals are non-configurable — leave as-is. */
  }
}

installMemoryStorage('localStorage');
installMemoryStorage('sessionStorage');

// jsdom has no matchMedia — Mantine's MantineProvider and many component
// libraries call it for color-scheme / media queries. Provide a minimal stub.
if (typeof window !== 'undefined' && typeof window.matchMedia !== 'function') {
  (window as any).matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}