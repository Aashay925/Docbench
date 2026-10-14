"""
Health and version endpoints.
"""

from datetime import datetime, timezone
from fastapi import APIRouter

from docbench.api.config import api_settings
from docbench.api.schemas import HealthResponse, VersionResponse

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse, summary="Service Health Check")
async def health_check():
    """Return operational health status."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/version", response_model=VersionResponse, summary="Application Version")
async def version_info():
    """Return application and API semantic version information."""
    return VersionResponse(
        app_name="document-ingestion-benchmark",
        app_version=api_settings.app_version,
        api_version=api_settings.api_version,
    )
