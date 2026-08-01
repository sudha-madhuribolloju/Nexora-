from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Schema for incoming AI chat request payload.
    """
    message: str = Field(..., description="User prompt or question message")
    conversation_id: Optional[str] = Field(None, description="Existing conversation UUID thread ID")
    stream: bool = Field(False, description="Streaming flag (default False)")


class ChatResponse(BaseModel):
    """
    Schema for outgoing AI chat response payload.
    """
    response: str = Field(..., description="Generated AI response text")
    conversation_id: str = Field(..., description="Conversation UUID thread ID")
    sources: list = Field(default_factory=list, description="Retrieved document RAG sources")
    tokens_used: int = Field(0, description="Estimated total tokens used")
