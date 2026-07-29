# NEXORA – AI Classroom Platform: Testing Guide

This document provides a comprehensive overview of the automated test suites, testing setup, and execution instructions for **NEXORA – AI Classroom Platform**.

---

## 1. Backend Testing Suite (pytest)

The backend test suite is powered by `pytest` and `httpx/TestClient`, utilizing an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`) and mock/cached Gemini API fallbacks for ultra-fast, reproducible local testing.

### Test Categories Covered

| Category | Test File | Description |
| :--- | :--- | :--- |
| **Authentication** | `tests/test_auth.py` | Registration, login, JWT access/refresh rotation, password hashing, forgot/reset password, and logout. |
| **Authorization / RBAC** | `tests/test_lecture_endpoints_rbac.py`, `tests/test_roles.py` | Enforces 7-role RBAC matrix (`Student`, `Teacher`, `Parent`, `Principal`, `Institute Admin`, `Super Admin`, `Support Engineer`), returning `401 Unauthorized` & `403 Forbidden`. |
| **AI Chat & RAG** | `tests/test_ai_chat.py` | Multi-turn chat memory, prompt grounding, confidence scoring, source citations, and PostgreSQL chat persistence. |
| **Vector Search & pgvector** | `tests/test_vector_search.py` | 768-dimensional Gemini embedding generation, LRU query caching, `pgvector` similarity search, and hybrid vector+keyword ranking. |
| **Document Management** | `tests/test_document_management.py` | Multi-format parser (`.pdf`, `.docx`, `.pptx`, `.txt`), extension validation, 50MB limit, SHA-256 duplicate detection, document replacement & version incrementing. |
| **Teacher Features** | `tests/test_teacher_features.py` | Dashboard analytics, AI quiz generation, AI lesson plan creation, and document summarization. |
| **Student Features** | `tests/test_student_features.py` | Student dashboard metrics, AI Homework Assistance, and personalized study recommendations. |
| **Parent Portal** | `tests/test_parent_portal.py` | Parent portal statistics and AI-generated child progress reports. |
| **Admin Features** | `tests/test_admin_features.py` | System analytics, storage statistics, AI query metrics, and audit log retrieval. |
| **Notifications** | `tests/test_notifications.py` | In-app/email notifications, unread count tracking, marking read, archiving, and deletion filtering. |
| **Security Hardening** | `tests/test_security.py` | Mandatory security headers (`nosniff`, `DENY`, `1; mode=block`, `HSTS`, `CSP`), invalid JWT token rejection, file upload validation, and SQL injection protection. |

### Running Backend Tests

Run all test suites sequentially using the Python 3.11 virtualenv:

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_auth.py tests/test_lecture_endpoints_rbac.py tests/test_ai_chat.py tests/test_vector_search.py tests/test_document_management.py tests/test_teacher_features.py tests/test_student_features.py tests/test_parent_portal.py tests/test_admin_features.py tests/test_notifications.py tests/test_security.py -v
```

---

## 2. Frontend Testing Suite (React Testing Library & Jest)

The frontend test suite utilizes **React Testing Library** and **Vitest / Jest** to test UI components, authentication context, page routing, and API integration hooks.

### Executing Frontend Tests

```bash
cd frontend
npm run test
```

### Key Frontend Test Files
- `src/__tests__/AuthContext.test.tsx` — Tests login, token refresh, and session restoration.
- `src/__tests__/TeacherDashboard.test.tsx` — Tests AI quiz generation modal and metrics display.
- `src/__tests__/AITutorModal.test.tsx` — Tests AI Chat RAG query and source citation rendering.
