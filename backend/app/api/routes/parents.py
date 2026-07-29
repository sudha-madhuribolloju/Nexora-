from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any
import uuid

from app.api.dependencies import get_db
from app.schemas.parent import ParentResponse, ParentCreate, ParentUpdate
from app.utils.helpers import format_response

router = APIRouter()

@router.get("/", response_model=Any)
async def get_parents(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get all parents.
    """
    return format_response(status="success", message="Get parents stub", data={"parents": []})

@router.get("/{parent_id}", response_model=Any)
async def get_parent(
    parent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get parent details.
    """
    return format_response(status="success", message="Get parent stub", data={"parent_id": str(parent_id)})

@router.post("/", response_model=Any, status_code=status.HTTP_201_CREATED)
async def create_parent(
    parent_in: ParentCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new parent profile.
    """
    return format_response(status="success", message="Create parent stub", data=parent_in.model_dump())

@router.put("/{parent_id}", response_model=Any)
async def update_parent(
    parent_id: uuid.UUID,
    parent_in: ParentUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update parent details.
    """
    return format_response(status="success", message="Update parent stub", data={"parent_id": str(parent_id)})

@router.delete("/{parent_id}", response_model=Any)
async def delete_parent(
    parent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Remove parent.
    """
    return format_response(status="success", message="Delete parent stub")
