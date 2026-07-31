"""
Shunya — Multi-Language AI Assistant (Text + Speech)

Any language. Any dialect. The user speaks, Shunya responds in their language.
Voice input, text input, speech output. All languages supported.
"""

import re
from typing import Optional


class LanguageEngine:
    """Handles multi-language text and speech for the AI Assistant."""

    # Supported languages with their codes
    LANGUAGES = {
        "en": "English",
        "hi": "Hindi (हिन्दी)",
        "bn": "Bengali (বাংলা)",
        "te": "Telugu (తెలుగు)",
        "mr": "Marathi (मराठी)",
        "ta": "Tamil (தமிழ்)",
        "ur": "Urdu (اردو)",
        "gu": "Gujarati (ગુજરાતી)",
        "kn": "Kannada (ಕನ್ನಡ)",
        "ml": "Malayalam (മലയാളം)",
        "pa": "Punjabi (ਪੰਜਾਬੀ)",
        "or": "Odia (ଓଡ଼ିଆ)",
        "as": "Assamese (অসমীয়া)",
        "mai": "Maithili (मैथिली)",
        "sat": "Santali (ᱥᱟᱱᱛᱟᱲᱤ)",
        "ks": "Kashmiri (कॉशुर)",
        "doi": "Dogri (डोगरी)",
        "sd": "Sindhi (سنڌي)",
        "kok": "Konkani (कोंकणी)",
        "ne": "Nepali (नेपाली)",
        "si": "Sinhala (සිංහල)",
        "th": "Thai (ไทย)",
        "vi": "Vietnamese (Tiếng Việt)",
        "zh": "Chinese (中文)",
        "ja": "Japanese (日本語)",
        "ko": "Korean (한국어)",
        "ar": "Arabic (العربية)",
        "fr": "French (Français)",
        "de": "German (Deutsch)",
        "es": "Spanish (Español)",
        "pt": "Portuguese (Português)",
        "ru": "Russian (Русский)",
        "it": "Italian (Italiano)",
        "nl": "Dutch (Nederlands)",
        "tr": "Turkish (Türkçe)",
    }

    # Common greetings in all languages
    GREETINGS = {
        "en": ("Good morning", "Good afternoon", "Good evening"),
        "hi": ("शुभ प्रभात", "शुभ अपराह्न", "शुभ संध्या"),
        "bn": ("সুপ্রভাত", "শুভ অপরাহ্ন", "শুভ সন্ধ্যা"),
        "te": ("శుభోదయం", "శుభ మధ్యాహ్నం", "శుభ సాయంత్రం"),
        "mr": ("शुभ प्रभात", "शुभ दुपार", "शुभ संध्याकाळ"),
        "ta": ("காலை வணக்கம்", "மதிய வணக்கம்", "மாலை வணக்கம்"),
        "gu": ("સુપ્રભાત", "શુભ બપોર", "શુભ સાંજ"),
        "kn": ("ಶುಭೋದಯ", "ಶುಭ ಮಧ್ಯಾಹ್ನ", "ಶುಭ ಸಂಜೆ"),
        "ml": ("സുപ്രഭാതം", "ശുഭ മധ്യാഹ്നം", "ശുഭ സായാഹ്നം"),
        "pa": ("ਸਤ ਸ੍ਰੀ ਅਕਾਲ", "ਸਤ ਸ੍ਰੀ ਅਕਾਲ", "ਸਤ ਸ੍ਰੀ ਅਕਾਲ"),
        "fr": ("Bonjour", "Bon après-midi", "Bonsoir"),
        "es": ("Buenos días", "Buenas tardes", "Buenas noches"),
        "de": ("Guten Morgen", "Guten Nachmittag", "Guten Abend"),
        "zh": ("早上好", "下午好", "晚上好"),
        "ar": ("صباح الخير", "مساء الخير", "مساء الخير"),
        "ja": ("おはようございます", "こんにちは", "こんばんは"),
        "ko": ("좋은 아침", "안녕하세요", "좋은 저녁"),
    }

    def __init__(self, lang: str = "en"):
        self.lang = lang if lang in self.LANGUAGES else "en"

    def greet(self, name: str = "", hour: int = None) -> dict:
        """Generate a greeting in the user's language."""
        if hour is None:
            from datetime import datetime
            hour = datetime.utcnow().hour
        
        period = 0 if hour < 12 else 1 if hour < 17 else 2
        greets = self.GREETINGS.get(self.lang, self.GREETINGS["en"])
        greeting = greets[period] if period < len(greets) else greets[0]
        
        lang_name = self.LANGUAGES.get(self.lang, "English")
        return {
            "text": f"{greeting}{', ' + name if name else ''}!",
            "voice_text": f"{greeting}{', ' + name if name else ''}!",
            "language": lang_name,
            "lang_code": self.lang,
        }

    def translate_ui(self, key: str) -> str:
        """Translate a UI element into the user's language."""
        translations = {
            "en": {
                "overview": "Overview", "pipeline": "Pipeline", "payments": "Payments",
                "invoices": "Invoices", "team": "Team", "reports": "Reports",
                "settings": "Settings", "logout": "Logout", "search": "Search...",
                "new_lead": "New Lead", "quick_actions": "Quick Actions",
                "recent_activity": "Recent Activity", "ai_suggestion": "AI Suggestion",
                "welcome_back": "Welcome back", "good_morning": "Good morning",
                "ask_anything": "Ask Shunya anything...",
                "victory_shared": "shared a victory", "promoted": "was promoted",
            },
            "hi": {
                "overview": "अवलोकन", "pipeline": "पाइपलाइन", "payments": "भुगतान",
                "invoices": "चालान", "team": "टीम", "reports": "रिपोर्ट",
                "settings": "सेटिंग्स", "logout": "लॉग आउट", "search": "खोजें...",
                "new_lead": "नया लीड", "quick_actions": "त्वरित कार्रवाई",
                "recent_activity": "हाल की गतिविधि", "ai_suggestion": "AI सुझाव",
                "welcome_back": "वापसी पर स्वागत है", "good_morning": "शुभ प्रभात",
                "ask_anything": "शुन्य से कुछ भी पूछें...",
                "victory_shared": "ने एक जीत साझा की", "promoted": "को पदोन्नत किया गया",
            },
            "bn": {
                "overview": "ওভারভিউ", "pipeline": "পাইপলাইন", "payments": "পেমেন্ট",
                "invoices": "চালান", "team": "টিম", "reports": "রিপোর্ট",
                "settings": "সেটিংস", "logout": "লগ আউট", "search": "অনুসন্ধান...",
                "new_lead": "নতুন লিড", "quick_actions": "দ্রুত কর্ম",
                "recent_activity": "সাম্প্রতিক কার্যকলাপ", "ai_suggestion": "AI পরামর্শ",
                "welcome_back": "ফিরে আসার জন্য স্বাগতম", "good_morning": "সুপ্রভাত",
                "ask_anything": "শুন্যকে কিছু জিজ্ঞাসা করুন...",
                "victory_shared": "একটি বিজয় শেয়ার করেছেন", "promoted": "পদোন্নতি পেয়েছেন",
            },
        }
        return translations.get(self.lang, translations["en"]).get(key, key)

    def detect_language(self, text: str) -> str:
        """Detect language from text input."""
        if not text:
            return "en"
        # Check for Unicode ranges
        ranges = {
            "hi": (0x0900, 0x097F), "bn": (0x0980, 0x09FF),
            "te": (0x0C00, 0x0C7F), "mr": (0x0900, 0x097F),  # Marathi uses Devanagari
            "ta": (0x0B80, 0x0BFF), "gu": (0x0A80, 0x0AFF),
            "kn": (0x0C80, 0x0CFF), "ml": (0x0D00, 0x0D7F),
            "pa": (0x0A00, 0x0A7F), "or": (0x0B00, 0x0B7F),
            "ar": (0x0600, 0x06FF), "zh": (0x4E00, 0x9FFF),
            "ja": (0x3040, 0x309F), "ko": (0xAC00, 0xD7AF),
            "th": (0x0E00, 0x0E7F), "ru": (0x0400, 0x04FF),
        }
        for lang, (start, end) in ranges.items():
            for char in text[:20]:
                if start <= ord(char) <= end:
                    return lang
        return "en"

    def get_voice_params(self) -> dict:
        """Get TTS parameters for the current language."""
        voices = {
            "en": {"rate": 1.0, "pitch": 1.0, "voice": "Google US English"},
            "hi": {"rate": 1.1, "pitch": 1.05, "voice": "Google हिन्दी"},
            "bn": {"rate": 1.1, "pitch": 1.05, "voice": "Google বাংলা"},
            "te": {"rate": 1.1, "pitch": 1.05, "voice": "Google తెలుగు"},
            "ta": {"rate": 1.1, "pitch": 1.05, "voice": "Google தமிழ்"},
            "ml": {"rate": 1.1, "pitch": 1.05, "voice": "Google മലയാളം"},
            "gu": {"rate": 1.1, "pitch": 1.05, "voice": "Google ગુજરાતી"},
            "kn": {"rate": 1.1, "pitch": 1.05, "voice": "Google ಕನ್ನಡ"},
            "mr": {"rate": 1.1, "pitch": 1.05, "voice": "Google मराठी"},
            "pa": {"rate": 1.1, "pitch": 1.05, "voice": "Google ਪੰਜਾਬੀ"},
            "fr": {"rate": 1.0, "pitch": 1.0, "voice": "Google Français"},
            "es": {"rate": 1.0, "pitch": 1.0, "voice": "Google Español"},
            "de": {"rate": 1.0, "pitch": 1.0, "voice": "Google Deutsch"},
            "ar": {"rate": 1.0, "pitch": 1.0, "voice": "Google العربية"},
            "zh": {"rate": 0.9, "pitch": 1.1, "voice": "Google 中文"},
            "ja": {"rate": 1.0, "pitch": 1.0, "voice": "Google 日本語"},
            "ko": {"rate": 1.0, "pitch": 1.0, "voice": "Google 한국어"},
        }
        return voices.get(self.lang, voices["en"])