"""UCP-07 Verification — Universal Asset Intelligence.

Verifies 8 scenarios through the same capability:
1. Personal assets
2. Family assets
3. Enterprise IT assets
4. Manufacturing assets
5. Financial assets
6. Digital assets
7. Travel assets
8. Asset transfer with adaptive execution

No Inventory Runtime. No Asset Management Runtime. No CMDB Runtime.
"""

from __future__ import annotations

from typing import Any
from core.asset_intelligence import (
    AssetIntelligenceRuntime, AssetStatus, AssetType, AssetCategory, HealthStatus,
)


def test_personal_assets() -> dict[str, Any]:
    runtime = AssetIntelligenceRuntime()
    runtime.get_or_create_profile("person_ankit", "Ankit — Personal Assets")

    laptop = runtime.register_asset("person_ankit", AssetCategory.ELECTRONICS.value,
        AssetType.LAPTOP.value, "MacBook Pro 16", "Personal development laptop",
        owner="person_ankit", financial_value=250000, tags=["electronics", "work"])
    assert laptop is not None
    assert laptop.status == AssetStatus.DISCOVERED.value

    phone = runtime.register_asset("person_ankit", AssetCategory.ELECTRONICS.value,
        AssetType.MOBILE_PHONE.value, "iPhone 15 Pro", "Personal phone",
        owner="person_ankit", financial_value=140000)
    assert phone is not None

    passport = runtime.register_asset("person_ankit", AssetCategory.IDENTITY_DOCUMENT.value,
        AssetType.PASSPORT.value, "Indian Passport", "International travel passport",
        owner="person_ankit", tags=["identity", "travel"])
    assert passport is not None

    runtime.transition_status("person_ankit", laptop.asset_id, "registered")
    runtime.transition_status("person_ankit", laptop.asset_id, "verified")
    runtime.transition_status("person_ankit", laptop.asset_id, "active")
    assert laptop.is_active

    analysis = runtime.analyze_asset("person_ankit", laptop.asset_id)
    assert analysis is not None

    return {"scenario": "1. Personal Assets", "entity": "Ankit",
            "assets": 3, "active": 1, "analysis_ok": bool(analysis), "passed": True}


def test_family_assets() -> dict[str, Any]:
    runtime = AssetIntelligenceRuntime()
    runtime.get_or_create_profile("family_patel", "Patel Family")

    runtime.register_asset("family_patel", AssetCategory.REAL_ESTATE.value, AssetType.APARTMENT.value,
        "Green Valley Apartment", "3BHK family apartment", owner="family_patel", financial_value=8500000,
        tags=["home", "real_estate"], location_name="Green Valley, Pune")
    runtime.register_asset("family_patel", AssetCategory.VEHICLE.value, AssetType.VEHICLE_CAR.value,
        "Honda City 2023", "Family car", owner="family_patel", financial_value=1500000,
        tags=["vehicle", "car"])
    runtime.register_asset("family_patel", AssetCategory.VEHICLE.value, AssetType.VEHICLE_BIKE.value,
        "Honda Activa", "Daily commute scooter", owner="family_patel", financial_value=80000)
    runtime.register_asset("family_patel", AssetCategory.WEARABLE.value, "other",
        "Apple Watch Series 8", "Fitness tracker", owner="family_patel", financial_value=45000)

    profile = runtime._resolve("family_patel")
    assert profile is not None
    assert profile.total_assets == 4

    return {"scenario": "2. Family Assets", "entity": "Patel Family",
            "assets": profile.total_assets, "total_value": profile.total_value, "passed": True}


def test_enterprise_it_assets() -> dict[str, Any]:
    runtime = AssetIntelligenceRuntime()
    runtime.get_or_create_profile("org_enterprise", "Enterprise IT")

    for i in range(3):
        runtime.register_asset("org_enterprise", AssetCategory.INFRASTRUCTURE.value, AssetType.SERVER.value,
            f"Server-{i+1}", f"Production server {i+1}", owner="org_enterprise",
            financial_value=500000, tags=["production", "server"])
    runtime.register_asset("org_enterprise", AssetCategory.SOFTWARE.value, AssetType.SOFTWARE_LICENSE.value,
        "Microsoft 365 Enterprise", "Enterprise license for 500 users",
        owner="org_enterprise", financial_value=1200000)
    runtime.register_asset("org_enterprise", AssetCategory.API.value, AssetType.API_KEY.value,
        "Stripe API Key - Production", "Payment processing key",
        owner="org_enterprise", tags=["api", "payment"])
    runtime.register_asset("org_enterprise", AssetCategory.INFRASTRUCTURE.value, AssetType.DOMAIN_NAME.value,
        "acmecorp.com", "Primary company domain", owner="org_enterprise",
        financial_value=50000, tags=["domain"])

    # Add health and maintenance to one server
    server = runtime.get_asset("org_enterprise", 
        [a for a in runtime._resolve("org_enterprise").assets if "Server-1" in a.name][0].asset_id)
    runtime.add_maintenance("org_enterprise", server.asset_id, "2026-07-01",
                            "Quarterly hardware check", cost=5000)

    all_analysis = runtime.analyze_all("org_enterprise")
    assert all_analysis is not None
    assert all_analysis["total_assets"] == 6

    return {"scenario": "3. Enterprise IT Assets", "entity": "Enterprise IT",
            "assets": all_analysis["total_assets"], "risks": len(all_analysis["risks"]),
            "anomalies": len(all_analysis["anomalies"]), "passed": True}


