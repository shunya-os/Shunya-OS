"""Authenticated HTTP isolation and persistence regressions; isolated SQLite only."""
import pytest
from app import db


@pytest.fixture
def chat_scope(app, client, monkeypatch):
    from app.auth import TeamMember
    from app.models import Organization, OrgMember
    from app.authz.services import seed_default_roles
    from app.objects.legacy_models import Workspace, ShunyaObject
    from app.founder.models import FounderConversation
    member = TeamMember(name='Chat owner', email='chat-owner@test.invalid', role='admin', is_active=True)
    member.set_password('isolated-test-password')
    db.session.add(member)
    org = Organization(name='Chat org', slug='chat-isolation')
    db.session.add(org)
    db.session.flush()
    db.session.add(OrgMember(organization_id=org.id, identity_id='sid_chat_owner',
                            email=member.email, role='admin', is_active=True))
    seed_default_roles(org.id)
    ws = Workspace(id='ws_chat_test', name='Chat', workspace_type='business',
                   organization_id=org.id, created_by='sid_chat_owner')
    db.session.add(ws)
    db.session.flush()
    obj = ShunyaObject(object_id='obj_other_chat', workspace_id=ws.id,
                       organization_id=org.id, object_type='conversation',
                       name='Private conversation', created_by='sid_other')
    db.session.add(obj)
    db.session.flush()
    db.session.add(FounderConversation(conv_id='conv_other', object_id=obj.object_id,
                                       title='Private', identity_id='sid_other', status='active'))
    db.session.commit()
    with client.session_transaction() as sess:
        sess.update(user_id=member.id, identity_id='sid_chat_owner', current_org_id=org.id,
                    workspace_id=ws.id)
    calls = []
    def answer(**kwargs):
        calls.append(kwargs)
        return {'content': 'Isolated unit-test inference response', 'model': 'test', 'provider': 'test'}
    monkeypatch.setattr('core.intelligence_runtime.integration.ask', answer)
    return org.id, ws.id, calls


@pytest.mark.parametrize('suffix', ['', '/outputs'])
def test_cannot_read_another_identity_conversation(client, chat_scope, suffix):
    response = client.get('/api/v1/ai/conversations/conv_other' + suffix)
    assert response.status_code == 404
    assert 'Private' not in response.get_data(as_text=True)


def test_cannot_append_to_another_identity_conversation(client, chat_scope):
    from app.founder.models import FounderMessage
    response = client.post('/api/v1/ai/chat', json={
        'conversation_id': 'conv_other', 'messages': [{'role': 'user', 'content': 'Hello'}]})
    assert response.status_code == 404
    assert FounderMessage.query.filter_by(conv_id='conv_other').count() == 0
    assert chat_scope[2] == []


def test_cannot_save_output_on_another_identity_conversation(client, chat_scope):
    response = client.post('/api/v1/ai/save-output', json={
        'conversation_id': 'conv_other', 'content': 'Unauthorized output'})
    assert response.status_code == 404


def test_new_chats_have_distinct_canonical_objects_and_persist(client, chat_scope):
    from app.founder.models import FounderConversation, FounderMessage, FounderSpace
    from app.objects.legacy_models import ShunyaObject
    responses = [client.post('/api/v1/ai/chat', json={
        'messages': [{'role': 'user', 'content': 'Hello'}]}) for _ in range(2)]
    assert all(r.status_code == 200 for r in responses)
    convs = [FounderConversation.query.filter_by(conv_id=r.json['conversation_id']).one() for r in responses]
    assert convs[0].object_id != convs[1].object_id
    for conv in convs:
        obj = ShunyaObject.query.filter_by(object_id=conv.object_id).one()
        assert (obj.organization_id, obj.workspace_id) == chat_scope[:2]
        assert conv.identity_id == 'sid_chat_owner'
        assert FounderMessage.query.filter_by(conv_id=conv.conv_id).count() == 2
    assert FounderSpace.query.filter_by(space_id='space_system').count() == 0


def test_persistence_failure_stops_before_inference(client, chat_scope, monkeypatch):
    from core.object_service import get_object_service
    def fail(**kwargs):
        raise RuntimeError('storage unavailable')
    monkeypatch.setattr(get_object_service(), 'create', fail)
    response = client.post('/api/v1/ai/chat', json={'messages': [{'role': 'user', 'content': 'Hello'}]})
    assert response.status_code == 503
    assert chat_scope[2] == []


def test_missing_workspace_fails_closed(client, chat_scope):
    with client.session_transaction() as sess:
        sess['workspace_id'] = 'missing_workspace'
    response = client.post('/api/v1/ai/chat', json={'messages': [{'role': 'user', 'content': 'Hello'}]})
    assert response.status_code == 400
    assert chat_scope[2] == []


def test_continuation_and_saved_output(client, chat_scope):
    first = client.post('/api/v1/ai/chat', json={'messages': [{'role': 'user', 'content': 'Hello'}]})
    assert first.status_code == 200
    cid = first.json['conversation_id']
    second = client.post('/api/v1/ai/chat', json={'conversation_id': cid,
        'messages': [{'role': 'user', 'content': 'Hello'}, {'role': 'assistant', 'content': 'Prior reply'},
                     {'role': 'user', 'content': 'Next question'}]})
    assert second.status_code == 200
    history = client.get('/api/v1/ai/conversations/' + cid)
    assert history.status_code == 200
    assert [m['content'] for m in history.json['data']['messages'] if m['role'] == 'human'] == ['Hello', 'Next question']
    saved = client.post('/api/v1/ai/save-output', json={'conversation_id': cid, 'content': 'My note', 'output_type': 'note'})
    assert saved.status_code == 200
    outputs = client.get('/api/v1/ai/conversations/' + cid + '/outputs')
    assert outputs.status_code == 200
    assert saved.json['data']['outcome_id'] in [o['outcome_id'] for o in outputs.json['data']['outcomes']]


def test_same_identity_cannot_cross_organization_scope(client, chat_scope):
    from app.models import Organization
    from app.founder.models import FounderConversation
    from app.objects.legacy_models import ShunyaObject, Workspace
    org = Organization(name='Other', slug='other-chat-org')
    db.session.add(org)
    db.session.flush()
    Workspace.query.filter_by(id=chat_scope[1]).update({'organization_id': org.id})
    ShunyaObject.query.filter_by(object_id='obj_other_chat').update({'organization_id': org.id})
    FounderConversation.query.filter_by(conv_id='conv_other').update({'identity_id': 'sid_chat_owner'})
    db.session.commit()
    assert client.get('/api/v1/ai/conversations/conv_other').status_code == 404
    assert client.get('/api/v1/ai/conversations').json['data'] == []
