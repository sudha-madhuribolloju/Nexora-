import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.notification import NotificationType


class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO
    action_url: Optional[str] = None


class NotificationCreate(NotificationBase):
    recipient_id: uuid.UUID


class NotificationResponse(NotificationBase):
    id: uuid.UUID
    recipient_id: uuid.UUID
    sender_id: Optional[uuid.UUID] = None
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    total: int
    unread_count: int
    skip: int
    limit: int
    data: List[NotificationResponse]
