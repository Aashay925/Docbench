"""
Document Ingestion Pipeline.
Handles end-to-end PDF processing, wall-clock timing, SHA-256 hashing, and diagnostics.
"""

import time
import hashlib
from pathlib import Path
from typing import Optional

from docbench.ingestion.models import IngestionResult, DiagnosticMessage
from docbench.ingestion.parser import parse_pdf
from docbench.ingestion.converter import convert_document


def ingest_document(pdf_path: str, doc_id: Optional[str] = None, output_md_path: Optional[str] = None) -> IngestionResult:
    """
    Ingest a PDF file, convert to Markdown, compute hashes, runtime, and extracted primitives.
    """
    path_obj = Path(pdf_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Input PDF does not exist: {pdf_path}")

    derived_doc_id = doc_id or path_obj.stem

    # Read binary bytes and compute SHA-256
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    pdf_sha256 = hashlib.sha256(pdf_bytes).hexdigest()

    # Time ingestion execution precisely in milliseconds
    t_start = time.perf_counter()
    try:
        parsed_doc = parse_pdf(pdf_path)
        markdown_content, headings, tables, lists, text_blocks, diagnostics = convert_document(parsed_doc)
        page_count = len(parsed_doc.pages)
    except Exception as exc:
        t_end = time.perf_counter()
        duration_ms = (t_end - t_start) * 1000.0
        raise RuntimeError(f"Error during PDF ingestion of {pdf_path}: {exc}") from exc

    t_end = time.perf_counter()
    duration_ms = (t_end - t_start) * 1000.0

    # Compute Markdown SHA-256
    md_bytes = markdown_content.encode("utf-8")
    md_sha256 = hashlib.sha256(md_bytes).hexdigest()

    # Diagnostic info: check for empty output
    if not markdown_content.strip():
        diagnostics.append(
            DiagnosticMessage(
                level="WARNING",
                message=f"Converted markdown for {path_obj.name} is empty.",
                context={"pdf_size": len(pdf_bytes), "page_count": page_count},
            )
        )

    # Optionally persist markdown output
    if output_md_path:
        out_p = Path(output_md_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(markdown_content)

    return IngestionResult(
        doc_id=derived_doc_id,
        source_pdf=str(pdf_path),
        pdf_sha256=pdf_sha256,
        markdown_content=markdown_content,
        markdown_sha256=md_sha256,
        duration_ms=round(duration_ms, 2),
        page_count=page_count,
        extracted_headings=headings,
        extracted_tables=tables,
        extracted_lists=lists,
        extracted_text_blocks=text_blocks,
        diagnostics=diagnostics,
    )
