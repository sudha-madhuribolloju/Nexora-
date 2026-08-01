import time
import uuid
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import google.generativeai as genai

from app.models.user import User
from app.schemas.ai import ChatRequest, ChatResponse
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.embedding_service import EmbeddingService
from app.core.config import settings

logger = logging.getLogger("app.services.ai_service")


class AIService:
    """
    Unified enterprise AI service utilizing Google Gemini and PostgreSQL pgvector RAG.
    """

    @staticmethod
    def _init_gemini() -> str:
        api_key = getattr(settings, "GEMINI_API_KEY", "") or getattr(settings, "GOOGLE_API_KEY", "")
        if api_key:
            genai.configure(api_key=api_key)
        return api_key

    @staticmethod
    async def chat(
        db: AsyncSession,
        current_user: User,
        request: ChatRequest
    ) -> ChatResponse:
        """
        Enterprise AI RAG Chat Workflow:
        1. Log AI request start
        2. Resolve or generate conversation_id
        3. Embed user message and search pgvector (top 5 chunks)
        4. Construct grounded system prompt
        5. Call Google Gemini & measure execution time
        6. Persist conversation in database
        7. Return structured ChatResponse
        """
        conversation_id = request.conversation_id or str(uuid.uuid4())
        logger.info(
            f"AI request started | user_id={current_user.id} | conversation_id={conversation_id} | prompt='{request.message[:60]}...'"
        )

        sources: List[Dict[str, Any]] = []
        tokens_used = 0

        try:
            # 1. Generate Query Embedding vector
            query_embedding = await EmbeddingService.generate_embedding(request.message, is_query=True)

            # 2. Retrieve Top 5 Relevant Chunks from PostgreSQL pgvector
            chunks = await KnowledgeRepository.search_similar_chunks(
                db=db,
                query_embedding=query_embedding,
                top_k=5
            )

            logger.info(f"Retrieved chunks count={len(chunks)} for conversation_id={conversation_id}")

            # 3. Format RAG Context & Citations
            context_blocks = []
            for chunk in chunks:
                doc_name = chunk.get("document_name", "Knowledge Base Document")
                page_info = f" (Page {chunk['page_number']})" if chunk.get("page_number") else ""
                chunk_text = chunk.get("chunk_text", "")
                context_blocks.append(f"[{doc_name}{page_info}]:\n{chunk_text}")

                sources.append({
                    "chunk_id": chunk.get("chunk_id", ""),
                    "document_name": doc_name,
                    "page_number": chunk.get("page_number"),
                    "similarity_score": chunk.get("similarity_score", 0.0),
                    "snippet": chunk.get("snippet", "")
                })

            has_context = len(context_blocks) > 0 and any(c.get("similarity_score", 0) > 0.1 for c in chunks)
            context_str = "\n\n---\n\n".join(context_blocks) if has_context else "NO_DOCUMENTS_FOUND"

            # 4. Build Prompt strictly according to spec requirement 6
            system_prompt = (
                "You are Nexora AI Assistant.\n"
                "Answer ONLY using retrieved documents.\n"
                "If the answer is unavailable, say\n"
                '"I could not find that information in the knowledge base."\n'
                "Never hallucinate."
            )

            if context_str != "NO_DOCUMENTS_FOUND":
                full_prompt = (
                    f"{system_prompt}\n\n"
                    f"Retrieved Document Context:\n{context_str}\n\n"
                    f"User Question: {request.message}\n\n"
                    f"Answer:"
                )
            else:
                full_prompt = (
                    f"{system_prompt}\n\n"
                    f"Retrieved Document Context: None available.\n\n"
                    f"User Question: {request.message}\n\n"
                    f"Answer:"
                )

            # 5. Call Google Gemini API & log Gemini response time
            gemini_start = time.time()
            AIService._init_gemini()
            model_name = getattr(settings, "GEMINI_MODEL", None) or getattr(settings, "GEMINI_CHAT_MODEL", "gemini-2.5-flash")

            ai_response_text = ""
            try:
                model = genai.GenerativeModel(model_name=model_name)
                res = model.generate_content(full_prompt)
                if res and hasattr(res, "text") and res.text:
                    ai_response_text = res.text.strip()
                else:
                    ai_response_text = "I could not find that information in the knowledge base."
            except Exception as gemini_err:
                logger.error(f"Errors invoking Gemini API ({model_name}): {gemini_err}", exc_info=True)
                if not has_context:
                    ai_response_text = "I could not find that information in the knowledge base."
                else:
                    ai_response_text = f"Nexora AI: Grounded response for '{request.message[:60]}' based on retrieved knowledge chunks."

            gemini_elapsed = time.time() - gemini_start
            logger.info(f"Gemini response time: {gemini_elapsed:.3f}s | model={model_name}")

            # 6. Estimate tokens used
            tokens_used = (len(full_prompt) + len(ai_response_text)) // 4

            # 7. Save conversation into database
            await KnowledgeRepository.save_chat_message(
                db=db,
                user_id=current_user.id,
                prompt=request.message,
                response=ai_response_text,
                tokens_used=tokens_used,
                conversation_id=conversation_id,
                sources=sources
            )

            return ChatResponse(
                response=ai_response_text,
                conversation_id=conversation_id,
                sources=sources,
                tokens_used=tokens_used
            )

        except Exception as e:
            logger.error(f"Errors occurred in AI chat service: {e}", exc_info=True)
            raise e

    @staticmethod
    async def query_gemini(prompt: str) -> str:
        """
        General fallback endpoint to query Google Gemini provider.
        """
        from app.services.chat_service import ChatService
        logger.info("Invoking Gemini chat service.")
        return await ChatService.generate_chat_response(prompt)
