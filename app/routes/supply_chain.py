"""Shunya Supply Chain Routes — Dashboard, Summary, Seed Data."""
from flask import Blueprint, render_template, jsonify, g
from app import db
from app.models import Entity, EntityDefinition
from app.routes.auth import login_required
from app.shunya.supply_chain import SC_ENTITY_TYPES, SCDashboard, _ensure_sc_types

supply_chain_bp = Blueprint("supply_chain", __name__, url_prefix="/supply-chain")


@supply_chain_bp.route("")
@login_required
def sc_dashboard():
    """Supply chain overview — inventory, POs, suppliers."""
    _ensure_sc_types(g.tenant.id)
    _seed_sample_data(g.tenant.id)

    overview = SCDashboard.get_overview(g.tenant.id)

    return render_template("supply_chain/dashboard.html",
        products=overview["products"],
        pos=overview["pos"],
        suppliers=overview["suppliers"],
        warehouses=overview["warehouses"],
        total_stock=overview["total_stock"],
        low_stock_items=overview["low_stock_items"],
        pending_pos=overview["pending_pos"],
        total_po_value=overview["total_po_value"],
        po_statuses=overview["po_statuses"],
        prod_def=overview["prod_def"],
        po_def=overview["po_def"],
        supp_def=overview["supp_def"],
        wh_def=overview["wh_def"],
    )


@supply_chain_bp.route("/api/summary")
@login_required
def sc_summary():
    """JSON summary for dashboard widgets."""
    prod_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="product"
    ).first()
    po_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="purchase_order"
    ).first()

    products = db.session.query(Entity).filter_by(
        tenant_id=g.tenant.id, definition_id=prod_def.id
    ).all() if prod_def else []

    pos = db.session.query(Entity).filter_by(
        tenant_id=g.tenant.id, definition_id=po_def.id
    ).all() if po_def else []

    low_stock = [
        p for p in products
        if float(p.data.get("current_stock", 0)) <= float(p.data.get("min_stock", 0))
    ]
    pending_po_value = sum(
        float(po.data.get("total_amount", 0))
        for po in pos if po.status in ("sent", "confirmed")
    )

    return jsonify({
        "total_products": len(products),
        "total_stock": sum(float(p.data.get("current_stock", 0)) for p in products),
        "low_stock_count": len(low_stock),
        "pending_po_count": len([po for po in pos if po.status in ("sent", "confirmed")]),
        "pending_po_value": pending_po_value,
        "total_po_count": len(pos),
    })


