"""
app/schemas/school.py
──────────────────────
Pydantic v2 schemas for School and AcademicYear API endpoints.

Design decisions:
  • SchoolCreate requires `name` and `code` only — all other fields are optional
    so a school can be onboarded quickly and filled in later.
  • SchoolUpdate is fully optional (PATCH semantics) so frontends only send
    changed fields — avoids accidental nullification of untouched columns.
  • AcademicYearCreate validates start_date < end_date at the Pydantic layer
    so the DB never receives an inverted date range.
  • SubscriptionTier is a Python enum in the schema layer — documents valid
    values in the OpenAPI spec and validates input before it hits the DB.
  • SchoolSummary is a lightweight version for list endpoints (no nested years)
    to avoid N+1 hydration of academic_years on every list call.
"""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ── Enums ──────────────────────────────────────────────────────────────────────

class SubscriptionTier(str, Enum):
    FREE       = "free"
    BASIC      = "basic"
    PRO        = "pro"
    ENTERPRISE = "enterprise"


# ══════════════════════════════════════════════════════════════════════════════
# ACADEMIC YEAR SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class AcademicYearBase(BaseModel):
    name:       str  = Field(..., max_length=100, examples=["2025-2026"])
    start_date: date = Field(..., examples=["2025-06-01"])
    end_date:   date = Field(..., examples=["2026-03-31"])
    is_current: bool = Field(default=False)

    @model_validator(mode="after")
    def end_after_start(self) -> "AcademicYearBase":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date.")
        return self


class AcademicYearCreate(AcademicYearBase):
    """Payload to create an academic year under a school."""
    pass


class AcademicYearUpdate(BaseModel):
    """Partial update — only supplied fields are applied."""
    name:       Optional[str]  = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date:   Optional[date] = None
    is_current: Optional[bool] = None

    @model_validator(mode="after")
    def end_after_start(self) -> "AcademicYearUpdate":
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date.")
        return self


class AcademicYearResponse(AcademicYearBase):
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    school_id:  uuid.UUID
    created_at: datetime
    updated_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
# SCHOOL SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class SchoolBase(BaseModel):
    name:              str                        = Field(..., max_length=255, examples=["Greenwood High School"])
    code:              str                        = Field(..., max_length=20,  examples=["GHS001"])
    email:             Optional[str]              = Field(None, max_length=255)
    phone:             Optional[str]              = Field(None, max_length=20)
    address_line1:     Optional[str]              = Field(None, max_length=255)
    address_line2:     Optional[str]              = Field(None, max_length=255)
    city:              Optional[str]              = Field(None, max_length=100)
    state:             Optional[str]              = Field(None, max_length=100)
    country:           str                        = Field(default="India",          max_length=100)
    postal_code:       Optional[str]              = Field(None, max_length=20)
    timezone:          str                        = Field(default="Asia/Kolkata",   max_length=50)
    logo_url:          Optional[str]              = None
    website:           Optional[str]              = Field(None, max_length=255)
    subscription_tier: SubscriptionTier           = SubscriptionTier.FREE
    is_active:         bool                       = True


class SchoolCreate(SchoolBase):
    """Payload to create a new school. Only name + code are required."""
    pass


class SchoolUpdate(BaseModel):
    """Partial update — all fields optional (PATCH semantics)."""
    name:              Optional[str]              = Field(None, max_length=255)
    email:             Optional[str]              = Field(None, max_length=255)
    phone:             Optional[str]              = Field(None, max_length=20)
    address_line1:     Optional[str]              = None
    address_line2:     Optional[str]              = None
    city:              Optional[str]              = Field(None, max_length=100)
    state:             Optional[str]              = Field(None, max_length=100)
    country:           Optional[str]              = Field(None, max_length=100)
    postal_code:       Optional[str]              = Field(None, max_length=20)
    timezone:          Optional[str]              = Field(None, max_length=50)
    logo_url:          Optional[str]              = None
    website:           Optional[str]              = Field(None, max_length=255)
    subscription_tier: Optional[SubscriptionTier] = None
    is_active:         Optional[bool]             = None


class SchoolSummary(BaseModel):
    """Lightweight school object for list endpoints — no nested years."""
    model_config = ConfigDict(from_attributes=True)

    id:                uuid.UUID
    name:              str
    code:              str
    city:              Optional[str]
    country:           str
    subscription_tier: str
    is_active:         bool
    created_at:        datetime


class SchoolResponse(SchoolBase):
    """Full school detail response."""
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool


class SchoolWithAcademicYears(SchoolResponse):
    """School detail with embedded academic years list."""
    academic_years: List[AcademicYearResponse] = []
