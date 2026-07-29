import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class SourceCitation(BaseModel):
    chunk_id: str
    document_name: str
    page_number: Optional[int] = None
    similarity_score: float
    snippet: str


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    sender_type: str
    content: str
    sources_json: Optional[List[SourceCitation]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionCreate(BaseModel):
    title: Optional[str] = Field("New AI Chat Session", description="Session title")


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[ChatMessageResponse]] = []

    model_config = ConfigDict(from_attributes=True)


class ChatQueryRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Student question prompt")
    session_id: Optional[uuid.UUID] = Field(None, description="Existing chat session ID")
    document_id: Optional[uuid.UUID] = Field(None, description="Scope query to specific document")
    top_k: int = Field(5, ge=1, le=20, description="Top-K vector chunks to retrieve")


class ChatQueryResponse(BaseModel):
    session_id: uuid.UUID
    question: str
    answer: str
    confidence_score: float
    confidence_label: str
    sources: List[SourceCitation]
    retrieved_chunks_count: int
    conversation_history: List[Dict[str, str]]
