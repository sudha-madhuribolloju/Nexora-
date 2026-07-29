"""
Knowledge Base service — CRUD, search, and like operations.
"""
import uuid
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status

from app.models.knowledge_base import KnowledgeBaseArticle, ArticleStatus
from app.schemas.knowledge_base import KBArticleCreate, KBArticleUpdate


def _slugify(text: str) -> str:
    """Convert title to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text


class KnowledgeBaseService:

    @staticmethod
    async def list_articles(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        status_filter: Optional[ArticleStatus] = None,
    ) -> Tuple[int, List[KnowledgeBaseArticle]]:
        q = select(KnowledgeBaseArticle)
        if category:
            q = q.where(KnowledgeBaseArticle.category == category)
        if status_filter:
            q = q.where(KnowledgeBaseArticle.status == status_filter)
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        articles = (await db.execute(
            q.order_by(KnowledgeBaseArticle.created_at.desc()).offset(skip).limit(limit)
        )).scalars().all()
        return total, list(articles)

    @staticmethod
    async def get_article(db: AsyncSession, article_id: uuid.UUID) -> KnowledgeBaseArticle:
        result = await db.execute(
            select(KnowledgeBaseArticle).where(KnowledgeBaseArticle.id == article_id)
        )
        article = result.scalar_one_or_none()
        if not article:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        # Increment view count
        article.views += 1
        await db.commit()
        await db.refresh(article)
        return article

    @staticmethod
    async def create_article(
        db: AsyncSession, data: KBArticleCreate, author_id: uuid.UUID
    ) -> KnowledgeBaseArticle:
        slug = data.slug or _slugify(data.title)
        # Ensure slug uniqueness
        existing = (await db.execute(
            select(KnowledgeBaseArticle).where(KnowledgeBaseArticle.slug == slug)
        )).scalar_one_or_none()
        if existing:
            slug = f"{slug}-{str(uuid.uuid4())[:8]}"
        payload = data.model_dump(exclude={"slug"})
        article = KnowledgeBaseArticle(**payload, slug=slug, author_id=author_id)
        db.add(article)
        await db.commit()
        await db.refresh(article)
        return article

    @staticmethod
    async def update_article(
        db: AsyncSession, article_id: uuid.UUID, data: KBArticleUpdate
    ) -> KnowledgeBaseArticle:
        article = await KnowledgeBaseService.get_article(db, article_id)
        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("status") == ArticleStatus.PUBLISHED and not article.published_at:
            article.published_at = datetime.now(timezone.utc)
        for field, value in update_data.items():
            setattr(article, field, value)
        await db.commit()
        await db.refresh(article)
        return article

    @staticmethod
    async def delete_article(db: AsyncSession, article_id: uuid.UUID) -> None:
        article = await KnowledgeBaseService.get_article(db, article_id)
        await db.delete(article)
        await db.commit()

    @staticmethod
    async def search_articles(
        db: AsyncSession, query: str, skip: int = 0, limit: int = 20
    ) -> Tuple[int, List[KnowledgeBaseArticle]]:
        pattern = f"%{query}%"
        q = select(KnowledgeBaseArticle).where(
            or_(
                KnowledgeBaseArticle.title.ilike(pattern),
                KnowledgeBaseArticle.content.ilike(pattern),
                KnowledgeBaseArticle.summary.ilike(pattern),
                KnowledgeBaseArticle.category.ilike(pattern),
            )
        ).where(KnowledgeBaseArticle.status == ArticleStatus.PUBLISHED)
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        articles = (await db.execute(q.offset(skip).limit(limit))).scalars().all()
        return total, list(articles)

    @staticmethod
    async def like_article(db: AsyncSession, article_id: uuid.UUID) -> KnowledgeBaseArticle:
        article = (await db.execute(
            select(KnowledgeBaseArticle).where(KnowledgeBaseArticle.id == article_id)
        )).scalar_one_or_none()
        if not article:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        article.likes += 1
        await db.commit()
        await db.refresh(article)
        return article
