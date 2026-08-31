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

    # ── Conversation Identity & Persistence ──
    conversation_id = data.get('conversation_id')
    from flask import session as flask_session
    tenant_id = flask_session.get('tenant_id', 0)
    identity_id = str(flask_session.get('identity_id', flask_session.get('user_id', '')))
    conv_object_id = data.get('object_id', '')  # Link to a founder_object

    # Create or resolve conversation for persistence
    import uuid as _uuid
    if not conversation_id:
        conversation_id = f"conv_{_uuid.uuid4().hex[:16]}"
    elif not tenant_id and flask_session.get('current_org_id'):
        tenant_id = flask_session.get('current_org_id')

    # Persist the user message(s) to FounderConversation
    try:
        from app.founder.models import FounderConversation, FounderMessage
        from app import db as _db
        from datetime import datetime as _dt

        # Find or create conversation with a valid object_id (FK to founder_objects)
        conv_object_ref = conv_object_id or "conv_system"
        conv = FounderConversation.query.filter_by(conv_id=conversation_id).first()
        if not conv:
            # Ensure the founder_object exists for the FK constraint
            from app.founder.models import FounderObject, FounderSpace
            existing_obj = FounderObject.query.filter_by(object_id=conv_object_ref).first()
            if not existing_obj:
                # Find or create a system space
                system_space = FounderSpace.query.filter_by(space_id="space_system").first()
                if not system_space:
                    system_space = FounderSpace(
                        space_id="space_system",
                        name="System Space",
                        space_type="system",
                        identity_id=identity_id or 'system',
                    )
                    _db.session.add(system_space)
                    _db.session.flush()
                obj = FounderObject(
                    object_id=conv_object_ref,
                    space_id=system_space.space_id,
                    object_type="conversation",
                    name=messages[-1].get('content', 'Conversation')[:100] if messages else 'Conversation',
                    created_by=identity_id or 'system',
                )
                _db.session.add(obj)
                _db.session.flush()
            conv = FounderConversation(
                conv_id=conversation_id,
                object_id=conv_object_ref,
                title=messages[-1].get('content', 'New conversation')[:100] if messages else 'New conversation',
                identity_id=identity_id or 'anonymous',
                status='active',
            )
            _db.session.add(conv)
            _db.session.commit()

        # Store each user message
        for m in messages:
            if m.get('role') in ('user', 'human'):
                existing = FounderMessage.query.filter_by(
                    conv_id=conversation_id,
                    role='human',
                    content=m.get('content', '')[:500]
                ).first()
                if not existing:
                    fm = FounderMessage(
                        conv_id=conversation_id,
                        role='human',
                        content=m.get('content', '')[:5000],
                    )
                    _db.session.add(fm)
        _db.session.commit()
    except Exception as e:
        logger.warning(f'Conversation persistence (user msg): {e}')
        _db.session.rollback()

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

    # ── Canonical Inference via Orchestrator ──
    # Uses the InferenceOrchestrator (classify→policy→select→execute→observe)
    # as the primary routing path. Falls back to direct provider chain on failure.
    fallback_used = False
    last_error = ''
    result = None
    p = None  # provider reference for side effects

    # Extract the last user message for the orchestrator
    input_text = ''
    for m in reversed(messages):
        if m.get('role') == 'user':
            input_text = m.get('content', '')
            break

    # Try canonical orchestrator first
    if input_text:
        try:
            from core.inference_orchestrator import (
                get_orchestrator, OrchestratorRequest,
            )
            orch = get_orchestrator()
            orch_request = OrchestratorRequest(
                input_text=input_text,
                session_id=conversation_id or 'ai_chat',
                temperature=temperature,
                max_tokens=max_tokens,
                request_type='chat',
            )
            orch_response = orch.process(orch_request)
            if orch_response.success:
                result = {
                    'content': orch_response.content or '',
                    'model': orch_response.model or 'unknown',
                    'provider': orch_response.provider or 'orchestrator',
                    'usage': orch_response.usage or {},
                    'finish_reason': orch_response.finish_reason or 'stop',
                    '_orchestrator_pipeline': (
                        [s.to_dict() for s in orch_response.pipeline]
                        if orch_response.pipeline else []
                    ),
                }
                p = type('ProviderRef', (), {'name': 'orchestrator', 'model': orch_response.model or 'unknown'})()
            else:
                last_error = orch_response.error or 'Orchestrator returned no success'
                logger.warning(f'Orchestrator fell through: {last_error}')
        except Exception as e:
            last_error = str(e)
            logger.warning(f'Orchestrator failed, falling back to provider chain: {last_error}')

    # Fallback: try providers in order
    if result is None:
        provider = _registry.resolve()
        chain = _registry.chain
        for p in chain:
            if not p.is_available():
                continue
            try:
                result = p.complete(messages, temperature=temperature, max_tokens=max_tokens)
                if result.get('finish_reason') == 'error':
                    last_error = result.get('error', 'Provider error')
                    logger.warning(f'AI provider {p.name} failed: {last_error}')
                    fallback_used = True
                    result = None
                    continue
                break
            except Exception as e:
                last_error = str(e)
                logger.warning(f'AI provider {p.name} exception: {last_error}')
                fallback_used = True
                result = None
                continue

    if result is None:
        return jsonify({
            'error': f'All providers unavailable. Last error: {last_error}',
            'model': 'none',
            'fallback': True,
        }), 503

    # ── Side Effects (preserved after canonical inference) ──
    # PHASE 2A: Evidence log for AI response
    try:
        from app.evidence.service import log_evidence
        log_evidence(
            action="ai_response",
            source=result.get('provider', p.name if p else 'unknown'),
            confidence=0.92 if not fallback_used else 0.65,
            evidence_type="ai",
            inputs={"model": result.get('model', 'unknown'), "messages_count": len(messages)},
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
            provider=result.get('provider', 'unknown'),
            model=result.get('model', 'unknown'),
            confidence=0.92 if not fallback_used else 0.65,
            fallback_used=fallback_used,
        )
    except Exception:
        pass
    # PHASE 3: Command lifecycle — create execution for meaningful commands
    execution_info = None
    _chat_conv_id = conversation_id or data.get('conversation_id')
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

    # PHASE 4: Create Outcome record for this chat turn
    chat_outcome_id = None
    try:
        from app.execution.models import Outcome as _Outcome
        from app import db as _db3
        import uuid as _uuid3
        from datetime import datetime, timezone

        chat_outcome_id = f"o{_uuid3.uuid4().hex[:11]}"
        chat_outcome = _Outcome(
            outcome_id=chat_outcome_id,
            identity_id=flask_session.get('identity_id', flask_session.get('user_id', 'anonymous')),
            intention=last_user_msg[:500] if last_user_msg else 'AI chat',
            state={
                'type': 'chat_response',
                'source': 'ai_chat',
                'source_id': conversation_id,
                'conversation_id': conversation_id,
                'description': (result.get('content', '') or '')[:2000],
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        _db3.session.add(chat_outcome)
        _db3.session.commit()
    except Exception as e_out:
        logger.warning(f'Chat outcome persistence error: {e_out}')
        chat_outcome_id = None

    response_data = {
        'content': result.get('content', ''),
        'model': result.get('model', 'unknown'),
        'provider': result.get('provider', 'unknown'),
        'usage': result.get('usage', {}),
        'finish_reason': result.get('finish_reason', 'stop'),
        'fallback': fallback_used,
        'outcome_id': chat_outcome_id,
    }
    if result.get('_orchestrator_pipeline'):
        response_data['orchestrator_pipeline'] = result['_orchestrator_pipeline']
    if execution_info:
        response_data['command'] = {
            'outcome_id': execution_info.get('outcome_id'),
            'task_id': execution_info.get('task_id'),
            'drilldown': execution_info.get('drilldown'),
        }
    # Persist AI response to conversation
    response_data['conversation_id'] = conversation_id
    try:
        from app.founder.models import FounderMessage
        from app import db as _db2
        ai_content = result.get('content', '')
        if ai_content:
            fm = FounderMessage(
                conv_id=conversation_id,
                role='assistant',
                content=ai_content[:5000],
            )
            _db2.session.add(fm)
            _db2.session.commit()
    except Exception as e_ai:
        logger.warning(f'Conversation persistence (AI msg): {e_ai}')
    return jsonify(response_data)


@ai_bp.route('/conversations', methods=['GET'])
def list_conversations():
    """List recent conversations for the current identity."""
    from flask import session as flask_session
    identity_id = str(flask_session.get('identity_id', flask_session.get('user_id', '')))
    if not identity_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    try:
        from app.founder.models import FounderConversation
        convs = FounderConversation.query.filter_by(identity_id=identity_id)\
            .order_by(FounderConversation.updated_at.desc()).limit(50).all()
        return jsonify({
            'success': True,
            'data': [c.to_dict() for c in convs],
        })
    except Exception as e:
        logger.warning(f'List conversations error: {e}')
        return jsonify({'success': True, 'data': [], 'note': 'No conversations yet'})


@ai_bp.route('/conversations/<conv_id>', methods=['GET'])
def get_conversation(conv_id):
    """Get a conversation with its messages."""
    try:
        from app.founder.models import FounderConversation, FounderMessage
        conv = FounderConversation.query.filter_by(conv_id=conv_id).first()
        if not conv:
            return jsonify({'error': 'Conversation not found'}), 404
        msgs = FounderMessage.query.filter_by(conv_id=conv_id)\
            .order_by(FounderMessage.created_at.asc()).all()
        return jsonify({
            'success': True,
            'data': {
                'conversation': conv.to_dict(),
                'messages': [m.to_dict() for m in msgs],
            }
        })
    except Exception as e:
        logger.warning(f'Get conversation error: {e}')
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/conversations/<conv_id>/outputs', methods=['GET'])
def get_conversation_outputs(conv_id):
    """Get outcomes (outputs) linked to an AI conversation.

    Queries Outcome records where state['source'] == 'ai_chat'
    and state['source_id'] == conv_id. Returns the outcomes
    alongside the conversation metadata.

    GET /api/v1/ai/conversations/<conv_id>/outputs
    """
    try:
        from app.execution.models import Outcome
        from app.founder.models import FounderConversation
        from sqlalchemy import text

        conv = FounderConversation.query.filter_by(conv_id=conv_id).first()
        if not conv:
            return jsonify({'error': 'Conversation not found'}), 404

        # Query outcomes where state->>'source' = 'ai_chat' and state->>'source_id' = conv_id
        outcomes = Outcome.query.filter(
            Outcome.state['source'].astext == 'ai_chat',
            Outcome.state['source_id'].astext == conv_id,
        ).order_by(Outcome.created_at.desc()).all()

        return jsonify({
            'success': True,
            'data': {
                'conversation': conv.to_dict(),
                'outcomes': [o.to_dict() for o in outcomes],
                'count': len(outcomes),
            }
        })
    except Exception as e:
        logger.warning(f'Get conversation outputs error: {e}')
        return jsonify({'success': True, 'data': {'outcomes': [], 'count': 0}})


@ai_bp.route('/save-output', methods=['POST'])
def save_output():
    """Save an AI response as an actionable organisational object.

    POST /api/v1/ai/save-output
    {
        "conversation_id": "conv_xxx",
        "content": "AI response text to save",
        "output_type": "task|note|proposal|document",
        "title": "Optional title"
    }

    Creates an Outcome + ExecutionLog entry so the output is
    discoverable through execution visibility APIs.
    """
    data = request.get_json(silent=True) or {}
    conversation_id = data.get('conversation_id', '')
    content = data.get('content', '').strip()
    output_type = data.get('output_type', 'task')
    title = data.get('title', '') or content[:80]

    if not content:
        return jsonify({'error': 'content is required'}), 400

    from flask import session as flask_session
    tenant_id = flask_session.get('tenant_id', flask_session.get('current_org_id', 0))
    identity_id = str(flask_session.get('identity_id', flask_session.get('user_id', '')))

    try:
        from app.execution.models import Outcome
        from app import db as _db
        import uuid as _uuid
        from datetime import datetime, timezone

        outcome_id = f"o{_uuid.uuid4().hex[:11]}"
        now = datetime.now(timezone.utc)

        outcome = Outcome(
            outcome_id=outcome_id,
            identity_id=identity_id or 'anonymous',
            intention=title[:500],
            state={
                'type': output_type or 'task',
                'conversation_id': conversation_id,
                'source_id': conversation_id,
                'description': content[:2000],
                'source': 'ai_chat',
            },
            created_at=now,
            updated_at=now,
        )
        _db.session.add(outcome)
        _db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'outcome_id': outcome_id,
                'type': output_type or 'task',
                'title': title,
                'conversation_id': conversation_id,
            }
        })
    except Exception as e:
        logger.error(f'Save output error: {e}')
        return jsonify({'error': str(e)}), 500