"""Shunya OS — Settings & Admin."""
import json, os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from app import db
from app.models import Tenant, TeamMember, EntityDefinition, Supplier
from app.routes.auth import login_required

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("")
@login_required
def settings_page():
    suppliers = Supplier.query.filter_by(tenant_id=g.tenant.id)\
        .order_by(Supplier.created_at.desc()).limit(200).all()
    definitions = EntityDefinition.query.filter_by(tenant_id=g.tenant.id).all()
    team = TeamMember.query.filter_by(tenant_id=g.tenant.id).all()
    return render_template("settings.html", suppliers=suppliers,
                           definitions=definitions, team=team)