"""
Deterministic synthetic multi-page report generator and reference ground truth.
"""

import io
from typing import Tuple
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from docbench.ingestion.models import (
    DocumentManifest,
    HeadingItem,
    TableBlock,
    ListItem,
)


def get_multipage_data() -> Tuple[DocumentManifest, str]:
    """Return the ground truth manifest and reference markdown for the multi-page report."""
    manifest = DocumentManifest(
        doc_id="multipage_report",
        filename="multipage_report.pdf",
        title="Enterprise Systems Architecture Report",
        page_count=3,
        headings=[
            HeadingItem(level=1, text="Enterprise Systems Architecture Report", page=1),
            HeadingItem(level=2, text="Executive Overview and Scope", page=1),
            HeadingItem(level=2, text="1. High-Level System Objectives", page=1),
            HeadingItem(level=2, text="2. Core Service Infrastructure", page=2),
            HeadingItem(level=3, text="2.1 Event Streaming and Messaging", page=2),
            HeadingItem(level=2, text="3. Security, Compliance, and Data Governance", page=3),
            HeadingItem(level=2, text="4. Architectural Conclusions and Next Steps", page=3),
        ],
        tables=[
            TableBlock(
                table_id=1,
                headers=["Component", "Technology", "Target Latency", "Redundancy"],
                rows=[
                    ["API Gateway", "Envoy Proxy", "< 5 ms", "N+2 Active"],
                    ["Auth Engine", "OAuth2 / OIDC", "< 12 ms", "Multi-Region"],
                    ["Event Broker", "Apache Kafka", "< 15 ms", "3x Replicas"],
                    ["Primary Store", "PostgreSQL HA", "< 25 ms", "Synchronous Leader"],
                ],
                page=2,
            )
        ],
        lists=[
            ListItem(
                text="Achieve 99.99% availability across multi-region deployment zones.",
                list_type="numbered",
                depth=0,
                page=1,
            ),
            ListItem(
                text="Maintain p99 API response latencies below 85 milliseconds under peak loads.",
                list_type="numbered",
                depth=0,
                page=1,
            ),
            ListItem(
                text="Enforce zero-trust mutual TLS authentication between all internal services.",
                list_type="numbered",
                depth=0,
                page=1,
            ),
            ListItem(
                text="Guarantee automated database failover within 120 seconds of telemetry loss.",
                list_type="numbered",
                depth=0,
                page=1,
            ),
            ListItem(
                text="Hardware Security Module key rotation enforced every 90 days",
                list_type="bullet",
                depth=0,
                page=3,
            ),
            ListItem(
                text="Role-based access control policies validated via automated CI tests",
                list_type="bullet",
                depth=0,
                page=3,
            ),
            ListItem(
                text="Continuous static and dynamic vulnerability analysis on all container images",
                list_type="bullet",
                depth=0,
                page=3,
            ),
        ],
        text_blocks=[
            "This document establishes the production architectural standards for the next-generation distributed transaction processing system.",
            "All core subsystems are designed for fault-tolerant operation across three geographic regions with active-active routing topologies.",
            "The microservice plane isolates stateless business logic from stateful storage engines, facilitating elastic horizontal autoscaling during unpredictable traffic surges.",
            "Event-driven streaming via distributed commit logs enables decoupled communication patterns and reliable change data capture between asynchronous consumers.",
            "Enterprise compliance requirements necessitate immutable audit logging and strict cryptographic isolation for customer financial transactions.",
            "Implementation will proceed in staged delivery milestones, commencing with canary verification of edge gateway proxies and foundational database replication.",
        ],
        reading_order_anchors=[
            "Enterprise Systems Architecture Report",
            "Executive Overview and Scope",
            "1. High-Level System Objectives",
            "Achieve 99.99% availability across multi-region deployment zones.",
            "2. Core Service Infrastructure",
            "API Gateway",
            "2.1 Event Streaming and Messaging",
            "3. Security, Compliance, and Data Governance",
            "Hardware Security Module key rotation enforced every 90 days",
            "4. Architectural Conclusions and Next Steps",
        ],
        expected_char_count=3200,
        expected_word_count=380,
    )

    ref_md = """# Enterprise Systems Architecture Report

## Executive Overview and Scope

This document establishes the production architectural standards for the next-generation distributed transaction processing system.

## 1. High-Level System Objectives

All core subsystems are designed for fault-tolerant operation across three geographic regions with active-active routing topologies.

1. Achieve 99.99% availability across multi-region deployment zones.
2. Maintain p99 API response latencies below 85 milliseconds under peak loads.
3. Enforce zero-trust mutual TLS authentication between all internal services.
4. Guarantee automated database failover within 120 seconds of telemetry loss.

## 2. Core Service Infrastructure

The microservice plane isolates stateless business logic from stateful storage engines, facilitating elastic horizontal autoscaling during unpredictable traffic surges.

| Component | Technology | Target Latency | Redundancy |
| --- | --- | --- | --- |
| API Gateway | Envoy Proxy | < 5 ms | N+2 Active |
| Auth Engine | OAuth2 / OIDC | < 12 ms | Multi-Region |
| Event Broker | Apache Kafka | < 15 ms | 3x Replicas |
| Primary Store | PostgreSQL HA | < 25 ms | Synchronous Leader |

### 2.1 Event Streaming and Messaging

Event-driven streaming via distributed commit logs enables decoupled communication patterns and reliable change data capture between asynchronous consumers.

## 3. Security, Compliance, and Data Governance

Enterprise compliance requirements necessitate immutable audit logging and strict cryptographic isolation for customer financial transactions.

* Hardware Security Module key rotation enforced every 90 days
* Role-based access control policies validated via automated CI tests
* Continuous static and dynamic vulnerability analysis on all container images

## 4. Architectural Conclusions and Next Steps

Implementation will proceed in staged delivery milestones, commencing with canary verification of edge gateway proxies and foundational database replication.
"""
    return manifest, ref_md


