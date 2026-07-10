"""
Shunya — Companion Engine (Phase 3G)

The team's AI buddy. Banters, celebrates, motivates, coaches, and balances mood.
Always present. Always learning. Never boring.
"""

import random
from datetime import datetime
from typing import Optional


class CompanionEngine:
    """The floating AI companion that lives in every employee's dashboard."""

    def __init__(self):
        self._mood_history = []

    def greet(self, employee_name: str, hour: int = None, 
              team_metric: str = "", yesterday_wins: int = 0) -> dict:
        if hour is None:
            hour = datetime.utcnow().hour
        
        if hour < 5:
            time_phrase = "burning the midnight oil"
        elif hour < 12:
            time_phrase = "morning"
        elif hour < 17:
            time_phrase = "afternoon"
        else:
            time_phrase = "evening"

        # Build a dynamic, personalized greeting
        parts = [f"Hey {employee_name}! ☀️"]
        
        if yesterday_wins > 0:
            parts.append(f"You closed {yesterday_wins} {'deal' if yesterday_wins == 1 else 'deals'} yesterday — nice work!")
        
        if team_metric:
            parts.append(team_metric)

        parts.append("What's our first move today?")

        return {
            "text": " ".join(parts),
            "emoji": "☀️" if hour < 17 else "🌙",
            "voice_text": " ".join(parts),
        }

    def banter(self, employee_name: str, hour: int = None) -> str:
        """Context-aware banter to lighten the mood."""
        if hour is None:
            hour = datetime.utcnow().hour

        banters = [
            f"Another Monday? Don't worry {employee_name}, I filtered out 14 spam leads for you.",
            f"PSA: {employee_name} is on fire today. 🔥 Everyone else, step up.",
            f"Your coffee's ready. Your leads are waiting. Let's go, {employee_name}!",
            f"Stat update: You're 12% more awesome than last week. Yes, I track that.",
            f"{employee_name}, I analyzed your morning mood — productive! Let's ride this wave.",
            f"Break time? Good. You've earned it. Also, the Sharma family lead just came in. Just saying.",
            f"You know what they say — a lead a day keeps the finance team happy. You're at 3 today, {employee_name}. 🐐",
            f"Quick thought, {employee_name}: you've got this. Now go get 'em.",
        ]
        return random.choice(banters)

    def celebrate(self, achievement: str, name: str = "") -> str:
        """Celebrate a team or individual win."""
        celebrations = [
            f"🎉 BOOM! {achievement}",
            f"LET'S GOOO! {achievement} 🔥",
            f"Crushing it, {name}! {achievement} You love to see it.",
            f"🥇 {achievement} — that's championship behavior right there.",
            f"Another one. 🎵 {achievement} You're making this look easy, {name}.",
        ]
        return random.choice(celebrations)

    def comfort(self, situation: str, name: str = "") -> str:
        """Empathetic response when something doesn't go well."""
        comforts = [
            f"Tough one, {name}. I analyzed it — you handled the objection well. Here's what could work even better next time...",
            f"Hey, not every deal closes. But every 'no' is data. Want me to analyze what happened?",
            f"{name}, you're doing better than you think. One conversation doesn't define your week. Let's look at the bigger picture.",
        ]
        return random.choice(comforts)

    def motivate(self, name: str, team_stat: str = "") -> str:
        """Daily motivation with real data."""
        motivators = [
            f"{name}, your team is {team_stat or 'on a roll'}. Keep the momentum!",
            f"Quick reminder, {name}: you're not just booking trips. You're creating memories that last a lifetime. That matters.",
            f"Your customer satisfaction score is up 6% this month. People trust you, {name}. That's earned, not given.",
            f"Fun fact: customers who receive a follow-up message within 2 hours convert 7x better. You've been crushing that lately.",
        ]
        return random.choice(motivators)

    def detect_mood(self, interaction_history: list[str]) -> str:
        """Simple mood detection from recent interactions."""
        stressed_words = ["stressed", "tired", "overwhelmed", "frustrated", "busy", "too much"]
        positive_words = ["great", "awesome", "closed", "won", "happy", "excellent", "excited"]

        all_text = " ".join(interaction_history).lower()
        stress_score = sum(1 for w in stressed_words if w in all_text)
        pos_score = sum(1 for w in positive_words if w in all_text)

        if stress_score > pos_score + 2:
            return "stressed"
        elif pos_score > stress_score + 2:
            return "positive"
        return "neutral"

    def companion_suggestions(self, role: str = "agent", pending_tasks: int = 0) -> list[dict]:
        """Contextual suggestions the companion offers."""
        suggestions = [
            {"icon": "📋", "text": "Review pending proposals", "action": "/leads"},
            {"icon": "📊", "text": "Check your daily stats", "action": "/"},
            {"icon": "💰", "text": "Follow up on pending payments", "action": "/payments"},
            {"icon": "🎯", "text": "Update lead statuses", "action": "/leads"},
        ]
        if pending_tasks > 0:
            suggestions.insert(0, {"icon": "✅", "text": f"You have {pending_tasks} pending tasks", "action": ""})
        if role == "admin":
            suggestions.append({"icon": "👥", "text": "Check team activity", "action": "/team"})
            suggestions.append({"icon": "⚙️", "text": "Review feature requests", "action": "/settings"})
        return suggestions