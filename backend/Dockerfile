# ==========================================================
# NEXORA AI Classroom Portal - FastAPI Backend Dockerfile
# Multi-stage build supporting Development & Production
# ==========================================================

# ----------------------------------------------------------
# Stage 1: Base Runtime Environment
# ----------------------------------------------------------
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    APP_DIR=/app

WORKDIR ${APP_DIR}

# Install essential system runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------------------------------------
# Stage 2: Development Stage (Default target for dev compose)
# ----------------------------------------------------------
FROM base AS development

# Install Python requirements directly in development
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create required upload and log directories
RUN mkdir -p /app/uploads/recordings \
             /app/uploads/documents \
             /app/uploads/images \
             /app/logs

EXPOSE 8000

# Development command with hot-reloading
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ----------------------------------------------------------
# Stage 3: Builder Stage for Production
# ----------------------------------------------------------
FROM base AS builder

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ----------------------------------------------------------
# Stage 4: Production Stage (Hardened & Non-root)
# ----------------------------------------------------------
FROM python:3.11-slim AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_DIR=/app

WORKDIR ${APP_DIR}

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built dependencies from builder
COPY --from=builder /install /usr/local

# Create non-root system user and group
RUN groupadd -g 10001 nexora && \
    useradd -u 10001 -g nexora -m -s /bin/bash appuser

# Copy application source code
COPY --chown=appuser:nexora . ${APP_DIR}

# Create persistent folders with appuser ownership
RUN mkdir -p ${APP_DIR}/uploads/recordings \
             ${APP_DIR}/uploads/documents \
             ${APP_DIR}/uploads/images \
             ${APP_DIR}/logs && \
    chown -R appuser:nexora ${APP_DIR}

USER appuser

EXPOSE 8000

# Health check targeting FastAPI /health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Production command using Uvicorn multi-worker mode
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers"]
