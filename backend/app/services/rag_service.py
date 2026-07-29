import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.pdf_service import PDFService
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService
from app.services.chat_service import ChatService
from app.services.chat_session_service import ChatSessionService

logger = logging.getLogger("app.services.rag_service")


class RAGService:
    """
    Orchestration service for PDF/DOCX/TXT indexing into pgvector and RAG Question-Answering workflows.
    """

    @staticmethod
    async def index_pdf_document(
        db: AsyncSession,
        document_id: uuid.UUID,
        pdf_bytes: bytes,
        uploaded_by: uuid.UUID,
        filename: str = "document.pdf"
    ) -> int:
        """
        Extract text from PDF, DOCX, or TXT bytes, chunk text, generate Gemini embeddings, and store in PostgreSQL pgvector.
        Returns total chunks indexed.
        """
        # Fetch parent document
        result = await db.execute(
            Document.__table__.select().where(Document.id == document_id)
        )
        doc_row = result.first()
        doc_name = doc_row.title if doc_row else filename

        # 1. Extract text page by page / section by section
        pages = PDFService.extract_text_from_file_bytes(pdf_bytes, filename)
        if not pages:
            logger.warning(f"No text extracted from file {filename} for document {document_id}")
            return 0

        # 2. Chunk text
        chunks_data = PDFService.chunk_pdf_pages(pages)

        # 3. Generate Gemini embeddings in batch
        texts = [c["chunk_text"] for c in chunks_data]
        embeddings = await EmbeddingService.generate_batch_embeddings(texts)

        # 4. Save to PostgreSQL pgvector
        created_chunks = []
        for idx, item in enumerate(chunks_data):
            chunk_obj = DocumentChunk(
                document_id=document_id,
                document_name=doc_name,
                chunk_index=item["chunk_index"],
                chunk_text=item["chunk_text"],
                embedding=embeddings[idx],
                metadata_json={"source": doc_name, "chunk": item["chunk_index"]},
                page_number=item.get("page_number"),
                uploaded_by=uploaded_by
            )
            created_chunks.append(chunk_obj)

        db.add_all(created_chunks)
        await db.commit()
        logger.info(f"Successfully indexed {len(created_chunks)} chunks for document {document_id} in PostgreSQL pgvector.")
        return len(created_chunks)

    @staticmethod
    async def answer_question(
        db: AsyncSession,
        question: str,
        session_id: Optional[uuid.UUID] = None,
        document_id: Optional[uuid.UUID] = None,
        uploaded_by: Optional[uuid.UUID] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Complete Context-Grounded RAG Pipeline with Multi-Turn Memory:
        1. Ensure active chat session exists or create a new session
        2. Fetch recent conversation history
        3. Embed question via Gemini Embedding API
        4. Perform pgvector cosine similarity search
        5. Calculate confidence score and label
        6. Construct context and prompt with strict hallucination suppression
        7. Query Gemini and persist conversation entries to PostgreSQL
        8. Return answer with confidence & source citations
        """
        # 1. Session resolution
        if session_id:
            try:
                session = await ChatSessionService.get_session(db, session_id)
            except Exception:
                session = await ChatSessionService.create_session(db, uploaded_by or uuid.uuid4(), title=question[:50])
        else:
            session = await ChatSessionService.create_session(db, uploaded_by or uuid.uuid4(), title=question[:50])

        active_session_id = session.id

        # 2. Fetch history
        history = await ChatSessionService.get_recent_history(db, active_session_id, limit=6)

        # 3. Question embedding
        question_embedding = await EmbeddingService.generate_embedding(question, is_query=True)

        # 4. Vector search in PostgreSQL pgvector
        similar_chunks = await RetrievalService.search_similar_chunks(
            db=db,
            query_embedding=question_embedding,
            top_k=top_k,
            document_id=document_id,
            uploaded_by=uploaded_by
        )

        context_texts = []
        sources = []
        max_score = 0.0

        for chunk, score in similar_chunks:
            if score > max_score:
                max_score = score
            context_texts.append(
                f"[Document: {chunk.document_name} | Page {chunk.page_number or 'N/A'}]\n{chunk.chunk_text}"
            )
            sources.append({
                "chunk_id": str(chunk.id),
                "document_name": chunk.document_name,
                "page_number": chunk.page_number,
                "similarity_score": round(score, 4),
                "snippet": chunk.chunk_text[:150] + "..." if len(chunk.chunk_text) > 150 else chunk.chunk_text
            })

        # 5. Confidence scoring
        confidence_score = round(max_score, 4)
        if confidence_score >= 0.85:
            confidence_label = "High"
        elif confidence_score >= 0.65:
            confidence_label = "Medium"
        else:
            confidence_label = "Low"

        context_str = "\n\n---\n\n".join(context_texts) if context_texts else "No matching context found in uploaded documents."

        # Format history string
        history_str = ""
        if history:
            history_lines = [f"{item['role'].capitalize()}: {item['content']}" for item in history]
            history_str = "Prior Conversation History:\n" + "\n".join(history_lines) + "\n\n"

        # 6. Hallucination Suppression System Instruction
        system_instruction = (
            "You are NEXORA AI, an intelligent academic classroom assistant. "
            "Your answers must be strictly grounded ONLY in the provided document context below. "
            "Do NOT invent facts, infer unmentioned details, or rely on external general knowledge. "
            "If the provided context does not contain sufficient information to answer the question, state: "
            "'The provided document context does not contain sufficient information to answer this question.'"
        )

        full_prompt = (
            f"{system_instruction}\n\n"
            f"{history_str}"
            f"Context Information from Classroom Documents:\n{context_str}\n\n"
            f"Student Question: {question}\n\n"
            f"Grounded Answer:"
        )

        # 7. Generate response via ChatService
        answer = await ChatService.generate_chat_response(full_prompt)

        # 8. Save user question and AI answer to database
        await ChatSessionService.add_message(db, active_session_id, sender_type="user", content=question)
        await ChatSessionService.add_message(db, active_session_id, sender_type="ai", content=answer, sources_json=sources)

        return {
            "session_id": str(active_session_id),
            "question": question,
            "answer": answer,
            "confidence_score": confidence_score,
            "confidence_label": confidence_label,
            "sources": sources,
            "retrieved_chunks_count": len(similar_chunks),
            "conversation_history": history
        }
