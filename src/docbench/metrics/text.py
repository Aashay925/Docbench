"""
Text completeness, verbatim preservation, and duplication-penalizing metrics.
"""

from typing import List, Set
from collections import Counter
import difflib
import re

from docbench.ingestion.models import TextCompletenessScore


def tokenize_text(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric and word tokens including Unicode symbols."""
    return re.findall(r"\b[\w$€£¥\.\-\%\+\=]+\b", text.lower(), re.UNICODE)


def evaluate_text_completeness(
    extracted_markdown: str,
    reference_markdown: str,
) -> TextCompletenessScore:
    """
    Evaluate verbatim text completeness across character, token, and sequence levels.
    Penalizes missing text, hallucinated text, and duplicate content.
    """
    norm_ref = " ".join(reference_markdown.split())
    norm_ext = " ".join(extracted_markdown.split())

    # Case 1: Both empty -> perfect match
    if not norm_ref and not norm_ext:
        return TextCompletenessScore(
            char_recall=1.0,
            token_recall=1.0,
            token_precision=1.0,
            token_f1=1.0,
            sequence_similarity=1.0,
            jaccard_similarity=1.0,
            length_ratio=1.0,
            composite_text_score=1.0,
        )

    # Case 2: One empty, one non-empty -> total mismatch
    if not norm_ref or not norm_ext:
        return TextCompletenessScore(
            char_recall=0.0,
            token_recall=0.0,
            token_precision=0.0,
            token_f1=0.0,
            sequence_similarity=0.0,
            jaccard_similarity=0.0,
            length_ratio=0.0,
            composite_text_score=0.0,
        )

    # 1. Character-level counts & recall
    ref_char_counts = Counter(c.lower() for c in reference_markdown if not c.isspace())
    ext_char_counts = Counter(c.lower() for c in extracted_markdown if not c.isspace())

    total_ref_chars = sum(ref_char_counts.values())
    if total_ref_chars > 0:
        matched_chars = sum(
            min(count, ext_char_counts.get(char, 0))
            for char, count in ref_char_counts.items()
        )
        char_recall = matched_chars / total_ref_chars
    else:
        char_recall = 0.0

    # 2. Token-level metrics: recall, precision, and F1 (penalizes duplication & omission)
    ref_tokens = tokenize_text(reference_markdown)
    ext_tokens = tokenize_text(extracted_markdown)

    ref_token_counts = Counter(ref_tokens)
    ext_token_counts = Counter(ext_tokens)

    total_ref_tokens = len(ref_tokens)
    total_ext_tokens = len(ext_tokens)

    if total_ref_tokens > 0:
        matched_ref_tokens = sum(
            min(count, ext_token_counts.get(tok, 0))
            for tok, count in ref_token_counts.items()
        )
        token_recall = matched_ref_tokens / total_ref_tokens
    else:
        token_recall = 0.0

    if total_ext_tokens > 0:
        matched_ext_tokens = sum(
            min(count, ref_token_counts.get(tok, 0))
            for tok, count in ext_token_counts.items()
        )
        token_precision = matched_ext_tokens / total_ext_tokens
    else:
        token_precision = 0.0

    if (token_precision + token_recall) > 0:
        token_f1 = (2.0 * token_precision * token_recall) / (token_precision + token_recall)
    else:
        token_f1 = 0.0

    # Jaccard similarity of unique vocabulary
    ref_set: Set[str] = set(ref_tokens)
    ext_set: Set[str] = set(ext_tokens)
    union_set = ref_set | ext_set
    jaccard = len(ref_set & ext_set) / len(union_set) if union_set else 0.0

    # 3. Sequence Similarity (Ratcliff-Obershelp gestalt pattern match)
    matcher = difflib.SequenceMatcher(None, norm_ref, norm_ext)
    sequence_similarity = matcher.ratio()

    # 4. Length Ratio (penalizes massive text bloat or truncations)
    len_ref = len(norm_ref)
    len_ext = len(norm_ext)
    length_ratio = min(len_ref, len_ext) / max(len_ref, len_ext, 1)

    # 5. Composite Text Score
    composite_text = (
        0.30 * sequence_similarity +
        0.35 * token_f1 +
        0.20 * char_recall +
        0.15 * length_ratio
    )

    return TextCompletenessScore(
        char_recall=round(char_recall, 4),
        token_recall=round(token_recall, 4),
        token_precision=round(token_precision, 4),
        token_f1=round(token_f1, 4),
        sequence_similarity=round(sequence_similarity, 4),
        jaccard_similarity=round(jaccard, 4),
        length_ratio=round(length_ratio, 4),
        composite_text_score=round(composite_text, 4),
    )
