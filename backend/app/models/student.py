"""
app/models/student.py — compatibility shim
──────────────────────────────────────────
The canonical Student model now lives in app.models.people (Migration 005).
This file re-exports it so that legacy imports (services, routes, agents) that
use `from app.models.student import Student` continue to work unchanged.
"""
from app.models.people import Student  # noqa: F401

__all__ = ["Student"]
