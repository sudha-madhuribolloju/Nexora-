import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import AIConversation, ChatSession, ChatMessage
from app.models.document_chunk import DocumentChunk
from app.core.config import settings

logger = logging.getLogger("app.repositories.knowledge_repository")


class KnowledgeRepository:
    """
    Repository layer for pgvector knowledge chunk vector search and AI conversation persistence.
    """

    @staticmethod
    async def search_similar_chunks(
        db: AsyncSession,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge_chunks using cosine similarity via pgvector.
        Returns top_k (default 5) most relevant document chunks.
        Fallback to document_chunks if knowledge_chunks table is empty or unavailable.
        """
        results: List[Dict[str, Any]] = []

        # 1. Primary Query: Try searching 'knowledge_chunks' using pgvector cosine distance operator (<=>)
        try:
            vector_str = "[" + ",".join(str(f) for f in query_embedding) + "]"
            raw_sql = text(
                """
                SELECT id, chunk_text, document_name, page_number,
                       (1 - (embedding <=> :vector::vector)) AS similarity
                FROM knowledge_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :vector::vector
                LIMIT :top_k
                """
            )
            res = await db.execute(raw_sql, {"vector": vector_str, "top_k": top_k})
            rows = res.fetchall()

            for row in rows:
                results.append({
                    "chunk_id": str(row.id),
                    "chunk_text": row.chunk_text,
                    "document_name": getattr(row, "document_name", "Knowledge Base"),
                    "page_number": getattr(row, "page_number", None),
                    "similarity_score": float(row.similarity or 0.0),
                    "snippet": row.chunk_text[:200] + "..." if len(row.chunk_text) > 200 else row.chunk_text
                })

            if results:
                logger.info(f"Retrieved {len(results)} chunks from knowledge_chunks table.")
                return results
        except Exception as e:
            logger.debug(f"Query on knowledge_chunks table skipped/fallback: {e}")

        # 2. Fallback Query: Query 'document_chunks' table using ORM / pgvector
        try:
            if hasattr(DocumentChunk, "embedding") and DocumentChunk.embedding is not None:
                cosine_dist = DocumentChunk.embedding.cosine_distance(query_embedding)
                stmt = select(DocumentChunk, cosine_dist.label("distance")).where(
                    DocumentChunk.embedding.is_not(None)
                ).order_by(cosine_dist).limit(top_k)

                orm_res = await db.execute(stmt)
                rows = orm_res.all()

                for chunk, dist in rows:
                    similarity = max(0.0, 1.0 - float(dist if dist is not None else 1.0))
                    results.append({
                        "chunk_id": str(chunk.id),
                        "chunk_text": chunk.chunk_text,
                        "document_name": chunk.document_name or "Document",
                        "page_number": chunk.page_number,
                        "similarity_score": round(similarity, 4),
                        "snippet": chunk.chunk_text[:200] + "..." if len(chunk.chunk_text) > 200 else chunk.chunk_text
                    })
                if results:
                    logger.info(f"Retrieved {len(results)} chunks from document_chunks fallback.")
                    return results
        except Exception as exc:
            logger.warning(f"Fallback vector search failed: {exc}")

        # 3. Safe fallback if DB vector index is empty or non-PG dialect used in testing
        try:
            stmt = select(DocumentChunk).limit(top_k)
            fallback_res = await db.execute(stmt)
            chunks = fallback_res.scalars().all()
            for chunk in chunks:
                results.append({
                    "chunk_id": str(chunk.id),
                    "chunk_text": chunk.chunk_text,
                    "document_name": chunk.document_name or "Document",
                    "page_number": chunk.page_number,
                    "similarity_score": 0.5,
                    "snippet": chunk.chunk_text[:200] + "..." if len(chunk.chunk_text) > 200 else chunk.chunk_text
                })
        except Exception as e:
            logger.debug(f"Generic text fallback empty: {e}")

        return results

    @staticmethod
    async def save_chat_message(
        db: AsyncSession,
        user_id: uuid.UUID,
        prompt: str,
        response: str,
        tokens_used: int,
        conversation_id: str,
        sources: Optional[list] = None
    ) -> AIConversation:
        """
        Persist conversation into ai_conversations, chat_sessions, and chat_messages tables.
        """
        sources = sources or []
        conv_uuid = uuid.UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id

        # 1. Save or update ChatSession
        session_stmt = select(ChatSession).where(ChatSession.id == conv_uuid)
        session_res = await db.execute(session_stmt)
        session = session_res.scalar_one_or_none()

        if not session:
            session = ChatSession(
                id=conv_uuid,
                user_id=user_id,
                title=prompt[:50] if prompt else "Nexora AI Chat",
                is_active=True
            )
            db.add(session)
            await db.flush()

        # 2. Add ChatMessages (User prompt + AI response)
        user_msg = ChatMessage(
            session_id=conv_uuid,
            sender_type="user",
            content=prompt
        )
        ai_msg = ChatMessage(
            session_id=conv_uuid,
            sender_type="ai",
            content=response,
            sources_json=sources
        )
        db.add(user_msg)
        db.add(ai_msg)

        # 3. Add AIConversation entry
        ai_conv = AIConversation(
            user_id=user_id,
            agent_name="Nexora AI Assistant",
            prompt_text=prompt,
            response_text=response,
            tokens_used=tokens_used,
            model_version=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
        )
        db.add(ai_conv)

        await db.commit()
        await db.refresh(ai_conv)
        logger.info(f"Saved chat message and AIConversation entry for conversation_id={conversation_id}")
        return ai_conv

    @staticmethod
    async def load_conversation(
        db: AsyncSession,
        conversation_id: str,
        user_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve existing messages for a given conversation_id.
        """
        history: List[Dict[str, Any]] = []
        try:
            conv_uuid = uuid.UUID(conversation_id)
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.session_id == conv_uuid)
                .order_by(ChatMessage.created_at.asc())
            )
            res = await db.execute(stmt)
            messages = res.scalars().all()

            for msg in messages:
                history.append({
                    "id": str(msg.id),
                    "sender_type": msg.sender_type,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                })
        except Exception as e:
            logger.warning(f"Error loading conversation history for conversation_id={conversation_id}: {e}")

        return history
