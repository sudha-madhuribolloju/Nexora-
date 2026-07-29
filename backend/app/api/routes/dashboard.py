from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.admin_service import AdminService
from app.utils.helpers import format_response

router = APIRouter()


@router.get("/", summary="Get System Dashboard Analytics")
@router.get("/admin", summary="Get Admin Dashboard Analytics")
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get aggregated system analytics for Super Admin and Institute Admin.
    """
    analytics = await AdminService.get_system_analytics(db)
    return format_response(status="success", message="System analytics retrieved", data=analytics)


@router.get("/storage", summary="Get Storage & Document Statistics")
async def get_storage_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get storage statistics, byte sizes, and vector chunk counts.
    """
    storage_stats = await AdminService.get_storage_statistics(db)
    return format_response(status="success", message="Storage statistics retrieved", data=storage_stats)


@router.get("/ai-usage", summary="Get AI Usage Analytics")
async def get_ai_usage_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get Gemini AI API query counts and usage metrics.
    """
    ai_stats = await AdminService.get_ai_usage_analytics(db)
    return format_response(status="success", message="AI usage analytics retrieved", data=ai_stats)


@router.get("/audit-logs", summary="Get System Audit Logs")
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve system security audit logs.
    """
    total, logs = await AdminService.list_audit_logs(db, skip=skip, limit=limit)
    return format_response(status="success", message="Audit logs retrieved", data={"total": total, "logs": logs})
