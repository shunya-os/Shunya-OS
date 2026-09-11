"""Exercise the real deploy shell boundary with isolated command doubles.

This proves stop/continue ordering, not real database backup or deployment.
The backup itself is separately restored into an isolated PostgreSQL cluster.
"""
import os
from pathlib import Path
import subprocess


def test_failed_backup_prevents_upgrade_and_restart(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source = (root / 'infrastructure/scripts/deploy.sh').read_text()
    # Execute the actual migration boundary, not a rewritten simulation of it.
    start = source.index('# ---- Step 7:')
    end = source.index('# ---- Step 9:')
    commands = tmp_path / 'bin'
    commands.mkdir()
    trace = tmp_path / 'commands'
    for name, body in {
        'alembic': 'printf "alembic %s\\n" "$*" >> "$TRACE"; exit 0',
        'python3': 'printf "backup\\n" >> "$TRACE"; exit 7',
    }.items():
        executable = commands / name
        executable.write_text('#!/bin/sh\n' + body + '\n')
        executable.chmod(0o700)
    (tmp_path / 'alembic.ini').touch()
    result = subprocess.run(['bash', '-c', 'set -euo pipefail\n' + source[start:end]],
                            cwd=tmp_path, capture_output=True, text=True,
                            env={**os.environ, 'PATH': str(commands) + os.pathsep + os.environ['PATH'],
                                 'TRACE': str(trace), 'BACKUP_DIR': str(tmp_path / 'backup'),
                                 'DEPLOY_LOG': str(tmp_path / 'deploy.log')})
    assert result.returncode != 0
    assert 'backup' in trace.read_text()
    assert 'alembic upgrade' not in trace.read_text()
