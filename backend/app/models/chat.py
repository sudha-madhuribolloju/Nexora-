import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, ForeignKey, Index, JSON, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin


class ChatSession(TimestampMixin, Base):
    """
    Model representing an AI conversation thread / chat session between a student/user and NEXORA AI.
    """
    __tablename__ = "chat_sessions"
    __table_args__ = (
        Index("ix_chat_sessions_user_id", "user_id"),
        Index("ix_chat_sessions_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        default="New AI Chat Session",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Relationships
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} user_id={self.user_id} title={self.title!r}>"


class ChatMessage(TimestampMixin, Base):
    """
    Model representing individual message entries in a chat session.
    """
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_session_id", "session_id"),
        Index("ix_chat_messages_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="user | ai | system",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    sources_json: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
        doc="Retrieved document RAG source citations",
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} sender={self.sender_type!r}>"


class AIConversation(TimestampMixin, Base):
    """
    Model tracking AI agent conversations, prompt tokens, and completion metrics.
    """
    __tablename__ = "ai_conversations"
    __table_args__ = (
        Index("ix_ai_conversations_user_id", "user_id"),
        Index("ix_ai_conversations_agent_name", "agent_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_name: Mapped[str] = mapped_column(
        String(100),
        default="NexusAI",
        nullable=False,
    )
    prompt_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    response_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    tokens_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    model_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        default="gemini-2.5-flash",
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<AIConversation id={self.id} agent={self.agent_name!r}>"
