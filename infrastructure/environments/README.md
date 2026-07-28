# SHUNYA Environment Configuration
# =============================================================================
# Load: source infrastructure/environments/<env>.env
# Priority: environment variables > .env file > defaults
#
# Required variables (must be set in every environment):
#   SECRET_KEY
#   DATABASE_URL
#
# Optional variables with secure defaults:
#   GUNICORN_WORKERS=4
#   LOG_LEVEL=INFO
#   MAX_CONTENT_LENGTH=16777216
#
# Secrets (never commit to source):
#   SECRET_KEY
#   DATABASE_URL (password)
#   SENTRY_DSN
#   TELEGRAM_BOT_TOKEN
#   HEALTH_TOKEN
# =============================================================================