"""
API Route exports.
"""

from docbench.api.routes.health import router as health_router
from docbench.api.routes.ingest import router as ingest_router
from docbench.api.routes.evaluate import router as evaluate_router
from docbench.api.routes.benchmark import router as benchmark_router

__all__ = [
    "health_router",
    "ingest_router",
    "evaluate_router",
    "benchmark_router",
]
