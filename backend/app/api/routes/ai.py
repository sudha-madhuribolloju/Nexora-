import logging
from typing import Any, Optional, Dict
from fastapi import APIRouter, Depends, status, HTTPException, File, UploadFile, Form, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_current_user_optional
from app.database.database import get_db
from app.models.user import User
from app.schemas.ai import (
    ChatRequest, 
    ChatResponse, 
    VoiceProcessingRequest, 
    VoiceProcessingResponse,
    SummarizeRequest,
    SummarizeResponse,
    NLPRequest,
    NLPResponse,
    ResearchRequest,
    ResearchResponse,
    NotesRequest,
    NotesResponse
)
from app.services.ai_service import AIService
from app.utils.helpers import format_response

logger = logging.getLogger("app.api.routes.ai")

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Enterprise AI RAG Chat",
    description=(
        "Processes user message with RAG document grounding using pgvector cosine similarity search "
        "and Google Gemini LLM API. Automatically persists conversation history."
    ),
    response_description="Structured AI chat response with conversation ID, source citations, and token count"
)
async def ai_chat(
    request: ChatRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    POST /api/v1/ai/chat
    Enterprise-grade AI chat endpoint.
    """
    try:
        response = await AIService.chat(db=db, current_user=current_user, request=request)
        return response
    except Exception as e:
        logger.error(f"Error processing POST /api/v1/ai/chat request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your AI chat request."
        )



@router.post(
    "/voice-processing",
    response_model=VoiceProcessingResponse,
    status_code=status.HTTP_200_OK,
    summary="Audio Processing & Voice Recognition",
    description="Processes recorded audio stream or teacher voice biometrics and returns vocal identification metadata.",
    response_description="Vocal print authentication match results and noise reduced speech transcript"
)
async def process_voice(
    request: Request
) -> VoiceProcessingResponse:
    """
    POST /api/v1/ai/voice-processing
    """
    try:
        spk_name = None
        sess_id = None
        audio_bytes = None
        filename = None

        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type:
            form = await request.form()
            spk_name = form.get("speaker") or form.get("speakerName")
            sess_id = form.get("classroom_session_id")
            uploaded_file = form.get("file")
            if uploaded_file and hasattr(uploaded_file, "read"):
                audio_bytes = await uploaded_file.read()
                filename = getattr(uploaded_file, "filename", None)
        else:
            try:
                body = await request.json()
                spk_name = body.get("speaker") or body.get("speakerName")
                sess_id = body.get("classroom_session_id")
            except Exception:
                pass

        result = await AIService.process_voice(
            speaker_name=spk_name,
            classroom_session_id=sess_id,
            audio_bytes=audio_bytes,
            filename=filename
        )
        return VoiceProcessingResponse(**result)
    except Exception as e:
        logger.error(f"Error in POST /api/v1/ai/voice-processing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing voice input."
        )


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Compile Lecture Study Guide & Summary",
    description="Generates an academically structured Markdown study guide from lecture transcripts.",
    response_description="Generated Markdown lecture summary"
)
async def generate_summary(
    request: SummarizeRequest
) -> SummarizeResponse:
    """
    POST /api/v1/ai/summarize
    """
    try:
        summary_text = await AIService.summarize(transcript=request.transcript, custom_prompt=request.custom_prompt)
        return SummarizeResponse(summary=summary_text)
    except Exception as e:
        logger.error(f"Error in POST /api/v1/ai/summarize: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating lecture summary."
        )


@router.post(
    "/nlp",
    response_model=NLPResponse,
    status_code=status.HTTP_200_OK,
    summary="Classroom NLP Insights & Analytics",
    description="Analyzes transcript text to extract vocabulary definitions, key topics, sentiment, and action items.",
    response_description="Extracted NLP parameters"
)
async def analyze_nlp(
    request: NLPRequest
) -> NLPResponse:
    """
    POST /api/v1/ai/nlp
    """
    try:
        nlp_data = await AIService.analyze_nlp(transcript=request.transcript)
        return NLPResponse(**nlp_data)
    except Exception as e:
        logger.error(f"Error in POST /api/v1/ai/nlp: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while running NLP analysis."
        )


@router.post(
    "/research",
    response_model=ResearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Academic AI Research & Citations",
    description="Executes academic research query and returns grounded synthesis with citations.",
    response_description="Research findings and citations"
)
async def academic_research(
    request: ResearchRequest
) -> ResearchResponse:
    """
    POST /api/v1/ai/research
    """
    try:
        research_data = await AIService.research(query=request.query)
        return ResearchResponse(**research_data)
    except Exception as e:
        logger.error(f"Error in POST /api/v1/ai/research: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while running academic research."
        )


@router.post(
    "/notes",
    response_model=NotesResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Topic Study Notes",
    description="Generates comprehensive Markdown study notes with formulas and review questions.",
    response_description="Generated study notes"
)
async def generate_notes(
    request: NotesRequest
) -> NotesResponse:
    """
    POST /api/v1/ai/notes
    """
    try:
        notes_text = await AIService.generate_notes(topic=request.topic, subject=request.subject)
        return NotesResponse(notes=notes_text)
    except Exception as e:
        logger.error(f"Error in POST /api/v1/ai/notes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating study notes."
        )


@router.post("/query", response_model=Any)
async def query_ai(
    payload: dict
) -> Any:
    """
    General endpoint to query Google Gemini provider.
    Payload expectation: { "prompt": "..." }
    """
    prompt = payload.get("prompt", "Hello, Nexora AI!")
    response = await AIService.query_gemini(prompt)
    return format_response(status="success", message="AI query completed", data={"response": response})


@router.post("/agent/teacher", response_model=Any)
async def run_teacher_agent(
    task_description: dict
) -> Any:
    """
    Trigger the teacher assistant agent.
    """
    return format_response(status="success", message="Teacher agent execution triggered stub")


