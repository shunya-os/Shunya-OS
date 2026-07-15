"""Inspect all route registrations, decorators, and views."""
import inspect
import sys

from app import create_app
from app.routes import bp

app = create_app(config_override={
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SECRET_KEY': 'test',
})

with app.app_context():
    rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
    for rule in rules:
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f'{methods:10s} {rule.rule:40s} {rule.endpoint}')

print("\n\n=== View function sources ===")
# Get relevant view functions
for rule in rules:
    if 'static' in rule.endpoint:
        continue
    try:
        view_func = app.view_functions[rule.endpoint]
        module = inspect.getmodule(view_func)
        source = inspect.getsource(view_func)
        # Print first 15 lines to see decorators
        lines = source.split('\n')
        print(f"\n>>> {rule.endpoint} ({rule.rule})")
        for line in lines[:15]:
            print(f"  {line}")
    except Exception as e:
        print(f"  {rule.endpoint}: {e}")