#!/usr/bin/env python3
"""Ad-hoc verification for Marketing & Growth module."""
import ast, sys, os, inspect, importlib.util

errors = []

def check(ok, msg):
    if ok:
        print(f"  ✅ {msg}")
    else:
        print(f"  ❌ {msg}")
        errors.append(msg)

# ── 1. SYNTAX CHECK ──
print("=== 1. Syntax Check ===")
files = [
    "/root/shunya_os/app/__init__.py",
    "/root/shunya_os/app/shunya/marketing.py",
    "/root/shunya_os/app/routes/marketing.py",
    "/root/shunya_os/templates/base.html",
    "/root/shunya_os/templates/marketing/dashboard.html",
]
for f in files:
    ok = True
    try:
        with open(f) as fh:
            content = fh.read()
        if f.endswith(".py"):
            ast.parse(content)
    except Exception as e:
        ok = False
    check(ok, os.path.relpath(f))

# ── 2. IMPORT TEST ──
print("\n=== 2. Import & Logic Test ===")
sys.path.insert(0, "/root/shunya_os")
os.environ.setdefault("FLASK_ENV", "development")

try:
    from app.shunya.marketing import MarketingDashboard, MARKETING_ENTITY_TYPES
    check(True, "Module imports OK")
except Exception as e:
    check(False, f"Module import: {e}")
    sys.exit(1)

# Validate entity types
expected = {"campaign", "email_campaign", "lead_generator", "content_asset", "social_post", "webinar"}
actual = set(MARKETING_ENTITY_TYPES.keys())
check(actual == expected, f"Entity types: {actual}")

for etype, config in MARKETING_ENTITY_TYPES.items():
    check("label" in config, f"{etype}: label")
    check("icon" in config, f"{etype}: icon")
    check("schema" in config and len(config["schema"]) >= 3, f"{etype}: schema ({len(config['schema'])} fields)")
    check("statuses" in config and len(config["statuses"]) >= 2, f"{etype}: statuses ({len(config['statuses'])})")
    req = [f for f in config["schema"] if f.get("required")]
    check(len(req) >= 1, f"{etype}: required fields ({len(req)})")

# ── 3. MarketingDashboard METHODS ──
print("\n=== 3. MarketingDashboard Methods ===")
for m in ["get_overview", "get_campaign_stats", "get_lead_metrics", "ensure_types"]:
    check(hasattr(MarketingDashboard, m), f"Has method: {m}")
sig = inspect.signature(MarketingDashboard.__init__)
check("tenant_id" in sig.parameters, "__init__(self, tenant_id)")

# ── 4. BLUEPRINT ROUTES ──
print("\n=== 4. Blueprint Routes ===")
spec = importlib.util.spec_from_file_location("mkt_routes", "/root/shunya_os/app/routes/marketing.py")
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
    check(True, "Routes module loads")
except Exception as e:
    check(False, f"Routes module load: {e}")
    sys.exit(1)

bp = mod.marketing_bp
check(bp.name == "marketing", f"Blueprint name: {bp.name}")
check(bp.url_prefix == "/marketing", f"URL prefix: {bp.url_prefix}")
check(hasattr(mod, "marketing_dashboard"), "Route: marketing_dashboard")
check(hasattr(mod, "campaign_list"), "Route: campaign_list")
check(hasattr(mod, "marketing_metrics"), "Route: marketing_metrics")

# ── 5. APP INIT ──
print("\n=== 5. App Init Integration ===")
with open("/root/shunya_os/app/__init__.py") as f:
    init_content = f.read()
check("from app.routes.marketing import marketing_bp" in init_content, "Blueprint import")
check("app.register_blueprint(marketing_bp)" in init_content, "Blueprint registration")
check('"Marketing"' in init_content, "nav_modules entry")
check('/marketing/dashboard' in init_content, "nav URL")

# ── 6. BASE TEMPLATE ──
print("\n=== 6. Base Template ===")
with open("/root/shunya_os/templates/base.html") as f:
    base = f.read()
check('/marketing/dashboard' in base, "Marketing nav link")
check('Marketing' in base, "Marketing label")

# ── 7. DASHBOARD TEMPLATE ──
print("\n=== 7. Dashboard Template ===")
with open("/root/shunya_os/templates/marketing/dashboard.html") as f:
    tmpl = f.read()
check('extends "base.html"' in tmpl, "Extends base.html")
check("overview" in tmpl, "overview context")
check("recent_campaigns" in tmpl, "recent_campaigns context")
check("lead_metrics" in tmpl, "lead_metrics context")
check("campaign_statuses" in tmpl, "campaign_statuses context")

# ── SUMMARY ──
print(f"\n{'='*50}")
total = 7  # sections
passed = total - (1 if errors else 0)
if errors:
    print(f"❌ {len(errors)} check(s) FAILED:")
    for e in errors:
        print(f"   - {e}")
    sys.exit(1)
else:
    print(f"🎯 ALL {total} VERIFICATION SECTIONS PASSED")
    print(f"{'='*50}")
