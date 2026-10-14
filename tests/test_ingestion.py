"""
Unit tests for PDF ingestion pipeline and parsing primitives.
"""

from pathlib import Path
from docbench.config import SYNTHETIC_DIR, SAMPLE_DOCUMENTS
from docbench.ingestion.pipeline import ingest_document


def test_ingestion_all_corpus_documents():
    """Verify ingestion pipeline processes all 4 synthetic PDFs successfully."""
    for doc_id in SAMPLE_DOCUMENTS:
        pdf_path = SYNTHETIC_DIR / f"{doc_id}.pdf"
        result = ingest_document(str(pdf_path), doc_id=doc_id)

        assert result.doc_id == doc_id
        assert len(result.pdf_sha256) == 64
        assert len(result.markdown_sha256) == 64
        assert result.duration_ms > 0
        assert result.page_count >= 1
        assert len(result.markdown_content) > 100
        assert len(result.extracted_headings) >= 1


def test_ingestion_output_persistence(tmp_path: Path):
    """Verify that ingest_document writes markdown to output_md_path when specified."""
    pdf_path = SYNTHETIC_DIR / "contract.pdf"
    out_file = tmp_path / "custom_contract.md"

    result = ingest_document(str(pdf_path), doc_id="contract", output_md_path=str(out_file))
    assert out_file.exists()
    assert out_file.read_text(encoding="utf-8") == result.markdown_content


def test_multipage_page_count():
    """Verify multi-page report correctly identifies all 3 pages."""
    pdf_path = SYNTHETIC_DIR / "multipage_report.pdf"
    result = ingest_document(str(pdf_path))
    assert result.page_count == 3
