from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Schema for incoming AI chat request payload.
    """
    message: str = Field(..., description="User prompt or question message")
    conversation_id: Optional[str] = Field(None, description="Existing conversation UUID thread ID")
    stream: bool = Field(False, description="Streaming flag (default False)")
    history: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Recent conversation message history")
    document_id: Optional[str] = Field(None, description="Active document ID")


class ChatResponse(BaseModel):
    """
    Schema for outgoing AI chat response payload.
    """
    response: str = Field(..., description="Generated AI response text")
    reply: Optional[str] = Field(None, description="Alias for response for frontend compatibility")
    conversation_id: str = Field(..., description="Conversation UUID thread ID")
    sources: list = Field(default_factory=list, description="Retrieved document RAG sources")
    tokens_used: int = Field(0, description="Estimated total tokens used")



class VoiceProcessingRequest(BaseModel):
    """
    Schema for incoming voice processing request payload.
    """
    speakerName: Optional[str] = Field(None, description="Target teacher or speaker name")
    speaker: Optional[str] = Field(None, description="Target teacher or speaker name")
    classroom_session_id: Optional[str] = Field(None, description="Active classroom session ID")


class VoiceProcessingResponse(BaseModel):
    """
    Schema for outgoing voice processing response payload.
    """
    speaker: str = Field(..., description="Identified speaker name")
    confidence: float = Field(..., description="Voiceprint confidence match score between 0.0 and 1.0")
    voicePrintId: str = Field(..., description="Unique voice print ID in registry")
    clarityScore: str = Field(..., description="Acoustic clarity score percentage string")
    noiseReducedTranscript: str = Field(..., description="Noise reduced speech transcript")
    classroom_session_id: Optional[str] = Field(None, description="Active classroom session ID")



class SummarizeRequest(BaseModel):
    """
    Schema for incoming lecture summary request payload.
    """
    transcript: str = Field(..., description="Lecture transcript or academic text to summarize")
    custom_prompt: Optional[str] = Field(None, description="Optional focus instructions for summary generation")


class SummarizeResponse(BaseModel):
    """
    Schema for outgoing lecture summary response payload.
    """
    summary: str = Field(..., description="Generated Markdown study guide and comprehensive lecture summary")


class NLPRequest(BaseModel):
    """
    Schema for incoming NLP analysis request payload.
    """
    transcript: str = Field(..., description="Classroom lecture transcript text")


class NLPDefinitionItem(BaseModel):
    term: str = Field(..., description="Extracted academic vocabulary term")
    explanation: str = Field(..., description="Definition and explanation")


class NLPResponse(BaseModel):
    """
    Schema for outgoing NLP analysis response payload.
    """
    sentiment: str = Field(..., description="Estimated classroom sentiment and tone")
    topics: List[str] = Field(default_factory=list, description="Extracted technical topics")
    definitions: List[NLPDefinitionItem] = Field(default_factory=list, description="Vocabulary definitions")
    actionItems: List[str] = Field(default_factory=list, description="Homework and assignment action items")


class ResearchRequest(BaseModel):
    """
    Schema for incoming academic research request payload.
    """
    query: str = Field(..., description="Academic research query")


class ResearchCitationItem(BaseModel):
    title: str = Field(..., description="Source article or paper title")
    uri: str = Field(..., description="Citation source link URL")


class ResearchResponse(BaseModel):
    """
    Schema for outgoing academic research response payload.
    """
    findings: str = Field(..., description="Synthesized academic research findings")
    citations: List[ResearchCitationItem] = Field(default_factory=list, description="Reference source citations")


class NotesRequest(BaseModel):
    """
    Schema for incoming study notes request payload.
    """
    topic: str = Field(..., description="Academic topic")
    subject: str = Field(..., description="Course subject area")


class NotesResponse(BaseModel):
    """
    Schema for outgoing study notes response payload.
    """
    notes: str = Field(..., description="Structured Markdown study notes")


