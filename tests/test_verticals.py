"""Tests for the vertical template registry (app/shunya/verticals.py)."""

import pytest
from app.shunya.verticals import (
    VERTICAL_TEMPLATES,
    get_vertical,
    get_vertical_list,
    get_entity_types_for_vertical,
    get_dashboard_config,
)

# ── helpers ──────────────────────────────────────────────────────────────────

KNOWN_VERTICAL_IDS = sorted(VERTICAL_TEMPLATES.keys())
REQUIRED_VERTICAL_KEYS = {"label", "icon", "description", "code_prefix",
                          "entity_types", "dashboard_metrics"}
REQUIRED_ENTITY_KEYS = {"type", "label", "icon", "primary_field", "schema", "statuses"}
REQUIRED_METRIC_KEYS = {"key", "label", "icon"}


# ── 1.  Registry completeness ───────────────────────────────────────────────

class TestRegistryCompleteness:
    """Verify the set of known verticals."""

    def test_eight_verticals_defined(self):
        """There should be exactly 8 vertical templates."""
        assert len(VERTICAL_TEMPLATES) == 8

    @pytest.mark.parametrize("vid", [
        "travel", "healthcare", "legal", "government",
        "transport", "retail", "education", "custom",
    ])
    def test_vertical_exists(self, vid):
        """Every expected vertical ID must be present."""
        assert vid in VERTICAL_TEMPLATES, f"Missing vertical: {vid}"

    def test_vertical_ids_set(self):
        """The known IDs must be exactly the set of keys."""
        expected = {"travel", "healthcare", "legal", "government",
                    "transport", "retail", "education", "custom"}
        assert set(VERTICAL_TEMPLATES) == expected


# ── 2.  Vertical structure ──────────────────────────────────────────────────

class TestVerticalStructure:
    """Every vertical must define the mandatory top-level fields."""

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_vertical_has_required_keys(self, vid):
        """Each vertical must have all REQUIRED_VERTICAL_KEYS."""
        v = VERTICAL_TEMPLATES[vid]
        missing = REQUIRED_VERTICAL_KEYS - set(v)
        assert not missing, f"Vertical '{vid}' missing keys: {missing}"

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_label_is_nonempty_string(self, vid):
        assert isinstance(VERTICAL_TEMPLATES[vid]["label"], str)
        assert len(VERTICAL_TEMPLATES[vid]["label"]) > 0

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_icon_is_nonempty_string(self, vid):
        assert isinstance(VERTICAL_TEMPLATES[vid]["icon"], str)
        assert len(VERTICAL_TEMPLATES[vid]["icon"]) > 0

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_description_is_nonempty_string(self, vid):
        assert isinstance(VERTICAL_TEMPLATES[vid]["description"], str)
        assert len(VERTICAL_TEMPLATES[vid]["description"]) > 0

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_code_prefix_is_nonempty_string(self, vid):
        assert isinstance(VERTICAL_TEMPLATES[vid]["code_prefix"], str)
        assert len(VERTICAL_TEMPLATES[vid]["code_prefix"]) > 0

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_entity_types_is_list(self, vid):
        assert isinstance(VERTICAL_TEMPLATES[vid]["entity_types"], list)

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_dashboard_metrics_is_list(self, vid):
        assert isinstance(VERTICAL_TEMPLATES[vid]["dashboard_metrics"], list)

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_quick_actions_is_list(self, vid):
        assert isinstance(VERTICAL_TEMPLATES[vid].get("quick_actions", []), list)

    def test_custom_vertical_has_zero_entity_types(self):
        assert VERTICAL_TEMPLATES["custom"]["entity_types"] == []

    @pytest.mark.parametrize("vid", ["travel", "healthcare", "legal", "government",
                                      "transport", "retail", "education"])
    def test_non_custom_verticals_have_entity_types(self, vid):
        """Every non-custom vertical must define at least one entity type."""
        assert len(VERTICAL_TEMPLATES[vid]["entity_types"]) > 0

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_dashboard_metrics_at_least_two(self, vid):
        """Every vertical must have at least 2 dashboard metrics."""
        assert len(VERTICAL_TEMPLATES[vid]["dashboard_metrics"]) >= 2


# ── 3.  Entity-type structure ───────────────────────────────────────────────

class TestEntityTypeStructure:
    """Every entity type within every vertical must be well-formed."""

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_each_entity_type_has_required_keys(self, vid):
        for et in VERTICAL_TEMPLATES[vid]["entity_types"]:
            missing = REQUIRED_ENTITY_KEYS - set(et)
            assert not missing, \
                f"Vertical '{vid}' entity type '{et.get('type', '?')}' missing: {missing}"

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_each_entity_type_has_label_plural(self, vid):
        for et in VERTICAL_TEMPLATES[vid]["entity_types"]:
            assert "label_plural" in et, \
                f"Vertical '{vid}' entity '{et['type']}' missing label_plural"

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_each_entity_type_has_layout(self, vid):
        for et in VERTICAL_TEMPLATES[vid]["entity_types"]:
            assert "layout" in et, \
                f"Vertical '{vid}' entity '{et['type']}' missing layout"

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_each_entity_type_statuses_is_list(self, vid):
        for et in VERTICAL_TEMPLATES[vid]["entity_types"]:
            assert isinstance(et["statuses"], list), \
                f"Vertical '{vid}' entity '{et['type']}' statuses not a list"
            assert len(et["statuses"]) > 0, \
                f"Vertical '{vid}' entity '{et['type']}' has empty statuses"

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_each_entity_type_schema_is_list(self, vid):
        for et in VERTICAL_TEMPLATES[vid]["entity_types"]:
            assert isinstance(et["schema"], list), \
                f"Vertical '{vid}' entity '{et['type']}' schema not a list"
            assert len(et["schema"]) > 0, \
                f"Vertical '{vid}' entity '{et['type']}' has empty schema"

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_each_entity_type_schema_fields_have_name_label_type(self, vid):
        for et in VERTICAL_TEMPLATES[vid]["entity_types"]:
            for field in et["schema"]:
                for key in ("name", "label", "type"):
                    assert key in field, \
                        f"Vertical '{vid}' entity '{et['type']}' schema field missing '{key}'"


