# NEXORA – AI Classroom Platform: Comprehensive Architecture & System Guide

This document provides in-depth technical documentation covering system design, authentication, authorization (RBAC), RAG document workflows, Gemini integration, user roles, administration, and troubleshooting.

---

## 1. Authentication Guide

- **Mechanism**: Dual signed JSON Web Tokens (JWT) using `python-jose` with `HS256` HMAC signature algorithm.
- **Access Tokens**: Short-lived (60 minutes default) carried in standard HTTP `Authorization: Bearer <token>` header.
- **Refresh Tokens**: Long-lived (7 days default) used to obtain fresh access tokens via `POST /api/v1/auth/refresh`.
- **Password Security**: Hashing via `passlib[bcrypt]` with automatic 72-byte string truncation safety.
- **Password Reset**: Signed 15-minute reset tokens generated via `POST /api/v1/auth/forgot-password` and redeemed via `POST /api/v1/auth/reset-password`.

---

## 2. Authorization (RBAC) Guide

Centralized RBAC middleware (`RequireRole`) evaluates authenticated user role claims against 7 system roles:

1. `Student` — Access to student portal, AI Tutor, document chat, homework help, quiz attempts, and submission viewing.
2. `Teacher` — Access to course material uploads, AI quiz generation, AI lesson plan creation, submission grading, and class stats.
3. `Parent` — Access to linked student progress reports, marks, attendance, and AI-generated parent progress summaries.
4. `Principal` — Read-only oversight across academic performance, school statistics, and teacher activities.
5. `Institute Admin` — Full school-level administrative access, user management, course setup, and storage stats.
6. `Super Admin` — Global system configuration, multi-tenant school management, system health, and audit logs.
7. `Support Engineer` — System diagnostics, error monitoring, and maintenance access.

Enforces HTTP `401 Unauthorized` for missing/invalid credentials and HTTP `403 Forbidden` for insufficient role privileges.

---

## 3. RAG Pipeline & Gemini Integration

```
  Document File (.pdf/.docx/.pptx/.txt)
                 │
                 ▼
  Multi-Format Parser (pdf_service.py)
                 │
                 ▼
  Chunking (800 chars, 150 overlap)
                 │
                 ▼
  Google Gemini Embedding API (768-dim)
                 │
                 ▼
  PostgreSQL pgvector (document_chunks HNSW)
                 │
                 ▼
  Hybrid Vector + Text Search (retrieval_service.py)
                 │
                 ▼
  Grounding Prompt Construction (rag_service.py)
                 │
                 ▼
  Gemini Response Generation + Citations
```

---

## 4. User Manual

### Student Portal
- **AI Tutor**: Open AI Chat modal, select uploaded textbook/notes, and ask questions.
- **Homework Help**: Submit homework problems to receive step-by-step guidance.
- **Quiz Practice**: Take auto-graded multiple-choice quizzes and view instant score breakdowns.

### Teacher Dashboard
- **Material Upload**: Drag-and-drop lecture slides (`.pptx`), notes (`.pdf`), or handouts (`.docx`).
- **AI Quiz Generator**: Enter topic and question count to auto-generate MCQ quizzes.
- **Lesson Planner**: Generate structured 45-60 minute lesson plans with timing and homework.

### Parent Portal
- **Dashboard**: Track child attendance, marks, and pending homework.
- **AI Progress Report**: Generate encouraging 3-paragraph summary reports.

### Admin Console
- **Analytics**: Monitor total users, active schools, storage usage, and Gemini AI query metrics.
- **Audit Logs**: Review security events and login timestamps.

---

## 5. Troubleshooting Guide

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **`pgvector` query syntax error in SQLite** | SQLite does not support native `<=>` operator | `RetrievalService` automatically executes fallback text search in non-PostgreSQL dialects. |
| **401 Unauthorized on API requests** | Token expired or invalid signature | Login again to obtain a fresh access token or use `POST /auth/refresh`. |
| **Google Gemini API Key error** | Missing or invalid key | Ensure `GOOGLE_API_KEY` is set in `backend/.env`. |
| **File upload 413 Payload Too Large** | File size exceeds 50MB | Upload files under 50MB or compress documents. |
