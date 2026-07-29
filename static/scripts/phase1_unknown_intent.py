"""Phase 1 — Unknown Intent: Graceful Noop Verification"""
from core.os import get_os, reset_os

os = get_os()
os.bootstrap()

result = os.process_intent('nonexistent_action', {})
print(f'state={result.state}')
for s in result.trace:
    if s.stage == 'execution_update':
        print(f'  execution_update: status={s.status}  runtime={s.runtime}')
        assert s.status in ('completed', 'noop'), (
            f'Expected completed/noop, got {s.status}'
        )
        print('PASS: Unknown intent produces completed/noop, not failure')

reset_os()