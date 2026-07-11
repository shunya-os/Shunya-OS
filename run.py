#!/usr/bin/env python3
"""Shunya OS — Dev entry point."""
import os
os.environ.setdefault("FLASK_ENV", "development")
from app import create_app
app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
