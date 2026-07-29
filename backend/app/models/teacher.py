"""
app/models/teacher.py — compatibility shim
──────────────────────────────────────────
The canonical Teacher model now lives in app.models.people (Migration 005).
This file re-exports it so that legacy imports continue to work unchanged.
"""
from app.models.people import Teacher  # noqa: F401

__all__ = ["Teacher"]
