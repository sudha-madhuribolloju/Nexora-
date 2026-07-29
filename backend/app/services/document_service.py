"""
Document service — metadata CRUD for uploaded documents.
"""
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status

from app.models.document import Document
from app.schemas.document import DocumentCreate


class DocumentService:

    @staticmethod
    async def list_documents(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        uploader_id: Optional[uuid.UUID] = None,
        course_id: Optional[uuid.UUID] = None,
        is_public: Optional[bool] = None,
    ) -> Tuple[int, List[Document]]:
        q = select(Document)
        if uploader_id:
            q = q.where(Document.uploaded_by == uploader_id)
        if course_id:
            q = q.where(Document.course_id == course_id)
        if is_public is not None:
            q = q.where(Document.is_public == is_public)
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
        db: AsyncSession, data: DocumentCreate, uploaded_by: uuid.UUID
    ) -> Document:
        doc = Document(**data.model_dump(), uploaded_by=uploaded_by)
        db.add(doc)
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
