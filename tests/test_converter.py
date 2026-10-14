"""
Unit tests for conservative markdown converter and table formatting.
"""

from docbench.ingestion.models import TableBlock, HeadingItem, ListItem
from docbench.ingestion.converter import table_to_gfm, BULLET_REGEX, NUMBERED_REGEX


def test_table_to_gfm_basic():
    """Verify table_to_gfm formats headers, separators, and rows correctly."""
    table = TableBlock(
        table_id=1,
        headers=["Name", "Role", "Tenure"],
        rows=[
            ["Alice", "Architect", "4 yrs"],
            ["Bob", "Engineer", "2 yrs"],
        ],
        page=1,
    )
    gfm = table_to_gfm(table)
    lines = gfm.splitlines()

    assert len(lines) == 4
    assert lines[0] == "| Name | Role | Tenure |"
    assert lines[1] == "| --- | --- | --- |"
    assert lines[2] == "| Alice | Architect | 4 yrs |"
    assert lines[3] == "| Bob | Engineer | 2 yrs |"


def test_table_to_gfm_escapes_pipes():
    """Verify table_to_gfm escapes internal pipe characters in cell content."""
    table = TableBlock(
        table_id=2,
        headers=["Expression", "Meaning"],
        rows=[
            ["A | B", "Bitwise OR"],
        ],
        page=1,
    )
    gfm = table_to_gfm(table)
    assert "\\|" in gfm


def test_table_to_gfm_empty():
    """Verify empty table returns empty string."""
    table = TableBlock(table_id=3, headers=[], rows=[])
    assert table_to_gfm(table) == ""


def test_bullet_regex_variants():
    """Verify bullet regex matches multiple bullet symbols."""
    assert BULLET_REGEX.match("* First item").group(2) == "First item"
    assert BULLET_REGEX.match("- Second item").group(2) == "Second item"
    assert BULLET_REGEX.match("• Third item").group(2) == "Third item"
    assert BULLET_REGEX.match("(cid:127) Fourth item").group(2) == "Fourth item"


def test_numbered_regex():
    """Verify numbered list regex matches digits with period or parenthesis."""
    m1 = NUMBERED_REGEX.match("1. First step")
    assert m1 and m1.group(1) == "1" and m1.group(2) == "First step"

    m2 = NUMBERED_REGEX.match("12) Twelfth step")
    assert m2 and m2.group(1) == "12" and m2.group(2) == "Twelfth step"
