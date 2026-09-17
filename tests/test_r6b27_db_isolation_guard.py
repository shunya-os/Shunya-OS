"""R6B-2.7 §8 — database isolation regression guard.

Root cause being guarded: `tests/test_g11_identity_object.py` was executed with
DATABASE_URL pointing at the production cluster (localhost:5432/shunya_os) and
wrote 344 `object_type='test'` rows into the real Panchi Club organization
(org 7, workspace spc_business). These tests prove that:

  * the canonical predicate classifies production URLs as production-like
  * isolated URLs (sqlite memory, the 5433 certification cluster) are permitted
  * assert_isolated_database() fails closed on a production URL
  * create_app() refuses a production database under TESTING and under
    SHUNYA_REQUIRE_ISOLATED_DB=1 (the certification-script opt-in)
"""
import os

import pytest

from app.safety.db_guard import (
    assert_isolated_database,
    is_isolated_url,
    is_production_like,
)


PRODUCTION_URLS = [
    "postgresql://shunya:secret@localhost:5432/shunya_os",
    "postgresql://shunya:secret@localhost:5432/shunya_db",
    "postgresql://shunya:secret@localhost:5432/shunya",
    "postgresql://shunya:secret@db.internal:5432/shunya_os",
    "postgresql://shunya:secret@localhost:9999/production",
]

ISOLATED_URLS = [
    "sqlite:///:memory:",
    "sqlite:////tmp/shunya_test.db",
    "postgresql://shunya-deploy@127.0.0.1:5433/shunya_r6b27_cert2",
    "postgresql://shunya-deploy@127.0.0.1:5433/shunya_r6b27_cert",
    "postgresql://user@127.0.0.1:5433/shunya_r6b25_cert",
]


class TestProductionPredicate:
    @pytest.mark.parametrize("url", PRODUCTION_URLS)
    def test_production_urls_are_flagged(self, url):
        assert is_production_like(url) is True

    @pytest.mark.parametrize("url", ISOLATED_URLS)
    def test_isolated_urls_are_permitted(self, url):
        assert is_production_like(url) is False

    def test_sqlite_memory_is_isolated(self):
        assert is_isolated_url("sqlite:///:memory:") is True

    def test_empty_url_is_not_production(self):
        # Empty is handled separately (conftest requires an explicit URL).
        assert is_production_like("") is False


class TestFailClosed:
    @pytest.mark.parametrize("url", PRODUCTION_URLS)
    def test_assert_raises_on_production(self, url):
        with pytest.raises(RuntimeError):
            assert_isolated_database(url, context="test")

    @pytest.mark.parametrize("url", ISOLATED_URLS)
    def test_assert_allows_isolated(self, url):
        assert assert_isolated_database(url, context="test") is True


class TestCreateAppRefusesProduction:
    def test_testing_mode_refuses_production_db(self):
        from app import create_app

        with pytest.raises(RuntimeError):
            create_app({
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI":
                    "postgresql://shunya:secret@localhost:5432/shunya_os",
            })

    def test_certification_flag_refuses_production_db(self):
        from app import create_app

        os.environ["SHUNYA_REQUIRE_ISOLATED_DB"] = "1"
        try:
            with pytest.raises(RuntimeError):
                create_app({
                    "SQLALCHEMY_DATABASE_URI":
                        "postgresql://shunya:secret@localhost:5432/shunya_os",
                })
        finally:
            os.environ.pop("SHUNYA_REQUIRE_ISOLATED_DB", None)

    def test_certification_flag_allows_isolated_db(self):
        from app import create_app

        os.environ["SHUNYA_REQUIRE_ISOLATED_DB"] = "1"
        try:
            app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
            assert app is not None
        finally:
            os.environ.pop("SHUNYA_REQUIRE_ISOLATED_DB", None)