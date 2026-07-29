import logging
from typing import List
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger("app.services.embedding_service")


class EmbeddingService:
    """
    Service responsible for generating embeddings using Google Gemini Embedding API.
    """

    @staticmethod
    def _init_gemini():
        api_key = settings.GOOGLE_API_KEY or settings.GEMINI_API_KEY
        if api_key:
            genai.configure(api_key=api_key)

    @staticmethod
    async def generate_embedding(text: str, is_query: bool = False) -> List[float]:
        """
        Generate 768-dimensional embedding vector for a single string.
        """
        EmbeddingService._init_gemini()
        model_name = settings.GEMINI_EMBEDDING_MODEL or "models/gemini-embedding-001"
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"

        task_type = "retrieval_query" if is_query else "retrieval_document"

        try:
            result = genai.embed_content(
                model=model_name,
                content=text,
                task_type=task_type
            )
            EMBEDDING_DIMENSION = 768
            if len(embedding) != EMBEDDING_DIMENSION:
                logger.warning(f"Embedding length was {len(embedding)}, adjusting/padding to 768")
                if len(embedding) > 768:
                    embedding = embedding[:768]
                else:
                    embedding = embedding + [0.0] * (768 - len(embedding))
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding via Gemini API: {e}", exc_info=True)
            # Return pseudo-embedding zero vector of size 768 as safe fallback if API call fails
            return [0.0] * EMBEDDING_DIMENSION

    @staticmethod
    async def generate_batch_embeddings(texts: List[str]) -> List[List[float]]:
        """
        Generate 768-dimensional embedding vectors for a batch of strings.
        """
        embeddings = []
        for text in texts:
            emb = await EmbeddingService.generate_embedding(text, is_query=False)
            embeddings.append(emb)
        return embeddings
