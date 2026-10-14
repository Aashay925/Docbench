"""
Repeatability and determinism evaluation engine.
Verifies bitwise output stability and latency jitter across consecutive runs.
"""

import math
from pathlib import Path
from collections import Counter
from typing import List, Dict, Any, Optional

from docbench.config import (
    SYNTHETIC_DIR,
    SAMPLE_DOCUMENTS,
    DEFAULT_REPEATABILITY_RUNS,
)
from docbench.ingestion.models import RepeatabilityScore
from docbench.ingestion.pipeline import ingest_document


def run_repeatability_test(
    doc_ids: Optional[List[str]] = None,
    runs: int = DEFAULT_REPEATABILITY_RUNS,
    synthetic_dir: Path = SYNTHETIC_DIR,
) -> Dict[str, Any]:
    """
    Execute repeatability benchmark across specified documents.
    Verifies that the generated markdown SHA-256 is 100% stable across runs
    and measures latency jitter.
    """
    target_docs = doc_ids or SAMPLE_DOCUMENTS
    scores: List[RepeatabilityScore] = []

    for doc_id in target_docs:
        pdf_path = synthetic_dir / f"{doc_id}.pdf"
        if not pdf_path.exists():
            raise FileNotFoundError(f"Missing synthetic PDF for repeatability: {pdf_path}")

        hashes: List[str] = []
        durations: List[float] = []

        for _ in range(runs):
            res = ingest_document(str(pdf_path), doc_id=doc_id)
            hashes.append(res.markdown_sha256)
            durations.append(res.duration_ms)

        # Hash stability
        hash_counts = Counter(hashes)
        mode_count = hash_counts.most_common(1)[0][1]
        identical_rate = mode_count / runs
        unique_hashes = list(hash_counts.keys())

        # Duration statistics
        mean_dur = sum(durations) / len(durations)
        variance = sum((d - mean_dur) ** 2 for d in durations) / len(durations)
        std_dur = math.sqrt(variance)

        score = RepeatabilityScore(
            doc_id=doc_id,
            runs=runs,
            sha256_identical_rate=round(identical_rate, 4),
            unique_hashes=unique_hashes,
            mean_duration_ms=round(mean_dur, 2),
            std_duration_ms=round(std_dur, 2),
            min_duration_ms=round(min(durations), 2),
            max_duration_ms=round(max(durations), 2),
        )
        scores.append(score)

    overall_identical_rate = sum(s.sha256_identical_rate for s in scores) / len(scores)
    avg_mean_duration = sum(s.mean_duration_ms for s in scores) / len(scores)
    avg_std_duration = sum(s.std_duration_ms for s in scores) / len(scores)

    return {
        "runs": runs,
        "scores": scores,
        "overall_identical_rate": round(overall_identical_rate, 4),
        "avg_mean_duration_ms": round(avg_mean_duration, 2),
        "avg_std_duration_ms": round(avg_std_duration, 2),
    }
