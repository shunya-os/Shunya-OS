"""
Legacy health check wrapper.
The /health endpoint is now built into the main app (app/__init__.py).
This script is kept for Docker HEALTHCHECK compatibility.
Usage: python healthcheck.py  → exits 0 if healthy, 1 if not
"""
import sys
import urllib.request

HOST = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
try:
    resp = urllib.request.urlopen(f"{HOST}/health", timeout=10)
    if resp.status == 200:
        sys.exit(0)
    sys.exit(1)
except Exception:
    sys.exit(1)