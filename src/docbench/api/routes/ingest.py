"""
PDF ingestion endpoint.
"""

from fastapi import APIRouter, UploadFile, File
from docbench.api.schemas import IngestResponse
from docbench.api.security import bounded_temp_pdf
from docbench.api.service import benchmark_service

router = APIRouter(prefix="/v1", tags=["Ingestion"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Ingest PDF and Convert to Markdown",
)
async def ingest_document_endpoint(
    file: UploadFile = File(..., description="Binary PDF file to ingest"),
):
    """
    Accepts an uploaded PDF document, safely streams to an isolated temporary file,
    validates format boundaries, extracts conservative Markdown, and computes structural diagnostics.
    Temporary files are immediately cleaned up upon completion.
    """
    async with bounded_temp_pdf(file) as (temp_path, sanitized_name, file_size):
        res = await benchmark_service.ingest_pdf(temp_path, sanitized_name)

        has_usable = bool(res.markdown_content and res.markdown_content.strip())

        return IngestResponse(
            filename=sanitized_name,
            page_count=res.page_count,
            duration_ms=res.duration_ms,
            pdf_sha256=res.pdf_sha256,
            markdown_sha256=res.markdown_sha256,
            markdown_content=res.markdown_content,
            has_usable_text=has_usable,
            extracted_headings_count=len(res.extracted_headings),
            extracted_tables_count=len(res.extracted_tables),
            extracted_lists_count=len(res.extracted_lists),
            diagnostics=[d.model_dump() for d in res.diagnostics],
        )
