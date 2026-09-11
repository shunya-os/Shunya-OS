"""Deployment must stop before migrations if its backup is not restorable."""
import os
from pathlib import Path
import subprocess
import sys


def test_backup_failure_is_nonzero_and_not_published(tmp_path):
    scripts = Path(__file__).resolve().parents[1] / 'infrastructure' / 'scripts'
    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    dump = fake_bin / 'pg_dump'
    dump.write_text('#!/bin/sh\nexit 7\n')
    dump.chmod(0o700)
    dest = tmp_path / 'backup.dump'
    result = subprocess.run(
        [sys.executable, str(scripts / 'backup_database.py'), str(dest)],
        env={**os.environ, 'DATABASE_URL': 'postgresql://test:private-value@127.0.0.1:5433/test_backup',
             'PATH': str(fake_bin) + os.pathsep + os.environ['PATH']},
        capture_output=True, text=True,
    )
    assert result.returncode == 1, result.stderr
    assert 'Backup failed' in result.stderr
    assert 'private-value' not in result.stderr + result.stdout
    assert not dest.exists()


def test_backup_rejects_unsupported_database(tmp_path):
    scripts = Path(__file__).resolve().parents[1] / 'infrastructure' / 'scripts'
    result = subprocess.run(
        [sys.executable, str(scripts / 'backup_database.py'), str(tmp_path / 'backup.dump')],
        env={**os.environ, 'DATABASE_URL': 'sqlite:///:memory:'},
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert 'Backup failed' in result.stderr
