"""
Deterministic synthetic edge-case document generator and reference ground truth.
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


def get_edgecases_data() -> Tuple[DocumentManifest, str]:
    """Return the ground truth manifest and reference markdown for the edge-case document."""
    manifest = DocumentManifest(
        doc_id="edge_cases",
        filename="edge_cases.pdf",
        title="Document Ingestion Edge Cases and Structural Stress Test",
        page_count=1,
        headings=[
            HeadingItem(level=1, text="Document Ingestion Edge Cases and Structural Stress Test", page=1),
            HeadingItem(level=2, text="1. Special Characters and International Currencies", page=1),
            HeadingItem(level=2, text="2. Accented Characters and Multilingual Typography", page=1),
            HeadingItem(level=2, text="3. Hierarchical Nested Lists", page=1),
            HeadingItem(level=2, text="4. Boundary Condition Error Matrix Table", page=1),
            HeadingItem(level=2, text="5. Monospace Configuration Parameters", page=1),
        ],
        tables=[
            TableBlock(
                table_id=1,
                headers=["Error Code", "HTTP Status", "Failure Description", "Resolution Action"],
                rows=[
                    ["ERR_AUTH_01", "401 Unauthorized", "Expired OAuth2 bearer token", "Refresh access token via identity provider"],
                    ["ERR_RATE_02", "429 Too Many Requests", "Rate limit exceeded on endpoint /v1/ingest", "Apply exponential backoff and jitter"],
                    ["ERR_SRV_03", "503 Unavailable", "Upstream worker queue saturation", "Route traffic to secondary cluster"],
                    ["ERR_FALLBACK", "200 OK (Degraded)", "Cache hit served with stale header", "None"],
                ],
                page=1,
            )
        ],
        lists=[
            ListItem(
                text="Primary Tier: Ingestion Engine Configuration",
                list_type="bullet",
                depth=0,
                page=1,
            ),
            ListItem(
                text="Sub-tier A: Stream parsing with deterministic memory limits",
                list_type="bullet",
                depth=1,
                page=1,
            ),
            ListItem(
                text="Sub-tier B: Dynamic bounding-box reconciliation for multi-column layouts",
                list_type="bullet",
                depth=1,
                page=1,
            ),
            ListItem(
                text="Secondary Tier: Verification and Compliance Rules",
                list_type="bullet",
                depth=0,
                page=1,
            ),
            ListItem(
                text="Sub-tier C: Cryptographic checksum validation on rendered output",
                list_type="bullet",
                depth=1,
                page=1,
            ),
        ],
        text_blocks=[
            "Financial values include: US Dollar: $12,450.00 | British Pound: GBP 8,920.50 | Euro: EUR 11,340.25 | Japanese Yen: JPY 1,500,000.",
            "Mathematical conditions: tolerance delta <= 0.05, confidence score >= 0.98, variance != 0.0, and aggregate sum(x_i) = 1.0.",
            "Typographic punctuation: em-dash -- without padding -- and en-dash (range 10-20), plus \"standard quotes\" and 'single quotes'.",
            "International accented vocabulary: The Zurich analyst reviewed the resume with naive facade over an Uber-efficient pipeline.",
            "Runtime environment parameters: INGESTION_CHUNK_SIZE=4096, MAX_CONCURRENT_WORKERS=8, TIMEOUT_MS=15000, and ENABLE_STRICT_TABLES=true.",
        ],
        reading_order_anchors=[
            "Document Ingestion Edge Cases and Structural Stress Test",
            "1. Special Characters and International Currencies",
            "Financial values include",
            "2. Accented Characters and Multilingual Typography",
            "3. Hierarchical Nested Lists",
            "Primary Tier: Ingestion Engine Configuration",
            "4. Boundary Condition Error Matrix Table",
            "ERR_AUTH_01",
            "5. Monospace Configuration Parameters",
            "INGESTION_CHUNK_SIZE=4096",
        ],
        expected_char_count=2450,
        expected_word_count=290,
    )

    ref_md = """# Document Ingestion Edge Cases and Structural Stress Test

