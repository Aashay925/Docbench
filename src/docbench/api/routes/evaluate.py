"""
PDF evaluation endpoint against trusted ground truth.
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from docbench.api.schemas import EvaluateResponse
from docbench.api.security import bounded_temp_pdf
from docbench.api.service import benchmark_service

router = APIRouter(prefix="/v1", tags=["Evaluation"])


@router.post(
    "/evaluate",
    response_model=EvaluateResponse,
    summary="Evaluate PDF Ingestion against Ground-Truth Reference",
)
async def evaluate_document_endpoint(
    file: UploadFile = File(..., description="PDF document to evaluate"),
    reference_id: Optional[str] = Form(
        None,
        description="Explicit trusted reference ID (e.g. 'contract', 'tabular_report', 'multipage_report', 'edge_cases')",
    ),
):
    """
    Evaluates an uploaded PDF document against verified ground truth.
    Returns per-component structural scores, dynamic weight allocations,
    critical failure warnings, and overall composite score.
    """
    async with bounded_temp_pdf(file) as (temp_path, sanitized_name, file_size):
        eval_res, ingest_res, matched_ref_id, ref_md = await benchmark_service.evaluate_pdf(
            temp_pdf_path=temp_path,
            filename=sanitized_name,
            reference_id=reference_id,
        )

        status_str = "PASS" if not eval_res.critical_failure else "CRITICAL_FAIL"

        return EvaluateResponse(
            filename=sanitized_name,
            reference_id=matched_ref_id,
            composite_score=eval_res.composite_score,
            status=status_str,
            critical_failure=eval_res.critical_failure,
            min_component_score=eval_res.min_component_score,
            applicable_weights=eval_res.applicable_weights,
            heading_score=eval_res.heading_score.model_dump(),
            table_score=eval_res.table_score.model_dump(),
            text_score=eval_res.text_score.model_dump(),
            reading_order_score=eval_res.reading_order_score.model_dump(),
            list_score=eval_res.list_score.model_dump(),
            duration_ms=ingest_res.duration_ms,
            diagnostics=[d.model_dump() for d in ingest_res.diagnostics],
            reference_markdown=ref_md,
            extracted_markdown=ingest_res.markdown_content,
        )


@router.get(
    "/references",
    summary="List Trusted Benchmark Reference Documents",
)
async def list_trusted_references():
    """Returns list of available trusted ground-truth reference IDs and descriptive titles."""
    return benchmark_service.get_reference_descriptions()


@router.get(
    "/references/{reference_id}",
    summary="Get Trusted Reference Document Details",
)
async def get_reference_details(reference_id: str):
    """Returns ground-truth reference markdown and manifest details."""
    return await benchmark_service.get_reference_data(reference_id)
