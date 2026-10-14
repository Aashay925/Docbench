"""
Request and response Pydantic schemas for DocBench FastAPI REST Service.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service health indicator")
    timestamp: str = Field(..., description="UTC ISO-8601 timestamp")


class VersionResponse(BaseModel):
    app_name: str = Field(default="document-ingestion-benchmark")
    app_version: str = Field(..., description="Application semantic version")
    api_version: str = Field(..., description="API route version namespace")


class IngestResponse(BaseModel):
    filename: str = Field(..., description="Sanitized original document filename")
    page_count: int = Field(..., description="Total pages processed")
    duration_ms: float = Field(..., description="Total processing wall-clock latency in milliseconds")
    pdf_sha256: str = Field(..., description="SHA-256 hash of the received PDF binary")
    markdown_sha256: str = Field(..., description="SHA-256 hash of the generated Markdown")
    markdown_content: str = Field(..., description="Extracted conservative Markdown text")
    has_usable_text: bool = Field(..., description="True if non-whitespace text was successfully extracted")
    extracted_headings_count: int = Field(default=0)
    extracted_tables_count: int = Field(default=0)
    extracted_lists_count: int = Field(default=0)
    diagnostics: List[Dict[str, Any]] = Field(default_factory=list)


class EvaluateResponse(BaseModel):
    filename: str = Field(..., description="Sanitized original document filename")
    reference_id: str = Field(..., description="Identifier of trusted ground-truth reference used")
    composite_score: float = Field(..., description="Overall weighted score across applicable features (0.0 to 1.0)")
    status: str = Field(..., description="'PASS' or 'CRITICAL_FAIL'")
    critical_failure: bool = Field(..., description="True if any applicable component scored below threshold (<0.40)")
    min_component_score: float = Field(..., description="Minimum score among applicable components")
    applicable_weights: Dict[str, float] = Field(default_factory=dict)
    heading_score: Dict[str, Any] = Field(default_factory=dict)
    table_score: Dict[str, Any] = Field(default_factory=dict)
    text_score: Dict[str, Any] = Field(default_factory=dict)
    reading_order_score: Dict[str, Any] = Field(default_factory=dict)
    list_score: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = Field(..., description="Total evaluation latency in milliseconds")
    diagnostics: List[Dict[str, Any]] = Field(default_factory=list)
    reference_markdown: Optional[str] = Field(default=None, description="Ground-truth reference Markdown for side-by-side comparison")
    extracted_markdown: Optional[str] = Field(default=None, description="Extracted Markdown content")


class BenchmarkSummaryResponse(BaseModel):
    is_cached: bool = Field(..., description="True if returned from cached benchmark artifact; False if computed")
    timestamp: str = Field(..., description="Benchmark execution timestamp")
    overall_benchmark_score: float = Field(..., description="Corpus-wide score (0 to 100)")
    status: str = Field(..., description="Corpus health status: 'ALL_PASS' or count of failures")
    critical_failures_count: int = Field(default=0)
    aggregates: Dict[str, Any] = Field(default_factory=dict)
    repeatability_summary: Dict[str, Any] = Field(default_factory=dict)
    document_summaries: List[Dict[str, Any]] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Short error code or category")
    detail: str = Field(..., description="Actionable human-readable error explanation")
    request_id: Optional[str] = Field(default=None, description="Unique trace identifier")
