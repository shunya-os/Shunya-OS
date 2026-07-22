"""
Initialize Alembic for SHUNYA backend.

Usage:
  python scripts/init_alembic.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Lead, Payment, Supplier, Invoice, ItineraryRef
from alembic.config import Config
from alembic import command
from flask import current_app

app = create_app()
with app.app_context():
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'alembic.ini')
    alembic_cfg = Config(cfg_path)
    alembic_cfg.set_main_option('sqlalchemy.url', current_app.config['SQLALCHEMY_DATABASE_URI'])
    command.stamp(alembic_cfg, 'head')
    print('Alembic initialized to head')
