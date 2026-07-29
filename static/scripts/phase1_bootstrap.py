"""Phase 1 — Bootstrap Verification: Runtime Registration"""
from core.os import get_os, reset_os

os = get_os()
os.bootstrap()

h = os.health_check()
print(f'Registered runtimes: {h["runtime_count"]}')
print(f'Pipeline stages:     {h["pipeline"]["stage_count"]}')
print(f'Health status:       {h["status"]}')
print()

for name, rt in sorted(os.runtimes.items()):
    stages = getattr(rt, 'stages', None)
    stage_names = [s.value for s in stages] if stages else []
    print(f'  runtime={name:20s}  stages={stage_names}')

print()
print('--- Runtime health ---')
for name in sorted(h['pipeline']['runtimes'].keys()):
    rth = h['pipeline']['runtimes'][name]
    status = rth.get('status', '?')
    extras = {k: v for k, v in rth.items() if k not in ('status', 'runtime')}
    print(f'  {name:20s}  status={status}  {extras}')

reset_os()