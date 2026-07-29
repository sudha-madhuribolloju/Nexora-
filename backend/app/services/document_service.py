"""
Document service — metadata CRUD, multi-format validation, versioning, duplicate detection, and search for uploaded documents.
"""
import uuid
import hashlib
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status

from app.models.document import Document
from app.schemas.document import DocumentCreate

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".png", ".jpg", ".jpeg"}


class DocumentService:

    @staticmethod
    def validate_file(file_bytes: bytes, filename: str) -> str:
        """
        Validate file extension, size limit (50MB), and header magic bytes for security.
        Returns calculated SHA-256 hash.
        """
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds maximum limit of 50MB."
            )

        fname_lower = filename.lower()
        ext = "." + fname_lower.split(".")[-1] if "." in fname_lower else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Header magic bytes validation
        if ext == ".pdf" and not file_bytes.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file structure."
            )
        elif ext in (".docx", ".pptx") and not file_bytes.startswith(b"PK\x03\x04"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Office OpenXML document archive structure."
            )

        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    async def check_duplicate(db: AsyncSession, file_hash: str) -> Optional[Document]:
        stmt = select(Document).where(Document.file_hash == file_hash)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_documents(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        uploader_id: Optional[uuid.UUID] = None,
        course_id: Optional[uuid.UUID] = None,
        is_public: Optional[bool] = None,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> Tuple[int, List[Document]]:
        q = select(Document)
        if uploader_id:
            q = q.where(Document.uploaded_by == uploader_id)
        if course_id:
            q = q.where(Document.course_id == course_id)
        if is_public is not None:
            q = q.where(Document.is_public == is_public)
        if category:
            q = q.where(Document.category == category)
        if search_query:
            pattern = f"%{search_query}%"
            q = q.where(or_(Document.title.ilike(pattern), Document.file_name.ilike(pattern), Document.description.ilike(pattern)))

        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        docs = (await db.execute(q.order_by(Document.created_at.desc()).offset(skip).limit(limit))).scalars().all()
        return total, list(docs)

    @staticmethod
    async def get_document(db: AsyncSession, document_id: uuid.UUID) -> Document:
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return doc

    @staticmethod
    async def create_document(
        db: AsyncSession, data: DocumentCreate, uploaded_by: uuid.UUID, file_hash: Optional[str] = None
    ) -> Document:
        doc_dict = data.model_dump()
        if file_hash:
            doc_dict["file_hash"] = file_hash
        doc = Document(**doc_dict, uploaded_by=uploaded_by)
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def replace_document(
        db: AsyncSession,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        file_bytes: bytes,
        filename: str,
    ) -> Document:
        doc = await DocumentService.get_document(db, document_id)
        if doc.uploaded_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to replace this document"
            )

        new_hash = DocumentService.validate_file(file_bytes, filename)
        doc.file_name = filename
        doc.file_url = f"/uploads/{filename}"
        doc.file_size_bytes = len(file_bytes)
        doc.file_hash = new_hash
        doc.version += 1

        await db.commit()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def delete_document(
        db: AsyncSession, document_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> None:
        doc = await DocumentService.get_document(db, document_id)
        if user_id and doc.uploaded_by != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this document")
        await db.delete(doc)
        await db.commit()
