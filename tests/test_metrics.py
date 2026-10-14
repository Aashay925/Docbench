"""
Unit tests for all 6 evaluation metrics: headings, tables, text, reading order, lists, and composite.
"""

from docbench.ingestion.models import (
    HeadingItem,
    TableBlock,
    ListItem,
    DocumentManifest,
    IngestionResult,
)
from docbench.metrics.headings import evaluate_headings, normalize_heading_text
from docbench.metrics.tables import evaluate_tables, normalize_cell_value
from docbench.metrics.text import evaluate_text_completeness, tokenize_text
from docbench.metrics.reading_order import evaluate_reading_order, longest_increasing_subsequence_length
from docbench.metrics.lists import evaluate_lists
from docbench.metrics.evaluator import evaluate_document


# --- Heading Tests ---

def test_headings_perfect_match():
    headings = [
        HeadingItem(level=1, text="Introduction"),
        HeadingItem(level=2, text="System Architecture"),
    ]
    score = evaluate_headings(extracted=headings, expected=headings)
    assert score.precision == 1.0
    assert score.recall == 1.0
    assert score.f1 == 1.0
    assert score.matched_count == 2


def test_headings_level_mismatch():
    expected = [HeadingItem(level=1, text="Title")]
    extracted = [HeadingItem(level=2, text="Title")]  # Level mismatch
    score = evaluate_headings(extracted=extracted, expected=expected)
    assert score.f1 == 0.0
    assert score.matched_count == 0


def test_headings_missing_and_extra():
    expected = [
        HeadingItem(level=1, text="A"),
        HeadingItem(level=2, text="B"),
    ]
    extracted = [
        HeadingItem(level=1, text="A"),
        HeadingItem(level=2, text="C"),  # Extra
    ]
    score = evaluate_headings(extracted=extracted, expected=expected)
    assert score.precision == 0.5
    assert score.recall == 0.5
    assert score.f1 == 0.5
    assert score.matched_count == 1


# --- Table Tests ---

def test_tables_perfect_match():
    tables = [
        TableBlock(
            table_id=1,
            headers=["H1", "H2"],
            rows=[["A", "B"], ["C", "D"]],
        )
    ]
    score = evaluate_tables(extracted=tables, expected=tables)
    assert score.cell_accuracy == 1.0
    assert score.table_detection_precision == 1.0
    assert score.table_detection_recall == 1.0
    assert score.matched_cells == 6


def test_tables_cell_value_mismatch():
    expected = [
        TableBlock(table_id=1, headers=["H1", "H2"], rows=[["100", "200"]])
    ]
    extracted = [
        TableBlock(table_id=1, headers=["H1", "H2"], rows=[["100", "999"]])  # One mismatch
    ]
    score = evaluate_tables(extracted=extracted, expected=expected)
    assert score.matched_cells == 3
    assert score.total_expected_cells == 4
    assert score.cell_accuracy == 0.75


def test_tables_empty():
    score = evaluate_tables(extracted=[], expected=[])
    assert score.cell_accuracy == 1.0


# --- Text Completeness Tests ---

def test_text_completeness_identical():
    text = "The quick brown fox jumps over the lazy dog."
    score = evaluate_text_completeness(extracted_markdown=text, reference_markdown=text)
    assert score.char_recall == 1.0
    assert score.token_recall == 1.0
    assert score.sequence_similarity == 1.0
    assert score.composite_text_score == 1.0


def test_text_completeness_partial():
    ref = "The quick brown fox jumps over the lazy dog."
    ext = "The quick brown fox"
    score = evaluate_text_completeness(extracted_markdown=ext, reference_markdown=ref)
    assert score.token_recall < 1.0
    assert score.char_recall < 1.0
    assert score.sequence_similarity < 1.0
    assert score.composite_text_score < 1.0


# --- Reading Order Tests ---

def test_reading_order_lis_calculation():
    assert longest_increasing_subsequence_length([10, 20, 30, 40]) == 4
    assert longest_increasing_subsequence_length([40, 30, 20, 10]) == 1
    assert longest_increasing_subsequence_length([10, 30, 20, 40]) == 3


def test_reading_order_in_order():
    md = "# First Section\nSome text.\n## Second Section\nMore text.\n### Third Section"
    anchors = ["First Section", "Second Section", "Third Section"]
    score = evaluate_reading_order(extracted_markdown=md, anchors=anchors)
    assert score.lcs_ratio == 1.0
    assert score.kendall_tau == 1.0
    assert score.composite_order_score == 1.0


def test_reading_order_inverted():
    md = "### Third Section\n## Second Section\n# First Section"
    anchors = ["First Section", "Second Section", "Third Section"]
    score = evaluate_reading_order(extracted_markdown=md, anchors=anchors)
    assert score.lcs_ratio < 1.0
    assert score.kendall_tau < 0.5


# --- List Preservation Tests ---

def test_lists_perfect_match():
    lists = [
        ListItem(text="Audit architecture", list_type="bullet", depth=0),
        ListItem(text="Configure CI pipeline", list_type="bullet", depth=0),
    ]
    score = evaluate_lists(extracted=lists, expected=lists)
    assert score.precision == 1.0
    assert score.recall == 1.0
    assert score.f1 == 1.0
    assert score.matched_items == 2


def test_lists_type_mismatch():
    expected = [ListItem(text="Step one", list_type="numbered", depth=0)]
    extracted = [ListItem(text="Step one", list_type="bullet", depth=0)]
    score = evaluate_lists(extracted=extracted, expected=expected)
    assert score.f1 == 0.0


# --- End-to-End Composite Evaluation Test ---

def test_evaluate_document_composite():
    manifest = DocumentManifest(
        doc_id="test_doc",
        filename="test.pdf",
        title="Test Title",
        page_count=1,
        headings=[HeadingItem(level=1, text="Test Title")],
        tables=[],
        lists=[],
        text_blocks=["Some sample content."],
        reading_order_anchors=["Test Title", "sample content"],
    )
    ref_md = "# Test Title\n\nSome sample content.\n"
    res = IngestionResult(
        doc_id="test_doc",
        source_pdf="test.pdf",
        pdf_sha256="abc",
        markdown_content=ref_md,
        markdown_sha256="def",
        duration_ms=45.0,
        page_count=1,
        extracted_headings=[HeadingItem(level=1, text="Test Title")],
        extracted_tables=[],
        extracted_lists=[],
        extracted_text_blocks=["Some sample content."],
        diagnostics=[],
    )
    eval_res = evaluate_document(res, manifest, ref_md)
    assert eval_res.composite_score == 1.0
