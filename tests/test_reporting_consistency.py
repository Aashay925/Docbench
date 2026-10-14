"""
Integration tests for report consistency across Markdown, JSON, and CSV formats.
"""

import json
import csv
from pathlib import Path
from docbench.metrics.evaluator import evaluate_corpus
from docbench.repeatability.runner import run_repeatability_test
from docbench.reporting import generate_and_save_all_reports


def test_report_consistency_across_formats(tmp_path: Path):
    """
    Verify that generated Markdown, JSON, and CSV reports contain
    mutually consistent metric scores, document IDs, and repeatability values.
    """
    eval_results = evaluate_corpus()
    repeat_results = run_repeatability_test(runs=3)

    saved = generate_and_save_all_reports(
        eval_results=eval_results,
        repeat_results=repeat_results,
        output_dir=tmp_path,
        print_console=False,
    )

    md_path = saved["markdown"]
    json_path = saved["json"]
    csv_path = saved["csv"]

    assert md_path.exists()
    assert json_path.exists()
    assert csv_path.exists()

    # Parse JSON report
    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Parse CSV report
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        csv_rows = list(reader)

    # Read Markdown report
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Verify JSON structure
    assert "overall_benchmark_score" in json_data
    assert "document_evaluations" in json_data
    assert len(json_data["document_evaluations"]) == 4

    # Verify CSV rows match JSON document IDs
    doc_ids_json = [d["doc_id"] for d in json_data["document_evaluations"]]
    doc_ids_csv = [r["doc_id"] for r in csv_rows if r["doc_id"] != "CORPUS_AVERAGE"]
    assert doc_ids_json == doc_ids_csv

    # Verify scores match exactly across JSON and CSV
    json_eval_map = {d["doc_id"]: d for d in json_data["document_evaluations"]}
    for r in csv_rows:
        if r["doc_id"] == "CORPUS_AVERAGE":
            continue
        doc_id = r["doc_id"]
        json_eval = json_eval_map[doc_id]

        # Composite score check
        assert float(r["composite_score"]) == json_eval["composite_score"]
        # Markdown mentions doc_id and score
        assert f"`{doc_id}`" in md_text

    # Verify repeatability consistency
    assert json_data["repeatability_summary"]["overall_identical_rate"] == 1.0
    corpus_row = next(r for r in csv_rows if r["doc_id"] == "CORPUS_AVERAGE")
    assert float(corpus_row["sha256_stability"]) == 1.0
