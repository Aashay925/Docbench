"""
PDF parser extracting raw structural primitives, bounding boxes, tables, and typography.
Uses pdfplumber and pdfminer under MIT license.
"""

from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
import re
import pdfplumber

from docbench.ingestion.models import (
    DiagnosticMessage,
    TableBlock,
)


class ParsedLine:
    def __init__(
        self,
        text: str,
        x0: float,
        top: float,
        x1: float,
        bottom: float,
        font_size: float,
        font_name: str,
        is_bold: bool,
        page_number: int,
    ):
        self.text = text.strip()
        self.x0 = x0
        self.top = top
        self.x1 = x1
        self.bottom = bottom
        self.font_size = font_size
        self.font_name = font_name
        self.is_bold = is_bold
        self.page_number = page_number

    def __repr__(self):
        return f"<Line p={self.page_number} y={self.top:.1f} sz={self.font_size:.1f} bold={self.is_bold}: {self.text[:30]!r}>"


class ParsedPage:
    def __init__(self, page_number: int, width: float, height: float):
        self.page_number = page_number
        self.width = width
        self.height = height
        self.lines: List[ParsedLine] = []
        self.tables: List[TableBlock] = []
        self.table_bboxes: List[Tuple[float, float, float, float]] = []


class ParsedDocument:
    def __init__(self, filename: str):
        self.filename = filename
        self.pages: List[ParsedPage] = []
        self.body_font_size: float = 9.0
        self.diagnostics: List[DiagnosticMessage] = []


def is_inside_any_bbox(x0: float, top: float, x1: float, bottom: float, bboxes: List[Tuple[float, float, float, float]]) -> bool:
    """Check if a word/rect intersects with any table bounding box (with 2pt tolerance)."""
    for bx0, btop, bx1, bbottom in bboxes:
        if not (x1 < bx0 - 2 or x0 > bx1 + 2 or bottom < btop - 2 or top > bbottom + 2):
            return True
    return False


def parse_pdf(pdf_path: str) -> ParsedDocument:
    """
    Parse a PDF file, extracting pages, typography, text lines outside tables, and tables.
    """
    doc = ParsedDocument(filename=pdf_path)
    all_font_sizes = []

    with pdfplumber.open(pdf_path) as pdf:
        table_counter = 1

        for p_idx, page in enumerate(pdf.pages, start=1):
            parsed_page = ParsedPage(page_number=p_idx, width=float(page.width), height=float(page.height))

            # 1. Extract tables and their bounding boxes
            tables_found = page.find_tables()
            for t in tables_found:
                raw_matrix = t.extract()
                if not raw_matrix or len(raw_matrix) < 1:
                    continue

                parsed_page.table_bboxes.append(t.bbox)

                # Separate headers and rows
                headers = [str(c).strip() if c is not None else "" for c in raw_matrix[0]]
                rows = []
                for r in raw_matrix[1:]:
                    cleaned_row = [str(c).strip() if c is not None else "" for c in r]
                    rows.append(cleaned_row)

                table_block = TableBlock(
                    table_id=table_counter,
                    headers=headers,
                    rows=rows,
                    page=p_idx,
                )
                parsed_page.tables.append(table_block)
                table_counter += 1

                # Diagnostic check for irregular table cells
                col_counts = [len(r) for r in raw_matrix]
                if len(set(col_counts)) > 1:
                    doc.diagnostics.append(
                        DiagnosticMessage(
                            level="WARNING",
                            message=f"Table {table_block.table_id} on page {p_idx} has irregular column count: {col_counts}",
                            context={"page": p_idx, "table_id": table_block.table_id},
                        )
                    )

            # 2. Extract words outside of table bounding boxes
            words = page.extract_words(
                extra_attrs=["fontname", "size"],
                keep_blank_chars=False,
                use_text_flow=True,
            )

            # Filter out words that fall inside table bounding boxes
            non_table_words = []
            for w in words:
                x0, top, x1, bottom = float(w["x0"]), float(w["top"]), float(w["bottom"] - w["height"]), float(w["bottom"])
                if not is_inside_any_bbox(x0, top, x1, bottom, parsed_page.table_bboxes):
                    non_table_words.append(w)
                    all_font_sizes.append(round(float(w["size"]), 1))

            # 3. Cluster words into coherent lines by vertical proximity
            # Sort words primarily by vertical top (with small bucketing) then x0
            if non_table_words:
                non_table_words.sort(key=lambda w: (w["top"], w["x0"]))
                line_buckets: List[List[Dict[str, Any]]] = []

                for w in non_table_words:
                    placed = False
                    w_top = float(w["top"])
                    w_bottom = float(w["bottom"])
                    w_mid = (w_top + w_bottom) / 2.0

                    for bucket in line_buckets:
                        b_top = min(bw["top"] for bw in bucket)
                        b_bottom = max(bw["bottom"] for bw in bucket)
                        b_mid = (b_top + b_bottom) / 2.0

                        # If vertical center falls within 3.5 points, consider it the same line
                        if abs(w_mid - b_mid) < 3.5:
                            bucket.append(w)
                            placed = True
                            break

                    if not placed:
                        line_buckets.append([w])

                # Sort line buckets by top coordinate
                line_buckets.sort(key=lambda b: min(bw["top"] for bw in b))

                # Build ParsedLine objects
                for bucket in line_buckets:
                    bucket.sort(key=lambda w: float(w["x0"]))
                    line_text = " ".join(str(w["text"]).strip() for w in bucket if str(w["text"]).strip())
                    if not line_text:
                        continue

                    bx0 = min(float(w["x0"]) for w in bucket)
                    btop = min(float(w["top"]) for w in bucket)
                    bx1 = max(float(w["x1"]) for w in bucket)
                    bbottom = max(float(w["bottom"]) for w in bucket)

                    font_sizes = [float(w["size"]) for w in bucket]
                    avg_size = round(sum(font_sizes) / len(font_sizes), 1)

                    font_names = [str(w.get("fontname", "")) for w in bucket]
                    is_bold = any("bold" in fn.lower() or "black" in fn.lower() for fn in font_names)
                    primary_font = Counter(font_names).most_common(1)[0][0]

                    parsed_line = ParsedLine(
                        text=line_text,
                        x0=bx0,
                        top=btop,
                        x1=bx1,
                        bottom=bbottom,
                        font_size=avg_size,
                        font_name=primary_font,
                        is_bold=is_bold,
                        page_number=p_idx,
                    )
                    parsed_page.lines.append(parsed_line)

            doc.pages.append(parsed_page)

    # Determine dominant body font size across document
    if all_font_sizes:
        size_counts = Counter(all_font_sizes)
        # Most common font size that is not tiny (>= 7.0)
        valid_sizes = [sz for sz in size_counts if sz >= 7.0]
        if valid_sizes:
            doc.body_font_size = max(valid_sizes, key=lambda s: size_counts[s])
        else:
            doc.body_font_size = 9.0
    else:
        doc.body_font_size = 9.0

    return doc
