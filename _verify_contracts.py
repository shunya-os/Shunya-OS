"""Verify actual route contracts using the same fixture pattern as tests."""
import pytest

# Reuse the exact conftest fixtures via a tiny pytest runner
from app import create_app, db
from app.models import Lead, Payment, Invoice, Supplier, ActivityLog


def main():
    app = create_app(config_override={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test',
    })
    with app.app_context():
        db.create_all()

        with app.test_client() as client:
            # 1. Dashboard
            print("=== Dashboard (GET /) ===")
            try:
                r = client.get("/")
                print(f"  Status: {r.status_code}")
                html = r.data.decode("utf-8")
                for term in ["Shunya", "AI@panchi.club", "Dashboard", "Shunya OS"]:
                    count = html.count(term)
                    print(f"  {term!r}: found {count} time(s)")
                import re
                m = re.search(r"<title>(.*?)</title>", html)
                if m:
                    print(f"  <title>: {m.group(1)}")
                print(f"  Body length: {len(html)} bytes")
            except Exception as e:
                print(f"  ERROR: {e}")
            print()

            # 2. Settings
            print("=== Settings (GET /settings) ===")
            try:
                r = client.get("/settings")
                print(f"  Status: {r.status_code}")
                html2 = r.data.decode("utf-8")
                print(f"  'Settings' in body: {'Settings' in html2}")
                print(f"  200: {r.status_code == 200}")
                print(f"  Body length: {len(html2)} bytes")
            except Exception as e:
                print(f"  ERROR: {e}")
            print()

            # 3. API 404
            print("=== API 404 (GET /shunya/nonexistent) ===")
            r = client.get("/shunya/nonexistent")
            print(f"  Status: {r.status_code}")
            data = r.get_json()
            print(f"  JSON keys: {list(data.keys()) if data else None}")
            print(f"  'error' key: {'error' in data}")
            print(f"  Content-Type: {r.content_type}")
            print()

            # 4. UI 404
            print("=== UI 404 (GET /nonexistent-ui-route) ===")
            r = client.get("/nonexistent-ui-route")
            print(f"  Status: {r.status_code}")
            html4 = r.data.decode("utf-8")
            print(f"  '404' in body: {'404' in html4}")
            print(f"  'Page not found' in body: {'Page not found' in html4}")
            print(f"  Content-Type: {r.content_type}")
            print(f"  'errorhandler' is HTML: {not r.content_type or 'json' not in r.content_type}")
            print()

        db.drop_all()


if __name__ == "__main__":
    main()