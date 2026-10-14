"""
Heading structure evaluation metrics: Precision, Recall, F1, and Order Accuracy.
"""

from typing import List, Tuple
from bisect import bisect_left
import re
from docbench.ingestion.models import HeadingItem, HeadingScore


def normalize_heading_text(text: str) -> str:
    """Normalize heading string for robust comparison."""
    # Strip markdown symbols, lower-case, collapse whitespace
    t = re.sub(r"[#*_`]", "", text)
    t = re.sub(r"\s+", " ", t)
    return t.strip().lower()


def evaluate_headings(
    extracted: List[HeadingItem],
    expected: List[HeadingItem],
) -> HeadingScore:
    """
    Evaluate heading extraction precision, recall, F1, and sequential ordering.
    A match requires:
    - Identical normalized text
    - Identical heading level (H1 == H1, H2 == H2, etc.)
    """
    is_applicable = len(expected) > 0

    if not expected and not extracted:
        return HeadingScore(
            precision=1.0,
            recall=1.0,
            f1=1.0,
            matched_count=0,
            expected_count=0,
            extracted_count=0,
            order_accuracy=1.0,
            is_applicable=False,
        )

    if not expected and extracted:
        return HeadingScore(
            precision=0.0,
            recall=1.0,
            f1=0.0,
            matched_count=0,
            expected_count=0,
            extracted_count=len(extracted),
            order_accuracy=0.0,
            is_applicable=True,
        )

    if expected and not extracted:
        return HeadingScore(
            precision=1.0,
            recall=0.0,
            f1=0.0,
            matched_count=0,
            expected_count=len(expected),
            extracted_count=0,
            order_accuracy=0.0,
            is_applicable=True,
        )

    matched_count = 0
    matched_extracted_indices: List[int] = []
    used_extracted_indices = set()

    for exp_idx, exp in enumerate(expected):
        exp_norm = normalize_heading_text(exp.text)
        found_idx = None

        for ext_idx, ext in enumerate(extracted):
            if ext_idx in used_extracted_indices:
                continue
            ext_norm = normalize_heading_text(ext.text)
            # Exact level and text match
            if ext.level == exp.level and ext_norm == exp_norm:
                found_idx = ext_idx
                break

        if found_idx is not None:
            matched_count += 1
            used_extracted_indices.add(found_idx)
            matched_extracted_indices.append(found_idx)

    # Heading sequential order accuracy
    if len(matched_extracted_indices) > 1:
        tails: List[int] = []
        for x in matched_extracted_indices:
            idx = bisect_left(tails, x)
            if idx == len(tails):
                tails.append(x)
            else:
                tails[idx] = x
        order_accuracy = len(tails) / len(matched_extracted_indices)
    else:
        order_accuracy = 1.0 if matched_count > 0 else 0.0

    precision = matched_count / max(len(extracted), 1)
    recall = matched_count / max(len(expected), 1)
    raw_f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    # Structural F1 incorporates sequential order preservation
    structural_f1 = raw_f1 * (0.80 + 0.20 * order_accuracy)

    return HeadingScore(
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(structural_f1, 4),
        matched_count=matched_count,
        expected_count=len(expected),
        extracted_count=len(extracted),
        order_accuracy=round(order_accuracy, 4),
        is_applicable=is_applicable,
    )
