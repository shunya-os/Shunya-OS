"""Shunya OS — Configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "shunya-dev-key-change-in-production")
    DB_PASS = os.getenv("DB_PASSWORD", "shunya")
    DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql://shunya:{DB_PASS}@localhost:5432/shunya_os")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB upload

    # Auth
    JWT_SECRET = os.getenv("JWT_SECRET", SECRET_KEY)
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    MAGIC_LINK_EXPIRY_MINUTES = 15
    OTP_EXPIRY_MINUTES = 5

    # Multi-tenant
    DEFAULT_TENANT_PLAN = "free"

    # AI / Memory
    HONCHO_ENABLED = True
    KNOWLEDGE_PIPELINE_ENABLED = True
    CONFIDENCE_THRESHOLD = 0.6  # below this, AI flags uncertainty

    # Channels
    WHATSAPP_API_URL = None
    TELEGRAM_BOT_TOKEN = None
    SMTP_SERVER = None

    # Storage
    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")

    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100/hour"

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {"development": DevelopmentConfig, "production": ProductionConfig}
