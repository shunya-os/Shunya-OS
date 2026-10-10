/** Analytics API — client for /api/v1/analytics/dashboard. */

export interface DashboardData {
  total_objects: number;
  total_relationships: number;
  total_documents: number;
  total_ai_queries: number;
  recent_activity: { date: string; count: number }[];
  workspace_breakdown: { type: string; count: number }[];
  top_ai_queries: { query: string; count: number }[];
}

export interface DashboardResponse {
  success: boolean;
  data?: DashboardData;
  error?: string;
}

export async function fetchDashboard(): Promise<DashboardResponse> {
  try {
    const r = await fetch('/api/v1/analytics/dashboard', { credentials: 'include' });
    return r.json();
  } catch {
    return { success: false, error: 'Network error fetching dashboard data' };
  }
}