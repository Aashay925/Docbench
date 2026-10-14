"""
Application service layer bridging FastAPI routes to the core docbench ingestion and evaluation engine.
Executes CPU-bound parsing asynchronously in a thread pool.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from fastapi import HTTPException, status

from docbench.config import (
    MANIFESTS_DIR,
    REFERENCES_DIR,
    OUTPUTS_DIR,
    SAMPLE_DOCUMENTS,
)
from docbench.ingestion.models import DocumentManifest, IngestionResult, DocumentEvaluation
from docbench.ingestion.pipeline import ingest_document
from docbench.metrics.evaluator import evaluate_document, evaluate_corpus
from docbench.repeatability.runner import run_repeatability_test
from docbench.reporting import generate_and_save_all_reports


class BenchmarkService:
    """Service handling PDF ingestion, evaluation against trusted references, and summaries."""

    @staticmethod
    def get_trusted_references() -> Dict[str, Tuple[Path, Path]]:
        """
        Return the mapping of trusted ground-truth reference IDs to their manifest and reference MD files.
        References are strictly verified against the canonical corpus.
        """
        refs = {}
        for doc_id in SAMPLE_DOCUMENTS:
            manifest_p = MANIFESTS_DIR / f"{doc_id}.manifest.json"
            ref_md_p = REFERENCES_DIR / f"{doc_id}.ref.md"
            if manifest_p.exists() and ref_md_p.exists():
                refs[doc_id] = (manifest_p, ref_md_p)
        return refs

    @staticmethod
    def get_reference_descriptions() -> list[Dict[str, str]]:
        """Return list of available trusted ground-truth reference IDs and descriptive titles."""
        titles = {
            "contract": "Master Services Agreement (Contract)",
            "tabular_report": "Q4 Financial & Operating Metrics (Tabular Report)",
            "multipage_report": "Distributed Ingestion Engine Architecture (Multi-Page)",
            "edge_cases": "Typography & Stress Test (Accents, Symbols, Nested Lists)",
        }
        refs = BenchmarkService.get_trusted_references()
        return [
            {"id": ref_id, "title": titles.get(ref_id, ref_id)}
            for ref_id in sorted(refs.keys())
        ]

    async def get_reference_data(self, reference_id: str) -> Dict[str, Any]:
        """Fetch ground-truth reference markdown and manifest."""
        trusted_refs = self.get_trusted_references()
        if reference_id not in trusted_refs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reference document '{reference_id}' not found.",
            )
        manifest_p, ref_md_p = trusted_refs[reference_id]
        manifest_raw = await asyncio.to_thread(manifest_p.read_text, "utf-8")
        ref_md = await asyncio.to_thread(ref_md_p.read_text, "utf-8")
        manifest = json.loads(manifest_raw)
        return {
            "reference_id": reference_id,
            "reference_markdown": ref_md,
            "manifest": manifest,
        }

    async def ingest_pdf(self, temp_pdf_path: Path, filename: str) -> IngestionResult:
        """
        Execute PDF ingestion asynchronously offloaded to a thread pool.
        """
        stem = Path(filename).stem
        try:
            # Run CPU-bound parsing in a background thread to prevent blocking event loop
            result = await asyncio.to_thread(ingest_document, str(temp_pdf_path), doc_id=stem)
            return result
        except Exception as exc:
            # Do not leak internal filesystem paths in API responses
            clean_msg = str(exc).replace(str(temp_pdf_path), filename)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse and extract PDF: {clean_msg}",
            ) from exc

    async def evaluate_pdf(
        self,
        temp_pdf_path: Path,
        filename: str,
        reference_id: Optional[str] = None,
    ) -> Tuple[DocumentEvaluation, IngestionResult, str, str]:
        """
        Ingest uploaded PDF and evaluate against a verified, trusted ground-truth reference.
        """
        trusted_refs = self.get_trusted_references()
        if not trusted_refs:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Corpus reference ground truth manifests are not initialized on server.",
            )

        # Associate with reference_id, or infer from sanitized filename stem
        chosen_ref_id = reference_id
        if not chosen_ref_id:
            stem = Path(filename).stem.lower()
            if stem in trusted_refs:
                chosen_ref_id = stem

        if not chosen_ref_id or chosen_ref_id not in trusted_refs:
            available = list(trusted_refs.keys())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unknown or missing reference document ID: '{chosen_ref_id}'. "
                    f"Available trusted reference IDs: {available}. "
                    f"Specify reference_id explicitly or upload a file matching one of these names."
                ),
            )

        manifest_path, ref_md_path = trusted_refs[chosen_ref_id]

        # Load reference data safely (read-only)
        try:
            manifest_json = await asyncio.to_thread(manifest_path.read_text, "utf-8")
            ref_md = await asyncio.to_thread(ref_md_path.read_text, "utf-8")
            manifest = DocumentManifest.model_validate_json(manifest_json)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load trusted reference manifest for '{chosen_ref_id}'.",
            ) from exc

        # Ingest uploaded PDF
        ingest_res = await self.ingest_pdf(temp_pdf_path, filename)

        # Evaluate against ground truth in thread pool
        try:
            evaluation = await asyncio.to_thread(
                evaluate_document,
                ingestion_result=ingest_res,
                manifest=manifest,
                reference_markdown=ref_md,
            )
            return evaluation, ingest_res, chosen_ref_id, ref_md
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Evaluation execution failed: {exc}",
            ) from exc

    async def get_benchmark_summary(self) -> Dict[str, Any]:
        """
        Retrieve latest benchmark summary. Uses cached outputs/benchmark_report.json if present
        to avoid running an expensive benchmark run on every request.
        """
        cached_json_path = OUTPUTS_DIR / "benchmark_report.json"
        if cached_json_path.exists():
            try:
                content = await asyncio.to_thread(cached_json_path.read_text, "utf-8")
                data = json.loads(content)
                data["is_cached"] = True
                return data
            except Exception:
                pass  # Fallback to computing if cache read fails

        # Compute benchmark if no cache exists
        eval_results = await asyncio.to_thread(evaluate_corpus)
        repeat_results = await asyncio.to_thread(run_repeatability_test, runs=3)
        saved = await asyncio.to_thread(
            generate_and_save_all_reports,
            eval_results=eval_results,
            repeat_results=repeat_results,
            output_dir=OUTPUTS_DIR,
            print_console=False,
        )

        with open(saved["json"], "r", encoding="utf-8") as f:
            computed_data = json.load(f)
        computed_data["is_cached"] = False
        return computed_data


benchmark_service = BenchmarkService()
