"""Create a validated PostgreSQL archive before deployment; fail closed.

Credentials are read from configuration and passed using a mode-0600 temporary
pgpass file, never in argv or logs. Partial archives are retained as evidence.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from dotenv import load_dotenv
from sqlalchemy.engine import make_url


def backup(destination: Path) -> None:
    load_dotenv(Path(__file__).resolve().parents[2] / '.env')
    url = make_url(os.environ.get('DATABASE_URL', ''))
    if url.get_backend_name() != 'postgresql' or not url.database:
        raise ValueError('PostgreSQL configuration required')
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ValueError('Backup destination already exists')
    def escape(value):
        return str(value).replace('\\', '\\\\').replace(':', '\\:')
    host, port = url.host or 'localhost', url.port or 5432
    with tempfile.TemporaryDirectory(prefix='shunya-backup-auth-') as directory:
        pgpass = Path(directory) / 'pgpass'
        with open(pgpass, 'x', opener=lambda p, flags: os.open(p, flags, 0o600)) as stream:
            stream.write(':'.join(escape(v) for v in
                                 (host, port, url.database, url.username or '*', url.password or '')) + '\n')
        env = {k: v for k, v in os.environ.items() if k not in {'DATABASE_URL', 'PGPASSWORD'}}
        env['PGPASSFILE'] = str(pgpass)
        fd, partial_name = tempfile.mkstemp(prefix=destination.name + '.partial-', dir=destination.parent)
        os.close(fd)
        partial = Path(partial_name)
        command = ['pg_dump', '--no-password', '--format=custom', '--host', host,
                   '--port', str(port), '--dbname', url.database, '--file', str(partial)]
        if url.username:
            command.extend(['--username', url.username])
        subprocess.run(command, env=env, check=True, capture_output=True, timeout=600)
        if partial.stat().st_size == 0:
            raise ValueError('Empty backup')
        subprocess.run(['pg_restore', '--list', str(partial)], env=env,
                       check=True, capture_output=True, timeout=60)
        partial.replace(destination)


if __name__ == '__main__':
    try:
        backup(Path(sys.argv[1]))
    except Exception as error:
        # Do not expose connection strings or pg_dump diagnostics with credentials.
        print(f'Backup failed ({type(error).__name__}); migration must not proceed.', file=sys.stderr)
        sys.exit(1)
    print('Backup archive created and catalog verified.')
