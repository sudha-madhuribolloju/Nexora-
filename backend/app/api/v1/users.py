import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Retrieve profile details for the currently authenticated user.
    """
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update profile details for the currently authenticated user in PostgreSQL.
    """
    return await AuthService.update_user(db=db, db_user=current_user, user_in=user_in)

@router.get("/teachers")
async def get_teachers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve list of teachers/instructors from PostgreSQL.
    """
    try:
        result = await db.execute(
            select(User).where(User.is_deleted == False)
        )
        all_users = result.scalars().all()
        teachers = [u for u in all_users if u.role and ("teacher" in u.role.lower() or "admin" in u.role.lower())]
        if not teachers:
            teachers = [current_user]
    except Exception:
        teachers = [current_user]

    data = [
        {
            "id": str(t.id),
            "email": t.email,
            "first_name": t.first_name,
            "last_name": t.last_name,
            "fullName": f"{t.first_name or ''} {t.last_name or ''}".strip() or t.email,
            "role": t.role,
            "department": getattr(t, "department", "General Academics"),
            "voice_print_id": getattr(t, "voice_print_id", "Not registered")
        }
        for t in teachers
    ]
    return {"status": "success", "data": data}

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update profile details for a specific user ID or current user.
    """
    if current_user.id != user_id and current_user.role not in ["super_admin", "school_admin", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this profile."
        )
    target_user = current_user if current_user.id == user_id else await UserRepository.get_by_id(db, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return await AuthService.update_user(db=db, db_user=target_user, user_in=user_in)
