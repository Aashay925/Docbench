"""
Unit tests for repeatability runner and determinism validation.
"""

from docbench.config import SAMPLE_DOCUMENTS
from docbench.repeatability.runner import run_repeatability_test


def test_repeatability_runner_stability():
    """Verify repeatability across 3 runs achieves 100% hash stability."""
    rep = run_repeatability_test(doc_ids=["contract", "tabular_report"], runs=3)
    assert rep["runs"] == 3
    assert rep["overall_identical_rate"] == 1.0
    assert len(rep["scores"]) == 2

    for score in rep["scores"]:
        assert score.sha256_identical_rate == 1.0
        assert len(score.unique_hashes) == 1
        assert score.mean_duration_ms > 0
        assert score.std_duration_ms >= 0
        assert score.min_duration_ms <= score.max_duration_ms
