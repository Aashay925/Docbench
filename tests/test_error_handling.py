"""
Unit tests for edge cases and error handling during ingestion and evaluation.
"""

import pytest
from pathlib import Path
from pydantic import ValidationError

from docbench.ingestion.pipeline import ingest_document
from docbench.ingestion.models import DocumentManifest


def test_ingest_missing_file_raises_error():
    """Verify ingestion of a non-existent file path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        ingest_document("non_existent_document_12345.pdf")


def test_ingest_invalid_pdf_raises_error(tmp_path: Path):
    """Verify ingestion of a corrupted / non-PDF file raises RuntimeError."""
    corrupted_file = tmp_path / "corrupted.pdf"
    corrupted_file.write_text("NOT A VALID PDF BINARY CONTENT", encoding="utf-8")

    with pytest.raises(RuntimeError):
        ingest_document(str(corrupted_file))


def test_malformed_manifest_raises_validation_error():
    """Verify DocumentManifest raises ValidationError when required fields are missing."""
    with pytest.raises(ValidationError):
        # Missing doc_id, filename, title, page_count
        DocumentManifest(title="Incomplete")
