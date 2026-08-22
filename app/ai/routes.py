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


@ai_bp.route('/research', methods=['POST'])
def research():
    """Universal research endpoint — uses the canonical research orchestrator.
    
    POST /api/v1/ai/research
    {
        "question": "...",
        "freshness_seconds": 3600,
        "capability": "research"
    }
    """
    data = request.get_json(silent=True) or {}
    question = data.get('question', '')
    if not question:
        return jsonify({'error': 'question is required'}), 400
    
    from flask import session
    tenant_id = session.get('tenant_id', 0)
    actor_id = session.get('identity_id', '')
    
    from core.intelligence.research import get_research_orchestrator
    orch = get_research_orchestrator()
    response = orch.research(
        question=question,
        tenant_id=tenant_id,
        actor_id=actor_id,
        freshness_seconds=data.get('freshness_seconds'),
        capability=data.get('capability'),
    )
    
    return jsonify({
        'request_id': response.request_id,
        'answer': response.answer,
        'summary': response.summary,
        'claims': [
            {
                'statement': c.statement,
                'status': c.status.value,
                'confidence': c.confidence,
                'detail': c.detail,
            }
            for c in response.claims
        ],
        'context_used': [
            {'source': s.source, 'type': s.type, 'detail': s.detail}
            for s in response.context_used
        ],
        'external_sources': [
            {'source': s.source, 'url': s.url, 'detail': s.detail}
            for s in response.external_sources_used
        ],
        'deterministic': response.deterministic_result is not None,
        'model_used': response.model_used,
        'provider_used': response.provider_used,
        'freshness_verified': response.freshness_verified,
        'freshness_ok': response.freshness_ok,
        'freshness_note': response.freshness_note,
        'degraded': response.degraded,
        'error': response.error,
        'duration_ms': response.duration_ms,
    })


@ai_bp.route('/explain', methods=['POST'])
def explain():
    """Explain a previous intelligence result.
    
    POST /api/v1/ai/explain
    {
        "request_id": "..."
    }
    """
    data = request.get_json(silent=True) or {}
    request_id = data.get('request_id', '')
    if not request_id:
        return jsonify({'error': 'request_id is required'}), 400
    
    from flask import session
    tenant_id = session.get('tenant_id', 0)
    
    from core.intelligence.explain import ExplanationService
    from core.intelligence import get_intelligence_service
    service = ExplanationService()
    
    # For now, explain a fresh research result
    # (In production, this would look up a stored response by request_id)
    from core.intelligence import IntelligenceRequest, IntelligenceCapability
    question = data.get('question', 'Explain the previous result')
    req = IntelligenceRequest(question=question, request_id=request_id, tenant_id=tenant_id)
    iq = get_intelligence_service()
    response = iq.process(req)
    
    explanations = service.explain_response(response)
    return jsonify({
        'explanations': [
            {
                'claim': e.claim,
                'status': e.status,
                'conclusion': e.conclusion[:300],
                'evidence_count': e.evidence_count,
                'governed_evidence_count': e.governed_evidence_count,
                'external_evidence_count': e.external_evidence_count,
                'confidence': e.confidence,
                'confidence_known': e.confidence_known,
                'freshness_verified': e.freshness_verified,
                'freshness_ok': e.freshness_ok,
                'freshness_note': e.freshness_note,
                'assumptions': e.assumptions,
                'conflicts': e.conflicts,
                'missing_information': e.missing_information,
                'model_used': e.model_used,
                'provider_used': e.provider_used,
            }
            for e in explanations
        ],
    })


@ai_bp.route('/correct', methods=['POST'])
def correct():
    """Correct a previous intelligence conclusion.
    
    POST /api/v1/ai/correct
    {
        "request_id": "...",
        "target_claim": "...",
        "corrected_value": "...",
        "reason": "..."
    }
    """
    data = request.get_json(silent=True) or {}
    target_claim = data.get('target_claim', '')
    corrected_value = data.get('corrected_value', '')
    
    if not target_claim or not corrected_value:
        return jsonify({'error': 'target_claim and corrected_value are required'}), 400
    
    from flask import session
    tenant_id = session.get('tenant_id', 0)
    actor_id = session.get('identity_id', '')
    
    from core.intelligence.correction import (
        CorrectionService, CorrectionRecord, CorrectionType,
    )
    service = CorrectionService()
    
    correction = CorrectionRecord(
        correction_type=CorrectionType.FACTUAL,
        target_claim=target_claim,
        original_value=data.get('original_value', ''),
        corrected_value=corrected_value,
        reason=data.get('reason', ''),
        tenant_id=tenant_id,
        actor_id=actor_id,
    )
    
    valid, reason = service.validate_correction(correction, tenant_id)
    if not valid:
        return jsonify({'error': reason}), 403
    
    cid = service.record_correction(correction)
    return jsonify({
        'correction_id': cid,
        'target_claim': target_claim,
        'corrected_value': corrected_value,
        'original_value': correction.original_value,
        'tenant_id': tenant_id,
    })


