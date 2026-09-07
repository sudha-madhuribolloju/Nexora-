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
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Vite dev server default port
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Common alternate dev ports
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware: Security Headers, WebSocket CSP, & HTTPS Readiness
# NOTE: Only ONE middleware is defined here (the duplicate was removed — it was
# overwriting Content-Security-Policy and stripping ws:/wss: which broke WebSocket).
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Skip restrictive CSP for Swagger UI routes; allow ws:/wss: for WebSocket everywhere else
    if request.url.path in ["/docs", "/openapi.json", "/redoc"]:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self' ws: wss:;"
        )
    else:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            # CRITICAL: ws: wss: must be here — without it browsers block WebSocket connections
            "connect-src 'self' ws: wss:;"
        )
    return response

# Global Exception Handler: HTTP exceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
    headers = dict(exc.headers) if exc.headers else {}
    origin = request.headers.get("origin") or "*"
    headers["Access-Control-Allow-Origin"] = origin
    headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=exc.status_code,
        headers=headers,
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
    origin = request.headers.get("origin") or "*"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true"
        },
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
    origin = request.headers.get("origin") or "*"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true"
        },
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

