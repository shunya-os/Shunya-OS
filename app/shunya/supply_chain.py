"""Shunya Supply Chain Module — Inventory, Procurement, Suppliers.

Every business manages stock, purchases from vendors, and tracks inventory.
This module provides:
- Multi-warehouse inventory management
- Purchase orders and procurement
- Supplier management and rating
- Stock tracking with alerts
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from app import db
from app.models import Entity, EntityDefinition, ActivityLog

SC_ENTITY_TYPES = {
    "product": {
        "label": "Product",
        "icon": "📦",
        "schema": [
            {"name": "sku", "label": "SKU", "type": "text", "required": True},
            {"name": "name", "label": "Product Name", "type": "text", "required": True},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "category", "label": "Category", "type": "select", "options": ["raw_material", "finished_good", "consumable", "service", "spare_part"]},
            {"name": "unit_price", "label": "Unit Price", "type": "number"},
            {"name": "unit", "label": "Unit", "type": "select", "options": ["pcs", "kg", "ltr", "mtr", "box", "pack"]},
            {"name": "min_stock", "label": "Min Stock Level", "type": "number"},
            {"name": "current_stock", "label": "Current Stock", "type": "number"},
            {"name": "warehouse", "label": "Warehouse", "type": "text"},
            {"name": "supplier_id", "label": "Supplier ID", "type": "text"},
        ],
        "statuses": ["active", "low_stock", "out_of_stock", "discontinued"],
        "layout": "table",
        "searchable_fields": ["sku", "name", "category", "warehouse"],
    },
    "purchase_order": {
        "label": "Purchase Order",
        "icon": "📝",
        "schema": [
            {"name": "po_number", "label": "PO Number", "type": "text", "required": True},
            {"name": "supplier_name", "label": "Supplier", "type": "text", "required": True},
            {"name": "items", "label": "Items", "type": "json"},
            {"name": "total_amount", "label": "Total", "type": "number"},
            {"name": "order_date", "label": "Order Date", "type": "date"},
            {"name": "expected_date", "label": "Expected Delivery", "type": "date"},
            {"name": "payment_terms", "label": "Payment Terms", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["draft", "sent", "confirmed", "partially_received", "received", "cancelled"],
        "layout": "table",
        "searchable_fields": ["po_number", "supplier_name"],
    },
    "supplier": {
        "label": "Supplier",
        "icon": "🏢",
        "schema": [
            {"name": "company_name", "label": "Company", "type": "text", "required": True},
            {"name": "contact_person", "label": "Contact Person", "type": "text"},
            {"name": "email", "label": "Email", "type": "text"},
            {"name": "phone", "label": "Phone", "type": "text"},
            {"name": "category", "label": "Category", "type": "select", "options": ["raw_material", "packaging", "logistics", "services", "technology"]},
            {"name": "payment_terms", "label": "Payment Terms", "type": "text"},
            {"name": "rating", "label": "Rating", "type": "number"},
            {"name": "address", "label": "Address", "type": "textarea"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["active", "inactive", "blacklisted"],
        "layout": "table",
        "searchable_fields": ["company_name", "contact_person", "email", "category"],
    },
    "warehouse": {
        "label": "Warehouse",
        "icon": "🏗️",
        "schema": [
            {"name": "name", "label": "Warehouse Name", "type": "text", "required": True},
            {"name": "location", "label": "Location", "type": "text"},
            {"name": "capacity", "label": "Capacity", "type": "number"},
            {"name": "utilized", "label": "Utilized", "type": "number"},
            {"name": "manager", "label": "Manager", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["active", "full", "maintenance", "inactive"],
        "layout": "table",
        "searchable_fields": ["name", "location", "manager"],
    },
}


# ---------------------------------------------------------------------------
# Supply Chain Dashboard — Data Aggregation
# ---------------------------------------------------------------------------

class SCDashboard:
    """Aggregates supply chain data for the dashboard views."""

    @staticmethod
    def _get_def(tenant_id: int, entity_type: str):
        """Get entity definition for a type, or None."""
        return db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type=entity_type
        ).first()

    @staticmethod
    def get_overview(tenant_id: int) -> Dict[str, Any]:
        """Get all supply chain metrics for the overview dashboard."""
        prod_def = SCDashboard._get_def(tenant_id, "product")
        po_def = SCDashboard._get_def(tenant_id, "purchase_order")
        supp_def = SCDashboard._get_def(tenant_id, "supplier")
        wh_def = SCDashboard._get_def(tenant_id, "warehouse")

        products = []
        if prod_def:
            products = db.session.query(Entity).filter_by(
                tenant_id=tenant_id, definition_id=prod_def.id, is_archived=False
            ).all()

        pos = []
        if po_def:
            pos = db.session.query(Entity).filter_by(
                tenant_id=tenant_id, definition_id=po_def.id, is_archived=False
            ).all()

        suppliers = []
        if supp_def:
            suppliers = db.session.query(Entity).filter_by(
                tenant_id=tenant_id, definition_id=supp_def.id, is_archived=False
            ).all()

        warehouses = []
        if wh_def:
            warehouses = db.session.query(Entity).filter_by(
                tenant_id=tenant_id, definition_id=wh_def.id, is_archived=False
            ).all()

        total_stock = sum(float(p.data.get("current_stock", 0)) for p in products)
        low_stock_items = [
            p for p in products
            if float(p.data.get("current_stock", 0)) <= float(p.data.get("min_stock", 0))
        ]
        pending_pos = [
            po for po in pos if po.status in ("sent", "confirmed", "partially_received")
        ]
        total_po_value = sum(float(po.data.get("total_amount", 0)) for po in pending_pos)

        po_statuses = {}
        for po in pos:
            po_statuses[po.status] = po_statuses.get(po.status, 0) + 1

        return {
            "product_count": len(products),
            "total_stock": total_stock,
            "low_stock_count": len(low_stock_items),
            "pending_po_count": len(pending_pos),
            "total_po_value": total_po_value,
            "supplier_count": len(suppliers),
            "warehouse_count": len(warehouses),
            "po_statuses": po_statuses,
            # Full entity lists for the template
            "products": products,
            "pos": pos,
            "suppliers": suppliers,
            "warehouses": warehouses,
            "low_stock_items": low_stock_items,
            "pending_pos": pending_pos,
            "prod_def": prod_def,
            "po_def": po_def,
            "supp_def": supp_def,
            "wh_def": wh_def,
        }

    @staticmethod
    def get_recent(tenant_id: int, entity_type: str, limit: int = 10) -> List[Any]:
        """Get recent entities of a given supply chain type."""
        type_def = SCDashboard._get_def(tenant_id, entity_type)
        if not type_def:
            return []
        return db.session.query(Entity).filter_by(
            tenant_id=tenant_id, definition_id=type_def.id, is_archived=False
        ).order_by(Entity.created_at.desc()).limit(limit).all()


def _ensure_sc_types(tenant_id: int):
    """Ensure supply chain entity types exist for this tenant."""
    for etype, config in SC_ENTITY_TYPES.items():
        existing = db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type=etype
        ).first()
        if existing:
            continue
        definition = EntityDefinition(
            tenant_id=tenant_id,
            type=etype,
            label=config["label"],
            label_plural=f"{config['label']}s",
            icon=config["icon"],
            schema=config["schema"],
            statuses=config["statuses"],
            layout=config["layout"],
            searchable_fields=config["searchable_fields"],
            primary_field=config["schema"][0]["name"] if config["schema"] else "name",
        )
        db.session.add(definition)
    db.session.commit()