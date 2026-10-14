"""
Deterministic synthetic contract generator and reference ground truth.
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


def get_contract_data() -> Tuple[DocumentManifest, str]:
    """Return the ground truth manifest and reference markdown for the contract."""
    manifest = DocumentManifest(
        doc_id="contract",
        filename="contract.pdf",
        title="Master Services Agreement",
        page_count=1,
        headings=[
            HeadingItem(level=1, text="Master Services Agreement", page=1),
            HeadingItem(level=2, text="1. Engagement and Scope of Work", page=1),
            HeadingItem(level=2, text="2. Fees and Payment Terms", page=1),
            HeadingItem(level=2, text="3. Term and Termination", page=1),
            HeadingItem(level=2, text="4. Confidentiality and Proprietary Rights", page=1),
            HeadingItem(level=2, text="5. Signatures and Execution", page=1),
        ],
        tables=[
            TableBlock(
                table_id=1,
                headers=["Party", "Authorized Representative", "Title", "Date"],
                rows=[
                    ["Nexus Technologies LLC", "Eleanor Vance", "Chief Information Officer", "January 1, 2026"],
                    ["Apex Systems Inc.", "Marcus Sterling", "Chief Executive Officer", "January 1, 2026"],
                ],
                page=1,
            )
        ],
        lists=[
            ListItem(
                text="Cloud infrastructure architecture audit and remediation roadmap",
                list_type="bullet",
                depth=0,
                page=1,
            ),
            ListItem(
                text="Automated continuous integration and deployment pipeline setup",
                list_type="bullet",
                depth=0,
                page=1,
            ),
            ListItem(
                text="High-availability database clustering and replication configuration",
                list_type="bullet",
                depth=0,
                page=1,
            ),
            ListItem(
                text="24/7 incident response monitoring and escalation procedures",
                list_type="bullet",
                depth=0,
                page=1,
            ),
        ],
        text_blocks=[
            "This Master Services Agreement is entered into as of January 1, 2026, by and between Nexus Technologies LLC (\"Client\") and Apex Systems Inc. (\"Provider\").",
            "Provider shall render specialized systems engineering, reliability architecture, and platform automation services described herein.",
            "Client shall pay Provider a fixed monthly retainer of $24,500.00 USD, payable net 30 days from date of monthly invoice.",
            "This Agreement commences on January 1, 2026, and continues for an initial period of twelve (12) months unless terminated with thirty (30) days prior written notice.",
            "Each party agrees to maintain in strict confidence all proprietary data, architectural designs, and trade secrets disclosed during this engagement.",
        ],
        reading_order_anchors=[
            "Master Services Agreement",
            "This Master Services Agreement is entered into as of January 1, 2026",
            "1. Engagement and Scope of Work",
            "Cloud infrastructure architecture audit and remediation roadmap",
            "2. Fees and Payment Terms",
            "3. Term and Termination",
            "4. Confidentiality and Proprietary Rights",
            "5. Signatures and Execution",
            "Eleanor Vance",
        ],
        expected_char_count=1850,
        expected_word_count=260,
    )

    ref_md = """# Master Services Agreement

This Master Services Agreement is entered into as of January 1, 2026, by and between Nexus Technologies LLC ("Client") and Apex Systems Inc. ("Provider").

## 1. Engagement and Scope of Work

Provider shall render specialized systems engineering, reliability architecture, and platform automation services described herein.

* Cloud infrastructure architecture audit and remediation roadmap
* Automated continuous integration and deployment pipeline setup
* High-availability database clustering and replication configuration
* 24/7 incident response monitoring and escalation procedures

## 2. Fees and Payment Terms

Client shall pay Provider a fixed monthly retainer of $24,500.00 USD, payable net 30 days from date of monthly invoice.

## 3. Term and Termination

This Agreement commences on January 1, 2026, and continues for an initial period of twelve (12) months unless terminated with thirty (30) days prior written notice.

## 4. Confidentiality and Proprietary Rights

Each party agrees to maintain in strict confidence all proprietary data, architectural designs, and trade secrets disclosed during this engagement.

## 5. Signatures and Execution

| Party | Authorized Representative | Title | Date |
| --- | --- | --- | --- |
| Nexus Technologies LLC | Eleanor Vance | Chief Information Officer | January 1, 2026 |
| Apex Systems Inc. | Marcus Sterling | Chief Executive Officer | January 1, 2026 |
"""
    return manifest, ref_md


def build_contract_pdf() -> bytes:
    """Build the deterministic PDF binary for the contract."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "DocH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        spaceAfter=12,
        textColor=colors.HexColor("#0f172a"),
    )
    h2 = ParagraphStyle(
        "DocH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        spaceBefore=10,
        spaceAfter=6,
        textColor=colors.HexColor("#1e293b"),
    )
    body = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        spaceAfter=6,
        textColor=colors.HexColor("#334155"),
    )
    bullet = ParagraphStyle(
        "DocBullet",
        parent=body,
        leftIndent=16,
        firstLineIndent=-12,
        spaceAfter=3,
    )

    manifest, _ = get_contract_data()
    story = []

    story.append(Paragraph(manifest.title, h1))
    story.append(Paragraph(manifest.text_blocks[0], body))
    story.append(Spacer(1, 4))

    story.append(Paragraph(manifest.headings[1].text, h2))
    story.append(Paragraph(manifest.text_blocks[1], body))
    for item in manifest.lists:
        story.append(Paragraph(f"&bull; {item.text}", bullet))
    story.append(Spacer(1, 4))

    story.append(Paragraph(manifest.headings[2].text, h2))
    story.append(Paragraph(manifest.text_blocks[2], body))
    story.append(Spacer(1, 4))

    story.append(Paragraph(manifest.headings[3].text, h2))
    story.append(Paragraph(manifest.text_blocks[3], body))
    story.append(Spacer(1, 4))

    story.append(Paragraph(manifest.headings[4].text, h2))
    story.append(Paragraph(manifest.text_blocks[4], body))
    story.append(Spacer(1, 4))

    story.append(Paragraph(manifest.headings[5].text, h2))

    t_data = [manifest.tables[0].headers] + manifest.tables[0].rows
    table = Table(t_data, colWidths=[120, 130, 140, 114])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1e293b")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]
        )
    )
    story.append(table)

    doc.build(story)
    return buf.getvalue()