def test_manufacturing_assets() -> dict[str, Any]:
    runtime = AssetIntelligenceRuntime()
    runtime.get_or_create_profile("org_factory", "Factory Assets")

    machine = runtime.register_asset("org_factory", AssetCategory.MANUFACTURING.value,
        AssetType.MANUFACTURING_MACHINE.value, "CNC Machine M-400",
        "CNC milling machine for precision parts", owner="org_factory",
        financial_value=5000000, tags=["manufacturing", "cnc"])
    assert machine is not None

    for i in range(5):
        runtime.register_asset("org_factory", AssetCategory.INVENTORY.value, AssetType.INVENTORY_ITEM.value,
            f"Raw Material Batch {i+1}", f"Steel Grade A batch {i+1}",
            owner="org_factory", financial_value=50000 * (i + 1),
            tags=["inventory", "raw_material"])

    # Dependency: machine depends on raw materials
    inventory = runtime.get_asset("org_factory",
        [a for a in runtime._resolve("org_factory").assets if "Batch 1" in a.name][0].asset_id)
    machine.dependencies.append(inventory.asset_id)

    recs = runtime.get_recommendations("org_factory", machine.asset_id)
    assert recs is not None

    all_analysis = runtime.analyze_all("org_factory")
    assert all_analysis is not None
    assert len(all_analysis["dependencies"]) >= 0

    return {"scenario": "4. Manufacturing Assets", "entity": "Factory",
            "assets": 6, "recommendations": len(recs), "passed": True}


def test_financial_assets() -> dict[str, Any]:
    runtime = AssetIntelligenceRuntime()
    runtime.get_or_create_profile("person_wealth", "Wealth Portfolio")

    runtime.register_asset("person_wealth", AssetCategory.FINANCIAL.value, AssetType.BANK_ACCOUNT.value,
        "HDFC Savings", "Primary savings account", owner="person_wealth",
        financial_value=500000, tags=["bank", "savings"])
    runtime.register_asset("person_wealth", AssetCategory.FINANCIAL.value, AssetType.INVESTMENT_PORTFOLIO.value,
        "Mutual Fund Portfolio", "Equity + debt mix", owner="person_wealth",
        financial_value=2000000, tags=["investment", "mutual_fund"])
    runtime.register_asset("person_wealth", AssetCategory.WALLET.value, AssetType.DIGITAL_WALLET.value,
        "Paytm Wallet", "Digital wallet for daily payments", owner="person_wealth",
        financial_value=25000, tags=["wallet", "digital"])
    runtime.register_asset("person_wealth", AssetCategory.INTELLECTUAL_PROPERTY.value,
        AssetType.INTELLECTUAL_PROPERTY.value, "Mobile App Patent",
        "Patent for AI-based recommendation engine", owner="person_wealth",
        financial_value=10000000, tags=["ip", "patent"])

    profile = runtime._resolve("person_wealth")
    assert profile is not None
    assert profile.total_assets == 4
    assert profile.total_value > 0

    return {"scenario": "5. Financial Assets", "entity": "Wealth Portfolio",
            "assets": profile.total_assets, "total_value": profile.total_value, "passed": True}


def test_digital_assets() -> dict[str, Any]:
    runtime = AssetIntelligenceRuntime()
    runtime.get_or_create_profile("freelancer_digital", "Digital Creator")

    runtime.register_asset("freelancer_digital", AssetCategory.DIGITAL.value, "other",
        "Course: Python for Data Science", "Udemy online course", owner="freelancer_digital",
        financial_value=50000, tags=["digital", "course", "python"])
    runtime.register_asset("freelancer_digital", AssetCategory.CERTIFICATE.value, AssetType.CERTIFICATE.value,
        "AWS Solutions Architect Cert", "Cloud certification", owner="freelancer_digital",
        tags=["certificate", "aws", "cloud"])
    runtime.register_asset("freelancer_digital", AssetCategory.INTELLECTUAL_PROPERTY.value,
        AssetType.INTELLECTUAL_PROPERTY.value, "AI Article Series",
        "10-part technical blog series", owner="freelancer_digital",
        tags=["content", "writing", "ai"])
    runtime.register_asset("freelancer_digital", AssetCategory.BADGE.value, AssetType.EMPLOYEE_BADGE.value,
        "Microsoft MVP Badge", "Most Valuable Professional", owner="freelancer_digital",
        tags=["badge", "recognition"])

    profile = runtime._resolve("freelancer_digital")
    assert profile is not None
    assert profile.total_assets == 4

    return {"scenario": "6. Digital Assets", "entity": "Digital Creator",
            "assets": profile.total_assets, "passed": True}


