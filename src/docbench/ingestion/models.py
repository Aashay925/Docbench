"""
Data models for document ingestion, ground-truth manifests, and evaluation results.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

# --- Structure & Manifest Models ---

class HeadingItem(BaseModel):
    level: int = Field(..., description="Heading level, e.g. 1 for #, 2 for ##, 3 for ###")
    text: str = Field(..., description="Heading text content without markdown markers")
    page: Optional[int] = Field(default=None, description="Page number where heading appears (1-indexed)")


class TableBlock(BaseModel):
    table_id: int = Field(default=1, description="Sequential table index in document")
    headers: List[str] = Field(default_factory=list, description="Column header strings")
    rows: List[List[str]] = Field(default_factory=list, description="Matrix of table row cell values")
    page: Optional[int] = Field(default=None, description="Page number where table appears")


class ListItem(BaseModel):
    text: str = Field(..., description="Text content of the list item without bullet/number prefix")
    list_type: Literal["bullet", "numbered"] = Field(..., description="Type of list item")
    depth: int = Field(default=0, description="Nesting level (0-indexed)")
    page: Optional[int] = Field(default=None, description="Page number where item appears")


class DocumentManifest(BaseModel):
    doc_id: str = Field(..., description="Unique document identifier, e.g. 'contract'")
    filename: str = Field(..., description="Filename of source PDF, e.g. 'contract.pdf'")
    title: str = Field(..., description="Document title")
    page_count: int = Field(..., description="Expected number of pages")
    headings: List[HeadingItem] = Field(default_factory=list, description="Expected headings in order")
    tables: List[TableBlock] = Field(default_factory=list, description="Expected table matrices")
    lists: List[ListItem] = Field(default_factory=list, description="Expected list items in order")
    text_blocks: List[str] = Field(default_factory=list, description="Key verbatim text blocks / paragraphs")
    reading_order_anchors: List[str] = Field(
        default_factory=list,
        description="Key anchors representing the expected reading sequence throughout the document"
    )
    expected_char_count: int = Field(default=0, description="Approximate expected character count")
    expected_word_count: int = Field(default=0, description="Approximate expected word count")
    reference_markdown_sha256: Optional[str] = Field(default=None, description="SHA-256 of reference markdown")


# --- Ingestion & Diagnostics Models ---

class DiagnosticMessage(BaseModel):
    level: Literal["INFO", "WARNING", "ERROR"] = Field(...)
    message: str = Field(...)
    context: Dict[str, Any] = Field(default_factory=dict)


class IngestionResult(BaseModel):
    doc_id: str
    source_pdf: str
    pdf_sha256: str
    markdown_content: str
    markdown_sha256: str
    duration_ms: float
    page_count: int
    extracted_headings: List[HeadingItem] = Field(default_factory=list)
    extracted_tables: List[TableBlock] = Field(default_factory=list)
    extracted_lists: List[ListItem] = Field(default_factory=list)
    extracted_text_blocks: List[str] = Field(default_factory=list)
    diagnostics: List[DiagnosticMessage] = Field(default_factory=list)


# --- Metric Scores ---

class HeadingScore(BaseModel):
    precision: float
    recall: float
    f1: float
    matched_count: int
    expected_count: int
    extracted_count: int
    order_accuracy: float = Field(default=1.0, description="Relative sequence order preservation among matched headings")
    is_applicable: bool = Field(default=True, description="False if document has no headings in ground truth")


class TableScore(BaseModel):
    table_detection_precision: float
    table_detection_recall: float
    cell_accuracy: float
    matched_cells: int
    total_expected_cells: int
    total_extracted_cells: int
    table_count_expected: int = Field(default=0)
    table_count_extracted: int = Field(default=0)
    is_applicable: bool = Field(default=True, description="False if document has no tables in ground truth")


class TextCompletenessScore(BaseModel):
    char_recall: float
    token_recall: float
    token_precision: float = Field(default=1.0, description="Precision of extracted tokens against reference (penalizes hallucinations/duplications)")
    token_f1: float = Field(default=1.0, description="Harmonic mean of token precision and recall")
    sequence_similarity: float
    jaccard_similarity: float
    length_ratio: float = Field(default=1.0, description="Ratio of min/max text length to penalize severe length mismatch")
    composite_text_score: float


class ReadingOrderScore(BaseModel):
    lcs_ratio: float
    kendall_tau: float
    anchor_count_expected: int = Field(default=0)
    anchor_count_found: int = Field(default=0)
    composite_order_score: float


class ListPreservationScore(BaseModel):
    precision: float
    recall: float
    f1: float
    matched_items: int
    expected_items: int
    extracted_items: int
    depth_accuracy: float = Field(default=1.0, description="Accuracy of hierarchical nesting depth for matched list items")
    order_accuracy: float = Field(default=1.0, description="Relative sequence order preservation among matched list items")
    is_applicable: bool = Field(default=True, description="False if document has no list items in ground truth")


class DocumentEvaluation(BaseModel):
    doc_id: str
    heading_score: HeadingScore
    table_score: TableScore
    text_score: TextCompletenessScore
    reading_order_score: ReadingOrderScore
    list_score: ListPreservationScore
    composite_score: float
    weights: Dict[str, float]
    applicable_weights: Dict[str, float] = Field(default_factory=dict, description="Normalized weights applied across applicable components")
    critical_failure: bool = Field(default=False, description="True if any applicable component scored below critical threshold (<0.40)")
    min_component_score: float = Field(default=1.0, description="Minimum score across applicable components")


class RepeatabilityScore(BaseModel):
    doc_id: str
    runs: int
    sha256_identical_rate: float
    unique_hashes: List[str]
    mean_duration_ms: float
    std_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float


class CorpusBenchmarkReport(BaseModel):
    timestamp: str
    system_info: Dict[str, Any]
    document_evaluations: List[DocumentEvaluation]
    repeatability_scores: List[RepeatabilityScore]
    aggregate_metrics: Dict[str, float]
    overall_benchmark_score: float
