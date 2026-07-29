from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.api.dependencies import get_db, get_current_user, oauth2_scheme
from app.services.auth_service import AuthService
from app.schemas.auth import Token, LoginSchema, RefreshTokenRequest
from app.schemas.user import UserResponse, UserCreate, RegisterResponse, VerifyOTPRequest, ResendOTPRequest
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user profile.
    Returns verification_required = False when EMAIL_VERIFICATION_REQUIRED=False (Dev).
    Returns verification_required = True when EMAIL_VERIFICATION_REQUIRED=True (Prod).
    """
    return await AuthService.register_user(db, user_in)


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
    credentials: LoginSchema,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Log in using email and password. Returns access token and refresh token.
    Returns HTTP 403 if EMAIL_VERIFICATION_REQUIRED=True and email is unverified.
    """
    return await AuthService.authenticate(db, credentials)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Log out and invalidate the session.
    """
    await AuthService.logout(token)
    return {"status": "success", "message": "Successfully logged out."}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get the currently authenticated user profile.
    """
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh the session token using a valid refresh token.
    """
    return await AuthService.refresh_session(db, payload.refresh_token)
