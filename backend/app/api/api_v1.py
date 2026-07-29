from fastapi import APIRouter

from app.api.v1 import auth as auth_v1
from app.api.v1 import users as users_v1
from app.api.v1 import roles as roles_v1      # Migration 001 — RBAC
from app.api.v1 import schools as schools_v1  # Migration 002 — Schools
from app.api.v1 import academic as academic_v1  # Migration 003 — Academic
from app.api.v1 import people as people_v1      # Migration 005 — People
from app.api.routes import (
    students,
    teachers,
    parents,
    attendance,
    classes,
    fees,
    dashboard,
    ai,
    courses,
    subjects,
    sessions,
    attendance_v2,
    assignments,
    quizzes,
    analytics,
    notifications,
    documents,
    knowledge_base,
    chat,
    research,
    lecture,
    quiz,
    websocket,
    recordings,
)


api_router = APIRouter()

# ── Existing routes ──────────────────────────────────────────────────────────
api_router.include_router(auth_v1.router,     prefix="/auth",     tags=["Authentication"])
api_router.include_router(users_v1.router,    prefix="/users",    tags=["Users"])
api_router.include_router(roles_v1.router,    prefix="/roles",    tags=["Roles & Permissions"])  # 001
api_router.include_router(schools_v1.router,  prefix="/schools",  tags=["Schools"])               # 002
api_router.include_router(academic_v1.router, prefix="/academic", tags=["Academic"])              # 003
api_router.include_router(people_v1.router,   prefix="/people",   tags=["People"])                 # 005
api_router.include_router(students.router,    prefix="/students",   tags=["Students"])
api_router.include_router(teachers.router,    prefix="/teachers",   tags=["Teachers"])
api_router.include_router(parents.router,     prefix="/parents",    tags=["Parents"])
api_router.include_router(attendance.router,  prefix="/attendance-legacy", tags=["Attendance (Legacy)"])
api_router.include_router(classes.router,     prefix="/classes",    tags=["Classes"])
api_router.include_router(fees.router,        prefix="/fees",       tags=["Fees"])
api_router.include_router(dashboard.router,   prefix="/dashboard",  tags=["Dashboard"])
api_router.include_router(ai.router,          prefix="/ai",         tags=["AI Integration"])

# ── Feature & RAG routers ─────────────────────────────────────────────────────
api_router.include_router(courses.router,          prefix="/courses",          tags=["Courses"])
api_router.include_router(subjects.router,          prefix="/subjects",         tags=["Subjects"])
api_router.include_router(sessions.router,          prefix="/sessions",         tags=["Sessions"])
api_router.include_router(attendance_v2.router,     prefix="/attendance",       tags=["Attendance"])
api_router.include_router(assignments.router,       prefix="/assignments",      tags=["Assignments"])
api_router.include_router(quizzes.router,           prefix="/quizzes",          tags=["Quizzes"])
api_router.include_router(analytics.router,         prefix="/analytics",        tags=["Analytics"])
api_router.include_router(notifications.router,     prefix="/notifications",    tags=["Notifications"])
api_router.include_router(documents.router,         prefix="/documents",        tags=["Documents"])
api_router.include_router(knowledge_base.router,    prefix="/knowledge-base",   tags=["Knowledge Base"])

# ── Endpoints required by specification ─────────────────────────────
api_router.include_router(chat.router,               prefix="/chat",             tags=["Chat & RAG"])
api_router.include_router(research.router,           prefix="/research",         tags=["Research"])
api_router.include_router(lecture.router,            prefix="/lecture",          tags=["Lectures"])
api_router.include_router(recordings.router,         prefix="/recordings",       tags=["Recordings"])
api_router.include_router(quiz.router,               prefix="/quiz",             tags=["Quiz Generation"])

api_router.include_router(websocket.router,          prefix="/ws",               tags=["WebSockets"])
