"""
Notifications router — user notification management.
"""
import uuid
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationCreate, NotificationResponse, NotificationListResponse,
)

router = APIRouter()


@router.get("/", response_model=NotificationListResponse, summary="List notifications")
async def list_notifications(
    recipient_id: uuid.UUID = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve paginated notifications for a recipient user.
    """
    total, unread, notifications = await NotificationService.list_notifications(
        db, recipient_id, skip, limit, unread_only
    )
    return NotificationListResponse(total=total, unread_count=unread, skip=skip, limit=limit, data=notifications)


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED, summary="Create a notification")
async def create_notification(
    data: NotificationCreate,
    sender_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Send a notification to a user.
    """
    return await NotificationService.create_notification(db, data, sender_id=sender_id)


@router.get("/{notification_id}", response_model=NotificationResponse, summary="Get notification by ID")
async def get_notification(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve a specific notification by ID.
    """
    return await NotificationService.get_notification(db, notification_id)


@router.put("/read-all", summary="Mark all notifications as read")
async def mark_all_read(
    user_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Mark all unread notifications for a user as read.
    """
    count = await NotificationService.mark_all_read(db, user_id)
    return {"status": "success", "message": f"{count} notification(s) marked as read"}


@router.put("/{notification_id}/read", response_model=NotificationResponse, summary="Mark notification as read")
async def mark_read(
    notification_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Mark a single notification as read.
    """
    return await NotificationService.mark_read(db, notification_id, user_id)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete notification")
async def delete_notification(
    notification_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a notification.
    """
    await NotificationService.delete_notification(db, notification_id, user_id)
