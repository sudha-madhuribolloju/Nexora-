from fastapi import APIRouter, Depends
from typing import Any
from app.services.ai_service import AIService
from app.utils.helpers import format_response

router = APIRouter()


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
