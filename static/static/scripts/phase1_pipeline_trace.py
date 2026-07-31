"""Phase 1 — Pipeline Execution Trace: Real Runtimes Only"""
from core.os import get_os, reset_os

os = get_os()
os.bootstrap()

result = os.process_intent(
    'create_object',
    {'name': 'TestDoc', 'object_type': 'Document'},
    identity_id='audit_identity',
)
print(f'state={result.state}')
print(f'duration={result.total_duration_ms:.2f}ms')
print()

for s in result.trace:
    print(f'  stage={s.stage:25s}  runtime={s.runtime:30s}  status={s.status:10s}  '
          f'dur={s.duration_ms:.2f}ms  err={s.error}')

# Assert: no mock runtime in any trace
stage_runtimes = [(s.stage, s.runtime.lower()) for s in result.trace]
mock_stages = [(st, rt) for st, rt in stage_runtimes if 'mock' in rt]
if mock_stages:
    print(f'\nFAIL: Mock runtimes found: {mock_stages}')
    exit(1)
else:
    print(f'\nPASS: No mock runtimes in any pipeline stage')

# Assert: all 11 stages present
assert len(result.trace) == 11, f'Expected 11 stages, got {len(result.trace)}'
print(f'PASS: All 11 pipeline stages executed')

reset_os()