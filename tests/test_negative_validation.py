"""
Comprehensive negative validation and controlled defect test suite for Phase 2.
Verifies all 14 corruption scenarios against benchmark metrics.
"""

import copy
import pytest
from pathlib import Path
from pydantic import ValidationError

from docbench.config import SYNTHETIC_DIR, MANIFESTS_DIR, REFERENCES_DIR
from docbench.ingestion.models import (
    DocumentManifest,
    IngestionResult,
    HeadingItem,
    TableBlock,
    ListItem,
)
from docbench.ingestion.pipeline import ingest_document
from docbench.metrics.headings import evaluate_headings
from docbench.metrics.tables import evaluate_tables
from docbench.metrics.text import evaluate_text_completeness
from docbench.metrics.reading_order import evaluate_reading_order
from docbench.metrics.lists import evaluate_lists
from docbench.metrics.evaluator import evaluate_document
from docbench.repeatability.runner import run_repeatability_test


@pytest.fixture
def contract_fixture():
    """Load reference contract manifest and markdown."""
    manifest_path = MANIFESTS_DIR / "contract.manifest.json"
    ref_path = REFERENCES_DIR / "contract.ref.md"
    manifest = DocumentManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    ref_md = ref_path.read_text(encoding="utf-8")
    return manifest, ref_md


# --- Scenario 1: Perfect Conversion ---

def test_scenario_1_perfect_conversion(contract_fixture):
    manifest, ref_md = contract_fixture
    pdf_path = SYNTHETIC_DIR / "contract.pdf"
    res = ingest_document(str(pdf_path))

    evaluation = evaluate_document(res, manifest, ref_md)
    assert evaluation.composite_score == 1.0
    assert evaluation.critical_failure is False
    assert evaluation.heading_score.f1 == 1.0
    assert evaluation.table_score.cell_accuracy == 1.0
    assert evaluation.text_score.composite_text_score == 1.0
    assert evaluation.reading_order_score.composite_order_score == 1.0
    assert evaluation.list_score.f1 == 1.0


# --- Scenario 2: Missing Headings ---

def test_scenario_2_missing_headings(contract_fixture):
    manifest, ref_md = contract_fixture
    extracted = copy.deepcopy(manifest.headings)
    # Drop 2 headings
    extracted.pop()
    extracted.pop()

    score = evaluate_headings(extracted=extracted, expected=manifest.headings)
    assert score.recall == pytest.approx(4 / 6, 0.001)
    assert score.precision == 1.0
    assert score.f1 < 1.0
    assert score.matched_count == 4


# --- Scenario 3: Extra Headings ---

def test_scenario_3_extra_headings(contract_fixture):
    manifest, ref_md = contract_fixture
    extracted = copy.deepcopy(manifest.headings)
    # Add phantom hallucinated headings
    extracted.append(HeadingItem(level=2, text="6. Unauthorized Extraneous Section"))
    extracted.append(HeadingItem(level=3, text="6.1 Hallucinated Subsection"))

    score = evaluate_headings(extracted=extracted, expected=manifest.headings)
    assert score.recall == 1.0
    assert score.precision == pytest.approx(6 / 8, 0.001)
    assert score.f1 < 1.0
    assert score.extracted_count == 8


# --- Scenario 4: Incorrect Heading Levels ---

def test_scenario_4_incorrect_heading_levels(contract_fixture):
    manifest, ref_md = contract_fixture
    extracted = copy.deepcopy(manifest.headings)
    # Demote H1 to H3, and promote H2 to H1
    extracted[0].level = 3
    extracted[1].level = 1

    score = evaluate_headings(extracted=extracted, expected=manifest.headings)
    assert score.matched_count == 4
    assert score.recall == pytest.approx(4 / 6, 0.001)
    assert score.f1 < 1.0


# --- Scenario 5: Missing Text ---

