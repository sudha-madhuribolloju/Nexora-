"""
app/schemas/academic.py
────────────────────────
Pydantic v2 schemas for Class, Section, and Subject API endpoints.

Design decisions:
  • ClassCreate requires school_id + academic_year_id in the body rather than
    as path parameters to keep the route flat (/academic/classes/) and allow
    bulk creation in future.
  • SectionCreate only requires class_id + name; school_id is resolved server-
    side from the parent class to avoid client-side drift.
  • SubjectCreate requires a school_id so subjects can be created independently
    of any specific class or year.
  • color is validated to be a 7-character hex string ("#RRGGBB") via a
    field validator to prevent storing arbitrary strings in the colour column.
  • ClassWithSections embeds the sections list for the class-detail endpoint
    avoiding a separate round-trip.
"""

import re
import uuid
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# CLASS SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class ClassBase(BaseModel):
    name:             str           = Field(..., max_length=50,  examples=["Grade 10"])
    grade_level:      Optional[int] = Field(None, ge=0, le=20,  examples=[10])
    description:      Optional[str] = None


class ClassCreate(ClassBase):
    """Payload to create a class. school_id + academic_year_id are required."""
    school_id:        uuid.UUID
    academic_year_id: uuid.UUID


class ClassUpdate(BaseModel):
    """Partial update — all fields optional."""
    name:        Optional[str] = Field(None, max_length=50)
    grade_level: Optional[int] = Field(None, ge=0, le=20)
    description: Optional[str] = None


class ClassResponse(ClassBase):
    model_config = ConfigDict(from_attributes=True)

    id:               uuid.UUID
    school_id:        uuid.UUID
    academic_year_id: uuid.UUID
    is_deleted:       bool
    created_at:       datetime
    updated_at:       datetime


class ClassWithSections(ClassResponse):
    """Class detail response with embedded sections."""
    sections: List["SectionResponse"] = []


# ══════════════════════════════════════════════════════════════════════════════
# SECTION SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class SectionBase(BaseModel):
    name:        str           = Field(..., max_length=10, examples=["A"])
    capacity:    Optional[int] = Field(None, ge=1, le=500, examples=[40])
    room_number: Optional[str] = Field(None, max_length=20, examples=["101"])


class SectionCreate(SectionBase):
    """Payload to create a section under a class."""
    class_id:         uuid.UUID
    class_teacher_id: Optional[uuid.UUID] = None


class SectionUpdate(BaseModel):
    name:             Optional[str]       = Field(None, max_length=10)
    capacity:         Optional[int]       = Field(None, ge=1, le=500)
    room_number:      Optional[str]       = Field(None, max_length=20)
    class_teacher_id: Optional[uuid.UUID] = None


class SectionResponse(SectionBase):
    model_config = ConfigDict(from_attributes=True)

    id:               uuid.UUID
    class_id:         uuid.UUID
    school_id:        uuid.UUID
    class_teacher_id: Optional[uuid.UUID] = None
    is_deleted:       bool
    created_at:       datetime
    updated_at:       datetime


# ══════════════════════════════════════════════════════════════════════════════
# SUBJECT SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class SubjectBase(BaseModel):
    name:        str             = Field(..., max_length=255, examples=["Mathematics"])
    code:        str             = Field(..., max_length=20,  examples=["MATH"])
    description: Optional[str]  = None
    credits:     Optional[Decimal] = Field(None, ge=0, le=99.9, examples=[5.0])
    color:       Optional[str]  = Field(None, max_length=7, examples=["#4F46E5"])
    is_elective: bool           = False

    @field_validator("color", mode="before")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not _HEX_RE.match(v):
            raise ValueError("color must be a valid hex string, e.g. '#4F46E5'.")
        return v

    @field_validator("code", mode="before")
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()


class SubjectCreate(SubjectBase):
    """Payload to create a subject. school_id is required."""
    school_id: uuid.UUID


class SubjectUpdate(BaseModel):
    name:        Optional[str]     = Field(None, max_length=255)
    description: Optional[str]    = None
    credits:     Optional[Decimal] = Field(None, ge=0, le=99.9)
    color:       Optional[str]    = Field(None, max_length=7)
    is_elective: Optional[bool]   = None

    @field_validator("color", mode="before")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not _HEX_RE.match(v):
            raise ValueError("color must be a valid hex string, e.g. '#4F46E5'.")
        return v


class SubjectResponse(SubjectBase):
    model_config = ConfigDict(from_attributes=True)

    id:        uuid.UUID
    school_id: uuid.UUID
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


# Resolve forward references
ClassWithSections.model_rebuild()
