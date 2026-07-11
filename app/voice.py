"""
Panchi Club — Voice Processor (Conversation Mode)

Handles speech text input and returns contextual responses.
Recognizes common commands and routes to CompanionEngine for banter.
"""

import re
from typing import Optional


class VoiceProcessor:
    """Processes voice input text and returns contextual responses + optional actions."""

    def __init__(self, user_name: str = "there"):
        self.user_name = user_name or "there"
        self._load_companion()

    def _load_companion(self):
        """Lazy-load CompanionEngine for banter/greeting."""
        self._companion = None
        try:
            from app.companion import CompanionEngine
            self._companion = CompanionEngine()
        except Exception:
            pass

    def process(self, text: str) -> dict:
        """
        Main entry point. Takes speech-to-text input, returns a structured response.

        Returns:
            dict with keys:
                response (str): Natural language reply
                action (str): "suggestions", "redirect", "none"
                redirect_url (str): URL to navigate to if action == "redirect"
        """
        if not text or not text.strip():
            return {
                "response": "I didn't catch that. Could you say it again?",
                "action": "none",
                "redirect_url": "",
            }

        cleaned = text.strip().lower()

        # --- Greetings ---
        if re.search(r"^(hello|hi|hey|good morning|good afternoon|good evening|yo|sup|namaste|vanakkam)\b", cleaned):
            return self._handle_greeting()

        # --- New lead / create (must be checked before generic 'leads') ---
        if re.search(r"(new lead|create lead|add lead|register|new inquiry)", cleaned):
            return {
                "response": "Opening the new lead form for you. Just fill in the details and you're good to go!",
                "action": "redirect",
                "redirect_url": "/leads/new",
            }

        # --- Show leads / pipeline ---
        if re.search(r"(show\s+)?(leads?|pipeline|proposals?|inquiries?)", cleaned):
            return self._handle_leads()

        # --- Show payments ---
        if re.search(r"(show\s+)?(payments?|collection|revenue|money|income)", cleaned):
            return self._handle_payments()

        # --- Show invoices ---
        if re.search(r"(show\s+)?(invoices?|bills?|billing)", cleaned):
            return self._handle_invoices()

        # --- Dashboard / overview ---
        if re.search(r"(dashboard|overview|home|main|summary|stats?)", cleaned):
            return self._handle_dashboard()

        # --- Tasks / to-do ---
        if re.search(r"(tasks?|to.?do|pending|what'?s next|what should i do|follow.?up)", cleaned):
            return self._handle_tasks()

        # --- Help ---
        if re.search(r"(help|what can you do|commands?|capabilities|guide|tutorial)", cleaned):
            return self._handle_help()

        # --- Team ---
        if re.search(r"(team|colleagues?|coworkers?|staff|people)", cleaned):
            return self._handle_team()

        # --- Reports ---
        if re.search(r"(report|analytics|analytics|performance|kpi|metrics)", cleaned):
            return self._handle_reports()

        # --- Settings ---
        if re.search(r"(settings?|preferences?|config|profile)", cleaned):
            return self._handle_settings()

        # --- Fallback: use companion banter ---
        return self._handle_fallback(cleaned)

    def _handle_greeting(self) -> dict:
        if self._companion:
            try:
                greeting = self._companion.greet(self.user_name)
                banter = self._companion.banter(self.user_name)
                return {
                    "response": f"{greeting['text']} {banter}",
                    "action": "suggestions",
                    "redirect_url": "",
                }
            except Exception:
                pass
        return {
            "response": f"Hey {self.user_name}! Ready to make today productive? Try saying 'show leads' or 'help' to see what I can do.",
            "action": "suggestions",
            "redirect_url": "",
        }

    def _handle_leads(self) -> dict:
        return {
            "response": "Opening your leads pipeline. You can review, filter, or update statuses right from here.",
            "action": "redirect",
            "redirect_url": "/leads?view=pipeline",
        }

    def _handle_payments(self) -> dict:
        return {
            "response": "Here are your payments. All transactions are logged and tracked.",
            "action": "redirect",
            "redirect_url": "/payments",
        }

    def _handle_invoices(self) -> dict:
        return {
            "response": "Opening your invoices. You can view, download PDFs, or create new ones.",
            "action": "redirect",
            "redirect_url": "/invoices",
        }

    def _handle_dashboard(self) -> dict:
        return {
            "response": "Taking you back to the dashboard. Here's your overview at a glance.",
            "action": "redirect",
            "redirect_url": "/",
        }

    def _handle_tasks(self) -> dict:
        if self._companion:
            try:
                suggestions = self._companion.companion_suggestions()
                tasks_text = ". ".join(
                    [s["text"] for s in suggestions[:3]]
                )
                return {
                    "response": f"Here's what needs your attention: {tasks_text}. Want me to open any of these?",
                    "action": "suggestions",
                    "redirect_url": "",
                }
            except Exception:
                pass
        return {
            "response": "You have pending items to review. Check your pipeline for follow-ups and pending proposals.",
            "action": "suggestions",
            "redirect_url": "",
        }

    def _handle_help(self) -> dict:
        return {
            "response": (
                "I can help you with: • 'Show leads' — open your pipeline • "
                "'Show payments' — check transactions • 'Dashboard' — go home • "
                "'New lead' — create a lead • 'Invoices' — billing • "
                "'Tasks' — what's pending • 'Team' — see colleagues • "
                "'Reports' — analytics. Just speak naturally!"
            ),
            "action": "suggestions",
            "redirect_url": "",
        }

    def _handle_team(self) -> dict:
        return {
            "response": "Let me take you to the team page. You can see who's online and their activity.",
            "action": "redirect",
            "redirect_url": "/team",
        }

    def _handle_reports(self) -> dict:
        return {
            "response": "Opening reports. You'll find destination analytics, performance metrics, and more.",
            "action": "redirect",
            "redirect_url": "/reports",
        }

    def _handle_settings(self) -> dict:
        return {
            "response": "Opening settings. You can manage suppliers, preferences, and integrations here.",
            "action": "redirect",
            "redirect_url": "/settings",
        }

    def _handle_fallback(self, text: str) -> dict:
        """When nothing specific matches, use companion banter or a smart reply."""
        if self._companion:
            try:
                banter = self._companion.banter(self.user_name)
                mood = self._companion.detect_mood([text])
                if mood == "stressed":
                    comfort = self._companion.comfort("user seems stressed", self.user_name)
                    return {
                        "response": comfort,
                        "action": "suggestions",
                        "redirect_url": "",
                    }
                return {
                    "response": f"I hear you. {banter} Try saying 'help' to see what I can do.",
                    "action": "suggestions",
                    "redirect_url": "",
                }
            except Exception:
                pass
        return {
            "response": f"I'm not sure I understood that. Try saying 'show leads', 'help', or 'dashboard'.",
            "action": "suggestions",
            "redirect_url": "",
        }