# ── 4.  Dashboard metric structure ──────────────────────────────────────────

class TestDashboardMetricStructure:
    """Every dashboard metric must have the required keys."""

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_each_metric_has_required_keys(self, vid):
        for m in VERTICAL_TEMPLATES[vid]["dashboard_metrics"]:
            missing = REQUIRED_METRIC_KEYS - set(m)
            assert not missing, \
                f"Vertical '{vid}' metric '{m.get('key', '?')}' missing: {missing}"

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_each_metric_key_label_icon_are_strings(self, vid):
        for m in VERTICAL_TEMPLATES[vid]["dashboard_metrics"]:
            assert isinstance(m["key"], str), f"'{vid}' metric key not str"
            assert isinstance(m["label"], str), f"'{vid}' metric label not str"
            assert isinstance(m["icon"], str), f"'{vid}' metric icon not str"


# ── 5.  get_vertical() ──────────────────────────────────────────────────────

class TestGetVertical:
    """Functional tests for get_vertical()."""

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_get_vertical_returns_dict(self, vid):
        result = get_vertical(vid)
        assert result is not None
        assert isinstance(result, dict)
        assert result["label"] == VERTICAL_TEMPLATES[vid]["label"]

    def test_get_vertical_unknown_returns_none(self):
        assert get_vertical("nonexistent") is None
        assert get_vertical("") is None

    def test_get_vertical_returns_same_object(self):
        """get_vertical should return the actual dict, not a copy."""
        assert get_vertical("travel") is VERTICAL_TEMPLATES["travel"]


# ── 6.  get_vertical_list() ─────────────────────────────────────────────────

class TestGetVerticalList:
    """Functional tests for get_vertical_list()."""

    def test_get_vertical_list_returns_all(self):
        result = get_vertical_list()
        assert isinstance(result, list)
        assert len(result) == 8

    def test_get_vertical_list_entries_have_id_label_icon_description(self):
        for entry in get_vertical_list():
            for key in ("id", "label", "icon", "description"):
                assert key in entry, f"Missing key '{key}' in {entry.get('id')}"
                assert isinstance(entry[key], str)

    def test_get_vertical_list_ids_match(self):
        ids = {e["id"] for e in get_vertical_list()}
        assert ids == set(KNOWN_VERTICAL_IDS)


# ── 7.  get_entity_types_for_vertical() ─────────────────────────────────────

class TestGetEntityTypesForVertical:
    """Functional tests for get_entity_types_for_vertical()."""

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_returns_list(self, vid):
        result = get_entity_types_for_vertical(vid)
        assert isinstance(result, list)

    def test_returns_correct_count_travel(self):
        assert len(get_entity_types_for_vertical("travel")) == 5

    def test_returns_correct_count_healthcare(self):
        assert len(get_entity_types_for_vertical("healthcare")) == 4

    def test_returns_correct_count_custom(self):
        assert get_entity_types_for_vertical("custom") == []

    def test_returns_empty_for_unknown(self):
        assert get_entity_types_for_vertical("bogus") == []

    def test_type_field_matches(self):
        types = {et["type"] for et in get_entity_types_for_vertical("transport")}
        assert types == {"driver", "vehicle", "trip", "expense"}


# ── 8.  get_dashboard_config() ──────────────────────────────────────────────

class TestGetDashboardConfig:
    """Functional tests for get_dashboard_config()."""

    @pytest.mark.parametrize("vid", KNOWN_VERTICAL_IDS)
    def test_returns_metrics_and_quick_actions(self, vid):
        config = get_dashboard_config(vid)
        assert "metrics" in config
        assert "quick_actions" in config
        assert isinstance(config["metrics"], list)
        assert isinstance(config["quick_actions"], list)

    def test_unknown_vertical_returns_empty(self):
        config = get_dashboard_config("unknown")
        assert config == {"metrics": [], "quick_actions": []}

    def test_retail_has_four_metrics(self):
        config = get_dashboard_config("retail")
        assert len(config["metrics"]) == 4
        assert config["metrics"][0]["key"] == "total_orders"

    def test_travel_has_three_quick_actions(self):
        config = get_dashboard_config("travel")
        assert len(config["quick_actions"]) == 3
        labels = {a["label"] for a in config["quick_actions"]}
        assert labels == {"New Booking", "New Lead", "New Invoice"}
