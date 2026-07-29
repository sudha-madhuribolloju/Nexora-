import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document, DocumentCategory
from app.models.knowledge_base import KnowledgeBaseArticle, ArticleStatus

class DocumentRepository:
    @staticmethod
    async def list_documents(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        uploader_id: Optional[uuid.UUID] = None,
        course_id: Optional[uuid.UUID] = None,
        is_public: Optional[bool] = None,
    ) -> Tuple[int, List[Document]]:
        """
        List documents with pagination and optional filters.
        """
        q = select(Document)
        if uploader_id:
            q = q.where(Document.uploaded_by == uploader_id)
        if course_id:
            q = q.where(Document.course_id == course_id)
        if is_public is not None:
            q = q.where(Document.is_public == is_public)

        count_q = select(func.count()).select_from(q.subquery())
        total_result = await db.execute(count_q)
        total = total_result.scalar_one()

        records_q = q.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        records_result = await db.execute(records_q)
        docs = records_result.scalars().all()

        return total, list(docs)

    @staticmethod
    async def get_document_by_id(db: AsyncSession, document_id: uuid.UUID) -> Optional[Document]:
        """
        Get document by ID.
        """
        result = await db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_document(db: AsyncSession, doc_data: dict, uploaded_by: uuid.UUID) -> Document:
        """
        Create a new document.
        """
        doc = Document(**doc_data, uploaded_by=uploaded_by)
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def delete_document(db: AsyncSession, doc: Document) -> None:
        """
        Delete document from the DB.
        """
        await db.delete(doc)
        await db.commit()

    @staticmethod
    async def list_articles(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        status_filter: Optional[ArticleStatus] = None,
    ) -> Tuple[int, List[KnowledgeBaseArticle]]:
        """
        List KB articles with optional filters.
        """
        q = select(KnowledgeBaseArticle)
        if category:
            q = q.where(KnowledgeBaseArticle.category == category)
        if status_filter:
            q = q.where(KnowledgeBaseArticle.status == status_filter)

        count_q = select(func.count()).select_from(q.subquery())
        total_result = await db.execute(count_q)
        total = total_result.scalar_one()

        records_q = q.order_by(KnowledgeBaseArticle.created_at.desc()).offset(skip).limit(limit)
        records_result = await db.execute(records_q)
        articles = records_result.scalars().all()

        return total, list(articles)

    @staticmethod
    async def get_article_by_id(db: AsyncSession, article_id: uuid.UUID) -> Optional[KnowledgeBaseArticle]:
        """
        Get specific KB article by ID.
        """
        result = await db.execute(
            select(KnowledgeBaseArticle).where(KnowledgeBaseArticle.id == article_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_article_by_slug(db: AsyncSession, slug: str) -> Optional[KnowledgeBaseArticle]:
        """
        Get specific KB article by slug.
        """
        result = await db.execute(
            select(KnowledgeBaseArticle).where(KnowledgeBaseArticle.slug == slug)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_article(db: AsyncSession, article_data: dict) -> KnowledgeBaseArticle:
        """
        Create a new KB article.
        """
        article = KnowledgeBaseArticle(**article_data)
        db.add(article)
        await db.commit()
        await db.refresh(article)
        return article

    @staticmethod
    async def update_article(db: AsyncSession, article: KnowledgeBaseArticle, updates: dict) -> KnowledgeBaseArticle:
        """
        Update an existing KB article.
        """
        for field, value in updates.items():
            setattr(article, field, value)
        await db.commit()
        await db.refresh(article)
        return article

    @staticmethod
    async def delete_article(db: AsyncSession, article: KnowledgeBaseArticle) -> None:
        """
        Delete a KB article.
        """
        await db.delete(article)
        await db.commit()

    @staticmethod
    async def search_articles(
        db: AsyncSession, query: str, skip: int = 0, limit: int = 20
    ) -> Tuple[int, List[KnowledgeBaseArticle]]:
        """
        Search public KB articles by text match.
        """
        pattern = f"%{query}%"
        q = select(KnowledgeBaseArticle).where(
            or_(
                KnowledgeBaseArticle.title.ilike(pattern),
                KnowledgeBaseArticle.content.ilike(pattern),
                KnowledgeBaseArticle.summary.ilike(pattern),
                KnowledgeBaseArticle.category.ilike(pattern),
            )
        ).where(KnowledgeBaseArticle.status == ArticleStatus.PUBLISHED)

        count_q = select(func.count()).select_from(q.subquery())
        total_result = await db.execute(count_q)
        total = total_result.scalar_one()

        records_q = q.offset(skip).limit(limit)
        records_result = await db.execute(records_q)
        articles = records_result.scalars().all()

        return total, list(articles)
