"""
SHUNYA Health Check — used by Docker HEALTHCHECK and external monitoring.

Usage:
    python healthcheck.py                    # checks /health on 127.0.0.1:5000
    python healthcheck.py http://web:8000    # checks /health on custom host

Exits 0 if healthy, 1 if not.
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