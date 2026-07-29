import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, computed_field

class UserBase(BaseModel):
    """
    Base properties shared by all user schemas.
    """
    email: EmailStr
    role: str = "Student"
    is_active: bool = True

class UserCreate(UserBase):
    """
    Schema for user registration / creation.
    Requires password validation with at least 6 characters.
    """
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters long")
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

class UserUpdate(BaseModel):
    """
    Schema for updating user details. All fields are optional.
    """
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6, description="New password if updating")
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    """
    Schema representing user profile details returned by API endpoints.
    Uses Pydantic v2 from_attributes configuration for ORM mapping.
    """
    id: uuid.UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    @computed_field
    @property
    def full_name(self) -> str:
        parts = filter(None, [self.first_name, self.last_name])
        name = " ".join(parts).strip()
        return name if name else self.email.split("@")[0]

    model_config = ConfigDict(from_attributes=True)

class RegisterResponse(BaseModel):
    verification_required: bool
    message: str
    id: Optional[uuid.UUID] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)

class ResendOTPRequest(BaseModel):
    email: EmailStr

