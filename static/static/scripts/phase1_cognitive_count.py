"""Phase 1 — Cognitive Runtime: Engine Count Verification"""
from core.os import get_os, reset_os

os = get_os()
os.bootstrap()
h = os.health_check()
cognitive = h['pipeline']['runtimes'].get('cognitive', {})
print(f'Cognitive: {cognitive}')
assert cognitive.get('engine_count') == 8, (
    f'Expected 8 engines, got {cognitive.get("engine_count")}'
)
print('PASS: Cognitive runtime has 8 intelligence engines')
reset_os()