## 1. Special Characters and International Currencies

Financial values include: US Dollar: $12,450.00 | British Pound: GBP 8,920.50 | Euro: EUR 11,340.25 | Japanese Yen: JPY 1,500,000.

Mathematical conditions: tolerance delta <= 0.05, confidence score >= 0.98, variance != 0.0, and aggregate sum(x_i) = 1.0.

Typographic punctuation: em-dash -- without padding -- and en-dash (range 10-20), plus "standard quotes" and 'single quotes'.

## 2. Accented Characters and Multilingual Typography

International accented vocabulary: The Zurich analyst reviewed the resume with naive facade over an Uber-efficient pipeline.

## 3. Hierarchical Nested Lists

* Primary Tier: Ingestion Engine Configuration
  * Sub-tier A: Stream parsing with deterministic memory limits
  * Sub-tier B: Dynamic bounding-box reconciliation for multi-column layouts
* Secondary Tier: Verification and Compliance Rules
  * Sub-tier C: Cryptographic checksum validation on rendered output

## 4. Boundary Condition Error Matrix Table

| Error Code | HTTP Status | Failure Description | Resolution Action |
| --- | --- | --- | --- |
| ERR_AUTH_01 | 401 Unauthorized | Expired OAuth2 bearer token | Refresh access token via identity provider |
| ERR_RATE_02 | 429 Too Many Requests | Rate limit exceeded on endpoint /v1/ingest | Apply exponential backoff and jitter |
| ERR_SRV_03 | 503 Unavailable | Upstream worker queue saturation | Route traffic to secondary cluster |
| ERR_FALLBACK | 200 OK (Degraded) | Cache hit served with stale header | None |

## 5. Monospace Configuration Parameters

Runtime environment parameters: INGESTION_CHUNK_SIZE=4096, MAX_CONCURRENT_WORKERS=8, TIMEOUT_MS=15000, and ENABLE_STRICT_TABLES=true.
"""
    return manifest, ref_md


def build_edgecases_pdf() -> bytes:
    """Build the deterministic PDF binary for the edge-case document."""
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
        fontSize=16,
        leading=20,
        spaceAfter=8,
        textColor=colors.HexColor("#0f172a"),
    )
    h2 = ParagraphStyle(
        "DocH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        spaceBefore=7,
        spaceAfter=3,
        textColor=colors.HexColor("#1e293b"),
    )
    body = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        spaceAfter=4,
        textColor=colors.HexColor("#334155"),
    )
    bullet_l0 = ParagraphStyle(
        "DocBullet0",
        parent=body,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=2,
    )
    bullet_l1 = ParagraphStyle(
        "DocBullet1",
        parent=body,
        leftIndent=28,
        firstLineIndent=-10,
        spaceAfter=2,
    )

    manifest, _ = get_edgecases_data()
    story = []

    story.append(Paragraph(manifest.title, h1))

    # Section 1
    story.append(Paragraph(manifest.headings[1].text, h2))
    story.append(Paragraph(manifest.text_blocks[0], body))
    story.append(Paragraph(manifest.text_blocks[1], body))
    story.append(Paragraph(manifest.text_blocks[2], body))

    # Section 2
    story.append(Paragraph(manifest.headings[2].text, h2))
    story.append(Paragraph(manifest.text_blocks[3], body))

    # Section 3
    story.append(Paragraph(manifest.headings[3].text, h2))
    for item in manifest.lists:
        style = bullet_l1 if item.depth > 0 else bullet_l0
        story.append(Paragraph(f"&bull; {item.text}", style))
    story.append(Spacer(1, 4))

    # Section 4
    story.append(Paragraph(manifest.headings[4].text, h2))
    t_data = [manifest.tables[0].headers] + manifest.tables[0].rows
    table = Table(t_data, colWidths=[90, 100, 160, 154])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#475569")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 4))

    # Section 5
    story.append(Paragraph(manifest.headings[5].text, h2))
    story.append(Paragraph(manifest.text_blocks[4], body))

    doc.build(story)
    return buf.getvalue()
