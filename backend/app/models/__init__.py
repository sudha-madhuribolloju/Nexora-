"""
app/models/__init__.py
Import all SQLAlchemy models so Base.metadata is fully populated
for Alembic migrations and test suite table creation.
"""

from app.database.base import Base
from app.models.user import User
from app.models.roles import Role, Permission, RolePermission, UserRole
from app.models.school import School, AcademicYear
from app.models.academic import Class, Section, Subject
from app.models.people import Student, Teacher, Parent, ParentStudentLink
from app.models.course import Course, CourseEnrollment
from app.models.subject import CourseSubject
from app.models.session import ClassSession
from app.models.attendance import Attendance
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt
from app.models.notification import Notification
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.knowledge_base import KnowledgeBaseArticle as KBArticle
from app.models.fees import FeeStructure, StudentFeeInvoice, FeePayment, InvoiceStatus, PaymentMethod
from app.models.recording import Recording
from app.models.otp import EmailOTP
from app.models.audit import AuditLog
from app.models.chat import ChatSession, ChatMessage, AIConversation
from app.models.transcript import LectureSession, Transcript, LectureSummary

__all__ = [
    "Base",
    "User",
    "Role",
    "Permission",
    "RolePermission",
    "UserRole",
    "School",
    "AcademicYear",
    "Class",
    "Section",
    "Subject",
    "Student",
    "Teacher",
    "Parent",
    "ParentStudentLink",
    "Course",
    "CourseEnrollment",
    "CourseSubject",
    "ClassSession",
    "Attendance",
    "Assignment",
    "AssignmentSubmission",
    "Quiz",
    "QuizQuestion",
    "QuizAttempt",
    "Notification",
    "Document",
    "DocumentChunk",
    "KBArticle",
    "FeeStructure",
    "StudentFeeInvoice",
    "FeePayment",
    "InvoiceStatus",
    "PaymentMethod",
    "Recording",
    "EmailOTP",
    "AuditLog",
    "ChatSession",
    "ChatMessage",
    "AIConversation",
    "LectureSession",
    "Transcript",
    "LectureSummary",
]

