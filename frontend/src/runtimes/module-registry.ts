/**
 * Module Registry — Platform service for business module lifecycle.
 *
 * Responsibilities:
 * - Discover installed modules from the module manifest
 * - Load modules dynamically (no platform imports business modules by name)
 * - Coordinate discovery, registration, search, and AI across all modules
 * - Gracefully handle missing/empty modules (platform runs without any)
 *
 * The platform never imports a module by name. All module interaction
 * is through this registry, which discovers modules via a manifest.
 */

// ── Module Contract ────────────────────────────────────────────

export interface ShunyaModule {
  id: string;
  name: string;
  /** Called during bootstrap. Module discovers available data. */
  discover: () => Promise<Record<string, any>>;
  /** Called after discovery. Module registers workspaces, commands, etc. */
  register: (data: Record<string, any>) => Promise<void>;
  /** Search across the module's domain objects. */
  search: (query: string) => Promise<{ id: string; type: string; title: string; subtitle: string; status?: string }[]>;
  /** Answer a question from the module's domain expertise. */
  ask: (question: string) => Promise<string | null>;
}

// ── Module Manifest ────────────────────────────────────────────

/**
 * Module manifest — the only place where module identities are declared.
 * Adding a new module means adding one entry here.
 * No platform code changes required.
 *
 * Uses Vite's `import.meta.glob` for dynamic imports at build time,
 * or falls back to a static list for environments that don't support glob.
 */

interface ManifestEntry {
  id: string;
  path: () => Promise<{ default: ShunyaModule }>;
}

const MANIFEST: ManifestEntry[] = [
  // Add new modules here:
  { id: 'business', path: () => import('./modules/business') },
  // { id: 'hr', path: () => import('./modules/hr') },
  // { id: 'inventory', path: () => import('./modules/inventory') },
];

// ── Registry ───────────────────────────────────────────────────

const loaded = new Map<string, ShunyaModule>();

async function loadFromManifest(): Promise<void> {
  for (const entry of MANIFEST) {
    if (loaded.has(entry.id)) continue;
    try {
      const mod = await entry.path();
      loaded.set(entry.id, mod.default);
    } catch (err) {
      console.warn(`[ModuleRegistry] Failed to load module '${entry.id}':`, err);
    }
  }
}

export const ModuleRegistry = {
  /** Get a loaded module by ID. */
  get(id: string): ShunyaModule | undefined {
    return loaded.get(id);
  },

  /** Get all loaded modules. */
  getAll(): ShunyaModule[] {
    return Array.from(loaded.values());
  },

  /** Load all modules from the manifest. */
  async loadAll(): Promise<void> {
    await loadFromManifest();
  },

  /** Discover data from all loaded modules. Returns merged result. */
  async discoverAll(): Promise<Record<string, any>> {
    const data: Record<string, any> = {};
    for (const mod of loaded.values()) {
      try {
        const d = await mod.discover();
        Object.assign(data, d);
      } catch { /* module unavailable */ }
    }
    return data;
  },

  /** Register all loaded modules with the platform. */
  async registerAll(data: Record<string, any>): Promise<void> {
    for (const mod of loaded.values()) {
      try { await mod.register(data); } catch (err) { console.warn(`[ModuleRegistry] register ${mod.id}:`, err); }
    }
  },

  /** Search across all loaded modules. */
  async searchAll(query: string): Promise<{ id: string; type: string; title: string; subtitle: string; status?: string }[]> {
    const results: { id: string; type: string; title: string; subtitle: string; status?: string }[] = [];
    for (const mod of loaded.values()) {
      try {
        const hits = await mod.search(query);
        results.push(...hits);
      } catch { /* skip */ }
    }
    return results;
  },

  /** Ask all loaded modules. Returns first non-null answer. */
  async askAll(question: string): Promise<string | null> {
    for (const mod of loaded.values()) {
      try {
        const answer = await mod.ask(question);
        if (answer) return answer;
      } catch { /* skip */ }
    }
    return null;
  },

  /** Check if any modules are loaded. */
  get hasModules(): boolean {
    return loaded.size > 0;
  },

  /** Clear all modules (testing). */
  clear(): void {
    loaded.clear();
  },
};