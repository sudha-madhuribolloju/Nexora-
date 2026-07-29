from typing import Optional, Dict, Any
from pydantic import BaseModel


class OverviewStats(BaseModel):
    total_students: int
    total_teachers: int
    total_courses: int
    total_sessions: int
    active_courses: int
    pending_assignments: int


class AttendanceAnalytics(BaseModel):
    overall_attendance_rate: float
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    by_course: Optional[Dict[str, float]] = None   # course_id -> attendance_rate


class PerformanceAnalytics(BaseModel):
    average_assignment_score: Optional[float] = None
    average_quiz_score: Optional[float] = None
    assignment_submission_rate: float
    quiz_completion_rate: float
    top_performers: Optional[list] = None


class CourseAnalytics(BaseModel):
    course_id: str
    title: str
    enrolled_students: int
    completed_sessions: int
    total_sessions: int
    average_attendance: float
    average_score: Optional[float] = None


class TeacherAnalytics(BaseModel):
    teacher_id: str
    full_name: str
    total_courses: int
    total_sessions_conducted: int
    average_student_score: Optional[float] = None
