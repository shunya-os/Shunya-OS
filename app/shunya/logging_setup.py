"""Structured logging for Shunya OS."""
import logging
import json
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logging(app):
    """Configure structured logging with file and console handlers."""
    
    log_level = getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    
    # JSON formatter for production
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if hasattr(record, "tenant_id"):
                log_entry["tenant_id"] = record.tenant_id
            if hasattr(record, "user_id"):
                log_entry["user_id"] = record.user_id
            if hasattr(record, "entity_type"):
                log_entry["entity_type"] = record.entity_type
            if hasattr(record, "duration_ms"):
                log_entry["duration_ms"] = record.duration_ms
            if record.exc_info and record.exc_info[0]:
                log_entry["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_entry, default=str)
    
    # Ensure log directory exists
    log_dir = "/var/log/shunya"
    os.makedirs(log_dir, exist_ok=True)
    
    # File handler (JSON format)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "shunya.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JsonFormatter())
    
    # Console handler (human-readable)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    
    # Configure root logger
    root = logging.getLogger()
    root.setLevel(log_level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    
    # App-specific logger
    logger = logging.getLogger("shunya")
    logger.setLevel(log_level)
    
    app.logger = logger
    app.config["SHUNYA_LOGGER"] = logger
    
    return logger


def get_logger(name="shunya"):
    """Get a logger with shunya prefix."""
    return logging.getLogger(name)