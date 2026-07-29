# Nexora AI School ERP - FastAPI Backend

Nexora AI is a modular, scalable, enterprise-grade AI-powered School ERP backend.

## Tech Stack
- **Web Framework**: FastAPI
- **Database & Auth**: Supabase (PostgreSQL, Supabase Python Client)
- **ORM & Migrations**: SQLAlchemy 2.0 & Alembic
- **Validation**: Pydantic v2
- **Logging**: Production-grade structured logging
- **AI Agent Frameworks (Future-Ready)**: CrewAI & LangChain

---

## Directory Structure

```text
backend/
├── app/
│   ├── main.py              # Application entrypoint
│   ├── api/                 # Versioned API routes & dependencies
│   ├── core/                # Configuration, security & logging settings
│   ├── database/            # SQLAlchemy & Supabase connections
│   ├── models/              # Declarative database models
│   ├── schemas/             # Pydantic validation schemas
│   ├── services/            # Core business logic layer
│   ├── agents/              # CrewAI Agents (Teacher, Student, Attendance)
│   └── utils/               # Common helper utilities
├── tests/                   # Automated tests suite
├── Dockerfile               # Production multi-stage Docker build
├── docker-compose.yml       # Dev service orchestration (FastAPI + Redis)
└── requirements.txt         # Package dependencies
```

---

## Setup & Running Locally

### 1. Prerequisite
Ensure Python 3.12+ (Python 3.14.6 recommended) is installed on your local machine.

### 2. Configure Environment
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Populate the required configurations (such as `SUPABASE_URL`, `SUPABASE_KEY`, and `DATABASE_URL`).

### 3. Create a Virtual Environment and Install Dependencies
```bash
python -m venv .venv
# On Windows (PowerShell)
.venv\Scripts\Activate.ps1
# On Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Run the Dev Server
```bash
uvicorn app.main:app --reload
```

---

## Health Check and API Documentation
- **Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Base Route Health**: `GET http://localhost:8000/`
- **Component Health**: `GET http://localhost:8000/health`
