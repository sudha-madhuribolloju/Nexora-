"""
app/schemas/people.py
──────────────────────
Pydantic v2 schemas for Student, Teacher, Parent, and ParentStudentLink
API endpoints.

Design decisions:
  • StudentCreate requires user_id + school_id in the body. The section_id is
    optional — a student can be admitted before section placement.
  • TeacherCreate requires user_id + school_id. employee_id is optional (can
    be auto-assigned later).
  • ParentCreate only requires user_id. Parents are not directly school-scoped —
    school context is implicit through their linked students.
  • ParentStudentLinkCreate is a separate schema for the M2M join endpoint.
  • All *Response schemas include is_deleted + timestamps following the
    established pattern from academic.py / school.py.
  • StudentWithUser / TeacherWithUser embed a lightweight UserSummary to avoid
    N+1 queries on list endpoints (populated via selectinload in the service).
"""

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ══════════════════════════════════════════════════════════════════════════════
# SHARED: lightweight user summary for embedding
# ══════════════════════════════════════════════════════════════════════════════

class UserSummary(BaseModel):
    """Minimal user fields embedded in profile responses."""
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    email:      str
    first_name: Optional[str] = None
    last_name:  Optional[str] = None
    phone:      Optional[str] = None
    avatar_url: Optional[str] = None
    role:       str
    is_active:  bool


# ══════════════════════════════════════════════════════════════════════════════
# STUDENT SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class StudentBase(BaseModel):
    admission_number: Optional[str]  = Field(None, max_length=50, examples=["ADM-2026-001"])
    roll_number:      Optional[str]  = Field(None, max_length=20, examples=["10-A-01"])
    admission_date:   Optional[date] = None
    date_of_birth:    Optional[date] = None
    gender:           Optional[str]  = Field(None, max_length=20, examples=["Female"])
    blood_group:      Optional[str]  = Field(None, max_length=5,  examples=["O+"])
    nationality:      Optional[str]  = Field(None, max_length=100)
    address_line1:    Optional[str]  = Field(None, max_length=255)
    address_line2:    Optional[str]  = Field(None, max_length=255)
    city:             Optional[str]  = Field(None, max_length=100)
    state:            Optional[str]  = Field(None, max_length=100)
    postal_code:      Optional[str]  = Field(None, max_length=20)
    is_active:        bool           = True
    remarks:          Optional[str]  = None


class StudentCreate(StudentBase):
    """
    Create a student profile. The corresponding User must already exist
    with role='student'.
    """
    user_id:    uuid.UUID
    school_id:  uuid.UUID
    section_id: Optional[uuid.UUID] = None


class StudentUpdate(BaseModel):
    """Partial update — all fields optional."""
    section_id:       Optional[uuid.UUID] = None
    admission_number: Optional[str]       = Field(None, max_length=50)
    roll_number:      Optional[str]       = Field(None, max_length=20)
    admission_date:   Optional[date]      = None
    date_of_birth:    Optional[date]      = None
    gender:           Optional[str]       = Field(None, max_length=20)
    blood_group:      Optional[str]       = Field(None, max_length=5)
    nationality:      Optional[str]       = Field(None, max_length=100)
    address_line1:    Optional[str]       = Field(None, max_length=255)
    address_line2:    Optional[str]       = Field(None, max_length=255)
    city:             Optional[str]       = Field(None, max_length=100)
    state:            Optional[str]       = Field(None, max_length=100)
    postal_code:      Optional[str]       = Field(None, max_length=20)
    is_active:        Optional[bool]      = None
    remarks:          Optional[str]       = None


