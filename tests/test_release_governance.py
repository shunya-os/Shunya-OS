"""Release evidence must not manufacture certification (no production writes)."""
import json
import pytest
from app import release_governance as release


@pytest.fixture
def provenance_file(tmp_path, monkeypatch):
    path = tmp_path / 'release_provenance.json'
    monkeypatch.setattr(release, 'RELEASE_PROVENANCE_FILE', str(path))
    monkeypatch.setattr(release, '_current_sha', lambda: 'a' * 40)
    return path


def test_missing_record_is_unverified(provenance_file):
    result = release.get_release_provenance()
    assert result['release_type'] == 'UNVERIFIED'
    assert result['health_verified'] is False
    assert result['authorized_by'] == ''
    assert result['deployed_at'] == ''


@pytest.mark.parametrize('payload', ['invalid json', '[]', 'null', '{}'])
def test_invalid_record_is_unverified(provenance_file, payload):
    provenance_file.write_text(payload)
    result = release.get_release_provenance()
    assert result['release_type'] == 'UNVERIFIED'
    assert result['health_verified'] is False


def test_stale_record_cannot_certify_running_sha(provenance_file):
    record = release.record_normal_deployment('b' * 40)
    result = release.get_release_provenance()
    assert result['release_type'] == 'UNVERIFIED'
    assert result['health_verified'] is False
    assert result['recorded_git_commit'] == record['git_commit']
    assert json.loads(provenance_file.read_text()) == record


def test_valid_record_preserves_evidence(provenance_file):
    record = release.record_normal_deployment('a' * 40)
    assert release.get_release_provenance() == record


def test_explicit_running_sha_not_mutable_checkout(provenance_file):
    release.record_normal_deployment('a' * 40)
    result = release.get_release_provenance(running_sha='c' * 40)
    assert result['release_type'] == 'UNVERIFIED'
    assert result['git_commit'] == 'c' * 40


def test_normal_deployment_records_previous_release(provenance_file):
    record = release.record_normal_deployment('a' * 40, previous_sha='b' * 40)
    assert record['rollback_sha'] == 'b' * 40


def test_health_never_certifies_failed_record_read(client, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError('unavailable')
    monkeypatch.setattr(release, 'get_release_provenance', fail)
    result = client.get('/health')
    assert result.status_code == 200
    assert result.json['release_type'] == 'UNVERIFIED'
    assert result.json['release_health_verified'] is False


def test_health_matches_record_to_loaded_build(client, provenance_file, monkeypatch):
    import app
    monkeypatch.setattr(app, '_GIT_COMMIT', 'c' * 40)
    release.record_normal_deployment('a' * 40)
    result = client.get('/health')
    assert result.status_code == 200
    assert result.json['git_commit'] == 'c' * 40
    assert result.json['release_type'] == 'UNVERIFIED'
    assert result.json['release_health_verified'] is False
