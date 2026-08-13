import json
import logging
import sys
from typing import Dict, Any
from app.core.config import settings

SENSITIVE_KEYS = {"api_key", "password", "secret", "authorization", "auth_token", "access_token", "credentials", "private_key"}



def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively strip or redact sensitive keys from structured dictionaries."""
    sanitized = {}
    for k, v in data.items():
        if any(s in k.lower() for s in SENSITIVE_KEYS):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_dict(v)
        else:
            sanitized[k] = v
    return sanitized


def log_observability(self, event_name: str, payload: Dict[str, Any]):
    sanitized = sanitize_dict(payload)
    log_entry = {
        "event": event_name,
        "data": sanitized
    }
    self.info(f"[OBSERVABILITY] {json.dumps(log_entry)}")


# Attach log_observability to standard Logger class
logging.Logger.log_observability = log_observability


def setup_logging() -> logging.Logger:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Suppress verbose third party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)

    logger = logging.getLogger("load2ask")
    logger.info(f"Logging initialized with level: {settings.LOG_LEVEL}")
    return logger


logger = setup_logging()