def test_scenario_5_missing_text(contract_fixture):
    manifest, ref_md = contract_fixture
    # Drop the second half of the document
    lines = ref_md.splitlines()
    truncated_md = "\n".join(lines[: len(lines) // 2])

    score = evaluate_text_completeness(extracted_markdown=truncated_md, reference_markdown=ref_md)
    assert score.char_recall < 1.0
    assert score.token_recall < 1.0
    assert score.sequence_similarity < 1.0
    assert score.length_ratio < 1.0
    assert score.composite_text_score < 0.70


# --- Scenario 6: Duplicated Text ---

def test_scenario_6_duplicated_text(contract_fixture):
    manifest, ref_md = contract_fixture
    # Duplicate the document text 3 times
    duplicated_md = ref_md + "\n\n" + ref_md + "\n\n" + ref_md

    score = evaluate_text_completeness(extracted_markdown=duplicated_md, reference_markdown=ref_md)
    # Token recall is high because all tokens are present, but precision and length ratio drop heavily!
    assert score.token_recall == 1.0
    assert score.token_precision <= 0.35
    assert score.token_f1 <= 0.55
    assert score.length_ratio <= 0.35
    assert score.sequence_similarity <= 0.50
    # Composite text score must strongly penalize duplication
    assert score.composite_text_score < 0.65


# --- Scenario 7: Reordered Paragraphs ---

def test_scenario_7_reordered_paragraphs():
    ref_md = """# Section A
Paragraph alpha content.

## Section B
Paragraph beta content.

## Section C
Paragraph gamma content.

## Section D
Paragraph delta content.
"""
    anchors = ["Section A", "Section B", "Section C", "Section D"]

    # Invert Section B and Section C
    swapped_md = """# Section A
Paragraph alpha content.

## Section C
Paragraph gamma content.

## Section B
Paragraph beta content.

## Section D
Paragraph delta content.
"""
    score_normal = evaluate_reading_order(extracted_markdown=ref_md, anchors=anchors)
    score_swapped = evaluate_reading_order(extracted_markdown=swapped_md, anchors=anchors)

    assert score_normal.composite_order_score == 1.0
    assert score_swapped.kendall_tau < 1.0
    assert score_swapped.lcs_ratio < 1.0
    assert score_swapped.composite_order_score < 0.90


# --- Scenario 8: Missing, Extra, and Incorrect Table Cells ---

def test_scenario_8a_missing_table_cells():
    expected = [
        TableBlock(table_id=1, headers=["A", "B", "C"], rows=[["1", "2", "3"], ["4", "5", "6"]])
    ]
    # Extracted is missing row 2
    extracted = [
        TableBlock(table_id=1, headers=["A", "B", "C"], rows=[["1", "2", "3"]])
    ]
    score = evaluate_tables(extracted=extracted, expected=expected)
    assert score.total_expected_cells == 9
    assert score.total_extracted_cells == 6
    assert score.matched_cells == 6
    assert score.cell_accuracy == pytest.approx(6 / 9, 0.001)


def test_scenario_8b_extra_table_cells():
    expected = [
        TableBlock(table_id=1, headers=["A", "B"], rows=[["1", "2"]])
    ]
    # Extracted has extra column "C" and extra row
    extracted = [
        TableBlock(table_id=1, headers=["A", "B", "C"], rows=[["1", "2", "3"], ["4", "5", "6"]])
    ]
    score = evaluate_tables(extracted=extracted, expected=expected)
    assert score.total_expected_cells == 4
    assert score.total_extracted_cells == 9
    assert score.matched_cells == 4
    assert score.cell_accuracy == pytest.approx(4 / 9, 0.001)


def test_scenario_8c_incorrect_table_cell_values():
    expected = [
        TableBlock(table_id=1, headers=["Metric", "Value"], rows=[["Revenue", "$100M"], ["Profit", "$25M"]])
    ]
    # Profit value is corrupted
    extracted = [
        TableBlock(table_id=1, headers=["Metric", "Value"], rows=[["Revenue", "$100M"], ["Profit", "$999B"]])
    ]
    score = evaluate_tables(extracted=extracted, expected=expected)
    assert score.matched_cells == 5
    assert score.total_expected_cells == 6
    assert score.cell_accuracy == pytest.approx(5 / 6, 0.001)


def test_scenario_8d_reordered_table_columns():
    expected = [
        TableBlock(table_id=1, headers=["Col1", "Col2"], rows=[["Val1", "Val2"]])
    ]
    # Columns swapped
    extracted = [
        TableBlock(table_id=1, headers=["Col2", "Col1"], rows=[["Val2", "Val1"]])
    ]
    score = evaluate_tables(extracted=extracted, expected=expected)
    assert score.matched_cells == 0
    assert score.cell_accuracy == 0.0


# --- Scenario 9: Reordered List Items ---

def test_scenario_9_reordered_list_items():
    expected = [
        ListItem(text="Step Alpha", list_type="bullet", depth=0),
        ListItem(text="Step Beta", list_type="bullet", depth=0),
        ListItem(text="Step Gamma", list_type="bullet", depth=0),
        ListItem(text="Step Delta", list_type="bullet", depth=0),
    ]
    # Reordered: Delta, Gamma, Beta, Alpha (completely inverted)
    extracted = list(reversed(expected))

    score = evaluate_lists(extracted=extracted, expected=expected)
    assert score.matched_items == 4
    assert score.order_accuracy < 1.0
    assert score.f1 < 1.0


# --- Scenario 10: Changed List Types ---

def test_scenario_10_changed_list_type():
    expected = [
        ListItem(text="Item One", list_type="numbered", depth=0),
        ListItem(text="Item Two", list_type="numbered", depth=0),
    ]
    # Converted to bullet instead of numbered
    extracted = [
        ListItem(text="Item One", list_type="bullet", depth=0),
        ListItem(text="Item Two", list_type="bullet", depth=0),
    ]
    score = evaluate_lists(extracted=extracted, expected=expected)
    assert score.matched_items == 0
    assert score.precision == 0.0
    assert score.recall == 0.0
    assert score.f1 == 0.0


# --- Scenario 11: Changed List Nesting Depth ---

def test_scenario_11_changed_list_nesting_depth():
    expected = [
        ListItem(text="Top level", list_type="bullet", depth=0),
        ListItem(text="Nested sub-item", list_type="bullet", depth=1),
    ]
    # Flattened to depth 0
    extracted = [
        ListItem(text="Top level", list_type="bullet", depth=0),
        ListItem(text="Nested sub-item", list_type="bullet", depth=0),
    ]
    score = evaluate_lists(extracted=extracted, expected=expected)
    assert score.matched_items == 1
    assert score.depth_accuracy == 0.5
    assert score.f1 < 1.0


# --- Scenario 12: Empty, Malformed, and Unsupported Inputs ---

def test_scenario_12a_empty_extraction(contract_fixture):
    manifest, ref_md = contract_fixture
    empty_result = IngestionResult(
        doc_id="contract",
        source_pdf="contract.pdf",
        pdf_sha256="abc",
        markdown_content="",
        markdown_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        duration_ms=10.0,
        page_count=1,
        extracted_headings=[],
        extracted_tables=[],
        extracted_lists=[],
        extracted_text_blocks=[],
        diagnostics=[],
    )
    evaluation = evaluate_document(empty_result, manifest, ref_md)
    assert evaluation.text_score.composite_text_score == 0.0
    assert evaluation.reading_order_score.composite_order_score == 0.0
    assert evaluation.heading_score.f1 == 0.0
    assert evaluation.table_score.cell_accuracy == 0.0
    assert evaluation.list_score.f1 == 0.0
    assert evaluation.composite_score == 0.0
    assert evaluation.critical_failure is True


def test_scenario_12b_non_applicable_components():
    """Document without tables or lists has those components excluded from composite score."""
    manifest = DocumentManifest(
        doc_id="text_only",
        filename="text_only.pdf",
        title="Simple Text Document",
        page_count=1,
        headings=[HeadingItem(level=1, text="Simple Text Document")],
        tables=[],  # No tables
        lists=[],   # No lists
        text_blocks=["Verbatim paragraph."],
        reading_order_anchors=["Simple Text Document", "Verbatim paragraph"],
    )
    res = IngestionResult(
        doc_id="text_only",
        source_pdf="text_only.pdf",
        pdf_sha256="123",
        markdown_content="# Simple Text Document\n\nVerbatim paragraph.\n",
        markdown_sha256="456",
        duration_ms=25.0,
        page_count=1,
        extracted_headings=[HeadingItem(level=1, text="Simple Text Document")],
        extracted_tables=[],
        extracted_lists=[],
        extracted_text_blocks=["Verbatim paragraph."],
        diagnostics=[],
    )
    eval_res = evaluate_document(res, manifest, "# Simple Text Document\n\nVerbatim paragraph.\n")
    assert eval_res.table_score.is_applicable is False
    assert eval_res.list_score.is_applicable is False
    assert "table_cell_accuracy" not in eval_res.applicable_weights
    assert "list_preservation_f1" not in eval_res.applicable_weights
    # Sum of applicable weights must be 1.0
    assert sum(eval_res.applicable_weights.values()) == pytest.approx(1.0, 0.001)
    assert eval_res.composite_score == 1.0


def test_scenario_12c_missing_file_error():
    with pytest.raises(FileNotFoundError):
        ingest_document("non_existent_path_xyz_123.pdf")


def test_scenario_12d_corrupted_pdf_error(tmp_path: Path):
    bad_pdf = tmp_path / "corrupt.pdf"
    bad_pdf.write_bytes(b"CORRUPT DATA NOT A PDF")
    with pytest.raises(RuntimeError):
        ingest_document(str(bad_pdf))


def test_scenario_12e_malformed_manifest_error():
    with pytest.raises(ValidationError):
        DocumentManifest(title="Incomplete", doc_id="test")  # Missing page_count, filename


# --- Scenario 13: Unicode, Accents, and Currency Symbols ---

def test_scenario_13_unicode_accents_and_currency():
    ref = "Values: $1,250.00 | EUR €1.150,25 | GBP £980.75 | JPY ¥180,000 | café | Über | façade | naïve."

    # Corrupt accents and currency
    corrupted = "Values: $1,250.00 | EUR $1.150,25 | GBP $980.75 | JPY $180,000 | cafe | Uber | facade | naive."

    score = evaluate_text_completeness(extracted_markdown=corrupted, reference_markdown=ref)
    assert score.char_recall < 1.0
    assert score.token_recall < 1.0
    assert score.sequence_similarity < 1.0
    assert score.composite_text_score < 1.0


# --- Scenario 14: Repeated Identical Conversions ---

def test_scenario_14_repeated_identical_conversions():
    rep = run_repeatability_test(doc_ids=["contract"], runs=5)
    assert rep["runs"] == 5
    score = rep["scores"][0]
    assert score.sha256_identical_rate == 1.0
    assert len(score.unique_hashes) == 1
    assert score.mean_duration_ms > 0
    assert score.std_duration_ms >= 0
