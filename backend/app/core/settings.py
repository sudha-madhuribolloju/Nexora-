"""
app/core/settings.py
────────────────────
Re-exports settings object from app.core.config for direct module imports.
"""
from app.core.config import settings

GEMINI_API_KEY = settings.GEMINI_API_KEY
GEMINI_MODEL = settings.GEMINI_MODEL

__all__ = ["settings", "GEMINI_API_KEY", "GEMINI_MODEL"]
