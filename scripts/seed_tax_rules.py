"""
Seed baseline tax rules and schedule 24-hour auto-refresh.

Run once after migration:
  cd /home/shunya-deploy/shunya_os && .venv/bin/python scripts/seed_tax_rules.py

The cron schedule is managed via Hermes cronjob_manage.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.taxation.fetcher import seed_baseline_rules
from app.taxation.models import TaxRule

app = create_app()
with app.app_context():
    db.create_all()
    seed_baseline_rules()
    count = TaxRule.query.count()
    print(f"Seeded tax rules. Total: {count}")