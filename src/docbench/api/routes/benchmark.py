"""
Benchmark summary reporting endpoint.
"""

from fastapi import APIRouter
from docbench.api.schemas import BenchmarkSummaryResponse
from docbench.api.service import benchmark_service

router = APIRouter(prefix="/v1", tags=["Benchmark"])


@router.get(
    "/benchmark/summary",
    response_model=BenchmarkSummaryResponse,
    summary="Get Latest Benchmark Summary",
)
async def get_benchmark_summary_endpoint():
    """
    Returns latest benchmark evaluation summary across the corpus.
    Uses cached benchmark results when available to minimize redundant computation.
    """
    data = await benchmark_service.get_benchmark_summary()

    crit_count = data.get("aggregates", {}).get("critical_failures_count", 0)
    status_str = "ALL_PASS" if crit_count == 0 else f"{crit_count}_CRITICAL_FAILS"

    return BenchmarkSummaryResponse(
        is_cached=data.get("is_cached", True),
        timestamp=data.get("timestamp", ""),
        overall_benchmark_score=data.get("overall_benchmark_score", 0.0),
        status=status_str,
        critical_failures_count=crit_count,
        aggregates=data.get("aggregates", {}),
        repeatability_summary=data.get("repeatability_summary", {}),
        document_summaries=data.get("document_evaluations", []),
    )


@router.get(
    "/benchmark/samples/{doc_id}",
    summary="Download Synthetic Sample PDF",
)
async def get_sample_pdf_endpoint(doc_id: str):
    """Serve a synthetic sample PDF for interactive testing."""
    from fastapi import HTTPException, status
    from fastapi.responses import FileResponse
    from docbench.config import SYNTHETIC_DIR

    pdf_path = SYNTHETIC_DIR / f"{doc_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample document '{doc_id}' not found.",
        )
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{doc_id}.pdf",
    )
