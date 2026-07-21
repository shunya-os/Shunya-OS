"""
Shunya — Tenant/Company Model & Branding Engine (Phase 3G + Universal)

Multi-company white-label foundation. Every company gets:
- Isolated data namespace
- Custom logo, theme, brand name, welcome message
- Own AI Companion personality
- Business-type specific ontology (travel, healthcare, school, retail, etc.)
"""

import json
import os
import uuid
import secrets
from datetime import datetime
from enum import Enum
from typing import Optional

from app import db
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey


class TenantTheme(db.Model):
    """Per-company theme configuration."""
    __tablename__ = "tenant_themes"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True)
    primary_color = Column(String(30), default="#2563eb")    # blue-600
    accent_color = Column(String(30), default="#7c3aed")     # violet-600
    bg_color = Column(String(30), default="#f8fafc")         # slate-50
    sidebar_bg = Column(String(30), default="#0f172a")       # slate-900
    font_family = Column(String(60), default="Inter")
    logo_path = Column(String(500), default="")
    logo_style = Column(String(30), default="contain")       # contain, cover, circle
    welcome_message = Column(Text, default="Time to make today count.")
    company_motto = Column(String(255), default="")
    custom_css = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "primary_color": self.primary_color,
            "accent_color": self.accent_color,
            "bg_color": self.bg_color,
            "sidebar_bg": self.sidebar_bg,
            "font_family": self.font_family,
            "logo_path": f"/media/tenant/{self.logo_path}" if self.logo_path else None,
            "logo_style": self.logo_style,
            "welcome_message": self.welcome_message,
            "company_motto": self.company_motto,
            "custom_css": self.custom_css,
        }


class Tenant(db.Model):
    """A company using Shunya OS. Isolated data namespace."""
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    company_name = Column(String(255), nullable=False)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    business_type = Column(String(60), default="other")  # travel, hospital, school, retail, other, multi_brand
    parent_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)  # For multi-brand
    subdomain = Column(String(120), unique=True)
    domain = Column(String(255))
    is_active = Column(Boolean, default=True)
    plan = Column(String(30), default="free")
    max_team_members = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)
    theme = db.relationship("TenantTheme", uselist=False, backref="tenant", cascade="all,delete")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "company_name": self.company_name,
            "slug": self.slug,
            "business_type": self.business_type,
            "parent_id": self.parent_id,
            "subdomain": self.subdomain,
            "domain": self.domain,
            "is_active": self.is_active,
            "plan": self.plan,
            "max_team_members": self.max_team_members,
            "theme": self.theme.to_dict() if self.theme else {},
        }


class BrandingEngine:
    """Handles company branding — logo, theme, prompts."""

    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media", "tenant")

    def __init__(self, tenant: Optional[Tenant] = None):
        self.tenant = tenant
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)

    def apply_theme_from_prompt(self, prompt: str) -> dict:
        """Parse a natural language prompt and generate theme."""
        prompt_lower = prompt.lower()
        
        theme = {
            "primary_color": "#2563eb",
            "accent_color": "#7c3aed",
            "bg_color": "#f8fafc",
            "sidebar_bg": "#0f172a",
        }

        # Detect color requests
        color_map = {
            "purple": ("#7c3aed", "#a78bfa"),
            "gold": ("#f59e0b", "#fbbf24"),
            "green": ("#059669", "#34d399"),
            "red": ("#dc2626", "#f87171"),
            "pink": ("#ec4899", "#f472b6"),
            "orange": ("#ea580c", "#fb923c"),
            "teal": ("#0d9488", "#2dd4bf"),
            "indigo": ("#4f46e5", "#818cf8"),
            "dark blue": ("#1e3a5f", "#2563eb"),
            "emerald": ("#059669", "#6ee7b7"),
        }

        for color_name, (primary, accent) in color_map.items():
            if color_name in prompt_lower:
                theme["primary_color"] = primary
                theme["accent_color"] = accent
                break

        # Detect dark mode
        if "dark" in prompt_lower:
            theme["bg_color"] = "#0f172a"
            theme["sidebar_bg"] = "#1e293b"

        # Detect company name
        for prefix in ["call my company", "name my company", "called", "named"]:
            if prefix in prompt_lower:
                idx = prompt_lower.find(prefix) + len(prefix)
                rest = prompt[idx:].strip()
                name = rest.split(",")[0].split(".")[0].split(" with")[0].strip()
                if name and len(name) < 100:
                    theme["company_name"] = name

        return theme

    def save_logo(self, file_data: bytes, filename: str) -> str:
        """Save company logo and return the path."""
        ext = os.path.splitext(filename)[1] or ".png"
        stored = f"{uuid.uuid4().hex}{ext}"
        dest = os.path.join(self.UPLOAD_DIR, stored)
        with open(dest, "wb") as f:
            f.write(file_data)
        return stored

    def generate_welcome(self, employee_name: str, hour: int = None) -> dict:
        """Generate a personalized welcome message with voice intent."""
        if hour is None:
            hour = datetime.utcnow().hour

        if hour < 12:
            greeting = "Good morning"
            vibe = "☀️"
        elif hour < 17:
            greeting = "Good afternoon"
            vibe = "🌤️"
        else:
            greeting = "Good evening"
            vibe = "🌙"

        company = self.tenant.company_name if self.tenant else "your team"
        motto = self.tenant.theme.company_motto if self.tenant and self.tenant.theme else ""

        default_motto = "Let's make today productive."
        return {
            "greeting": f"{greeting}, {employee_name}! {vibe}",
            "company": company,
            "message": f"Welcome back to {company}. {motto or 'Time to make today count.'}",
            "voice_text": f"{greeting} {employee_name}. Welcome back to {company}. {motto or default_motto}",
        }