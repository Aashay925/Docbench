"""
List preservation metrics: Precision, Recall, F1, Depth Accuracy, and Order Accuracy.
"""

from typing import List, Set
from bisect import bisect_left
import re
from docbench.ingestion.models import ListItem, ListPreservationScore


def normalize_item_text(text: str) -> str:
    """Normalize list item text for robust comparison."""
    t = re.sub(r"^\s*(\*|-|•|\(cid:127\)|\d+[\.\)])\s*", "", text)
    t = re.sub(r"\s+", " ", t)
    return t.strip().lower()


def evaluate_lists(
    extracted: List[ListItem],
    expected: List[ListItem],
) -> ListPreservationScore:
    """
    Evaluate list item preservation precision, recall, F1, nesting depth, and ordering.
    A full match requires:
    - Same list type (bullet or numbered)
    - High text similarity / normalized equality
    - Matching nesting depth (depth level 0 vs 1)
    """
    is_applicable = len(expected) > 0

    if not expected and not extracted:
        return ListPreservationScore(
            precision=1.0,
            recall=1.0,
            f1=1.0,
            matched_items=0,
            expected_items=0,
            extracted_items=0,
            depth_accuracy=1.0,
            order_accuracy=1.0,
            is_applicable=False,
        )

    if not expected and extracted:
        return ListPreservationScore(
            precision=0.0,
            recall=1.0,
            f1=0.0,
            matched_items=0,
            expected_items=0,
            extracted_items=len(extracted),
            depth_accuracy=0.0,
            order_accuracy=0.0,
            is_applicable=True,
        )

    if expected and not extracted:
        return ListPreservationScore(
            precision=1.0,
            recall=0.0,
            f1=0.0,
            matched_items=0,
            expected_items=len(expected),
            extracted_items=0,
            depth_accuracy=0.0,
            order_accuracy=0.0,
            is_applicable=True,
        )

    matched_exact_count = 0
    text_and_type_matched_count = 0
    used_extracted_indices: Set[int] = set()
    matched_extracted_indices: List[int] = []

    for exp in expected:
        exp_norm = normalize_item_text(exp.text)
        found_exact_idx = None
        found_relaxed_idx = None

        for ext_idx, ext in enumerate(extracted):
            if ext_idx in used_extracted_indices:
                continue
            ext_norm = normalize_item_text(ext.text)
            if ext.list_type == exp.list_type and ext_norm == exp_norm:
                if ext.depth == exp.depth:
                    found_exact_idx = ext_idx
                    break
                elif found_relaxed_idx is None:
                    found_relaxed_idx = ext_idx

        # Prefer exact depth match
        if found_exact_idx is not None:
            matched_exact_count += 1
            text_and_type_matched_count += 1
            used_extracted_indices.add(found_exact_idx)
            matched_extracted_indices.append(found_exact_idx)
        elif found_relaxed_idx is not None:
            # Matched text and type, but depth differed
            text_and_type_matched_count += 1
            used_extracted_indices.add(found_relaxed_idx)
            matched_extracted_indices.append(found_relaxed_idx)

    # Depth accuracy
    if text_and_type_matched_count > 0:
        depth_accuracy = matched_exact_count / text_and_type_matched_count
    else:
        depth_accuracy = 0.0

    # Sequential order accuracy
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
        order_accuracy = 1.0 if text_and_type_matched_count > 0 else 0.0

    # Strict precision and recall require exact depth match
    precision = matched_exact_count / max(len(extracted), 1)
    recall = matched_exact_count / max(len(expected), 1)
    raw_f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    # Composite list F1 penalizes both depth errors and reordering
    effective_f1 = raw_f1 * (0.80 + 0.20 * order_accuracy)

    return ListPreservationScore(
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(effective_f1, 4),
        matched_items=matched_exact_count,
        expected_items=len(expected),
        extracted_items=len(extracted),
        depth_accuracy=round(depth_accuracy, 4),
        order_accuracy=round(order_accuracy, 4),
        is_applicable=is_applicable,
    )
