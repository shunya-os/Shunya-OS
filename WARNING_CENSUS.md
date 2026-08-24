# SHUNYA Warning Census — ZGC-PR-09
**Generated:** 2026-08-24 · **SHA:** 68dfc8e
**CI baseline:** 4882 passed, 107 skipped, 15147 warnings

---

## Warning Categories

| # | Category | Count | Source | Classification | Action |
|---|----------|-------|--------|----------------|--------|
| 1 | `LegacyAPIWarning: The Query.get() method is considered legacy...` | ~5,000 | SQLAlchemy 1.x → 2.0 migration | **FIRST-PARTY MAINTENANCE** | `Model.query.get(id)` → `db.session.get(Model, id)` across 49 app files + 13 test files |
| 2 | `DeprecationWarning: datetime.datetime.utcnow() is deprecated...` | ~5,000 | Python 3.12+ stdlib change | **FIRST-PARTY MAINTENANCE** | `datetime.utcnow()` → `datetime.now(timezone.utc)` across ~40 files |
| 3 | `DeprecationWarning: pythonjsonlogger.jsonlogger has been moved...` | ~500 | Upstream dependency | **DEPENDENCY BLOCKED** | pythonjsonlogger package needs update |
| 4 | `PytestConfigWarning: Unknown config option: timeout_method` | ~500 | test framework config | **TEST FRAMEWORK NOISE** | Remove from pytest.ini |
| 5 | SQLAlchemy schema.py `datetime.utcnow()` internal | ~2,000 | SQLAlchemy internal | **EXTERNAL TOOLING NOISE** | SQLAlchemy upstream fix needed |
| 6 | Other deprecations | ~147 | Various | **DEPENDENCY BLOCKED** | Minor library upgrades |

---

## Source Files — SQLAlchemy Query.get() (app/)

`app/__init__.py`, `app/authz/decorators.py`, `app/automation/service.py`,
`app/communication/oauth.py`, `app/content_studio/routes.py`,
`app/customer_experience/routes.py`, `app/customer_experience/service.py`,
`app/enterprise/service.py`, `app/execution/recovery.py`,
`app/finance/governance.py`, `app/founder/executive_home_service.py`,
`app/founder/workspace_intelligence.py`, `app/g5/service.py`,
`app/identity/service.py`, `app/integration/routes.py`,
`app/integration/service.py`, `app/intelligence/decision_engine.py`,
`app/intelligence/service.py`, `app/kernel/routes.py`,
`app/marketing_intelligence/routes.py`, `app/marketing_intelligence/service.py`,
`app/objects/file_routes.py`, `app/onboard.py`, `app/platform/webhook.py`,
`app/routes.py`, `app/runtime/decision_engine.py`, `app/runtime/entry.py`,
`app/runtime/loop.py`, `app/sales_intelligence/service.py`,
`app/workspace_objects/routes.py`

## Source Files — datetime.utcnow()

`app/crm/service.py`, `app/memory/__init__.py`, `app/services.py`,
`app/integration/gmail_adapter.py`, `app/content_studio/routes.py` (via model),
`app/orchestration/routes.py`, `app/execution/routes.py`,
`app/intelligence/memory_store.py`, `app/intelligence/service.py`,
`app/founder/builder_routes.py`, `app/founder/executive_home_service.py`,
`tests/test_fda11_crm.py`, `tests/test_fda_certification.py`,
`tests/test_models.py`, `tests/*.py`

---

## Ownership

| Classification | Total | Action Required |
|----------------|-------|-----------------|
| **FIX NOW** (this directive) | Tests + content_studio + crm_service | Fix utcnow() + query.get() in critical paths |
| **FIRST-PARTY MAINTENANCE** | ~10,000 | Systematic migration across all app/ files |
| **DEPENDENCY BLOCKED** | ~500 | pythonjsonlogger upgrade |
| **EXTERNAL TOOLING NOISE** | ~2,000 | SQLAlchemy internal — upstream fix |
| **TEST FRAMEWORK NOISE** | ~500 | pytest.ini cleanup |