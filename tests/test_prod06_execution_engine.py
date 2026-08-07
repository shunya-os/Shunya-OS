"""PROD-06: Execution Engine + Truth Layer tests."""


class TestExecutionEngine:

    def test_execute_activates_new_object(self, app, client):
        r = client.post('/api/v1/objects/', json={'type': 'entity', 'state': {'status': 'new'}})
        obj = r.get_json()
        assert obj['state'] == {'status': 'new'}

        r = client.post(f'/api/v1/execution/{obj["id"]}/run')
        result = r.get_json()
        assert result['decision'] == 'activate'
        assert result['final_state'] == {'status': 'active'}
        assert 'execution_id' in result

    def test_execute_noop_on_active_object(self, app, client):
        r = client.post('/api/v1/objects/', json={'type': 'entity', 'state': {'status': 'new'}})
        obj = r.get_json()

        r = client.post(f'/api/v1/execution/{obj["id"]}/run')
        assert r.get_json()['decision'] == 'activate'

        r = client.post(f'/api/v1/execution/{obj["id"]}/run')
        result = r.get_json()
        assert result['decision'] == 'noop'
        assert result['final_state'] == {'status': 'active'}

    def test_execution_persisted(self, app, client):
        from app.execution_engine.models import Execution
        r = client.post('/api/v1/objects/', json={'type': 'entity', 'state': {'status': 'new'}})
        obj = r.get_json()
        client.post(f'/api/v1/execution/{obj["id"]}/run')
        client.post(f'/api/v1/execution/{obj["id"]}/run')

        execs = Execution.query.filter_by(object_id=obj['id']).all()
        assert len(execs) == 2
        assert all(e.status == 'completed' for e in execs)

    def test_execution_404_for_missing_object(self, client):
        r = client.post('/api/v1/execution/99999/run')
        assert r.status_code == 404