"""
SHUNYA AI — Chat API Route.

POST /api/v1/ai/chat — Unified AI chat endpoint using the provider registry
with automatic fallback chain: Groq → Gemini → OpenRouter → Cloudflare → HuggingFace → Local.
Supports optional web_search flag that fetches search results from /api/v1/search
and prepends them as system context.
"""
from flask import Blueprint, request, jsonify
import logging
import requests
from urllib.parse import quote

from .provider import _registry

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__, url_prefix='/api/v1/ai')


@ai_bp.route('/chat', methods=['POST'])
def chat():
    """Send a chat completion request. Auto-fallsback through provider chain on failure."""
    data = request.get_json(silent=True) or {}
    messages = data.get('messages', [])
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens', 1024)
    web_search = data.get('web_search', False)

    if not messages:
        return jsonify({'error': 'messages is required'}), 400

    # ── Web Search Integration ──
    # When web_search is true, extract the last user message, call the search endpoint,
    # and prepend results as system context before sending to the AI provider.
    if web_search:
        try:
            # Find the last user message to use as search query
            last_user_msg = ''
            for m in reversed(messages):
                if m.get('role') == 'user':
                    last_user_msg = m.get('content', '')[:200]
                    break

            if last_user_msg:
                # Call the internal search API (same process, same Flask app)
                from flask import current_app
                with current_app.app_context():
                    search_response = requests.get(
                        f'http://localhost:5001/api/v1/search?q={quote(last_user_msg)}',
                        timeout=10,
                    )

                    if search_response.ok:
                        search_data = search_response.json()
                        results = search_data.get('data', [])

                        if results:
                            # Build web search context string
                            context_parts = [f"Web search results for '{last_user_msg}':"]
                            for r in results[:5]:
                                title = r.get('title', '')
                                snippet = r.get('snippet', '')
                                url = r.get('url', r.get('id', ''))
                                context_parts.append(f"- {title}: {snippet} ({url})")

                            context = '\n'.join(context_parts)

                            # Prepend as a system message (insert after the first system message,
                            # or at position 0)
                            sys_idx = -1
                            for i, m in enumerate(messages):
                                if m.get('role') == 'system':
                                    sys_idx = i
                                    break

                            if sys_idx >= 0:
                                messages.insert(sys_idx + 1, {
                                    'role': 'system',
                                    'content': context
                                })
                            else:
                                messages.insert(0, {
                                    'role': 'system',
                                    'content': context
                                })
        except Exception as e:
            logger.warning(f'AI web search integration failed: {e}')
            # Non-critical — continue with the original messages

    # Get all available providers (resolved chain)
    provider = _registry.resolve()
    chain = _registry.chain

    # Try providers in order, falling back on error
    fallback_used = False
    last_error = ''

    for p in chain:
        if not p.is_available():
            continue

        try:
            result = p.complete(messages, temperature=temperature, max_tokens=max_tokens)
            if result.get('finish_reason') == 'error':
                last_error = result.get('error', 'Provider error')
                logger.warning(f'AI provider {p.name} failed: {last_error}')
                fallback_used = True
                continue
            # PHASE 2A: Evidence log for AI response
            try:
                from app.evidence.service import log_evidence
                log_evidence(
                    action="ai_response",
                    source=p.name,
                    confidence=0.92 if not fallback_used else 0.65,
                    evidence_type="ai",
                    inputs={"model": getattr(p, 'model', 'unknown'), "messages_count": len(messages)},
                    outputs={
                        "finish_reason": result.get('finish_reason', 'stop'),
                        "fallback_used": fallback_used,
                    },
                )
            except Exception:
                pass
            # PHASE 2C: Cortex observation for AI response
            try:
                from app.intelligence.cortex_bridge import observe_ai_response
                observe_ai_response(
                    provider=p.name,
                    model=getattr(p, 'model', 'unknown'),
                    confidence=0.92 if not fallback_used else 0.65,
                    fallback_used=fallback_used,
                )
            except Exception:
                pass
            return jsonify({
                'content': result.get('content', ''),
                'model': result.get('model', getattr(p, 'model', 'unknown')),
                'provider': p.name,
                'usage': result.get('usage', {}),
                'finish_reason': result.get('finish_reason', 'stop'),
                'fallback': fallback_used,
            })
        except Exception as e:
            last_error = str(e)
            logger.warning(f'AI provider {p.name} exception: {last_error}')
            fallback_used = True
            continue

    return jsonify({
        'error': f'All providers unavailable. Last error: {last_error}',
        'model': 'none',
        'fallback': True,
    }), 503