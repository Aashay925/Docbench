"""
Table extraction and cell-level preservation metrics.
"""

from typing import List, Set, Tuple, Optional
import re
from docbench.ingestion.models import TableBlock, TableScore


def normalize_cell_value(val: str) -> str:
    """Normalize cell text for robust cell comparison."""
    # Collapse whitespace, normalize dashes and lower-case
    v = re.sub(r"\s+", " ", str(val)).strip().lower()
    return v


def header_jaccard(h1: List[str], h2: List[str]) -> float:
    """Compute Jaccard similarity between two sets of table headers."""
    s1 = {normalize_cell_value(c) for c in h1 if normalize_cell_value(c)}
    s2 = {normalize_cell_value(c) for c in h2 if normalize_cell_value(c)}
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)


def evaluate_tables(
    extracted: List[TableBlock],
    expected: List[TableBlock],
) -> TableScore:
    """
    Evaluate table detection and cell-by-cell accuracy.
    Aligns tables by header similarity to avoid positional index fragility.
    """
    is_applicable = len(expected) > 0

    # Calculate total expected cells
    total_expected_cells = sum(
        len(t.headers) + sum(len(r) for r in t.rows)
        for t in expected
    )

    # Calculate total extracted cells
    total_extracted_cells = sum(
        len(t.headers) + sum(len(r) for r in t.rows)
        for t in extracted
    )

    # Case 1: No tables expected and none extracted
    if not expected and not extracted:
        return TableScore(
            table_detection_precision=1.0,
            table_detection_recall=1.0,
            cell_accuracy=1.0,
            matched_cells=0,
            total_expected_cells=0,
            total_extracted_cells=0,
            table_count_expected=0,
            table_count_extracted=0,
            is_applicable=False,
        )

    # Case 2: No tables expected, but extracted found hallucinated tables
    if not expected and extracted:
        return TableScore(
            table_detection_precision=0.0,
            table_detection_recall=1.0,
            cell_accuracy=0.0,
            matched_cells=0,
            total_expected_cells=0,
            total_extracted_cells=total_extracted_cells,
            table_count_expected=0,
            table_count_extracted=len(extracted),
            is_applicable=True,
        )

    # Case 3: Tables expected, but none extracted
    if expected and not extracted:
        return TableScore(
            table_detection_precision=1.0,
            table_detection_recall=0.0,
            cell_accuracy=0.0,
            matched_cells=0,
            total_expected_cells=total_expected_cells,
            total_extracted_cells=0,
            table_count_expected=len(expected),
            table_count_extracted=0,
            is_applicable=True,
        )

    # Case 4: Match expected tables to extracted tables using header overlap
    matched_pairs: List[Tuple[TableBlock, TableBlock]] = []
    unmatched_extracted = list(extracted)

    for exp_t in expected:
        best_match_idx = None
        best_score = -1.0

        for idx, ext_t in enumerate(unmatched_extracted):
            sim = header_jaccard(exp_t.headers, ext_t.headers)
            if sim > best_score:
                best_score = sim
                best_match_idx = idx

        if best_match_idx is not None and best_score > 0.0:
            matched_pairs.append((exp_t, unmatched_extracted.pop(best_match_idx)))
        elif unmatched_extracted:
            # Fallback to sequential pairing if headers have zero overlap
            matched_pairs.append((exp_t, unmatched_extracted.pop(0)))

    matched_cells = 0

    for exp_table, ext_table in matched_pairs:
        # Compare headers
        for col_idx in range(min(len(exp_table.headers), len(ext_table.headers))):
            exp_val = normalize_cell_value(exp_table.headers[col_idx])
            ext_val = normalize_cell_value(ext_table.headers[col_idx])
            if exp_val == ext_val:
                matched_cells += 1

        # Compare row cells position by position (r, c)
        for row_idx in range(min(len(exp_table.rows), len(ext_table.rows))):
            exp_row = exp_table.rows[row_idx]
            ext_row = ext_table.rows[row_idx]
            for col_idx in range(min(len(exp_row), len(ext_row))):
                exp_val = normalize_cell_value(exp_row[col_idx])
                ext_val = normalize_cell_value(ext_row[col_idx])
                if exp_val == ext_val:
                    matched_cells += 1

    denominator = max(total_expected_cells, total_extracted_cells, 1)
    cell_accuracy = matched_cells / denominator

    detection_precision = len(matched_pairs) / max(len(extracted), 1)
    detection_recall = len(matched_pairs) / max(len(expected), 1)

    return TableScore(
        table_detection_precision=round(detection_precision, 4),
        table_detection_recall=round(detection_recall, 4),
        cell_accuracy=round(cell_accuracy, 4),
        matched_cells=matched_cells,
        total_expected_cells=total_expected_cells,
        total_extracted_cells=total_extracted_cells,
        table_count_expected=len(expected),
        table_count_extracted=len(extracted),
        is_applicable=is_applicable,
    )
