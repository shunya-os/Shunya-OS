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
    """The loaded build SHA, not the checkout, decides release certification.

    The recorded deployment is 'a'*40 while the loaded build is 'c'*40, so the
    release evidence must NOT certify the running build.

    Frontend provenance is isolated to ``worktree_build`` mode so this test
    asserts ONLY the release-governance contract deterministically. The
    immutable-release mismatch contract is covered separately below.
    """
    import app
    from app import frontend_release

    monkeypatch.setattr(app, '_GIT_COMMIT', 'c' * 40)
    monkeypatch.setattr(frontend_release, 'frontend_provenance', lambda *a, **k: {
        'frontend_dist_mode': 'worktree_build',
        'frontend_dist_exists': True,
        'frontend_release_sha': None,
        'frontend_asset_manifest_sha256': None,
        'frontend_release_verified': False,
    })
    release.record_normal_deployment('a' * 40)

    result = client.get('/health')
    assert result.status_code == 200
    assert result.json['git_commit'] == 'c' * 40
    assert result.json['release_type'] == 'UNVERIFIED'
    assert result.json['release_health_verified'] is False


def test_health_fails_closed_when_immutable_release_sha_differs(client, monkeypatch):
    """An immutable release whose SHA differs from the loaded build is a
    fail-closed condition: health must report degraded, never 'ok'."""
    import app
    from app import frontend_release

    monkeypatch.setattr(app, '_GIT_COMMIT', 'c' * 40)
    monkeypatch.setattr(frontend_release, 'frontend_provenance', lambda *a, **k: {
        'frontend_dist_mode': 'immutable_release',
        'frontend_dist_exists': True,
        'frontend_release_sha': 'd' * 40,
        'frontend_asset_manifest_sha256': 'e' * 64,
        'frontend_release_verified': True,
    })

    result = client.get('/health')
    assert result.status_code == 503
    assert result.json['status'] == 'degraded'
    assert result.json['frontend_release_matches_backend'] is False


def test_health_ok_when_immutable_release_sha_matches(client, monkeypatch):
    """A matching immutable release keeps health 'ok' (200)."""
    import app
    from app import frontend_release

    monkeypatch.setattr(app, '_GIT_COMMIT', 'c' * 40)
    monkeypatch.setattr(frontend_release, 'frontend_provenance', lambda *a, **k: {
        'frontend_dist_mode': 'immutable_release',
        'frontend_dist_exists': True,
        'frontend_release_sha': 'c' * 40,
        'frontend_asset_manifest_sha256': 'e' * 64,
        'frontend_release_verified': True,
    })

    result = client.get('/health')
    assert result.status_code == 200
    assert result.json['frontend_release_matches_backend'] is True
