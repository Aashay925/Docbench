"""
Generate structured JSON benchmark report.
"""

import json
from typing import Dict, Any


def generate_json_report(
    eval_results: Dict[str, Any],
    repeat_results: Dict[str, Any],
    system_info: Dict[str, Any],
) -> str:
    """
    Format benchmark results into structured JSON string.
    """
    report_dict = {
        "timestamp": system_info.get("timestamp"),
        "system_info": system_info,
        "overall_benchmark_score": eval_results["overall_benchmark_score"],
        "aggregates": eval_results["aggregates"],
        "repeatability_summary": {
            "runs": repeat_results["runs"],
            "overall_identical_rate": repeat_results["overall_identical_rate"],
            "avg_mean_duration_ms": repeat_results["avg_mean_duration_ms"],
            "avg_std_duration_ms": repeat_results["avg_std_duration_ms"],
        },
        "document_evaluations": [
            ev.model_dump(mode="json") for ev in eval_results["evaluations"]
        ],
        "ingestion_summaries": [
            {
                "doc_id": r.doc_id,
                "pdf_sha256": r.pdf_sha256,
                "markdown_sha256": r.markdown_sha256,
                "duration_ms": r.duration_ms,
                "page_count": r.page_count,
                "headings_extracted": len(r.extracted_headings),
                "tables_extracted": len(r.extracted_tables),
                "lists_extracted": len(r.extracted_lists),
                "diagnostics": [d.model_dump(mode="json") for d in r.diagnostics],
            }
            for r in eval_results.get("ingestion_results", [])
        ],
        "repeatability_scores": [
            rs.model_dump(mode="json") for rs in repeat_results["scores"]
        ],
    }

    return json.dumps(report_dict, indent=2)
