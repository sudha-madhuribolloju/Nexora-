"""
Notification service — CRUD for user notifications.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from fastapi import HTTPException, status

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate


class NotificationService:

    @staticmethod
    async def list_notifications(
        db: AsyncSession,
        recipient_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
    ) -> Tuple[int, int, List[Notification]]:
        q = select(Notification).where(Notification.recipient_id == recipient_id)
        if unread_only:
            q = q.where(Notification.is_read == False)
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        unread = (await db.execute(
            select(func.count(Notification.id)).where(
                Notification.recipient_id == recipient_id, Notification.is_read == False
            )
        )).scalar_one()
        notifications = (await db.execute(
            q.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        )).scalars().all()
        return total, unread, list(notifications)

    @staticmethod
    async def get_notification(db: AsyncSession, notification_id: uuid.UUID) -> Notification:
        result = await db.execute(select(Notification).where(Notification.id == notification_id))
        n = result.scalar_one_or_none()
        if not n:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        return n

    @staticmethod
    async def create_notification(
        db: AsyncSession, data: NotificationCreate, sender_id: Optional[uuid.UUID] = None
    ) -> Notification:
        n = Notification(**data.model_dump(), sender_id=sender_id)
        db.add(n)
        await db.commit()
        await db.refresh(n)
        return n

    @staticmethod
    async def mark_read(db: AsyncSession, notification_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Notification:
        n = await NotificationService.get_notification(db, notification_id)
        if user_id and n.recipient_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        n.is_read = True
        n.read_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(n)
        return n

    @staticmethod
    async def mark_all_read(db: AsyncSession, user_id: Optional[uuid.UUID] = None) -> int:
        q = update(Notification).where(Notification.is_read == False)
        if user_id:
            q = q.where(Notification.recipient_id == user_id)
        result = await db.execute(
            q.values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        await db.commit()
        return result.rowcount

    @staticmethod
    async def delete_notification(db: AsyncSession, notification_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> None:
        n = await NotificationService.get_notification(db, notification_id)
        if user_id and n.recipient_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        await db.delete(n)
        await db.commit()
