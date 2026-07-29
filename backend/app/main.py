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

# Mount modular routers under /api/v1 prefix
app.include_router(api_router, prefix=settings.API_V1_STR)
# Direct route mount for convenience
app.include_router(api_router)

