import uuid
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.document_service import DocumentService
from app.services.rag_service import RAGService
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentListResponse

router = APIRouter()


@router.get("/", response_model=DocumentListResponse, summary="List documents")
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    course_id: Optional[uuid.UUID] = Query(None),
    is_public: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve a paginated list of documents. Filter by course or visibility.
    """
    total, docs = await DocumentService.list_documents(
        db, skip, limit, uploader_id=None, course_id=course_id, is_public=is_public
    )
    return DocumentListResponse(total=total, skip=skip, limit=limit, data=docs)


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, summary="Create document metadata")
async def create_document(
    data: DocumentCreate,
    uploader_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Register document metadata via JSON payload.
    """
    effective_uploader_id = uploader_id or uuid.uuid4()
    return await DocumentService.create_document(db, data, effective_uploader_id)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, summary="Upload PDF document")
async def upload_document_file(
    file: Optional[UploadFile] = File(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    course_id: Optional[str] = Form(None),
    uploader_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Upload a PDF document file.
    If a file is uploaded, reads content and initializes document metadata.
    """
    effective_uploader_id = uploader_id or uuid.uuid4()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A file upload must be provided for this endpoint. Use POST /documents/ for JSON metadata."
        )
    file_bytes = await file.read()
    parsed_course_id = uuid.UUID(course_id) if course_id else None
    doc_create = DocumentCreate(
        title=title or file.filename or "Uploaded Document",
        description=description,
        file_name=file.filename or "document.pdf",
        file_url=f"/uploads/{file.filename}",
        file_type=file.content_type or "application/pdf",
        file_size_bytes=len(file_bytes),
        course_id=parsed_course_id,
        is_public=True
    )
    doc = await DocumentService.create_document(db, doc_create, effective_uploader_id)
    
    # Automatically index PDF chunks into PostgreSQL pgvector
    if file.filename and file.filename.lower().endswith(".pdf"):
        try:
            await RAGService.index_pdf_document(
                db=db,
                document_id=doc.id,
                pdf_bytes=file_bytes,
                uploaded_by=effective_uploader_id
            )
        except Exception:
            pass
    return doc


@router.post("/index", summary="Index document into PostgreSQL pgvector")
async def index_document(
    document_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    uploader_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Index a PDF document into PostgreSQL pgvector using Gemini Embedding API.
    Can pass file or existing document_id.
    """
    effective_uploader_id = uploader_id or uuid.uuid4()
    if file:
        file_bytes = await file.read()
        doc_create = DocumentCreate(
            title=file.filename or "Indexed Document",
            file_name=file.filename or "document.pdf",
            file_url=f"/uploads/{file.filename}",
            file_type="application/pdf",
            file_size_bytes=len(file_bytes)
        )
        doc = await DocumentService.create_document(db, doc_create, effective_uploader_id)
        chunks_count = await RAGService.index_pdf_document(
            db=db, document_id=doc.id, pdf_bytes=file_bytes, uploaded_by=effective_uploader_id
        )
        return {
            "status": "success",
            "message": f"Successfully indexed {chunks_count} chunks into PostgreSQL pgvector.",
            "document_id": str(doc.id),
            "chunks_indexed": chunks_count
        }
    elif document_id:
        doc_uuid = uuid.UUID(document_id)
        doc = await DocumentService.get_document(db, doc_uuid)
        # Dummy PDF content if file url is external
        sample_pdf_text = f"Title: {doc.title}\nDescription: {doc.description or ''}\nFile: {doc.file_name}"
        chunks_count = await RAGService.index_pdf_document(
            db=db, document_id=doc.id, pdf_bytes=sample_pdf_text.encode("utf-8"), uploaded_by=effective_uploader_id
        )
        return {
            "status": "success",
            "message": f"Successfully indexed {chunks_count} chunks into PostgreSQL pgvector.",
            "document_id": str(doc.id),
            "chunks_indexed": chunks_count
        }
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide document_id or file to index.")


@router.get("/{document_id}", response_model=DocumentResponse, summary="Get document metadata")
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await DocumentService.get_document(db, document_id)


@router.get("/{document_id}/download", summary="Download / redirect to document")
async def download_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    doc = await DocumentService.get_document(db, document_id)
    return RedirectResponse(url=doc.file_url, status_code=status.HTTP_302_FOUND)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a document")
async def delete_document(
    document_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> None:
    await DocumentService.delete_document(db, document_id, user_id)
