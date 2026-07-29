import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    """
    Schema for login request payload containing email and password.
    """
    email: EmailStr
    password: str

# Alias for backwards compatibility
LoginSchema = LoginRequest

class RefreshTokenRequest(BaseModel):
    """
    Schema for refreshing access tokens.
    """
    refresh_token: str

class Token(BaseModel):
    """
    Schema representing the access token response.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """
    Schema representing decoded data stored in the JWT access token.
    """
    id: Optional[uuid.UUID] = None
    email: Optional[str] = None