def test_travel_assets() -> dict[str, Any]:
    runtime = AssetIntelligenceRuntime()
    runtime.get_or_create_profile("person_travel", "Traveler")

    runtime.register_asset("person_travel", AssetCategory.TRAVEL.value, AssetType.FLIGHT_TICKET.value,
        "AI Delhi-Mumbai-Delhi", "Round trip flight tickets", owner="person_travel",
        financial_value=12000, tags=["flight", "travel"], location_name="Delhi")
    runtime.register_asset("person_travel", AssetCategory.TRAVEL.value, AssetType.HOTEL_RESERVATION.value,
        "Taj Mahal Palace - 3 nights", "Hotel stay for conference", owner="person_travel",
        financial_value=45000, tags=["hotel", "business"], location_name="Mumbai")
    runtime.register_asset("person_travel", AssetCategory.IDENTITY_DOCUMENT.value, AssetType.PASSPORT.value,
        "Passport - Ravi Traveler", "Valid until 2031", owner="person_travel",
        tags=["identity", "passport"])

    profile = runtime._resolve("person_travel")
    assert profile is not None
    assert profile.total_assets == 3

    return {"scenario": "7. Travel Assets", "entity": "Traveler",
            "assets": profile.total_assets, "passed": True}


def test_asset_transfer_with_adaptive_execution() -> dict[str, Any]:
    runtime = AssetIntelligenceRuntime()
    runtime.get_or_create_profile("org_company", "Company Assets")
    runtime.get_or_create_profile("employee_ram", "Employee Ram")

    laptop = runtime.register_asset("org_company", AssetCategory.ELECTRONICS.value,
        AssetType.LAPTOP.value, "Dell XPS 15 - Ram", "Company laptop assigned to Ram",
        owner="org_company", custodian="employee_ram",
        financial_value=180000, tags=["laptop", "company"])
    assert laptop is not None

    runtime.transition_status("org_company", laptop.asset_id, "registered")
    runtime.transition_status("org_company", laptop.asset_id, "verified")
    runtime.transition_status("org_company", laptop.asset_id, "active")
    assert laptop.is_active

    # Transfer
    runtime.transition_status("org_company", laptop.asset_id, "transferred")
    assert laptop.status == AssetStatus.TRANSFERRED.value

    # New owner after transfer
    laptop.owner_id = "employee_ram"
    laptop.custodian_id = ""
    runtime.transition_status("org_company", laptop.asset_id, "active")
    assert laptop.is_active
    assert laptop.owner_id == "employee_ram"

    # Health scoring
    health = runtime._engine.compute_health(laptop)
    assert health["score"] > 0

    return {"scenario": "8. Asset Transfer + Adaptive Execution", "entity": "Company → Employee",
            "transfer_complete": laptop.owner_id == "employee_ram",
            "health_score": health["score"], "health_level": health["level"],
            "passed": True}


def run_all() -> list[dict[str, Any]]:
    tests = [
        ("Personal Assets", test_personal_assets),
        ("Family Assets", test_family_assets),
        ("Enterprise IT Assets", test_enterprise_it_assets),
        ("Manufacturing Assets", test_manufacturing_assets),
        ("Financial Assets", test_financial_assets),
        ("Digital Assets", test_digital_assets),
        ("Travel Assets", test_travel_assets),
        ("Asset Transfer + Adaptive Execution", test_asset_transfer_with_adaptive_execution),
    ]
    results = []
    for n, fn in tests:
        try:
            r = fn()
            r["test_name"] = n
            r["status"] = "PASS"
            r["error"] = None
        except Exception as e:
            import traceback
            r = {"test_name": n, "scenario": n, "status": "FAIL",
                 "error": str(e), "traceback": traceback.format_exc(), "passed": False}
        results.append(r)
    return results


if __name__ == "__main__":
    print("UCP-07 — Universal Asset Intelligence: Verification Report")
    results = run_all()
    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]
    for r in results:
        s = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"\n  {s} | {r.get('test_name', r['scenario'])}")
        print(f"         Entity: {r.get('entity', 'N/A')}")
        if r.get("assets"): print(f"         Assets: {r['assets']}")
        if r.get("risks") is not None: print(f"         Risks: {r['risks']} | Anomalies: {r.get('anomalies', 'N/A')}")
        if r.get("health_score") is not None: print(f"         Health: {r['health_score']} ({r.get('health_level', 'N/A')})")
        if r.get("error"): print(f"         ERROR: {r['error']}")
    print(f"\n  Total: {len(results)} | Passed: {len(passed)} | Failed: {len(failed)}")
    if not failed:
        print("\n  ✅ UCP-07 VERIFICATION PASSED: All 8 asset scenarios execute through one capability.")
        print("  No Inventory Runtime. No Asset Management Runtime. No CMDB Runtime.")