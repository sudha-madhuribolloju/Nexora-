import logging
import logging.config
import sys
from typing import Any, Dict
from app.core.config import settings

def setup_logging() -> None:
    """
    Configures structured logging for Nexora AI.
    Uses basic stdout formatting in development, and detailed structured formatting in production.
    """
    log_level = logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG
    
    # Define logging configuration
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "production": {
                "format": '{"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
                "datefmt": "%Y-%m-%dT%H:%M:%SZ",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "production" if settings.ENVIRONMENT == "production" else "default",
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
        "loggers": {
            "uvicorn": {
                "level": logging.INFO,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": logging.INFO,
                "propagate": True,
            },
            "uvicorn.access": {
                "level": logging.INFO,
                "handlers": ["console"],
                "propagate": False,
            },
        }
    }
    
    # Configure logging module
    logging.config.dictConfig(logging_config)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized in {settings.ENVIRONMENT} mode.")
