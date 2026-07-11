"""Brand Guardian — ensures outgoing communication reflects Panchi Club's desired personality.

Panchi Club's voice: caring, comfortable, respectful, premium, clear.
Suggests revisions when language becomes cold, transactional, or confusing.
"""
import re


class BrandGuardian:
    COLD_PATTERNS = [
        (r"\bplease find attached\b", "Use 'Here is your...' instead — warmer and clearer"),
        (r"\bper our conversation\b", "Use 'As we discussed' — more natural"),
        (r"\bhereinafter\b", "Legalese — use simpler language"),
        (r"\bnotwithstanding\b", "Legalese — use 'even though' or 'despite'"),
        (r"\bhereby\b", "Legalese — remove, adds no meaning"),
        (r"\bkindly\b", "Use 'please' instead — 'kindly' can feel stiff"),
        (r"\brevert\b", "Use 'get back to you' instead"),
        (r"\bdo the needful\b", "Use 'please take care of' or 'please handle'"),
        (r"\boptimum\b", "Use 'best' or 'ideal' instead"),
        (r"\binitiate\b", "Use 'start' instead"),
    ]

    WARM_PATTERNS = [
        r"\bI understand\b",
        r"\bI'd love to\b",
        r"\bhere's what\b",
        r"\bwhat matters most\b",
        r"\bI recommend\b",
        r"\blet me explain\b",
        r"\byou're welcome\b",
        r"\bmy pleasure\b",
    ]

    @staticmethod
    def review(message: str) -> dict:
        issues = []
        strengths = []

        if len(message) < 10:
            issues.append({"type": "too_short", "suggestion": "Add context to make it warmer."})

        for pattern, suggestion in BrandGuardian.COLD_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                issues.append({"type": "cold_language", "pattern": pattern.strip("\\b"), "suggestion": suggestion})

        for pattern in BrandGuardian.WARM_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                cleaned = pattern.strip("\\b").strip("\\")
                strengths.append(f"Good use of warm language: '{cleaned}'")

        if not re.match(r"^(Hi|Hello|Dear|Good\s)", message):
            issues.append({"type": "missing_greeting", "suggestion": "Start with 'Hi [name]!'"})

        if not re.search(r"(let me know|talk soon|best|regards|cheers|warmly|thank)", message, re.IGNORECASE):
            issues.append({"type": "missing_closing", "suggestion": "Add a warm closing"})

        caps = re.findall(r'\b[A-Z]{4,}\b', message)
        if caps:
            issues.append({"type": "shouting", "suggestion": f"Avoid ALL CAPS: {', '.join(caps[:3])}"})

        if message.count("!") > 3:
            issues.append({"type": "excessive_enthusiasm", "suggestion": "One exclamation is enough."})

        penalty = len(issues) * 10
        bonus = len(strengths) * 15
        score = max(0, min(100, 70 - penalty + bonus))

        return {"tone_score": score, "issues": issues, "strengths": strengths,
                "verdict": "On brand" if score >= 80 else "Minor issues" if score >= 60 else "Needs revision"}

    @staticmethod
    def suggest_rewrite(original: str) -> str:
        review = BrandGuardian.review(original)
        if review["tone_score"] >= 80:
            return original
        return "\n".join(i["suggestion"] for i in review["issues"])