def build_multipage_pdf() -> bytes:
    """Build the deterministic PDF binary for the multi-page report."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=44,
        bottomMargin=44,
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
        spaceBefore=10,
        spaceAfter=4,
        textColor=colors.HexColor("#1e293b"),
    )
    h3 = ParagraphStyle(
        "DocH3",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        spaceBefore=8,
        spaceAfter=3,
        textColor=colors.HexColor("#334155"),
    )
    body = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        spaceAfter=6,
        textColor=colors.HexColor("#334155"),
    )
    num_list_style = ParagraphStyle(
        "DocNumList",
        parent=body,
        leftIndent=16,
        firstLineIndent=-12,
        spaceAfter=3,
    )
    bullet_style = ParagraphStyle(
        "DocBullet",
        parent=body,
        leftIndent=16,
        firstLineIndent=-12,
        spaceAfter=3,
    )

    manifest, _ = get_multipage_data()
    story = []

    # Page 1
    story.append(Paragraph(manifest.title, h1))
    story.append(Paragraph(manifest.headings[1].text, h2))
    story.append(Paragraph(manifest.text_blocks[0], body))

    story.append(Paragraph(manifest.headings[2].text, h2))
    story.append(Paragraph(manifest.text_blocks[1], body))

    for idx, item in enumerate(manifest.lists[:4], start=1):
        story.append(Paragraph(f"{idx}. {item.text}", num_list_style))

    story.append(PageBreak())

    # Page 2
    story.append(Paragraph(manifest.headings[3].text, h2))
    story.append(Paragraph(manifest.text_blocks[2], body))

    t_data = [manifest.tables[0].headers] + manifest.tables[0].rows
    table = Table(t_data, colWidths=[130, 130, 110, 134])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0fdfa"), colors.white]),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 8))

    story.append(Paragraph(manifest.headings[4].text, h3))
    story.append(Paragraph(manifest.text_blocks[3], body))

    story.append(PageBreak())

    # Page 3
    story.append(Paragraph(manifest.headings[5].text, h2))
    story.append(Paragraph(manifest.text_blocks[4], body))

    for item in manifest.lists[4:]:
        story.append(Paragraph(f"&bull; {item.text}", bullet_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph(manifest.headings[6].text, h2))
    story.append(Paragraph(manifest.text_blocks[5], body))

    doc.build(story)
    return buf.getvalue()
