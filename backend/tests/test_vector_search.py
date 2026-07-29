import pytest
import uuid
from tests.conftest import TestingSessionLocal
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService


@pytest.mark.asyncio
async def test_phase_7_vector_and_hybrid_search() -> None:
    async with TestingSessionLocal() as db_session:
        doc_id = uuid.uuid4()
        uploader_id = uuid.uuid4()

        # 1. Test Embedding Generation & LRU Caching
        emb1 = await EmbeddingService.generate_embedding("quantum mechanics physics", is_query=True)
        assert len(emb1) == 768
        emb2 = await EmbeddingService.generate_embedding("quantum mechanics physics", is_query=True)
        assert emb1 == emb2  # Cache hit

        # 2. Insert mock document chunks with embeddings
        chunk1 = DocumentChunk(
            document_id=doc_id,
            uploaded_by=uploader_id,
            document_name="Quantum Physics Guide.pdf",
            chunk_index=0,
            chunk_text="Quantum mechanics describes physical properties of nature at the scale of atoms and subatomic particles.",
            embedding=emb1,
            page_number=1,
            metadata_json={"topic": "Quantum"}
        )
        chunk2 = DocumentChunk(
            document_id=doc_id,
            uploaded_by=uploader_id,
            document_name="Quantum Physics Guide.pdf",
            chunk_index=1,
            chunk_text="Classical mechanics fails to describe atomic structure accurately, necessitating wave-particle duality concepts.",
            embedding=await EmbeddingService.generate_embedding("classical mechanics wave particle duality", is_query=False),
            page_number=2,
            metadata_json={"topic": "Duality"}
        )
        db_session.add_all([chunk1, chunk2])
        await db_session.commit()

        # 3. Vector Similarity Search
        vec_results = await RetrievalService.search_similar_chunks(
            db=db_session,
            query_embedding=emb1,
            top_k=2,
            document_id=doc_id
        )
        assert len(vec_results) >= 1
        top_chunk, score = vec_results[0]
        assert top_chunk.document_name == "Quantum Physics Guide.pdf"
        assert isinstance(score, float)

        # 4. Hybrid Search (Vector + Keyword)
        hybrid_results = await RetrievalService.hybrid_search_chunks(
            db=db_session,
            query_text="quantum mechanics atoms subatomic",
            query_embedding=emb1,
            top_k=2,
            document_id=doc_id,
            alpha=0.7
        )
        assert len(hybrid_results) >= 1
        h_chunk, h_score = hybrid_results[0]
        assert h_chunk.document_name == "Quantum Physics Guide.pdf"
        assert h_score > 0.0