def _seed_sample_data(tenant_id: int):
    """Create sample supply chain entities if none exist for this tenant."""
    prod_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type="product"
    ).first()
    po_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type="purchase_order"
    ).first()
    supp_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type="supplier"
    ).first()
    wh_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type="warehouse"
    ).first()

    if not prod_def or not po_def or not supp_def or not wh_def:
        return

    existing_count = db.session.query(db.func.count(Entity.id)).filter_by(
        tenant_id=tenant_id, definition_id=prod_def.id
    ).scalar() or 0

    if existing_count > 0:
        return  # Already seeded

    now = __import__("datetime").datetime.utcnow()

    # -- Suppliers --
    supplier_data = [
        ("TechVentures Ltd.", "Rahul Mehta", "rahul@techventures.in", "+91-9876543210", "technology", "Net 30", 4),
        ("Global Supplies Co.", "Anita Desai", "anita@globalsupplies.com", "+91-9876543211", "raw_material", "Net 45", 5),
        ("PackRight Solutions", "Vikram Singh", "vikram@packright.in", "+91-9876543212", "packaging", "Net 30", 4),
        ("LogiTrans Logistics", "Priya Sharma", "priya@logitrans.com", "+91-9876543213", "logistics", "Net 60", 3),
        ("Quality Parts Inc.", "Suresh Patel", "suresh@qualityparts.com", "+91-9876543214", "raw_material", "Net 30", 5),
        ("Office Essentials Co.", "Neha Kapoor", "neha@officeessentials.in", "+91-9876543215", "services", "Net 15", 3),
    ]
    suppliers = []
    for i, data in enumerate(supplier_data):
        suppliers.append(Entity(
            tenant_id=tenant_id, definition_id=supp_def.id,
            code=f"SUP-{i:04d}",
            status="active",
            data={
                "company_name": data[0],
                "contact_person": data[1],
                "email": data[2],
                "phone": data[3],
                "category": data[4],
                "payment_terms": data[5],
                "rating": data[6],
                "address": f"#{i+1}, Business District, Mumbai",
            },
        ))

    # -- Warehouses --
    warehouse_data = [
        ("Main Warehouse", "Mumbai Industrial Area", 50000, 32000, "Rajesh Kumar"),
        ("East Distribution Centre", "Kolkata Freight Hub", 35000, 18000, "Sneha Roy"),
        ("Southern Storage", "Chennai Logistics Park", 40000, 28000, "Arun Prasad"),
        ("North Fulfillment", "Noida Sector 62", 30000, 15000, "Meera Joshi"),
        ("Cold Storage Unit", "Pune MIDC", 15000, 12000, "Deepak Chavan"),
    ]
    warehouses = []
    for i, data in enumerate(warehouse_data):
        warehouses.append(Entity(
            tenant_id=tenant_id, definition_id=wh_def.id,
            code=f"WH-{i:04d}",
            status="active",
            data={
                "name": data[0],
                "location": data[1],
                "capacity": data[2],
                "utilized": data[3],
                "manager": data[4],
                "notes": "",
            },
        ))

    # -- Products --
    product_data = [
        ("SKU-001", "Industrial Bolt M12", "finished_good", 12.50, "pcs", 500, 1200, "Main Warehouse", "SUP-0000"),
        ("SKU-002", "Steel Rod 6mm", "raw_material", 85.00, "kg", 1000, 5000, "Main Warehouse", "SUP-0001"),
        ("SKU-003", "Corrugated Box Lg", "consumable", 28.00, "box", 200, 50, "East Distribution Centre", "SUP-0002"),
        ("SKU-004", "Packing Tape Roll", "consumable", 45.00, "pcs", 300, 150, "East Distribution Centre", "SUP-0002"),
        ("SKU-005", "Server Rack 42U", "finished_good", 45000.00, "pcs", 10, 25, "Southern Storage", "SUP-0000"),
        ("SKU-006", "Network Cable Cat6", "finished_good", 350.00, "mtr", 200, 800, "Southern Storage", "SUP-0000"),
        ("SKU-007", "Aluminium Sheet 2mm", "raw_material", 220.00, "kg", 500, 3000, "North Fulfillment", "SUP-0004"),
        ("SKU-008", "Coolant Fluid 5L", "consumable", 180.00, "ltr", 50, 200, "Cold Storage Unit", "SUP-0001"),
        ("SKU-009", "Spare Gasket Set", "spare_part", 95.00, "pack", 30, 100, "Main Warehouse", "SUP-0004"),
        ("SKU-010", "LED Panel Light", "finished_good", 650.00, "pcs", 80, 180, "North Fulfillment", "SUP-0005"),
    ]
    products = []
    for i, data in enumerate(product_data):
        status = "active"
        if data[6] <= data[5]:  # current_stock <= min_stock
            status = "low_stock"
        if data[6] == 0:
            status = "out_of_stock"
        products.append(Entity(
            tenant_id=tenant_id, definition_id=prod_def.id,
            code=f"PRD-{i:04d}",
            status=status,
            data={
                "sku": data[0],
                "name": data[1],
                "category": data[2],
                "unit_price": data[3],
                "unit": data[4],
                "min_stock": data[5],
                "current_stock": data[6],
                "warehouse": data[7],
                "supplier_id": data[8],
            },
        ))

    # -- Purchase Orders --
    po_data = [
        ("PO-2026-001", "TechVentures Ltd.", [{"item": "Bolt M12", "qty": 500}], 6250.00, "2026-06-01", "2026-06-15", "Net 30", "Routine restock"),
        ("PO-2026-002", "Global Supplies Co.", [{"item": "Steel Rod 6mm", "qty": 2000}], 170000.00, "2026-06-05", "2026-06-20", "Net 45", "Monthly raw material order"),
        ("PO-2026-003", "Quality Parts Inc.", [{"item": "Aluminium Sheet", "qty": 500}], 110000.00, "2026-06-10", "2026-07-10", "Net 30", "Production batch #42"),
        ("PO-2026-004", "Office Essentials Co.", [{"item": "LED Panel Light", "qty": 50}], 32500.00, "2026-06-12", "2026-06-22", "Net 15", "Office renovation"),
        ("PO-2026-005", "PackRight Solutions", [{"item": "Box Lg", "qty": 1000}], 28000.00, "2026-06-15", "2026-06-25", "Net 30", "Packaging for new product line"),
    ]
    pos = []
    for i, data in enumerate(po_data):
        status = ["sent", "confirmed", "draft", "received", "partially_received"][i % 5]
        pos.append(Entity(
            tenant_id=tenant_id, definition_id=po_def.id,
            code=data[0],
            status=status,
            data={
                "po_number": data[0],
                "supplier_name": data[1],
                "items": data[2],
                "total_amount": data[3],
                "order_date": data[4],
                "expected_date": data[5],
                "payment_terms": data[6],
                "notes": data[7],
            },
        ))

    all_entities = suppliers + warehouses + products + pos
    for entity in all_entities:
        db.session.add(entity)
    db.session.commit()