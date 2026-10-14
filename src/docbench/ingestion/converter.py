"""
Conservative, deterministic Markdown converter and structural feature extractor.
"""

import re
from typing import List, Tuple, Dict, Any, Optional

from docbench.ingestion.models import (
    HeadingItem,
    TableBlock,
    ListItem,
    DiagnosticMessage,
)
from docbench.ingestion.parser import ParsedDocument, ParsedPage, ParsedLine


BULLET_REGEX = re.compile(r"^(\(cid:127\)|•|\u2022|\*|-)\s*(.*)", re.UNICODE)
NUMBERED_REGEX = re.compile(r"^(\d+)[\.\)]\s+(.*)")


def table_to_gfm(table: TableBlock) -> str:
    """Format a TableBlock into standard GitHub Flavored Markdown (GFM)."""
    if not table.headers and not table.rows:
        return ""

    headers = table.headers if table.headers else [f"Col {i+1}" for i in range(len(table.rows[0]))]
    # Clean cells of internal newlines or pipes
    clean_headers = [h.replace("|", "\\|").replace("\n", " ").strip() for h in headers]
    
    header_line = "| " + " | ".join(clean_headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(clean_headers)) + " |"

    row_lines = []
    for row in table.rows:
        # Pad row to match header length if needed
        padded_row = list(row) + [""] * (len(clean_headers) - len(row))
        clean_row = [str(c).replace("|", "\\|").replace("\n", " ").strip() for c in padded_row[:len(clean_headers)]]
        row_lines.append("| " + " | ".join(clean_row) + " |")

    return "\n".join([header_line, separator_line] + row_lines)


class PageElement:
    """Unified container for page elements (lines or tables) for reading order."""
    def __init__(self, kind: str, top: float, payload: Any):
        self.kind = kind  # 'line' or 'table'
        self.top = top
        self.payload = payload


def convert_document(doc: ParsedDocument) -> Tuple[str, List[HeadingItem], List[TableBlock], List[ListItem], List[str], List[DiagnosticMessage]]:
    """
    Convert a ParsedDocument into:
    - Conservative Markdown string
    - Extracted Headings
    - Extracted Tables
    - Extracted Lists
    - Extracted Text Blocks (paragraphs)
    - Diagnostics
    """
    extracted_headings: List[HeadingItem] = []
    extracted_tables: List[TableBlock] = []
    extracted_lists: List[ListItem] = []
    extracted_text_blocks: List[str] = []
    diagnostics = list(doc.diagnostics)

    markdown_sections: List[str] = []
    body_size = doc.body_font_size

    for page in doc.pages:
        elements: List[PageElement] = []

        # Add text lines as elements
        for line in page.lines:
            elements.append(PageElement(kind="line", top=line.top, payload=line))

        # Add tables as elements using their bounding box top
        for idx, table in enumerate(page.tables):
            top_coord = page.table_bboxes[idx][1] if idx < len(page.table_bboxes) else 0.0
            elements.append(PageElement(kind="table", top=top_coord, payload=table))

        # Sort elements strictly by vertical reading order (top)
        elements.sort(key=lambda el: el.top)

        page_blocks: List[str] = []
        current_para_lines: List[str] = []
        current_list_lines: List[str] = []
        last_line_bottom: Optional[float] = None

        def flush_paragraph():
            nonlocal current_para_lines, last_line_bottom
            if current_para_lines:
                text_block = " ".join(current_para_lines).strip()
                if text_block:
                    page_blocks.append(text_block)
                    extracted_text_blocks.append(text_block)
                current_para_lines = []
            last_line_bottom = None

        def flush_list():
            nonlocal current_list_lines
            if current_list_lines:
                page_blocks.append("\n".join(current_list_lines))
                current_list_lines = []

        for el in elements:
            if el.kind == "table":
                flush_paragraph()
                flush_list()
                table: TableBlock = el.payload
                gfm_table = table_to_gfm(table)
                if gfm_table:
                    page_blocks.append(gfm_table)
                    extracted_tables.append(table)
                continue

            # It's a text line
            line: ParsedLine = el.payload
            text = line.text

            # 1. Check for headings by font size and style
            is_h1 = (line.font_size >= 1.45 * body_size and line.is_bold)
            is_h2 = (line.font_size >= 1.22 * body_size and line.font_size < 1.45 * body_size and line.is_bold)
            is_h3 = (line.font_size >= 1.05 * body_size and line.font_size < 1.22 * body_size and line.is_bold)

            if is_h1:
                flush_paragraph()
                flush_list()
                clean_title = text
                page_blocks.append(f"# {clean_title}")
                extracted_headings.append(HeadingItem(level=1, text=clean_title, page=page.page_number))
                continue

            if is_h2:
                flush_paragraph()
                flush_list()
                clean_title = text
                page_blocks.append(f"## {clean_title}")
                extracted_headings.append(HeadingItem(level=2, text=clean_title, page=page.page_number))
                continue

            if is_h3:
                flush_paragraph()
                flush_list()
                clean_title = text
                page_blocks.append(f"### {clean_title}")
                extracted_headings.append(HeadingItem(level=3, text=clean_title, page=page.page_number))
                continue

            # 2. Check for bullet list item
            bullet_match = BULLET_REGEX.match(text)
            if bullet_match:
                flush_paragraph()
                bullet_char = bullet_match.group(1)
                item_text = bullet_match.group(2).strip()
                # Indentation: x0 > 70 indicates nested list level 1
                depth = 1 if line.x0 > 70.0 else 0
                indent = "  " * depth
                current_list_lines.append(f"{indent}* {item_text}")
                extracted_lists.append(ListItem(text=item_text, list_type="bullet", depth=depth, page=page.page_number))
                continue

            # 3. Check for numbered list item
            num_match = NUMBERED_REGEX.match(text)
            if num_match:
                flush_paragraph()
                num_idx = num_match.group(1)
                item_text = num_match.group(2).strip()
                depth = 1 if line.x0 > 70.0 else 0
                indent = "  " * depth
                current_list_lines.append(f"{indent}{num_idx}. {item_text}")
                extracted_lists.append(ListItem(text=item_text, list_type="numbered", depth=depth, page=page.page_number))
                continue

            # 4. Standard body line -> check if continuing paragraph or starting new one
            flush_list()
            if last_line_bottom is not None:
                vertical_gap = line.top - last_line_bottom
                # A vertical gap above 5.5 pt indicates an intentional paragraph separation
                if vertical_gap > 5.5:
                    flush_paragraph()

            current_para_lines.append(text)
            last_line_bottom = line.bottom

        flush_paragraph()
        flush_list()

        if page_blocks:
            page_md = "\n\n".join(page_blocks)
            markdown_sections.append(page_md)

    # Join pages cleanly with double newline
    full_markdown = "\n\n".join(markdown_sections).strip() + "\n"
    return full_markdown, extracted_headings, extracted_tables, extracted_lists, extracted_text_blocks, diagnostics
