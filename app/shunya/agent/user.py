"""Shunya Personal Agent — User Profile & Correction Engine.

Every user gets a profile that the agent reads before every interaction.
Corrections are the most valuable signal — the agent learns from them.
"""
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UserProfile:
    """What the agent knows about this user."""
    user_id: int
    name: str
    role: str
    tenant_id: int
    email: str = ""

    # Communication style (auto-learned)
    communication_style: str = "casual"    # formal | casual | direct | coaching
    verbosity: str = "balanced"            # concise | balanced | detailed
    emoji_style: str = "moderate"          # none | moderate | expressive

    # Behavioral patterns (auto-learned)
    preferred_working_hours: tuple = (9, 18)
    common_actions: dict = field(default_factory=dict)
    last_active_hour: int = 0

    # Relationship
    session_count: int = 0
    first_seen: str = ""
    last_seen: str = ""
    correction_count: int = 0
    trust_score: float = 0.5

    # Learned preferences
    pet_peeves: list[str] = field(default_factory=list)
    preferred_persona: str = "assistant"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "role": self.role,
            "style": self.communication_style,
            "verbosity": self.verbosity,
            "emoji": self.emoji_style,
            "persona": self.preferred_persona,
            "trust": round(self.trust_score, 2),
            "sessions": self.session_count,
            "corrections": self.correction_count,
            "pet_peeves": self.pet_peeves[:3],
        }

    def to_prompt(self) -> str:
        """Compact string for LLM context injection."""
        return (
            f"User: {self.name} ({self.role})\n"
            f"Style: {self.communication_style}, {self.verbosity}, emoji={self.emoji_style}\n"
            f"Persona: {self.preferred_persona}\n"
            f"Trust: {round(self.trust_score, 2)} ({self.session_count} sessions, {self.correction_count} corrections)\n"
            f"Pet peeves: {', '.join(self.pet_peeves[:3]) or 'none yet'}"
        )


class ProfileStore:
    """Loads and saves user profiles via Honcho."""

    @staticmethod
    def load(user_id: int, tenant_id: int) -> UserProfile:
        """Load or create a user profile."""
        from app.models import TeamMember
        from app.shunya.memory import MemoryStore, MemoryClass

        user = TeamMember.query.get(user_id)
        if not user:
            return UserProfile(user_id=user_id, name="User", role="agent", tenant_id=tenant_id)

        profile = UserProfile(
            user_id=user.id,
            name=user.name,
            role=user.role,
            tenant_id=user.tenant_id,
            email=user.email or "",
        )

        # Try to load learned preferences from memory
        memories = MemoryStore.retrieve(MemoryClass.RELATIONSHIP, tenant_id, entity_id=user_id, limit=5)
        for mem in memories:
            content = mem.get("content", "")
            if "style:" in content:
                profile.communication_style = content.split("style:")[-1].split(",")[0].strip()
            if "verbosity:" in content:
                profile.verbosity = content.split("verbosity:")[-1].split(",")[0].strip()
            if "persona:" in content:
                profile.preferred_persona = content.split("persona:")[-1].strip()
            if "trust:" in content:
                try:
                    profile.trust_score = float(content.split("trust:")[-1].split()[0])
                except ValueError:
                    pass
            if "peeves:" in content:
                peeves = content.split("peeves:")[-1].strip()
                if peeves:
                    profile.pet_peeves = [p.strip() for p in peeves.split(",")]

        profile.session_count = len(MemoryStore.retrieve(
            MemoryClass.RELATIONSHIP, tenant_id, entity_id=user_id, limit=20
        ))
        profile.last_active_hour = datetime.utcnow().hour
        return profile

    @staticmethod
    def save(profile: UserProfile):
        """Save profile preferences to memory."""
        from app.shunya.memory import MemoryStore, MemoryClass
        content = (
            f"style:{profile.communication_style}, verbosity:{profile.verbosity}, "
            f"emoji:{profile.emoji_style}, persona:{profile.preferred_persona}, "
            f"trust:{profile.trust_score}, sessions:{profile.session_count}, "
            f"corrections:{profile.correction_count}, peeves:{','.join(profile.pet_peeves[:5])}"
        )
        MemoryStore.store(MemoryClass.RELATIONSHIP, profile.tenant_id,
                          key=f"profile_{profile.user_id}",
                          content=content, entity_id=profile.user_id)


# ---------------------------------------------------------------------------
# Correction Engine
# ---------------------------------------------------------------------------

class CorrectionEngine:
    """Learns from user corrections — the most valuable signal."""

    @staticmethod
    def ingest(user_id: int, tenant_id: int, original_query: str,
               correction: str, agent_action: dict):
        """Process a user correction and update the profile."""
        from app.shunya.memory import MemoryStore, MemoryClass

        # 1. Store the correction
        content = f"CORRECTION: user said '{correction}' for query '{original_query}'"
        MemoryStore.store(MemoryClass.RELATIONSHIP, tenant_id,
                          key=f"correction_{user_id}_{int(__import__('time').time())}",
                          content=content, entity_id=user_id)

        # 2. Extract pet peeves
        CorrectionEngine._learn_pet_peeve(user_id, tenant_id, original_query, correction)

        # 3. Update profile correction count
        profile = ProfileStore.load(user_id, tenant_id)
        profile.correction_count += 1
        ProfileStore.save(profile)

    @staticmethod
    def _learn_pet_peeve(user_id: int, tenant_id: int, query: str, correction: str):
        """Extract and store recurring corrections as pet peeves."""
        from app.shunya.memory import MemoryStore, MemoryClass

        # Simple pattern: "don't do X" or "I meant Y not Z"
        query_lower = query.lower()
        correction_lower = correction.lower()

        patterns = []
        if "don't" in correction_lower or "dont" in correction_lower or "never" in correction_lower:
            patterns.append(correction)
        if "not" in correction_lower:
            # Extract what they don't want
            for phrase in ["not ", "instead of "]:
                if phrase in correction_lower:
                    idx = correction_lower.find(phrase) + len(phrase)
                    patterns.append(correction[idx:].strip())

        if patterns:
            MemoryStore.store(
                MemoryClass.RELATIONSHIP, tenant_id,
                key=f"peeve_{user_id}",
                content=f"peeve:{'; '.join(patterns[:3])}",
                entity_id=user_id,
            )

    @staticmethod
    def get_correction_context(user_id: int, tenant_id: int, limit: int = 3) -> str:
        """Get recent corrections as context for the agent."""
        from app.shunya.memory import MemoryStore, MemoryClass
        memories = MemoryStore.retrieve(MemoryClass.RELATIONSHIP, tenant_id,
                                         entity_id=user_id, query="CORRECTION", limit=limit)
        if not memories:
            return ""
        return "Recent corrections from user: " + "; ".join(
            m.get("content", "") for m in memories
        )