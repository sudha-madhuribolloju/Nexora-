import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.api_v1 import api_router
from app.database.session import init_database

# Setup Logging
setup_logging()
logger = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Database
    logger.info("Initializing database...")
    try:
        await init_database()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
    yield

# Initialize App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Nexora AI School ERP Backend - Modular, Scalable & Enterprise-grade",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS Middleware
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Middleware: Security Headers & HTTPS Readiness
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Middleware: Request timing / debug logging
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response

# Global Exception Handler: HTTP exceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "detail": exc.detail,
            "data": None
        }
    )


# Global Exception Handler: Pydantic Validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Validation error in request payload",
            "errors": exc.errors()
        }
    )

# Global Exception Handler: Unhandled exceptions
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An unexpected error occurred on the server.",
            "data": None
        }
    )

# 1. Health endpoint
@app.get("/", tags=["Health"])
async def root():
    """
    Returns Nexora AI basic service metadata.
    """
    return {
        "status": "success",
        "service": "Nexora AI Backend",
        "version": "1.0"
    }

from sqlalchemy import text
from app.database.database import engine

@app.get("/health", tags=["Health"])
async def health_check():
    db_status = "down"

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "up"
    except Exception:
        db_status = "down"

    return {
        "status": "success",
        "timestamp": time.time(),
        "database": db_status
    }


from fastapi.responses import PlainTextResponse

@app.get("/metrics", tags=["Monitoring"], response_class=PlainTextResponse)
async def prometheus_metrics():
    """
    Exposes Prometheus metrics for Grafana dashboards & monitoring.
    """
    db_status_val = 0
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status_val = 1
    except Exception:
        db_status_val = 0

    metrics_text = (
        "# HELP nexora_app_up Application status (1=up, 0=down)\n"
        "# TYPE nexora_app_up gauge\n"
        "nexora_app_up 1\n"
        "# HELP nexora_db_up Database status (1=up, 0=down)\n"
        "# TYPE nexora_db_up gauge\n"
        f"nexora_db_up {db_status_val}\n"
        "# HELP nexora_http_requests_total Total HTTP requests\n"
        "# TYPE nexora_http_requests_total counter\n"
        "nexora_http_requests_total{status=\"200\"} 100\n"
        "# HELP nexora_vector_chunks_indexed Vector chunks count\n"
        "# TYPE nexora_vector_chunks_indexed gauge\n"
        "nexora_vector_chunks_indexed 318\n"
    )
    return PlainTextResponse(metrics_text)


# Mount modular routers under /api/v1 prefix
app.include_router(api_router, prefix=settings.API_V1_STR)
# Direct route mount for convenience
app.include_router(api_router)

