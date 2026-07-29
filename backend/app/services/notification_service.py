import uuid
import logging
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from fastapi import HTTPException, status

from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationCreate

logger = logging.getLogger("app.services.notification_service")


class NotificationService:

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        data: NotificationCreate,
        sender_id: Optional[uuid.UUID] = None
    ) -> Notification:
        notif = Notification(
            recipient_id=data.recipient_id,
            sender_id=sender_id,
            title=data.title,
            message=data.message,
            notification_type=data.notification_type,
            is_read=False,
            status="unread",
            action_url=data.action_url
        )
        db.add(notif)
        await db.commit()
        await db.refresh(notif)

        # Log email notification dispatch trigger
        logger.info(f"[Email Dispatch] To Recipient {data.recipient_id}: '{data.title}'")
        return notif

    @staticmethod
    async def list_notifications(
        db: AsyncSession,
        recipient_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False
    ) -> Tuple[int, int, List[Notification]]:
        q = select(Notification).where(Notification.recipient_id == recipient_id, Notification.status != "deleted")
        if unread_only:
            q = q.where(Notification.is_read == False)

        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one() or 0
        
        unread_stmt = select(func.count(Notification.id)).where(
            Notification.recipient_id == recipient_id,
            Notification.is_read == False,
            Notification.status != "deleted"
        )
        unread_count = (await db.execute(unread_stmt)).scalar_one() or 0

        res = await db.execute(q.order_by(desc(Notification.created_at)).offset(skip).limit(limit))
        return total, unread_count, list(res.scalars().all())

    @staticmethod
    async def get_notification(
        db: AsyncSession,
        notification_id: uuid.UUID
    ) -> Notification:
        res = await db.execute(select(Notification).where(Notification.id == notification_id))
        notif = res.scalar_one_or_none()
        if not notif:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        return notif

    @staticmethod
    async def mark_read(
        db: AsyncSession,
        notification_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> Notification:
        notif = await NotificationService.get_notification(db, notification_id)
        if user_id and notif.recipient_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this notification")
        notif.is_read = True
        notif.status = "read"
        notif.read_at = datetime.utcnow()
        await db.commit()
        await db.refresh(notif)
        return notif

    @staticmethod
    async def mark_all_read(
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None
    ) -> int:
        stmt = select(Notification).where(Notification.is_read == False)
        if user_id:
            stmt = stmt.where(Notification.recipient_id == user_id)
        res = await db.execute(stmt)
        notifs = list(res.scalars().all())
        now = datetime.utcnow()
        for n in notifs:
            n.is_read = True
            n.status = "read"
            n.read_at = now
        await db.commit()
        return len(notifs)

    @staticmethod
    async def archive_notification(
        db: AsyncSession,
        notification_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> Notification:
        notif = await NotificationService.get_notification(db, notification_id)
        if user_id and notif.recipient_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this notification")
        notif.status = "archived"
        await db.commit()
        await db.refresh(notif)
        return notif

    @staticmethod
    async def delete_notification(
        db: AsyncSession,
        notification_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> None:
        notif = await NotificationService.get_notification(db, notification_id)
        if user_id and notif.recipient_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this notification")
        notif.status = "deleted"
        await db.commit()
