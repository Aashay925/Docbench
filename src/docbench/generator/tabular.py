"""
Deterministic synthetic tabular business report generator and reference ground truth.
"""

import io
from typing import Tuple
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from docbench.ingestion.models import (
    DocumentManifest,
    HeadingItem,
    TableBlock,
    ListItem,
)


def get_tabular_data() -> Tuple[DocumentManifest, str]:
    """Return the ground truth manifest and reference markdown for the tabular report."""
    manifest = DocumentManifest(
        doc_id="tabular_report",
        filename="tabular_report.pdf",
        title="Acme Holdings - Q4 Financial & Operational Report",
        page_count=1,
        headings=[
            HeadingItem(level=1, text="Acme Holdings - Q4 Financial & Operational Report", page=1),
            HeadingItem(level=2, text="Executive Summary", page=1),
            HeadingItem(level=2, text="Financial Performance Summary", page=1),
            HeadingItem(level=2, text="Business Segment Breakdown", page=1),
            HeadingItem(level=2, text="Operational Efficiency Commentary", page=1),
        ],
        tables=[
            TableBlock(
                table_id=1,
                headers=["Metric", "Q3 2025", "Q4 2025", "Variance (%)", "YoY Growth (%)"],
                rows=[
                    ["Total Revenue ($M)", "142.50", "168.20", "+18.0%", "+24.6%"],
                    ["Gross Profit ($M)", "98.30", "119.40", "+21.5%", "+28.1%"],
                    ["Operating Income ($M)", "34.20", "44.80", "+31.0%", "+36.2%"],
                    ["Net Income ($M)", "26.80", "35.10", "+31.0%", "+33.0%"],
                    ["Diluted EPS ($)", "0.82", "1.07", "+30.5%", "+32.1%"],
                ],
                page=1,
            ),
            TableBlock(
                table_id=2,
                headers=["Division", "Revenue ($M)", "Operating Margin", "Headcount", "Key Growth Driver"],
                rows=[
                    ["Cloud Infrastructure", "78.40", "32.5%", "420", "Enterprise Migration"],
                    ["Enterprise Software", "54.60", "28.0%", "310", "AI Integration Suite"],
                    ["Professional Services", "35.20", "18.5%", "215", "Advisory Engagements"],
                ],
                page=1,
            ),
        ],
        lists=[],
        text_blocks=[
            "Acme Holdings delivered strong operating results for the fourth quarter ended December 31, 2025, driven by accelerating adoption of enterprise cloud products and high-margin recurring subscriptions.",
            "Consolidated net revenue grew 24.6% year-over-year to $168.20 million, with gross margins expanding 180 basis points due to infrastructure efficiencies.",
            "Operating margin expansion reflected disciplined expense management alongside strategic investment in machine learning infrastructure and engineering talent.",
        ],
        reading_order_anchors=[
            "Acme Holdings - Q4 Financial & Operational Report",
            "Executive Summary",
            "Financial Performance Summary",
            "Total Revenue ($M)",
            "Business Segment Breakdown",
            "Cloud Infrastructure",
            "Operational Efficiency Commentary",
        ],
        expected_char_count=1920,
        expected_word_count=230,
    )

    ref_md = """# Acme Holdings - Q4 Financial & Operational Report

## Executive Summary

Acme Holdings delivered strong operating results for the fourth quarter ended December 31, 2025, driven by accelerating adoption of enterprise cloud products and high-margin recurring subscriptions.

## Financial Performance Summary

Consolidated net revenue grew 24.6% year-over-year to $168.20 million, with gross margins expanding 180 basis points due to infrastructure efficiencies.

| Metric | Q3 2025 | Q4 2025 | Variance (%) | YoY Growth (%) |
| --- | --- | --- | --- | --- |
| Total Revenue ($M) | 142.50 | 168.20 | +18.0% | +24.6% |
| Gross Profit ($M) | 98.30 | 119.40 | +21.5% | +28.1% |
| Operating Income ($M) | 34.20 | 44.80 | +31.0% | +36.2% |
| Net Income ($M) | 26.80 | 35.10 | +31.0% | +33.0% |
| Diluted EPS ($) | 0.82 | 1.07 | +30.5% | +32.1% |

## Business Segment Breakdown

| Division | Revenue ($M) | Operating Margin | Headcount | Key Growth Driver |
| --- | --- | --- | --- | --- |
| Cloud Infrastructure | 78.40 | 32.5% | 420 | Enterprise Migration |
| Enterprise Software | 54.60 | 28.0% | 310 | AI Integration Suite |
| Professional Services | 35.20 | 18.5% | 215 | Advisory Engagements |

## Operational Efficiency Commentary

Operating margin expansion reflected disciplined expense management alongside strategic investment in machine learning infrastructure and engineering talent.
"""
    return manifest, ref_md


def build_tabular_pdf() -> bytes:
    """Build the deterministic PDF binary for the tabular report."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "DocH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        spaceAfter=10,
        textColor=colors.HexColor("#0f172a"),
    )
    h2 = ParagraphStyle(
        "DocH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        spaceBefore=8,
        spaceAfter=4,
        textColor=colors.HexColor("#1e293b"),
    )
    body = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12.5,
        spaceAfter=6,
        textColor=colors.HexColor("#334155"),
    )

    manifest, _ = get_tabular_data()
    story = []

    story.append(Paragraph(manifest.title, h1))
    story.append(Paragraph(manifest.headings[1].text, h2))
    story.append(Paragraph(manifest.text_blocks[0], body))

    story.append(Paragraph(manifest.headings[2].text, h2))
    story.append(Paragraph(manifest.text_blocks[1], body))

    t1_data = [manifest.tables[0].headers] + manifest.tables[0].rows
    table1 = Table(t1_data, colWidths=[164, 85, 85, 85, 85])
    table1.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ]
        )
    )
    story.append(table1)
    story.append(Spacer(1, 8))

    story.append(Paragraph(manifest.headings[3].text, h2))
    t2_data = [manifest.tables[1].headers] + manifest.tables[1].rows
    table2 = Table(t2_data, colWidths=[144, 90, 100, 70, 100])
    table2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 0), (3, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ]
        )
    )
    story.append(table2)
    story.append(Spacer(1, 8))

    story.append(Paragraph(manifest.headings[4].text, h2))
    story.append(Paragraph(manifest.text_blocks[2], body))

    doc.build(story)
    return buf.getvalue()
