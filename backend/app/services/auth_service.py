import uuid
import random
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User
from app.models.otp import EmailOTP
from app.services.email_service import EmailService

logger = logging.getLogger("app.services.auth_service")



class AuthService:
    """
    Service layer containing core business logic for user registration,
    email verification, authentication, and token management.
    """

    @staticmethod
    async def register_user(db: AsyncSession, user_in: UserCreate) -> Dict[str, Any]:
        """
        Registers a new user account.
        
        When EMAIL_VERIFICATION_REQUIRED is False (Development):
          • User account is automatically activated and email marked verified.
          • OTP generation and email sending are skipped.
          • Returns verification_required = False.
        
        When EMAIL_VERIFICATION_REQUIRED is True (Production):
          • User account is created with is_verified = False.
          • A 6-digit OTP is generated, saved in DB, and sent via EmailService.
          • Returns verification_required = True.
        """
        # Validate email uniqueness
        existing_user = await UserRepository.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists."
            )

        hashed_password = get_password_hash(user_in.password)

        first_name = None
        last_name = None
        if user_in.full_name:
            parts = user_in.full_name.strip().split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

        if settings.EMAIL_VERIFICATION_REQUIRED:
            # Production: Require OTP Verification
            user = await UserRepository.create_user(
                db=db,
                email=user_in.email,
                hashed_password=hashed_password,
                role=user_in.role,
                is_active=False,
                is_verified=False,
                first_name=first_name,
                last_name=last_name
            )

            # Generate 6-digit OTP
            otp_code = str(random.randint(100000, 999999))
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

            otp_record = EmailOTP(
                email=user.email,
                otp_code=otp_code,
                expires_at=expires_at,
                is_used=False
            )
            db.add(otp_record)
            await db.commit()

            # Dispatch Email
            await EmailService.send_verification_otp(user.email, otp_code)

            return {
                "verification_required": True,
                "message": "Registration successful. Please verify your email with the 6-digit OTP sent to your inbox.",
                "user": user,
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name
            }
        else:
            # Development: Auto-activate and skip verification
            user = await UserRepository.create_user(
                db=db,
                email=user_in.email,
                hashed_password=hashed_password,
                role=user_in.role,
                is_active=True,
                is_verified=True,
                first_name=first_name,
                last_name=last_name
            )

            return {
                "verification_required": False,
                "message": "Registration successful. You may now log in.",
                "user": user,
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name
            }

    @staticmethod
    async def authenticate(db: AsyncSession, credentials: LoginRequest) -> Token:
        """
        Authenticates user credentials.
        
        If EMAIL_VERIFICATION_REQUIRED is True and email is not verified:
          • Raises HTTP 403 Forbidden: {"detail": "Please verify your email before logging in."}
        """
        user = await UserRepository.get_by_email(db, email=credentials.email)
        logger.info(f"Login Email: {credentials.email}")
        logger.info(f"User Found: {user is not None}")

        # Raise 401 if user not found
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"DB Email: {user.email}")
        logger.info(f"Is Active: {user.is_active}")
        logger.info(f"Is Verified: {user.is_verified}")

        # Verify password
        password_ok = verify_password(credentials.password, user.hashed_password)
        logger.info(f"Password Match: {password_ok}")

        if not password_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check Email Verification requirement if enabled
        if settings.EMAIL_VERIFICATION_REQUIRED and not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before logging in."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is inactive."
            )

        access_token = create_access_token(subject=user.id, role=user.role, email=user.email)
        refresh_token = create_refresh_token(subject=user.id)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    @staticmethod
    async def verify_email_otp(db: AsyncSession, email: str, otp_code: str) -> Dict[str, Any]:
        """
        Verifies 6-digit OTP and activates the user account.
        """
        if not settings.EMAIL_VERIFICATION_REQUIRED:
            return {
                "status": "success",
                "message": "Email verification is disabled in development environment.",
                "verified": True
            }

        stmt = (
            select(EmailOTP)
            .where(
                EmailOTP.email == email,
                EmailOTP.otp_code == otp_code,
                EmailOTP.is_used == False,
                EmailOTP.expires_at > datetime.now(timezone.utc)
            )
            .order_by(desc(EmailOTP.created_at))
        )
        result = await db.execute(stmt)
        otp_record = result.scalar_one_or_none()

        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code."
            )

        otp_record.is_used = True

        user = await UserRepository.get_by_email(db, email=email)
        if user:
            user.is_verified = True
            user.is_active = True

        await db.commit()
        return {
            "status": "success",
            "message": "Email verified successfully. Account activated.",
            "verified": True
        }

    @staticmethod
    async def resend_otp(db: AsyncSession, email: str) -> Dict[str, Any]:
        """
        Resends a new 6-digit OTP code if verification is required.
        """
        if not settings.EMAIL_VERIFICATION_REQUIRED:
            return {
                "status": "success",
                "message": "Email verification is disabled in development environment."
            }

        user = await UserRepository.get_by_email(db, email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found."
            )

        if user.is_verified:
            return {
                "status": "info",
                "message": "Email is already verified."
            }

        otp_code = str(random.randint(100000, 999999))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        otp_record = EmailOTP(
            email=user.email,
            otp_code=otp_code,
            expires_at=expires_at,
            is_used=False
        )
        db.add(otp_record)
        await db.commit()

        await EmailService.send_verification_otp(user.email, otp_code)
        return {
            "status": "success",
            "message": "A new verification code has been dispatched to your email."
        }

    @staticmethod
    async def refresh_session(db: AsyncSession, refresh_token: str) -> Token:
        payload = decode_access_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        try:
            user_id = uuid.UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in token",
            )

        user = await UserRepository.get_by_id(db, user_id=user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        new_access_token = create_access_token(subject=user.id, role=user.role, email=user.email)
        new_refresh_token = create_refresh_token(subject=user.id)

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    @staticmethod
    async def logout(token: str) -> None:
        return None

    @staticmethod
    async def update_user(db: AsyncSession, db_user: User, user_in: UserUpdate) -> User:
        updates = user_in.model_dump(exclude_unset=True)

        if "password" in updates:
            password = updates.pop("password")
            if password:
                updates["hashed_password"] = get_password_hash(password)

        if "full_name" in updates:
            full_name = updates.pop("full_name")
            if full_name:
                parts = full_name.strip().split(" ", 1)
                updates["first_name"] = parts[0]
                updates["last_name"] = parts[1] if len(parts) > 1 else ""

        if "email" in updates and updates["email"] != db_user.email:
            existing_user = await UserRepository.get_by_email(db, email=updates["email"])
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A user with this email already exists."
                )

        return await UserRepository.update_user(db, db_user=db_user, updates=updates)