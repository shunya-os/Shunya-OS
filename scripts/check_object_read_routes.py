"""Route registration check for the canonical object read surfaces.

The frontend reads these paths and they previously did not exist as GET
routes, so every read failed (405/404) and the workspace showed a FALSE EMPTY
STATE. This script is a fast fail-closed check that they are mounted with the
methods the product calls; it is used during development and is safe to rerun.
"""
import sys

sys.path.insert(0, "/home/shunya-deploy/shunya_os")

from app import create_app  # noqa: E402

app = create_app({
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    "WTF_CSRF_ENABLED": False,
})

wanted = {
    ("/api/v1/objects/types", "GET"),
    ("/api/v1/objects/<object_type>", "GET"),
    ("/api/v1/objects", "GET"),
    ("/api/v1/objects/", "GET"),
    ("/api/v1/objects/<int:object_id>", "GET"),
}
found = set()
for rule in app.url_map.iter_rules():
    for method in rule.methods or ():
        found.add((str(rule.rule), method))

for path, method in sorted(wanted):
    print(f"{'OK  ' if (path, method) in found else 'MISS'} {method:5s} {path}")

print("\nAll object read rules mounted:",
      all((p, m) in found for p, m in wanted))
