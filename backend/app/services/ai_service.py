import logging
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)


class AIService:
    """
    Unified AI Service utilizing Google Gemini models.
    """

    @staticmethod
    async def query_gemini(prompt: str) -> str:
        """
        Query Google Gemini Chat API.
        """
        logger.info("Invoking Gemini chat service.")
        return await ChatService.generate_chat_response(prompt)
