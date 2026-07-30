"""Intent Engine — classifies user intent from natural language input."""

from __future__ import annotations

import re
from typing import Any

from .types import IntentCategory, UrgencyLevel, UserIntent


# ── Intent Patterns ──────────────────────────────────────────────────────

INTENT_PATTERNS: list[tuple[re.Pattern, IntentCategory, float]] = [
    # Questions
    (re.compile(r'\b(what|how|why|when|where|who|which|does|is|are|can|could|would)\b.*\?', re.I), IntentCategory.QUESTION, 0.85),
    (re.compile(r'\bshow\b.*\b(me|list|all)\b', re.I), IntentCategory.QUESTION, 0.75),
    (re.compile(r'\btell me\b', re.I), IntentCategory.QUESTION, 0.8),
    (re.compile(r'\bexplain\b', re.I), IntentCategory.QUESTION, 0.7),
    (re.compile(r'\blist\b', re.I), IntentCategory.QUESTION, 0.65),

    # Commands
    (re.compile(r'\b(create|make|add|new)\b', re.I), IntentCategory.COMMAND, 0.8),
    (re.compile(r'\b(update|edit|change|modify)\b', re.I), IntentCategory.COMMAND, 0.8),
    (re.compile(r'\b(delete|remove|cancel|archive)\b', re.I), IntentCategory.COMMAND, 0.8),
    (re.compile(r'\b(send|email|notify|remind)\b', re.I), IntentCategory.COMMAND, 0.75),
    (re.compile(r'\b(mark|set|flag)\b', re.I), IntentCategory.COMMAND, 0.7),

    # Search
    (re.compile(r'\bfind\b', re.I), IntentCategory.SEARCH, 0.85),
    (re.compile(r'\bsearch\b', re.I), IntentCategory.SEARCH, 0.9),
    (re.compile(r'\blookup\b', re.I), IntentCategory.SEARCH, 0.8),
    (re.compile(r'\bwhere is\b', re.I), IntentCategory.SEARCH, 0.75),

    # Navigate
    (re.compile(r'\bgo to\b', re.I), IntentCategory.NAVIGATE, 0.85),
    (re.compile(r'\bnavigate\b', re.I), IntentCategory.NAVIGATE, 0.9),
    (re.compile(r'\bopen\b', re.I), IntentCategory.NAVIGATE, 0.75),
    (re.compile(r'\btake me\b', re.I), IntentCategory.NAVIGATE, 0.8),

    # Explain
    (re.compile(r'\bwhy did you\b', re.I), IntentCategory.EXPLAIN, 0.9),
    (re.compile(r'\bhow did you\b', re.I), IntentCategory.EXPLAIN, 0.85),
    (re.compile(r'\btrace\b', re.I), IntentCategory.EXPLAIN, 0.8),
    (re.compile(r'\bevidence\b', re.I), IntentCategory.EXPLAIN, 0.75),

    # Suggest
    (re.compile(r'\bsuggest\b', re.I), IntentCategory.SUGGEST, 0.85),
    (re.compile(r'\brecommend\b', re.I), IntentCategory.SUGGEST, 0.8),
    (re.compile(r'\bwhat next\b', re.I), IntentCategory.SUGGEST, 0.75),
    (re.compile(r'\bwhat should\b', re.I), IntentCategory.SUGGEST, 0.7),

    # Automate
    (re.compile(r'\bautomate\b', re.I), IntentCategory.AUTOMATE, 0.9),
    (re.compile(r'\bset up automation\b', re.I), IntentCategory.AUTOMATE, 0.95),
    (re.compile(r'\baudomate\b', re.I), IntentCategory.AUTOMATE, 0.85),
]

# ── Urgency Patterns ────────────────────────────────────────────────────

URGENCY_PATTERNS: list[tuple[re.Pattern, UrgencyLevel]] = [
    (re.compile(r'\b(urgent|immediately|asap|right now|emergency)\b', re.I), UrgencyLevel.CRITICAL),
    (re.compile(r'\b(soon|today|important|critical|deadline)\b', re.I), UrgencyLevel.HIGH),
    (re.compile(r'\b(later|sometime|eventually|whenever)\b', re.I), UrgencyLevel.LOW),
]

# ── Entity Extraction Patterns ──────────────────────────────────────────

OBJECT_TYPE_PATTERNS = [
    re.compile(r'\b(customer|client|patient|lead)\b', re.I),
    re.compile(r'\b(invoice|bill|payment|receipt)\b', re.I),
    re.compile(r'\b(booking|order|appointment|reservation)\b', re.I),
    re.compile(r'\b(project|task|todo|milestone)\b', re.I),
    re.compile(r'\b(product|item|service|inventory)\b', re.I),
    re.compile(r'\b(supplier|vendor|partner)\b', re.I),
    re.compile(r'\b(contract|agreement|proposal|quote)\b', re.I),
    re.compile(r'\b(report|document|file|attachment)\b', re.I),
    re.compile(r'\b(user|employee|staff|member)\b', re.I),
]


class IntentEngine:
    """Classifies user intent from raw input."""

    def classify(self, raw_input: str, context_hint: str = "") -> UserIntent:
        """Classify the user's intent from their input."""
        intent = UserIntent(raw_input=raw_input)
        text = raw_input.strip()

        if not text:
            return intent

        # Score against known intent patterns
        best_category = IntentCategory.UNKNOWN
        best_score = 0.0
        matched_entities = []

        for pattern, category, weight in INTENT_PATTERNS:
            m = pattern.search(text)
            if m:
                score = weight
                if score > best_score:
                    best_score = score
                    best_category = category

        # Entity extraction
        for pattern in OBJECT_TYPE_PATTERNS:
            m = pattern.search(text)
            if m:
                word = m.group(1).lower()
                if word not in [e.get("value", "").lower() for e in matched_entities]:
                    matched_entities.append({
                        "type": "object_type",
                        "value": word,
                        "confidence": 0.8,
                    })

        intent.category = best_category if best_score >= 0.4 else IntentCategory.UNKNOWN
        intent.confidence = best_score
        intent.ambiguity = 1.0 - best_score if best_score > 0 else 1.0
        intent.entities = matched_entities

        # Urgency classification
        if best_score < 0.4:
            intent.ambiguity = 0.8  # High ambiguity for unrecognized patterns

        for pattern, urgency in URGENCY_PATTERNS:
            if pattern.search(text):
                intent.urgency = urgency
                break

        # Requested outcome extraction
        intent.requested_outcome = self._extract_outcome(text)

        return intent

    def _extract_outcome(self, text: str) -> str:
        """Extract what the user wants to accomplish."""
        # Remove common prefixes
        cleaned = re.sub(r'\b(can you|could you|would you|i want to|i need to|please)\b', '', text, flags=re.I).strip()
        return cleaned[:150]