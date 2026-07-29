from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.database.database import get_db
from app.schemas.auth import LoginRequest, Token, RefreshTokenRequest
from app.schemas.user import UserCreate, UserResponse, RegisterResponse, VerifyOTPRequest, ResendOTPRequest
from app.services.auth_service import AuthService
from app.core.security import get_current_user, oauth2_scheme
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user account.
    Returns verification_required = False when EMAIL_VERIFICATION_REQUIRED=False (Dev).
    Returns verification_required = True when EMAIL_VERIFICATION_REQUIRED=True (Prod).
    """
    return await AuthService.register_user(db=db, user_in=user_in)


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    payload: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Verify 6-digit email OTP and activate user account.
    """
    return await AuthService.verify_email_otp(db=db, email=payload.email, otp_code=payload.code)


@router.post("/resend-otp", status_code=status.HTTP_200_OK)
async def resend_otp(
    payload: ResendOTPRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Resend a fresh 6-digit email OTP verification code.
    """
    return await AuthService.resend_otp(db=db, email=payload.email)


@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Authenticate user credentials (email & password) and return signed JWT access and refresh tokens.
    Returns HTTP 403 if EMAIL_VERIFICATION_REQUIRED=True and email is unverified.
    """
    return await AuthService.authenticate(db=db, credentials=credentials)


@router.post("/refresh", response_model=Token)
async def refresh(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Refresh the access token using a valid refresh token.
    """
    return await AuthService.refresh_session(db=db, refresh_token=payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Log out and invalidate session token.
    """
    await AuthService.logout(token)
    return {"status": "success", "message": "Successfully logged out."}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Retrieve profile details for the currently authenticated user.
    """
    return current_user
