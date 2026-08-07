/**
 * AI Chat Service — Frontend interface for the Groq-backed AI chat API.
 *
 * POST /api/v1/ai/chat — Unified endpoint with automatic provider fallback.
 * Supports optional web search integration (enabled by default).
 *
 * Usage:
 *   import { aiChat } from './api/ai-chat';
 *   const result = await aiChat([{ role: 'user', content: 'Hello' }]);
 *   console.log(result.content); // "Hello! I'm SHUNYA..."
 */

export interface AIChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface AIChatResult {
  content: string;
  model: string;
  provider: string;
  usage: Record<string, number>;
  finish_reason: string;
  fallback: boolean;
  error?: string;
}

/**
 * Send a chat completion request through the unified AI provider chain.
 * Falls back automatically: Groq → Gemini → OpenRouter → Cloudflare → HF → Local.
 * When webSearch is true (default), the backend fetches search results and prepends them
 * as context before sending to the AI provider.
 */
export async function aiChat(
  messages: AIChatMessage[],
  options?: { temperature?: number; max_tokens?: number; webSearch?: boolean },
): Promise<AIChatResult> {
  const resp = await fetch('/api/v1/ai/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages,
      temperature: options?.temperature ?? 0.7,
      max_tokens: options?.max_tokens ?? 1024,
      web_search: options?.webSearch ?? true,  // Web search enabled by default
    }),
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: 'Request failed' }));
    return {
      content: '',
      model: 'none',
      provider: 'error',
      usage: {},
      finish_reason: 'error',
      fallback: true,
      error: err.error || `HTTP ${resp.status}`,
    };
  }

  return resp.json();
}

/**
 * Quick one-shot: single user message → AI response text.
 * Supports optional web search (enabled by default).
 */
export async function aiAsk(prompt: string, system?: string, webSearch?: boolean): Promise<string> {
  const messages: AIChatMessage[] = [];
  if (system) messages.push({ role: 'system', content: system });
  messages.push({ role: 'user', content: prompt });

  const result = await aiChat(messages, { max_tokens: 512, webSearch });
  return result.content || result.error || '(empty response)';
}