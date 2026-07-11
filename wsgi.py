#!/usr/bin/env python3
"""Shunya OS — WSGI entry point."""
import os
os.environ.setdefault("FLASK_ENV", "production")
from app import create_app
app = create_app(os.getenv("FLASK_ENV", "production"))
