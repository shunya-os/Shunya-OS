"""
Shunya — Creative Generation Engine

The AI Assistant doesn't just answer questions. It creates.
Instagram posts, brochures, video scripts, proposals, invitations.
Anything a business needs to communicate.

Pattern: User says what they need → Shunya generates it → User approves → Done.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Optional

from app import db
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime


class CreativeAsset(db.Model):
    """A generated creative asset (post, brochure, script, etc.)."""
    __tablename__ = "creative_assets"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=True)
    created_by = Column(String(120), default="")
    asset_type = Column(String(60), default="social_post")  # social_post, brochure, script, invitation, proposal
    title = Column(String(255), default="")
    copy_text = Column(Text, default="")
    image_url = Column(String(500), default="")
    image_path = Column(String(500), default="")
    status = Column(String(30), default="draft")  # draft, approved, posted, archived
    platform = Column(String(60), default="instagram")  # instagram, facebook, whatsapp, email, print
    brand_name = Column(String(120), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime)
    approved_by = Column(String(120))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "asset_type": self.asset_type,
            "title": self.title,
            "copy_text": self.copy_text[:200] if self.copy_text else "",
            "image_url": self.image_url,
            "status": self.status,
            "platform": self.platform,
            "brand_name": self.brand_name,
            "created_at": self.created_at.isoformat(),
        }


class CreativeEngine:
    """Generates creative assets using AI. Connects to the AI Assistant bar."""

    def __init__(self):
        self._output_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "media", "creative"
        )
        os.makedirs(self._output_dir, exist_ok=True)

    def understand_intent(self, user_input: str) -> dict:
        """Parse what the user wants to create."""
        input_lower = user_input.lower()

        # Detect asset type
        asset_type = "social_post"
        if any(w in input_lower for w in ["brochure", "flyer", "pamphlet", "leaflet"]):
            asset_type = "brochure"
        elif any(w in input_lower for w in ["video", "reel", "short", "tiktok"]):
            asset_type = "video_script"
        elif any(w in input_lower for w in ["invitation", "invite", "wedding card"]):
            asset_type = "invitation"
        elif any(w in input_lower for w in ["proposal", "presentation", "deck"]):
            asset_type = "proposal"
        elif any(w in input_lower for w in ["email", "newsletter"]):
            asset_type = "email"
        elif any(w in input_lower for w in ["banner", "ad", "advertisement"]):
            asset_type = "ad"

        # Detect platform
        platform = "instagram"
        if "facebook" in input_lower: platform = "facebook"
        elif "linkedin" in input_lower: platform = "linkedin"
        elif "twitter" in input_lower or "x.com" in input_lower: platform = "twitter"
        elif "whatsapp" in input_lower: platform = "whatsapp"
        elif "email" in input_lower: platform = "email"

        # Extract topic/subject
        topic = self._extract_topic(user_input)

        # Extract brand
        brand = ""
        brand_keywords = {"for": 1, "from": 1, "about": 1}
        words = user_input.split()
        for i, w in enumerate(words):
            if w.lower() in brand_keywords and i + 1 < len(words):
                brand = " ".join(words[i+1:i+3]).strip(" '\",.!?")

        return {
            "asset_type": asset_type,
            "platform": platform,
            "topic": topic,
            "brand": brand or "Your Brand",
            "original_input": user_input,
        }

    def _extract_topic(self, text: str) -> str:
        """Extract the main topic from user input."""
        text_lower = text.lower()
        # Remove common prefixes
        for prefix in ["create", "make", "generate", "design", "build", "write",
                        "i need", "i want", "can you", "could you"]:
            if text_lower.startswith(prefix):
                text_lower = text_lower[len(prefix):].strip()
                break
        # Remove platform mentions
        for plat in ["for instagram", "for facebook", "for whatsapp", "post about",
                     "story about", "reel about", "ad for", "banner for"]:
            text_lower = text_lower.replace(plat, "").strip()
        # Capitalize and return
        return text_lower.strip().strip(" '\",").title() or "Your Content"

    def generate_copy(self, intent: dict) -> str:
        """Generate marketing copy based on intent."""
        platform = intent["platform"]
        asset_type = intent["asset_type"]
        topic = intent["topic"]
        brand = intent["brand"]

        # Social media post copy
        if asset_type == "social_post":
            if platform == "instagram":
                return (
                    f"✨ {topic} ✨\n\n"
                    f"Experience the magic with {brand}. "
                    f"Your journey begins here.\n\n"
                    f"📅 Book now\n"
                    f"📍 [Location]\n"
                    f"💬 DM for inquiries\n\n"
                    f"#{topic.replace(' ', '')} #{brand.replace(' ', '')} #Travel #Explore"
                )
            elif platform == "linkedin":
                return (
                    f"We're proud to announce our latest achievement in {topic.lower()}.\n\n"
                    f"At {brand}, we believe in delivering excellence every single day. "
                    f"Our team has been working tirelessly to bring you the best experience possible.\n\n"
                    f"Read more: [link]\n\n"
                    f"#{brand.replace(' ', '')} #{topic.replace(' ', '')} #Leadership #Growth"
                )
            elif platform == "twitter":
                return f"🚀 {topic} is here!\n\nBook your experience with {brand} today.\n\n[link]"
            else:
                return f"🌟 {topic} — Only with {brand}. Experience the difference. Book now!"

        # Brochure copy
        elif asset_type == "brochure":
            return (
                f"{topic.upper()}\n"
                f"{'='*40}\n\n"
                f"Presented by {brand}\n\n"
                f"Discover an experience that goes beyond expectations. "
                f"Our curated packages are designed to create memories that last a lifetime.\n\n"
                f"What's Included:\n"
                f"• Premium accommodations\n"
                f"• Expert guides\n"
                f"• 24/7 support\n"
                f"• Customizable itinerary\n\n"
                f"Starting from ₹XX,XXX\n"
                f"Contact us today!\n"
                f"[Phone] | [Email] | [Website]"
            )

        # Video script
        elif asset_type == "video_script":
            return (
                f"🎬 VIDEO SCRIPT: {topic.upper()}\n\n"
                f"TIME: 30 seconds\n"
                f"FORMAT: Reel/Short\n\n"
                f"[0:00-0:05] OPEN: Beautiful drone shot of destination\n"
                f"  TEXT: 'Dreaming of {topic}?'\n\n"
                f"[0:05-0:15] MID: Happy customers enjoying experience\n"
                f"  TEXT: '{brand} makes it real.'\n\n"
                f"[0:15-0:25] MID: Quick cuts of highlights\n"
                f"  TEXT: 'Premium experiences. Unforgettable memories.'\n\n"
                f"[0:25-0:30] CLOSE: Logo + CTA\n"
                f"  TEXT: 'Book now. Link in bio.'\n\n"
                f"SOUND: Upbeat, inspiring background music"
            )

        return f"{topic} — presented by {brand}. Your journey starts here."

    def generate_prompt_for_image(self, intent: dict) -> str:
        """Generate an image generation prompt based on intent."""
        topic = intent["topic"]
        brand = intent["brand"]
        platform = intent["platform"]

        style_map = {
            "instagram": "vibrant, social media ready, instagram story style, modern design",
            "facebook": "engaging, shareable, facebook feed optimized",
            "linkedin": "professional, clean, corporate style",
            "twitter": "bold, eye-catching, simple text overlay",
            "whatsapp": "clean, mobile-first design",
        }

        style = style_map.get(platform, "modern, clean design")
        return (
            f"A professional marketing graphic for '{topic}' by {brand}. "
            f"Style: {style}. "
            f"Use beautiful colors, elegant typography, "
            f"and a clean layout suitable for social media. "
            f"Include space for text overlay. "
            f"Photorealistic quality, professional lighting, 16:9 aspect ratio."
        )

    def save_asset(self, intent: dict, copy_text: str,
                   image_path: str = "", image_url: str = "",
                   created_by: str = "AI Assistant") -> CreativeAsset:
        """Save the generated creative to the database."""
        asset = CreativeAsset(
            asset_type=intent["asset_type"],
            title=intent["topic"][:255],
            copy_text=copy_text,
            image_url=image_url,
            image_path=image_path,
            platform=intent["platform"],
            brand_name=intent["brand"],
            created_by=created_by,
            status="draft",
        )
        db.session.add(asset)
        db.session.commit()
        return asset

    def preview_response(self, asset: CreativeAsset) -> dict:
        """Format the creative for the AI Assistant's response."""
        type_labels = {
            "social_post": "📱 Social Media Post",
            "brochure": "📄 Brochure",
            "video_script": "🎬 Video Script",
            "invitation": "💌 Invitation",
            "proposal": "📋 Proposal",
            "email": "📧 Email",
            "ad": "📢 Advertisement",
        }
        return {
            "title": f"{type_labels.get(asset.asset_type, '📦 Creative')}: {asset.title}",
            "copy": asset.copy_text,
            "image_url": asset.image_url,
            "asset_id": asset.id,
            "platform": asset.platform,
            "status": asset.status,
            "message": (
                f"✅ Your {asset.asset_type.replace('_', ' ')} is ready!\n\n"
                f"{asset.copy_text[:300]}\n\n"
                f"📱 Platform: {asset.platform.title()}\n"
                f"📌 Status: Draft\n\n"
                f"Say 'Approve' to publish or 'Edit' to modify."
            ),
        }