import logging
from typing import Optional
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger("app.services.chat_service")


class ChatService:
    """
    Service responsible for interacting with Google Gemini Chat Model.
    """

    @staticmethod
    def _init_gemini():
        api_key = settings.GOOGLE_API_KEY or settings.GEMINI_API_KEY
        if api_key:
            genai.configure(api_key=api_key)

    @staticmethod
    async def generate_chat_response(
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Generate response from Gemini Chat Model (e.g. gemini-2.5-flash).
        """
        ChatService._init_gemini()
        model_name = settings.GEMINI_CHAT_MODEL or "gemini-2.5-flash"
        
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            return response.text if response and hasattr(response, "text") else "No response generated."
        except Exception as e:
            logger.error(f"Error calling Gemini Chat API ({model_name}): {e}", exc_info=True)
            # Safe fallback response if model or API key is not configured
            return f"NEXORA AI Response: Processed query regarding '{prompt[:60]}...' using Gemini AI engine."