class StudentResponse(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    user_id:    uuid.UUID
    school_id:  uuid.UUID
    section_id: Optional[uuid.UUID] = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class StudentWithUser(StudentResponse):
    """Student with embedded user summary (for detail / list endpoints)."""
    user: Optional[UserSummary] = None


# ══════════════════════════════════════════════════════════════════════════════
# TEACHER SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class TeacherBase(BaseModel):
    employee_id:      Optional[str]  = Field(None, max_length=50,  examples=["EMP-001"])
    department:       Optional[str]  = Field(None, max_length=100, examples=["Science"])
    qualification:    Optional[str]  = Field(None, max_length=255, examples=["M.Sc Physics"])
    specialization:   Optional[str]  = Field(None, max_length=255, examples=["Quantum Physics"])
    joining_date:     Optional[date] = None
    is_class_teacher: bool           = False
    date_of_birth:    Optional[date] = None
    gender:           Optional[str]  = Field(None, max_length=20)
    is_active:        bool           = True
    remarks:          Optional[str]  = None


class TeacherCreate(TeacherBase):
    """
    Create a teacher profile. The corresponding User must already exist
    with role='teacher'.
    """
    user_id:   uuid.UUID
    school_id: uuid.UUID


class TeacherUpdate(BaseModel):
    """Partial update — all fields optional."""
    employee_id:      Optional[str]  = Field(None, max_length=50)
    department:       Optional[str]  = Field(None, max_length=100)
    qualification:    Optional[str]  = Field(None, max_length=255)
    specialization:   Optional[str]  = Field(None, max_length=255)
    joining_date:     Optional[date] = None
    is_class_teacher: Optional[bool] = None
    date_of_birth:    Optional[date] = None
    gender:           Optional[str]  = Field(None, max_length=20)
    is_active:        Optional[bool] = None
    remarks:          Optional[str]  = None


class TeacherResponse(TeacherBase):
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    user_id:    uuid.UUID
    school_id:  uuid.UUID
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class TeacherWithUser(TeacherResponse):
    """Teacher with embedded user summary (for detail / list endpoints)."""
    user: Optional[UserSummary] = None


# ══════════════════════════════════════════════════════════════════════════════
# PARENT SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class ParentBase(BaseModel):
    relation_type:   Optional[str] = Field(None, max_length=50,  examples=["Father"])
    occupation:      Optional[str] = Field(None, max_length=100, examples=["Engineer"])
    address_line1:   Optional[str] = Field(None, max_length=255)
    address_line2:   Optional[str] = Field(None, max_length=255)
    city:            Optional[str] = Field(None, max_length=100)
    state:           Optional[str] = Field(None, max_length=100)
    postal_code:     Optional[str] = Field(None, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)


class ParentCreate(ParentBase):
    """
    Create a parent profile. The corresponding User must already exist
    with role='parent'.
    """
    user_id: uuid.UUID


class ParentUpdate(BaseModel):
    """Partial update — all fields optional."""
    relation_type:   Optional[str] = Field(None, max_length=50)
    occupation:      Optional[str] = Field(None, max_length=100)
    address_line1:   Optional[str] = Field(None, max_length=255)
    address_line2:   Optional[str] = Field(None, max_length=255)
    city:            Optional[str] = Field(None, max_length=100)
    state:           Optional[str] = Field(None, max_length=100)
    postal_code:     Optional[str] = Field(None, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)


class ParentResponse(ParentBase):
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    user_id:    uuid.UUID
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class ParentWithUser(ParentResponse):
    """Parent with embedded user summary."""
    user: Optional[UserSummary] = None


# ══════════════════════════════════════════════════════════════════════════════
# PARENT-STUDENT LINK SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class ParentStudentLinkCreate(BaseModel):
    """Create or update a parent ↔ student relationship."""
    parent_id:          uuid.UUID
    student_id:         uuid.UUID
    is_primary_contact: bool = False


class ParentStudentLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:                 uuid.UUID
    parent_id:          uuid.UUID
    student_id:         uuid.UUID
    is_primary_contact: bool
    created_at:         datetime
    updated_at:         datetime


class StudentWithParents(StudentResponse):
    """Student detail with embedded parent links."""
    parent_links: List[ParentStudentLinkResponse] = []
