"""
Runner to generate all synthetic PDFs, reference markdown, and ground-truth manifests.
"""

import io
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List
from pypdf import PdfReader, PdfWriter

from docbench.config import (
    SYNTHETIC_DIR,
    REFERENCES_DIR,
    MANIFESTS_DIR,
    ensure_directories,
)
from docbench.generator.contract import build_contract_pdf, get_contract_data
from docbench.generator.tabular import build_tabular_pdf, get_tabular_data
from docbench.generator.multipage import build_multipage_pdf, get_multipage_data
from docbench.generator.edgecases import build_edgecases_pdf, get_edgecases_data


def make_pdf_deterministic(raw_pdf_bytes: bytes) -> bytes:
    """
    Post-process PDF bytes to guarantee deterministic SHA-256 hashes across runs.
    Normalizes metadata and ensures repeatable trailer structure.
    """
    reader = PdfReader(io.BytesIO(raw_pdf_bytes))
    writer = PdfWriter()
    writer.append(reader)
    writer.add_metadata({
        "/CreationDate": "D:20260101000000+00'00'",
        "/ModDate": "D:20260101000000+00'00'",
        "/Producer": "DocBench Deterministic Generator v1.0",
        "/Creator": "ReportLab & PyPDF",
    })
    out_buf = io.BytesIO()
    writer.write(out_buf)
    return out_buf.getvalue()


def generate_all(
    synthetic_dir: Path = SYNTHETIC_DIR,
    references_dir: Path = REFERENCES_DIR,
    manifests_dir: Path = MANIFESTS_DIR,
) -> Dict[str, Dict[str, Any]]:
    """
    Generate all 4 synthetic documents:
    - PDF in synthetic_dir
    - Reference Markdown in references_dir
    - Manifest JSON in manifests_dir

    Returns a summary dictionary with file paths, sizes, and hashes.
    """
    ensure_directories()
    synthetic_dir.mkdir(parents=True, exist_ok=True)
    references_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)

    generators = [
        ("contract", build_contract_pdf, get_contract_data),
        ("tabular_report", build_tabular_pdf, get_tabular_data),
        ("multipage_report", build_multipage_pdf, get_multipage_data),
        ("edge_cases", build_edgecases_pdf, get_edgecases_data),
    ]

    summary = {}

    for doc_id, build_fn, get_data_fn in generators:
        manifest, ref_md = get_data_fn()

        # Compute reference MD hash and write
        ref_md_bytes = ref_md.encode("utf-8")
        ref_md_sha = hashlib.sha256(ref_md_bytes).hexdigest()
        manifest.reference_markdown_sha256 = ref_md_sha

        ref_md_path = references_dir / f"{doc_id}.ref.md"
        with open(ref_md_path, "w", encoding="utf-8") as f:
            f.write(ref_md)

        # Generate deterministic PDF
        raw_pdf = build_fn()
        deterministic_pdf = make_pdf_deterministic(raw_pdf)
        pdf_sha = hashlib.sha256(deterministic_pdf).hexdigest()

        pdf_path = synthetic_dir / f"{doc_id}.pdf"
        with open(pdf_path, "wb") as f:
            f.write(deterministic_pdf)

        # Write manifest JSON
        manifest_path = manifests_dir / f"{doc_id}.manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        summary[doc_id] = {
            "pdf_path": str(pdf_path),
            "pdf_sha256": pdf_sha,
            "pdf_size_bytes": len(deterministic_pdf),
            "ref_md_path": str(ref_md_path),
            "ref_md_sha256": ref_md_sha,
            "manifest_path": str(manifest_path),
            "headings_count": len(manifest.headings),
            "tables_count": len(manifest.tables),
            "lists_count": len(manifest.lists),
            "page_count": manifest.page_count,
        }

    return summary
