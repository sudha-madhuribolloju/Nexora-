"""
Analytics router — dashboard statistics and domain-specific analytics.
"""
from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    OverviewStats, AttendanceAnalytics, PerformanceAnalytics,
    CourseAnalytics, TeacherAnalytics,
)

router = APIRouter()


@router.get("/overview", response_model=OverviewStats, summary="Dashboard overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """
    Get high-level statistics: total students, teachers, courses, sessions, etc.
    """
    return await AnalyticsService.get_overview(db)


@router.get("/attendance", response_model=AttendanceAnalytics, summary="Attendance analytics")
async def get_attendance_analytics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """
    Get system-wide attendance breakdown: present, absent, late, excused rates.
    """
    return await AnalyticsService.get_attendance_analytics(db)


@router.get("/performance", response_model=PerformanceAnalytics, summary="Performance analytics")
async def get_performance_analytics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """
    Get average assignment scores, quiz scores, submission rates, and completion rates.
    """
    return await AnalyticsService.get_performance_analytics(db)


@router.get("/courses", response_model=List[CourseAnalytics], summary="Course analytics")
async def get_course_analytics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """
    Get per-course analytics: enrolled students, session completion, attendance rates.
    """
    return await AnalyticsService.get_course_analytics(db)


@router.get("/teachers", response_model=List[TeacherAnalytics], summary="Teacher analytics")
async def get_teacher_analytics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """
    Get per-teacher analytics: courses taught, sessions conducted.
    """
    return await AnalyticsService.get_teacher_analytics(db)
