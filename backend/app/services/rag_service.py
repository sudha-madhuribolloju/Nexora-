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

logger = logging.getLogger("app.services.rag_service")


class RAGService:
    """
    Orchestration service for PDF indexing into pgvector and RAG Question-Answering workflows.
    """

    @staticmethod
    async def index_pdf_document(
        db: AsyncSession,
        document_id: uuid.UUID,
        pdf_bytes: bytes,
        uploaded_by: uuid.UUID
    ) -> int:
        """
        Extract text from PDF bytes, chunk text, generate Gemini embeddings, and store in PostgreSQL pgvector.
        Returns total chunks indexed.
        """
        # Fetch parent document
        result = await db.execute(
            Document.__table__.select().where(Document.id == document_id)
        )
        doc_row = result.first()
        doc_name = doc_row.title if doc_row else "Document"

        # 1. Extract text page by page
        pages = PDFService.extract_text_from_pdf_bytes(pdf_bytes)
        if not pages:
            logger.warning(f"No text extracted from PDF for document {document_id}")
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
        document_id: Optional[uuid.UUID] = None,
        uploaded_by: Optional[uuid.UUID] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Complete RAG Pipeline:
        1. Embed student question via Gemini Embedding API
        2. Vector similarity search in PostgreSQL via pgvector
        3. Construct context from retrieved chunks
        4. Send prompt to Gemini Chat Model
        5. Return answer with sources
        """
        # 1. Question embedding
        question_embedding = await EmbeddingService.generate_embedding(question, is_query=True)

        # 2. Vector search in PostgreSQL
        similar_chunks = await RetrievalService.search_similar_chunks(
            db=db,
            query_embedding=question_embedding,
            top_k=top_k,
            document_id=document_id,
            uploaded_by=uploaded_by
        )

        context_texts = []
        sources = []

        for chunk, score in similar_chunks:
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

        context_str = "\n\n---\n\n".join(context_texts) if context_texts else "No context found in indexed documents."

        # 3. Prompt for Gemini
        system_instruction = (
            "You are NEXORA AI, an intelligent academic classroom assistant. "
            "Answer the student's question accurately using only the provided document context. "
            "If the context does not contain sufficient details to answer, state that clearly while remaining helpful."
        )

        full_prompt = (
            f"{system_instruction}\n\n"
            f"Context Information from Classroom Documents:\n{context_str}\n\n"
            f"Student Question: {question}\n\n"
            f"Detailed Answer:"
        )

        # 4. Generate response via ChatService
        answer = await ChatService.generate_chat_response(full_prompt)

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "retrieved_chunks_count": len(similar_chunks)
        }
