// SHUNYA Frontend — Component Registry
// Maps component IDs to components for dynamic resolution.

import type { ComponentType } from 'react';

type RegistryEntry = {
  component: ComponentType<any>;
  metadata?: {
    category: string;
    description?: string;
    version?: string;
  };
};

class ComponentRegistry {
  private registry = new Map<string, RegistryEntry>();

  register(name: string, component: ComponentType<any>, metadata?: RegistryEntry['metadata']): void {
    this.registry.set(name, { component, metadata });
  }

  get(name: string): ComponentType<any> | null {
    return this.registry.get(name)?.component ?? null;
  }

  has(name: string): boolean {
    return this.registry.has(name);
  }

  getMetadata(name: string): RegistryEntry['metadata'] | null {
    return this.registry.get(name)?.metadata ?? null;
  }

  getAll(): Array<{ name: string; metadata?: RegistryEntry['metadata'] }> {
    return Array.from(this.registry.entries()).map(([name, entry]) => ({ name, metadata: entry.metadata }));
  }

  getByCategory(category: string): Array<{ name: string; metadata?: RegistryEntry['metadata'] }> {
    return this.getAll().filter((e) => e.metadata?.category === category);
  }

  clear(): void {
    this.registry.clear();
  }
}

export const componentRegistry = new ComponentRegistry();
export { ComponentRegistry };
export type { RegistryEntry };
