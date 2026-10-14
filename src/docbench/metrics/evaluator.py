"""
Benchmark evaluator orchestrating all metric evaluations per document and corpus-wide.
Implements dynamic weight re-normalization for applicable components and critical failure detection.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from docbench.config import (
    DEFAULT_METRIC_WEIGHTS,
    SYNTHETIC_DIR,
    REFERENCES_DIR,
    MANIFESTS_DIR,
    SAMPLE_DOCUMENTS,
)
from docbench.ingestion.models import (
    DocumentManifest,
    IngestionResult,
    DocumentEvaluation,
)
from docbench.ingestion.pipeline import ingest_document
from docbench.metrics.headings import evaluate_headings
from docbench.metrics.tables import evaluate_tables
from docbench.metrics.text import evaluate_text_completeness
from docbench.metrics.reading_order import evaluate_reading_order
from docbench.metrics.lists import evaluate_lists


def evaluate_document(
    ingestion_result: IngestionResult,
    manifest: DocumentManifest,
    reference_markdown: str,
    weights: Optional[Dict[str, float]] = None,
) -> DocumentEvaluation:
    """
    Evaluate a single document against its ground-truth manifest and reference markdown.
    Re-normalizes component weights across applicable structural dimensions so that
    non-applicable features (e.g. documents without tables or lists) do not inflate or skew scores.
    """
    effective_weights = weights or dict(DEFAULT_METRIC_WEIGHTS)

    heading_score = evaluate_headings(
        extracted=ingestion_result.extracted_headings,
        expected=manifest.headings,
    )

    table_score = evaluate_tables(
        extracted=ingestion_result.extracted_tables,
        expected=manifest.tables,
    )

    text_score = evaluate_text_completeness(
        extracted_markdown=ingestion_result.markdown_content,
        reference_markdown=reference_markdown,
    )

    reading_order_score = evaluate_reading_order(
        extracted_markdown=ingestion_result.markdown_content,
        anchors=manifest.reading_order_anchors,
    )

    list_score = evaluate_lists(
        extracted=ingestion_result.extracted_lists,
        expected=manifest.lists,
    )

    # Determine applicable components and scores
    component_scores: Dict[str, float] = {
        "text_completeness": text_score.composite_text_score,
        "reading_order_accuracy": reading_order_score.composite_order_score,
    }
    applicable_keys = ["text_completeness", "reading_order_accuracy"]

    if heading_score.is_applicable:
        component_scores["heading_f1"] = heading_score.f1
        applicable_keys.append("heading_f1")

    if table_score.is_applicable:
        component_scores["table_cell_accuracy"] = table_score.cell_accuracy
        applicable_keys.append("table_cell_accuracy")

    if list_score.is_applicable:
        component_scores["list_preservation_f1"] = list_score.f1
        applicable_keys.append("list_preservation_f1")

    # Re-normalize weights across applicable components
    weight_sum = sum(effective_weights.get(k, 0.20) for k in applicable_keys)
    if weight_sum > 0:
        normalized_weights = {
            k: effective_weights.get(k, 0.20) / weight_sum
            for k in applicable_keys
        }
    else:
        normalized_weights = {k: 1.0 / len(applicable_keys) for k in applicable_keys}

    composite = sum(normalized_weights[k] * component_scores[k] for k in applicable_keys)

    # Check for critical component failures (< 0.40 score on any applicable component)
    min_score = min(component_scores.values()) if component_scores else 0.0
    critical_failure = (min_score < 0.40)

    return DocumentEvaluation(
        doc_id=manifest.doc_id,
        heading_score=heading_score,
        table_score=table_score,
        text_score=text_score,
        reading_order_score=reading_order_score,
        list_score=list_score,
        composite_score=round(composite, 4),
        weights=effective_weights,
        applicable_weights={k: round(v, 4) for k, v in normalized_weights.items()},
        critical_failure=critical_failure,
        min_component_score=round(min_score, 4),
    )


def evaluate_corpus(
    synthetic_dir: Path = SYNTHETIC_DIR,
    references_dir: Path = REFERENCES_DIR,
    manifests_dir: Path = MANIFESTS_DIR,
    doc_ids: Optional[List[str]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Evaluate all documents in the corpus and return individual evaluations + aggregate stats.
    Ground truth manifests and reference files are read-only and never modified.
    """
    target_docs = doc_ids or SAMPLE_DOCUMENTS
    evaluations: List[DocumentEvaluation] = []
    ingestion_results: List[IngestionResult] = []

    for doc_id in target_docs:
        pdf_path = synthetic_dir / f"{doc_id}.pdf"
        manifest_path = manifests_dir / f"{doc_id}.manifest.json"
        ref_path = references_dir / f"{doc_id}.ref.md"

        if not pdf_path.exists():
            raise FileNotFoundError(f"Missing synthetic PDF: {pdf_path}")
        if not manifest_path.exists():
            raise FileNotFoundError(f"Missing manifest JSON: {manifest_path}")
        if not ref_path.exists():
            raise FileNotFoundError(f"Missing reference markdown: {ref_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
            manifest = DocumentManifest(**manifest_data)

        with open(ref_path, "r", encoding="utf-8") as f:
            reference_markdown = f.read()

        ingest_res = ingest_document(str(pdf_path), doc_id=doc_id)
        ingestion_results.append(ingest_res)

        eval_res = evaluate_document(
            ingestion_result=ingest_res,
            manifest=manifest,
            reference_markdown=reference_markdown,
            weights=weights,
        )
        evaluations.append(eval_res)

    # Compute aggregate averages only across applicable evaluations for each metric
    applicable_heading_f1 = [e.heading_score.f1 for e in evaluations if e.heading_score.is_applicable]
    applicable_table_acc = [e.table_score.cell_accuracy for e in evaluations if e.table_score.is_applicable]
    applicable_list_f1 = [e.list_score.f1 for e in evaluations if e.list_score.is_applicable]

    avg_heading_f1 = sum(applicable_heading_f1) / len(applicable_heading_f1) if applicable_heading_f1 else 1.0
    avg_table_cell_acc = sum(applicable_table_acc) / len(applicable_table_acc) if applicable_table_acc else 1.0
    avg_text_comp = sum(e.text_score.composite_text_score for e in evaluations) / len(evaluations)
    avg_order_acc = sum(e.reading_order_score.composite_order_score for e in evaluations) / len(evaluations)
    avg_list_f1 = sum(applicable_list_f1) / len(applicable_list_f1) if applicable_list_f1 else 1.0
    avg_composite = sum(e.composite_score for e in evaluations) / len(evaluations)
    avg_duration_ms = sum(r.duration_ms for r in ingestion_results) / len(ingestion_results)

    critical_failures_count = sum(1 for e in evaluations if e.critical_failure)

    aggregates = {
        "avg_heading_f1": round(avg_heading_f1, 4),
        "avg_table_cell_accuracy": round(avg_table_cell_acc, 4),
        "avg_text_completeness": round(avg_text_comp, 4),
        "avg_reading_order_accuracy": round(avg_order_acc, 4),
        "avg_list_preservation_f1": round(avg_list_f1, 4),
        "avg_composite_score": round(avg_composite, 4),
        "avg_ingestion_duration_ms": round(avg_duration_ms, 2),
        "critical_failures_count": critical_failures_count,
    }

    return {
        "evaluations": evaluations,
        "ingestion_results": ingestion_results,
        "aggregates": aggregates,
        "overall_benchmark_score": round(avg_composite * 100.0, 2),
    }
