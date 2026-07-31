/** UBME API client — talks to /api/ubme/* endpoints. */

import type { ModuleDef, BusinessTemplate, ObjectTypeDef, ObjectInstance, NavGroup } from './types';

const BASE = '/api/ubme';

async function json<T>(path: string, options?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`);
  return data;
}

// ── Module Management ──

export async function listModules(): Promise<ModuleDef[]> {
  const res = await json<{ data: ModuleDef[] }>('/modules');
  return res.data;
}

export async function getModule(key: string): Promise<ModuleDef> {
  const res = await json<{ data: ModuleDef }>(`/modules/${key}`);
  return res.data;
}

export async function createModule(module: Partial<ModuleDef>): Promise<ModuleDef> {
  const res = await json<{ module: ModuleDef }>('/modules', {
    method: 'POST',
    body: JSON.stringify(module),
  });
  return res.module;
}

export async function updateModule(key: string, module: Partial<ModuleDef>): Promise<ModuleDef> {
  const res = await json<{ module: ModuleDef }>(`/modules/${key}`, {
    method: 'PUT',
    body: JSON.stringify(module),
  });
  return res.module;
}

export async function deleteModule(key: string): Promise<void> {
  await json<void>(`/modules/${key}`, { method: 'DELETE' });
}

// ── Templates ──

export async function listTemplates(): Promise<BusinessTemplate[]> {
  const res = await json<{ data: BusinessTemplate[] }>('/templates');
  return res.data;
}

export async function installTemplate(templateId: string): Promise<ModuleDef> {
  const res = await json<{ module: ModuleDef }>(`/modules/${templateId}/install`, {
    method: 'POST',
    body: JSON.stringify({ template_id: templateId }),
  });
  return res.module;
}

// ── Object Types ──

export async function listTypes(): Promise<Record<string, ObjectTypeDef[]>> {
  const res = await json<{ data: Record<string, ObjectTypeDef[]> }>('/types');
  return res.data;
}

export async function getType(typeKey: string): Promise<{ data: ObjectTypeDef; module_key: string }> {
  return json<{ data: ObjectTypeDef; module_key: string }>(`/types/${typeKey}`);
}

// ── Object Instances ──

export async function listObjects(objectType: string): Promise<ObjectInstance[]> {
  const res = await json<{ data: ObjectInstance[] }>(`/data/${objectType}`);
  return res.data;
}

export async function createObject(objectType: string, data: Record<string, any>): Promise<ObjectInstance> {
  const res = await json<{ data: ObjectInstance }>(`/data/${objectType}`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return res.data;
}

export async function getObject(objectType: string, id: string): Promise<ObjectInstance> {
  const res = await json<{ data: ObjectInstance }>(`/data/${objectType}/${id}`);
  return res.data;
}

export async function updateObject(objectType: string, id: string, data: Record<string, any>): Promise<ObjectInstance> {
  const res = await json<{ data: ObjectInstance }>(`/data/${objectType}/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
  return res.data;
}

export async function deleteObject(objectType: string, id: string): Promise<void> {
  await json<void>(`/data/${objectType}/${id}`, { method: 'DELETE' });
}

// ── Actions & Dashboard ──

export async function getActions(objectType: string): Promise<import('./types').ActionDef[]> {
  const res = await json<{ data: import('./types').ActionDef[] }>(`/actions/${objectType}`);
  return res.data;
}

export async function getDashboard(moduleKey: string): Promise<import('./types').DashboardCard[]> {
  const res = await json<{ data: import('./types').DashboardCard[] }>(`/dashboard/${moduleKey}`);
  return res.data;
}

export async function getViews(objectType: string): Promise<import('./types').ViewDef[]> {
  const res = await json<{ data: import('./types').ViewDef[] }>(`/views/${objectType}`);
  return res.data;
}

export async function getNavigation(): Promise<Record<string, NavGroup>> {
  const res = await json<{ data: Record<string, NavGroup> }>('/navigation');
  return res.data;
}