/**
 * Integrations API Client — All integration endpoints.
 *
 * Covers: API key management, social media, ad campaigns,
 * content generation, and proxy services.
 */

const BASE = '/api/v1/integration';

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const extraHeaders: Record<string, string> = {};
  try {
    const raw = sessionStorage.getItem('shunya_session');
    if (raw) {
      const session = JSON.parse(raw);
      if (session.identityId) {
        extraHeaders['X-Identity-Id'] = session.identityId;
      }
    }
  } catch {
    /* noop */
  }
  const r = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...extraHeaders, ...opts?.headers },
    credentials: 'include',
    ...opts,
  });
  if (r.status >= 500) {
    throw new Error(`Server error (${r.status}). Please try again.`);
  }
  return r.json();
}

// ── Types ──

export interface IntegrationProvider {
  id: string;
  name: string;
  type: string;
  icon: string;
  description: string;
  free: boolean;
  category: string;
  docs_url: string;
}

export interface IntegrationConfig {
  id: number;
  identity_id: string;
  provider: string;
  label: string;
  is_active: boolean;
  has_config: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface SocialAccount {
  id: number;
  identity_id: string;
  platform: string;
  account_name: string;
  account_id: string | null;
  profile_picture_url: string | null;
  profile_url: string | null;
  follower_count: number | null;
  is_active: boolean;
  last_sync_at: string | null;
  created_at: string | null;
}

export interface ScheduledPost {
  id: number;
  identity_id: string;
  platform: string;
  content: string;
  media_urls: string[];
  scheduled_at: string | null;
  status: string;
  published_at: string | null;
  post_url: string | null;
  error_message: string | null;
  engagement_metrics: Record<string, any>;
  created_at: string | null;
}

export interface AdCampaign {
  id: number;
  identity_id: string;
  platform: string;
  campaign_name: string;
  campaign_objective: string;
  budget: number | null;
  budget_type: string;
  start_date: string | null;
  end_date: string | null;
  targeting: Record<string, any>;
  creative: Record<string, any>;
  status: string;
  external_campaign_id: string | null;
  performance_metrics: Record<string, any>;
  error_message: string | null;
  created_at: string | null;
}

export interface ContentGeneration {
  id: number;
  identity_id: string;
  content_type: string;
  platform: string | null;
  prompt: string;
  generated_content: string | null;
  tone: string;
  target_audience: string | null;
  word_count: number | null;
  ai_model: string;
  is_favorited: boolean;
  created_at: string | null;
}

// ── Providers ──

export async function fetchProviders(): Promise<{ success: boolean; data: IntegrationProvider[] }> {
  return req('/providers');
}

// ── Configs (API Keys) ──

export async function fetchConfigs(): Promise<{ success: boolean; data: IntegrationConfig[] }> {
  return req('/configs');
}

export async function fetchConfig(provider: string): Promise<{ success: boolean; data: IntegrationConfig }> {
  return req(`/configs/${encodeURIComponent(provider)}`);
}

export async function saveConfig(
  provider: string,
  apiKey: string,
  label?: string,
): Promise<{ success: boolean; data: IntegrationConfig }> {
  return req(`/configs/${encodeURIComponent(provider)}`, {
    method: 'PUT',
    body: JSON.stringify({ api_key: apiKey, label }),
  });
}

export async function removeConfig(provider: string): Promise<{ success: boolean }> {
  return req(`/configs/${encodeURIComponent(provider)}`, { method: 'DELETE' });
}

// ── Social Accounts ──

export async function fetchSocialAccounts(): Promise<{ success: boolean; data: SocialAccount[] }> {
  return req('/social/accounts');
}

export async function linkSocialAccount(data: {
  platform: string;
  account_name: string;
  account_id?: string;
  access_token?: string;
  profile_picture_url?: string;
  profile_url?: string;
  follower_count?: number;
}): Promise<{ success: boolean; data: SocialAccount }> {
  return req('/social/accounts', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function unlinkSocialAccount(accountId: number): Promise<{ success: boolean }> {
  return req(`/social/accounts/${accountId}`, { method: 'DELETE' });
}

// ── Scheduled Posts ──

export async function fetchPosts(status?: string): Promise<{ success: boolean; data: ScheduledPost[] }> {
  const params = status ? `?status=${encodeURIComponent(status)}` : '';
  return req(`/social/posts${params}`);
}

export async function createPost(data: {
  platform: string;
  content: string;
  media_urls?: string[];
  scheduled_at?: string;
}): Promise<{ success: boolean; data: ScheduledPost }> {
  return req('/social/posts', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updatePost(
  postId: number,
  data: Partial<{ content: string; media_urls: string[]; scheduled_at: string; status: string }>,
): Promise<{ success: boolean; data: ScheduledPost }> {
  return req(`/social/posts/${postId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deletePost(postId: number): Promise<{ success: boolean }> {
  return req(`/social/posts/${postId}`, { method: 'DELETE' });
}

export async function publishPost(postId: number): Promise<{ success: boolean; data: any }> {
  return req(`/social/posts/${postId}/publish`, { method: 'POST' });
}

// ── Ad Campaigns ──

export async function fetchAdCampaigns(platform?: string): Promise<{ success: boolean; data: AdCampaign[] }> {
  const params = platform ? `?platform=${encodeURIComponent(platform)}` : '';
  return req(`/ads${params}`);
}

export async function createAdCampaign(data: {
  platform: string;
  campaign_name: string;
  campaign_objective?: string;
  budget?: number;
  budget_type?: string;
  start_date?: string;
  end_date?: string;
  targeting?: Record<string, any>;
  creative?: Record<string, any>;
}): Promise<{ success: boolean; data: AdCampaign }> {
  return req('/ads', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateAdCampaign(
  campaignId: number,
  data: Partial<AdCampaign>,
): Promise<{ success: boolean; data: AdCampaign }> {
  return req(`/ads/${campaignId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteAdCampaign(campaignId: number): Promise<{ success: boolean }> {
  return req(`/ads/${campaignId}`, { method: 'DELETE' });
}

// ── Content Generation ──

export async function generateContent(data: {
  prompt: string;
  content_type?: string;
  tone?: string;
  platform?: string;
  target_audience?: string;
  word_count?: number;
  additional_instructions?: string;
}): Promise<{ success: boolean; data: { content: string; word_count: number; content_type: string } }> {
  return req('/content/generate', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function fetchContentHistory(
  content_type?: string,
  limit?: number,
): Promise<{ success: boolean; data: ContentGeneration[] }> {
  const params = new URLSearchParams();
  if (content_type) params.set('content_type', content_type);
  if (limit) params.set('limit', String(limit));
  return req(`/content/history?${params}`);
}

export async function toggleFavoriteContent(contentId: number): Promise<{ success: boolean; data: ContentGeneration }> {
  return req(`/content/history/${contentId}/favorite`, { method: 'POST' });
}

export async function deleteContentGeneration(contentId: number): Promise<{ success: boolean }> {
  return req(`/content/history/${contentId}`, { method: 'DELETE' });
}

// ── Proxy Services ──

export async function proxyUnsplash(query: string): Promise<{ success: boolean; data: any[]; count: number }> {
  return req(`/proxy/unsplash?query=${encodeURIComponent(query)}`);
}

export async function proxyPexels(query: string): Promise<{ success: boolean; data: any[]; count: number }> {
  return req(`/proxy/pexels?query=${encodeURIComponent(query)}`);
}

export async function proxyNews(query: string): Promise<{ success: boolean; data: any[]; count: number }> {
  return req(`/proxy/news?query=${encodeURIComponent(query)}`);
}

export async function proxyWeather(city: string): Promise<{ success: boolean; data: any }> {
  return req(`/proxy/weather?city=${encodeURIComponent(city)}`);
}

export async function proxyYouTube(query: string): Promise<{ success: boolean; data: any[]; count: number }> {
  return req(`/proxy/youtube?query=${encodeURIComponent(query)}`);
}

export async function proxyGitHub(query: string): Promise<{ success: boolean; data: any[]; count: number }> {
  return req(`/proxy/github?query=${encodeURIComponent(query)}`);
}

// ── Notifications ──

export async function fetchNotifications(
  unreadOnly = false,
): Promise<{ success: boolean; data: any[]; count: number }> {
  return req(`/notifications${unreadOnly ? '?unread_only=true' : ''}`);
}

export async function fetchUnreadCount(): Promise<{ success: boolean; data: { unread_count: number } }> {
  return req('/notifications/unread-count');
}

export async function markNotificationRead(notifId: number): Promise<{ success: boolean }> {
  return req(`/notifications/${notifId}/read`, { method: 'POST' });
}

export async function markAllNotificationsRead(): Promise<{ success: boolean; data: { marked_read: number } }> {
  return req('/notifications/read-all', { method: 'POST' });
}

export async function fetchPreferences(): Promise<{ success: boolean; data: any }> {
  return req('/notifications/preferences');
}

export async function updatePreferences(data: any): Promise<{ success: boolean; data: any }> {
  return req('/notifications/preferences', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}
