"""
Reading order accuracy metrics: Longest Increasing Subsequence (LCS) and Kendall's Tau.
"""

from typing import List
from bisect import bisect_left
from docbench.ingestion.models import ReadingOrderScore


def longest_increasing_subsequence_length(sequence: List[int]) -> int:
    """Calculate length of longest strictly increasing subsequence."""
    if not sequence:
        return 0
    tails: List[int] = []
    for x in sequence:
        idx = bisect_left(tails, x)
        if idx == len(tails):
            tails.append(x)
        else:
            tails[idx] = x
    return len(tails)


def evaluate_reading_order(
    extracted_markdown: str,
    anchors: List[str],
) -> ReadingOrderScore:
    """
    Evaluate reading order preservation across landmark anchors.
    Penalizes missing anchors, empty extraction, and out-of-order text blocks.
    """
    if not anchors:
        return ReadingOrderScore(
            lcs_ratio=1.0,
            kendall_tau=1.0,
            anchor_count_expected=0,
            anchor_count_found=0,
            composite_order_score=1.0,
        )

    norm_extracted = extracted_markdown.strip()
    if not norm_extracted:
        return ReadingOrderScore(
            lcs_ratio=0.0,
            kendall_tau=0.0,
            anchor_count_expected=len(anchors),
            anchor_count_found=0,
            composite_order_score=0.0,
        )

    lower_md = norm_extracted.lower()
    found_positions: List[int] = []
    found_indices: List[int] = []

    for expected_idx, anchor in enumerate(anchors):
        pos = lower_md.find(anchor.lower())
        if pos != -1:
            found_positions.append(pos)
            found_indices.append(expected_idx)

    found_count = len(found_positions)
    anchor_recall = found_count / len(anchors)

    if found_count == 0:
        return ReadingOrderScore(
            lcs_ratio=0.0,
            kendall_tau=0.0,
            anchor_count_expected=len(anchors),
            anchor_count_found=0,
            composite_order_score=0.0,
        )

    # 1. LCS Ratio across total expected anchors
    lis_len = longest_increasing_subsequence_length(found_positions)
    lcs_ratio = lis_len / len(anchors)

    # 2. Kendall's Tau Rank Correlation among found anchors
    if found_count > 1:
        concordant = 0
        discordant = 0
        for i in range(found_count):
            for j in range(i + 1, found_count):
                if found_positions[i] < found_positions[j]:
                    concordant += 1
                elif found_positions[i] > found_positions[j]:
                    discordant += 1

        total_pairs = (found_count * (found_count - 1)) // 2
        raw_tau = (concordant - discordant) / total_pairs
        normalized_tau = (raw_tau + 1.0) / 2.0
    else:
        normalized_tau = 1.0

    # Scale tau by anchor recall to penalize missing anchors
    effective_tau = normalized_tau * anchor_recall

    # Composite reading order score
    composite = 0.5 * lcs_ratio + 0.5 * effective_tau

    return ReadingOrderScore(
        lcs_ratio=round(lcs_ratio, 4),
        kendall_tau=round(effective_tau, 4),
        anchor_count_expected=len(anchors),
        anchor_count_found=found_count,
        composite_order_score=round(composite, 4),
    )
