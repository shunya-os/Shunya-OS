"""
Shunya — Web Intelligence Layer

The AI Assistant searches the web, pulls real-time information,
and acts like a true personal assistant. Not just command routing.
"""

import json
import re
from datetime import datetime
from typing import Optional


class WebIntelligence:
    """Gives the AI Assistant real-time web intelligence."""

    @staticmethod
    def answer(query: str) -> dict:
        """Answer a user query with web intelligence where possible."""
        query_lower = query.lower().strip()

        # Time-based queries
        if any(w in query_lower for w in ["time", "date", "day", "today", "tomorrow"]):
            return WebIntelligence._handle_time_query(query)

        # Weather (simulated — would hit weather API in production)
        if any(w in query_lower for w in ["weather", "temperature", "rain", "forecast"]):
            return {
                "response": "I'll fetch live weather data for you. In production, this connects to OpenWeatherMap or AccuWeather API.",
                "source": "web_intelligence",
                "action": "info",
            }

        # General web search simulation
        return {
            "response": f"I understand you're asking about '{query}'. In production, I'd search the web for the latest information. For now, I can check your business data or help with tasks.",
            "source": "web_intelligence",
            "action": "suggestions",
        }

    @staticmethod
    def _handle_time_query(query: str) -> dict:
        now = datetime.now()
        day_name = now.strftime("%A")
        date_str = now.strftime("%d %B %Y")
        time_str = now.strftime("%I:%M %p")

        if "date" in query:
            return {
                "response": f"Today is {day_name}, {date_str}.",
                "source": "web_intelligence",
                "action": "none",
            }

        return {
            "response": f"It's {time_str} on {day_name}, {date_str}.",
            "source": "web_intelligence",
            "action": "none",
        }

    @staticmethod
    def search_travel_info(destination: str) -> dict:
        """Get travel information for a destination (simulated web search)."""
        dest_lower = destination.lower().strip()

        # Known destinations from knowledge base
        knowledge = {
            "bali": {
                "weather": "Tropical, 27-32°C year-round. Dry season April-October.",
                "visa": "Visa-free for Indian nationals (30 days). Extendable.",
                "currency": "Indonesian Rupiah (IDR). 1 INR ≈ 190 IDR",
                "best_time": "April to October (dry season)",
                "tips": "Book airport transfer in advance. Download Gojek app.",
            },
            "thailand": {
                "weather": "Hot and humid, 25-35°C. Cool season November-February.",
                "visa": "Visa on arrival for Indian nationals (15 days, ₹2,000).",
                "currency": "Thai Baht (THB). 1 INR ≈ 0.42 THB",
                "best_time": "November to February",
                "tips": "Get a local SIM at airport. Use Grab for taxis.",
            },
            "maldives": {
                "weather": "Tropical, 28-32°C. Dry season December-April.",
                "visa": "Visa-free for Indian nationals (30 days).",
                "currency": "Maldivian Rufiyaa (MVR). USD widely accepted.",
                "best_time": "December to April",
                "tips": "Book resort transfers (speedboat/seaplane) in advance.",
            },
            "sri lanka": {
                "weather": "Tropical, 25-32°C. Best time varies by coast.",
                "visa": "ETA required (Online, $20-35).",
                "currency": "Sri Lankan Rupee (LKR). 1 INR ≈ 3.60 LKR",
                "best_time": "December to March (west/south), May-September (east)",
                "tips": "Hire a driver for the day — affordable and convenient.",
            },
            "dubai": {
                "weather": "Hot, 20-45°C. Best Nov-March.",
                "visa": "Visa on arrival for Indian nationals (14 days).",
                "currency": "UAE Dirham (AED). 1 INR ≈ 0.044 AED",
                "best_time": "November to March",
                "tips": "Book Burj Khalifa tickets in advance. Metro is excellent.",
            },
        }

        for key, info in knowledge.items():
            if key in dest_lower:
                text = f"📍 **{destination.title()} Travel Info**\n\n"
                text += f"🌤️ **Weather:** {info['weather']}\n"
                text += f"🛂 **Visa:** {info['visa']}\n"
                text += f"💵 **Currency:** {info['currency']}\n"
                text += f"📅 **Best Time:** {info['best_time']}\n"
                text += f"💡 **Tip:** {info['tips']}\n"
                return {"response": text, "source": "knowledge_base", "action": "info"}

        return {
            "response": f"I don't have detailed info on {destination} yet. I can search the web for the latest information in the next update.",
            "source": "web_intelligence",
            "action": "suggestions",
        }