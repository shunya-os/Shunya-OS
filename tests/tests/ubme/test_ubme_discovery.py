"""Pytest tests for UBME Business Discovery Engine."""

from app.ubme.models import ModuleDef
from app.ubme import engine as ubme_engine


class TestBusinessDiscovery:
    def test_dental_clinic(self):
        from app.ubme.discovery import generate_module_from_description
        result = generate_module_from_description("I run a dental clinic with 3 dentists", "SmileCare")
        mod = ModuleDef.from_dict(result)
        assert mod.key == "smilecare"
        assert len(mod.object_types) >= 5
        assert any(ot.key == "patient" for ot in mod.object_types)
        assert any(ot.key == "dentist" for ot in mod.object_types)
        assert any(ot.key == "appointment" for ot in mod.object_types)
        assert len(mod.dashboard_cards or []) >= 3

    def test_manufacturing(self):
        from app.ubme.discovery import generate_module_from_description
        result = generate_module_from_description("I manufacture furniture and home decor")
        mod = ModuleDef.from_dict(result)
        assert len(mod.object_types) >= 4
        assert len(mod.dashboard_cards or []) >= 3

    def test_law_firm(self):
        from app.ubme.discovery import generate_module_from_description
        result = generate_module_from_description("I'm starting a law firm specializing in corporate law")
        mod = ModuleDef.from_dict(result)
        assert len(mod.object_types) >= 4
        assert any(ot.key == "client" for ot in mod.object_types)

    def test_retail_store(self):
        from app.ubme.discovery import generate_module_from_description
        result = generate_module_from_description("I own a retail store selling electronics")
        mod = ModuleDef.from_dict(result)
        assert len(mod.object_types) >= 4
        assert any(ot.key == "product" for ot in mod.object_types)

    def test_restaurant(self):
        from app.ubme.discovery import generate_module_from_description
        result = generate_module_from_description("I manage a restaurant in the city center")
        mod = ModuleDef.from_dict(result)
        assert len(mod.object_types) >= 4

    def test_real_estate(self):
        from app.ubme.discovery import generate_module_from_description
        result = generate_module_from_description("I am a real estate agent helping buyers find homes")
        mod = ModuleDef.from_dict(result)
        assert len(mod.object_types) >= 4

    def test_medical_clinic(self):
        from app.ubme.discovery import generate_module_from_description
        result = generate_module_from_description("I work in a medical clinic")
        mod = ModuleDef.from_dict(result)
        assert len(mod.object_types) >= 4
        assert any(ot.key == "patient" for ot in mod.object_types)

    def test_generated_modules_are_installable(self):
        from app.ubme.discovery import generate_module_from_description
        ubme_engine.reset()
        descriptions = [
            ("dental", "I run a dental clinic"),
            ("manufacturing", "I manufacture furniture"),
            ("legal", "I'm starting a law firm"),
        ]
        for key, desc in descriptions:
            result = generate_module_from_description(desc, key.title())
            mod = ModuleDef.from_dict(result)
            mod.key = key + "_test"
            ubme_engine.register_module(mod)
            assert ubme_engine.get_module(mod.key) is not None
        assert len(ubme_engine.list_modules()) == 3

    def test_business_name_extraction(self):
        from app.ubme.discovery import _guess_business_name
        assert "Dental" in _guess_business_name("I run a dental clinic")
        # Descriptions that don't match the regex group return raw text
        name = _guess_business_name("I am starting a law firm")
        assert name == "I am starting a law firm"  # "starting" not in regex group

    def test_key_generation(self):
        from app.ubme.discovery import _guess_key
        assert _guess_key("SmileCare Dental") == "smilecare_dental"
        assert _guess_key("Artisan Furniture Co.") == "artisan_furniture_co"
        assert _guess_key("LexCorp Legal") == "lexcorp_legal"

    def test_workflow_generation(self):
        from app.ubme.discovery import _generate_workflows
        from app.ubme.models import ObjectTypeDef, FieldDef, FieldType
        ot = ObjectTypeDef(key="order", name="Order", fields=[
            FieldDef(key="status", label="Status", field_type=FieldType.TEXT),
        ], lifecycle=["draft", "approved", "shipped", "delivered"])
        wfs = _generate_workflows([ot])
        assert len(wfs) == 1
        wf = wfs[0]
        assert wf["default_state"] == "draft"
        assert len(wf["states"]) == 4
        assert len(wf["transitions"]) == 3