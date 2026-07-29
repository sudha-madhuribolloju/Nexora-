"""
Knowledge Base router — article CRUD, full-text search, and likes.
"""
import uuid
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.knowledge_base import ArticleStatus
from app.services.knowledge_base_service import KnowledgeBaseService
from app.schemas.knowledge_base import (
    KBArticleCreate, KBArticleUpdate, KBArticleResponse,
    KBArticleListResponse, KBSearchResponse,
)

router = APIRouter()


@router.get("/search", response_model=KBSearchResponse, summary="Search knowledge base articles")
async def search_articles(
    q: str = Query(..., min_length=1, description="Search query string"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Full-text search across knowledge base articles (title, content, summary, category).
    Only returns published articles.
    """
    total, articles = await KnowledgeBaseService.search_articles(db, q, skip, limit)
    return KBSearchResponse(query=q, total=total, data=articles)


@router.get("/", response_model=KBArticleListResponse, summary="List knowledge base articles")
async def list_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    article_status: Optional[ArticleStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve a paginated list of knowledge base articles.
    """
    total, articles = await KnowledgeBaseService.list_articles(db, skip, limit, category, article_status)
    return KBArticleListResponse(total=total, skip=skip, limit=limit, data=articles)


@router.post("/", response_model=KBArticleResponse, status_code=status.HTTP_201_CREATED, summary="Create an article")
async def create_article(
    data: KBArticleCreate,
    author_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new knowledge base article. A slug is auto-generated from the title if not provided.
    """
    effective_author_id = author_id or uuid.uuid4()
    return await KnowledgeBaseService.create_article(db, data, effective_author_id)


@router.get("/{article_id}", response_model=KBArticleResponse, summary="Get article by ID")
async def get_article(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve a specific knowledge base article. Increments view count.
    """
    return await KnowledgeBaseService.get_article(db, article_id)


@router.put("/{article_id}", response_model=KBArticleResponse, summary="Update an article")
async def update_article(
    article_id: uuid.UUID,
    data: KBArticleUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update content, metadata, or status of a knowledge base article.
    Publishes the article (sets published_at) when status changes to PUBLISHED.
    """
    return await KnowledgeBaseService.update_article(db, article_id, data)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an article")
async def delete_article(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Permanently delete a knowledge base article.
    """
    await KnowledgeBaseService.delete_article(db, article_id)


@router.post("/{article_id}/like", response_model=KBArticleResponse, summary="Like an article")
async def like_article(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Increment the like count for a knowledge base article.
    """
    return await KnowledgeBaseService.like_article(db, article_id)