@ai_bp.route('/preference', methods=['POST'])
def preference():
    """Record a user preference.
    
    POST /api/v1/ai/preference
    {
        "key": "risk_threshold",
        "value": "high",
        "scope": "user"
    }
    """
    data = request.get_json(silent=True) or {}
    key = data.get('key', '')
    value = data.get('value', '')
    
    if not key or not value:
        return jsonify({'error': 'key and value are required'}), 400
    
    from flask import session
    tenant_id = session.get('tenant_id', 0)
    actor_id = session.get('identity_id', '')
    
    from core.intelligence.correction import CorrectionService, PreferenceRecord
    service = CorrectionService()
    
    pref = PreferenceRecord(
        key=key,
        value=value,
        tenant_id=tenant_id,
        actor_id=actor_id,
        scope=data.get('scope', 'tenant'),
    )
    
    pid = service.record_preference(pref)
    return jsonify({
        'preference_id': pid,
        'key': key,
        'value': value,
        'scope': pref.scope,
        'tenant_id': tenant_id,
    })


@ai_bp.route('/outcome', methods=['POST'])
def outcome():
    """Record an observed outcome for a recommendation.
    
    POST /api/v1/ai/outcome
    {
        "recommendation_id": "...",
        "action_taken": "accepted",
        "result": "success",
        "outcome_description": "..."
    }
    """
    data = request.get_json(silent=True) or {}
    recommendation_id = data.get('recommendation_id', '')
    if not recommendation_id:
        return jsonify({'error': 'recommendation_id is required'}), 400
    
    from flask import session
    tenant_id = session.get('tenant_id', 0)
    actor_id = session.get('identity_id', '')
    
    from core.intelligence.correction import CorrectionService, OutcomeRecord
    service = CorrectionService()
    
    outcome = OutcomeRecord(
        recommendation_id=recommendation_id,
        recommendation_summary=data.get('recommendation_summary', ''),
        action_taken=data.get('action_taken', 'unknown'),
        result=data.get('result', 'unknown'),
        outcome_description=data.get('outcome_description', ''),
        tenant_id=tenant_id,
        actor_id=actor_id,
    )
    
    oid = service.record_outcome(outcome)
    return jsonify({
        'outcome_id': oid,
        'recommendation_id': recommendation_id,
        'action_taken': outcome.action_taken,
        'result': outcome.result,
    })


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
    # When web_search is true, extract the last user message, call the search
    # function directly (in-process, no HTTP loop) and prepend results as
    # system context before sending to the AI provider.
    if web_search:
        try:
            # Find the last user message to use as search query
            last_user_msg = ''
            for m in reversed(messages):
                if m.get('role') == 'user':
                    last_user_msg = m.get('content', '')[:200]
                    break

            if last_user_msg:
                # Use in-process search (avoids auth/Session issues of HTTP loopback)
                from app.search.routes import _web_search
                results = _web_search(last_user_msg, max_results=5)

                if results:
                    context_parts = [f"Web search results for '{last_user_msg}':"]
                    for r in results[:5]:
                        title = r.get('title', '')
                        snippet = r.get('snippet', '')
                        url = r.get('url', r.get('id', ''))
                        context_parts.append(f"- {title}: {snippet} ({url})")

                    context = '\n'.join(context_parts)

                    # Prepend as a system message
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
                from app import db
                db.session.commit()
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
            # PHASE 3: Command lifecycle — create execution for meaningful commands
            execution_info = None
            conversation_id = data.get('conversation_id')
            try:
                from app.ai.command_lifecycle import _is_command_message, create_execution_for_command
                from flask import session as flask_session
                last_user_msg = ''
                for m in reversed(messages):
                    if m.get('role') == 'user':
                        last_user_msg = m.get('content', '')
                        break
                is_cmd, action_type = _is_command_message(last_user_msg)
                if is_cmd:
                    execution_info = create_execution_for_command(
                        user_message=last_user_msg,
                        ai_response=result.get('content', ''),
                        conversation_id=conversation_id,
                        tenant_id=flask_session.get('tenant_id', 0),
                        identity_id=str(flask_session.get('user_id', '')),
                    )
            except Exception as e:
                logger.warning(f'AI command lifecycle error: {e}')
            response_data = {
                'content': result.get('content', ''),
                'model': result.get('model', getattr(p, 'model', 'unknown')),
                'provider': p.name,
                'usage': result.get('usage', {}),
                'finish_reason': result.get('finish_reason', 'stop'),
                'fallback': fallback_used,
            }
            if execution_info:
                response_data['command'] = {
                    'outcome_id': execution_info.get('outcome_id'),
                    'task_id': execution_info.get('task_id'),
                    'drilldown': execution_info.get('drilldown'),
                }
            return jsonify(response_data)
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