"""
Generate CSV summary report for tabular benchmark analysis with applicability and status transparency.
"""

import io
import csv
from typing import Dict, Any, List
from docbench.ingestion.models import DocumentEvaluation, RepeatabilityScore


def generate_csv_report(
    eval_results: Dict[str, Any],
    repeat_results: Dict[str, Any],
) -> str:
    """
    Format benchmark evaluations and repeatability metrics into standard CSV.
    Uses 'N/A' for non-applicable metrics and adds status column.
    """
    evaluations: List[DocumentEvaluation] = eval_results["evaluations"]
    aggregates: Dict[str, float] = eval_results["aggregates"]
    repeat_scores: List[RepeatabilityScore] = repeat_results["scores"]
    repeat_map = {rs.doc_id: rs for rs in repeat_scores}
    ingest_map = {r.doc_id: r for r in eval_results.get("ingestion_results", [])}

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    # Header
    writer.writerow([
        "doc_id",
        "heading_f1",
        "table_cell_accuracy",
        "text_completeness",
        "reading_order_accuracy",
        "list_preservation_f1",
        "composite_score",
        "status",
        "duration_ms",
        "sha256_stability",
        "mean_latency_ms",
        "std_latency_ms",
    ])

    # Per-document rows
    for ev in evaluations:
        rs = repeat_map.get(ev.doc_id)
        dur = ingest_map[ev.doc_id].duration_ms if ev.doc_id in ingest_map else 0.0
        stability = rs.sha256_identical_rate if rs else 1.0
        mean_dur = rs.mean_duration_ms if rs else dur
        std_dur = rs.std_duration_ms if rs else 0.0

        h_val = f"{ev.heading_score.f1:.4f}" if ev.heading_score.is_applicable else "N/A"
        t_val = f"{ev.table_score.cell_accuracy:.4f}" if ev.table_score.is_applicable else "N/A"
        l_val = f"{ev.list_score.f1:.4f}" if ev.list_score.is_applicable else "N/A"
        status_val = "PASS" if not ev.critical_failure else "CRITICAL_FAIL"

        writer.writerow([
            ev.doc_id,
            h_val,
            t_val,
            f"{ev.text_score.composite_text_score:.4f}",
            f"{ev.reading_order_score.composite_order_score:.4f}",
            l_val,
            f"{ev.composite_score:.4f}",
            status_val,
            f"{dur:.2f}",
            f"{stability:.4f}",
            f"{mean_dur:.2f}",
            f"{std_dur:.2f}",
        ])

    # Aggregate row
    crit_count = aggregates.get("critical_failures_count", 0)
    agg_status = "ALL_PASS" if crit_count == 0 else f"{crit_count}_FAILS"

    writer.writerow([
        "CORPUS_AVERAGE",
        f"{aggregates['avg_heading_f1']:.4f}",
        f"{aggregates['avg_table_cell_accuracy']:.4f}",
        f"{aggregates['avg_text_completeness']:.4f}",
        f"{aggregates['avg_reading_order_accuracy']:.4f}",
        f"{aggregates['avg_list_preservation_f1']:.4f}",
        f"{aggregates['avg_composite_score']:.4f}",
        agg_status,
        f"{aggregates['avg_ingestion_duration_ms']:.2f}",
        f"{repeat_results['overall_identical_rate']:.4f}",
        f"{repeat_results['avg_mean_duration_ms']:.2f}",
        f"{repeat_results['avg_std_duration_ms']:.2f}",
    ])

    return output.getvalue()
