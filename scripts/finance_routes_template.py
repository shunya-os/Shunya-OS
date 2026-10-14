return jsonify({"invoice": inv.to_dict()}), 201


@finance_bp.route("/invoices/<int:inv_id>", methods=["PUT"])
@require_permission("finance.edit_invoice")
def api_update_invoice(inv_id):
    """Edit invoice fields. Locked invoices require unlock first.
    Creates a version snapshot when a non-draft invoice is edited.
    """
    auth = _require_auth()
    if auth:
        return auth
    org_id = _org()
    if not org_id:
        return jsonify({"error": "No org"}), 400
    inv = db.session.get(Invoice, inv_id)
    if not inv or inv.organization_id != org_id:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json(silent=True) or {}
    identity = _identity()
    if inv.locked_by and inv.locked_by != identity:
        return jsonify({"error": "Invoice is locked by " + str(inv.locked_by) + ". Unlock first."}), 403
    if inv.status != "draft":
        old = Invoice(
            organization_id=inv.organization_id, relationship_id=inv.relationship_id,
            proposal_id=inv.proposal_id,
            number=inv.number + "-v" + str(inv.version_number or 1),
            type=inv.type, status="historical",
            issue_date=inv.issue_date, due_date=inv.due_date,
            currency=inv.currency, subtotal=inv.subtotal,
            tax_amount=inv.tax_amount, discount_amount=inv.discount_amount,
            total_amount=inv.total_amount, paid_amount=inv.paid_amount,
            notes=inv.notes, terms=inv.terms, created_by=inv.created_by,
            locked_by=inv.locked_by, locked_at=inv.locked_at,
            version_number=inv.version_number,
            parent_invoice_id=inv.parent_invoice_id or inv_id,
        )
        db.session.add(old)
        inv.version_number = (inv.version_number or 1) + 1
    if "due_date" in data:
        try:
            inv.due_date = date.fromisoformat(data["due_date"])
        except (ValueError, TypeError):
            pass
    if "currency" in data:
        inv.currency = data["currency"]
    if "notes" in data:
        inv.notes = data["notes"]
    if "terms" in data:
        inv.terms = data["terms"]
    if "total_amount" in data:
        inv.total_amount = Decimal(str(data["total_amount"]))
    if "subtotal" in data:
        inv.subtotal = Decimal(str(data["subtotal"]))
    if "tax_amount" in data:
        inv.tax_amount = Decimal(str(data["tax_amount"]))
    if "discount_amount" in data:
        inv.discount_amount = Decimal(str(data["discount_amount"]))
    inv.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"invoice": inv.to_dict(), "version": inv.version_number})


@finance_bp.route("/invoices/<int:inv_id>/lock", methods=["POST"])
@require_permission("finance.edit_invoice")
def api_lock_invoice(inv_id):
    """Lock an invoice. Only the locking user can unlock."""
    auth = _require_auth()
    if auth:
        return auth
    org_id = _org()
    if not org_id:
        return jsonify({"error": "No org"}), 400
    inv = db.session.get(Invoice, inv_id)
    if not inv or inv.organization_id != org_id:
        return jsonify({"error": "Not found"}), 404
    identity = _identity()
    inv.locked_by = identity
    inv.locked_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"invoice": inv.to_dict()})


@finance_bp.route("/invoices/<int:inv_id>/unlock", methods=["POST"])
@require_permission("finance.edit_invoice")
def api_unlock_invoice(inv_id):
    """Unlock an invoice. Restricted to the locker."""
    auth = _require_auth()
    if auth:
        return auth
    org_id = _org()
    if not org_id:
        return jsonify({"error": "No org"}), 400
    inv = db.session.get(Invoice, inv_id)
    if not inv or inv.organization_id != org_id:
        return jsonify({"error": "Not found"}), 404
    identity = _identity()
    if inv.locked_by and inv.locked_by != identity:
        return jsonify({"error": "Only " + str(inv.locked_by) + " can unlock"}), 403
    inv.locked_by = None
    inv.locked_at = None
    db.session.commit()
    return jsonify({"invoice": inv.to_dict()})


@finance_bp.route("/invoices/<int:inv_id>/versions", methods=["GET"])
@require_permission("finance.view")
def api_invoice_versions(inv_id):
    """Get all historical versions of an invoice."""
    auth = _require_auth()
    if auth:
        return auth
    org_id = _org()
    if not org_id:
        return jsonify({"error": "No org"}), 400
    inv = db.session.get(Invoice, inv_id)
    if not inv or inv.organization_id != org_id:
        return jsonify({"error": "Not found"}), 404
    root_id = inv.parent_invoice_id if inv.parent_invoice_id else inv_id
    versions = Invoice.query.filter(
        Invoice.organization_id == org_id,
        (Invoice.id == root_id) | (Invoice.parent_invoice_id == root_id),
    ).order_by(Invoice.version_number.asc()).all()
    return jsonify({"versions": [v.to_dict() for v in versions], "current_id": inv_id, "root_id": root_id})


@finance_bp.route("/invoices", methods=["GET"])