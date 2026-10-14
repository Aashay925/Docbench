"""
Unit tests for deterministic PDF generation and ground truth manifests.
"""

import json
from pathlib import Path
from docbench.config import SYNTHETIC_DIR, MANIFESTS_DIR, REFERENCES_DIR, SAMPLE_DOCUMENTS
from docbench.generator.runner import generate_all
from docbench.ingestion.models import DocumentManifest


def test_generator_creates_all_files():
    """Verify that all 4 sample documents generate PDF, Ref MD, and Manifest JSON."""
    summary = generate_all()
    assert len(summary) == 4

    for doc_id in SAMPLE_DOCUMENTS:
        assert doc_id in summary
        pdf_path = Path(summary[doc_id]["pdf_path"])
        ref_path = Path(summary[doc_id]["ref_md_path"])
        manifest_path = Path(summary[doc_id]["manifest_path"])

        assert pdf_path.exists()
        assert ref_path.exists()
        assert manifest_path.exists()

        assert pdf_path.stat().st_size > 0
        assert ref_path.stat().st_size > 0
        assert manifest_path.stat().st_size > 0


def test_generator_determinism():
    """Verify that re-running generator produces exact bitwise identical PDF and MD hashes."""
    s1 = generate_all()
    s2 = generate_all()

    for doc_id in SAMPLE_DOCUMENTS:
        assert s1[doc_id]["pdf_sha256"] == s2[doc_id]["pdf_sha256"], f"PDF hash changed for {doc_id}"
        assert s1[doc_id]["ref_md_sha256"] == s2[doc_id]["ref_md_sha256"], f"Ref MD hash changed for {doc_id}"


def test_manifest_schema_conformance():
    """Verify that all generated manifest JSON files conform strictly to DocumentManifest schema."""
    for doc_id in SAMPLE_DOCUMENTS:
        manifest_path = MANIFESTS_DIR / f"{doc_id}.manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        manifest = DocumentManifest(**data)
        assert manifest.doc_id == doc_id
        assert manifest.page_count >= 1
        assert len(manifest.headings) >= 1
        assert len(manifest.reading_order_anchors) >= 1
