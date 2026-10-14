"""
FastAPI application factory, middleware, structured logging, and exception handling for DocBench.
"""

import time
import uuid
import logging
from pathlib import Path
from typing import Callable
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from docbench.api.config import api_settings
from docbench.api.routes import (
    health_router,
    ingest_router,
    evaluate_router,
    benchmark_router,
)

# Configure logger
logger = logging.getLogger("docbench.api")
logging.basicConfig(
    level=getattr(logging, api_settings.log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="Document Ingestion Benchmark API",
        description="High-precision, deterministic PDF-to-Markdown document ingestion and evaluation REST API.",
        version=api_settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 1. CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Request Timing & Structured Logging Middleware
    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next: Callable) -> Response:
        # Extract or generate Request ID
        req_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        request.state.request_id = req_id

        # Determine approximate content length if available
        content_len = request.headers.get("content-length", "0")
        t_start = time.perf_counter()

        try:
            response: Response = await call_next(request)
            duration_ms = (time.perf_counter() - t_start) * 1000.0

            response.headers["X-Request-ID"] = req_id

            logger.info(
                "request_id=%s method=%s path=%s status=%d duration_ms=%.2f upload_bytes=%s",
                req_id,
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                content_len,
            )
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - t_start) * 1000.0
            logger.error(
                "request_id=%s method=%s path=%s duration_ms=%.2f error=%s",
                req_id,
                request.method,
                request.url.path,
                duration_ms,
                type(exc).__name__,
            )
            raise

    # 3. Custom Exception Handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        req_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": f"HTTP_{exc.status_code}",
                "detail": exc.detail,
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id} if req_id else None,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        req_id = getattr(request.state, "request_id", None)
        # Log error internally without exposing details to user
        logger.exception("request_id=%s unhandled_exception: %s", req_id, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "detail": "An internal error occurred while processing the request.",
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id} if req_id else None,
        )

    # 4. Include Route Handlers
    app.include_router(health_router)
    app.include_router(ingest_router)
    app.include_router(evaluate_router)
    app.include_router(benchmark_router)

    # 5. Serve Interactive Frontend Dashboard
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
        if (frontend_dir / "css").exists():
            app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
        if (frontend_dir / "js").exists():
            app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")

        @app.get("/", include_in_schema=False)
        async def serve_dashboard():
            index_path = frontend_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return JSONResponse({"status": "dashboard_ready", "detail": "index.html not found"})

    return app


app = create_app()
