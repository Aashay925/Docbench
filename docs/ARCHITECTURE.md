# Document Ingestion Architecture

## 1. System Overview

`document-ingestion-benchmark` (`docbench`) implements a modular, high-throughput, conservative PDF-to-Markdown ingestion pipeline designed specifically for deterministic document transformation and evaluation.

```
+-------------------------------------------------------------------------+
|                              INPUT LAYER                                |
|  - Deterministic Synthetic PDFs (ReportLab + PyPDF Normalizer)          |
|  - External Enterprise PDFs (Contracts, Reports, Financial Statements)  |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                           PARSING SUBSYSTEM                             |
|  (docbench.ingestion.parser)                                            |
|                                                                         |
|  +--------------------+         +------------------------------------+  |
|  |  Table Detection   |         |      Word & Geometry Extractor     |  |
|  |  (Explicit BBox)   |         |  (pdfplumber / pdfminer.six core)  |  |
|  +--------------------+         +------------------------------------+  |
|            |                                      |                     |
|            +------------------+-------------------+                     |
|                               v                                         |
|                 Spatial Bounding-Box Filter                             |
|                 (Removes text within table BBoxes)                      |
|                               v                                         |
|                 Vertical Line Clusterer                                 |
|                 (Top-coordinate bucketing & font metrics)               |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                         CONVERSION SUBSYSTEM                            |
|  (docbench.ingestion.converter)                                         |
|                                                                         |
|  - Font Distribution Analyzer (Calculates baseline body size)            |
|  - Heading Level Classifier (H1, H2, H3 from font size & bold weight)   |
|  - List Recognizer (Bullet characters, numbered patterns, indent depth) |
|  - Table Formatter (Converts TableBlock matrix to clean GFM tables)     |
|  - Paragraph Flow Manager (Dynamic vertical leading gap detection)     |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                          PIPELINE & METRICS                             |
|  (docbench.ingestion.pipeline & docbench.metrics)                       |
|                                                                         |
|  - Input PDF SHA-256 Hash Calculation                                   |
|  - Wall-clock High-Resolution Profiling (time.perf_counter)             |
|  - Output Markdown SHA-256 Hash Verification                            |
|  - Metric Evaluator (Headings, Tables, Text, Reading Order, Lists)      |
|  - Repeatability Runner (Determinism & Jitter Profiler)                 |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                           OUTPUT ARTIFACTS                              |
|  - Markdown Report (outputs/benchmark_report.md)                        |
|  - JSON Metric Manifest (outputs/benchmark_report.json)                 |
|  - CSV Summary Table (outputs/benchmark_summary.csv)                    |
|  - Rich Interactive Console Terminal Output                             |
+-------------------------------------------------------------------------+
```

---

## 2. Core Architectural Decisions

### 2.1 Spatial Table Isolation (Preventing Duplicate Extraction)
A fundamental flaw in naive PDF extractors is that text inside tables is extracted twice: first as disconnected raw lines during text extraction, and second during table extraction.

`docbench` resolves this by executing table detection first:
1. `page.find_tables()` isolates the exact bounding box `(x0, top, x1, bottom)` for each detected table.
2. The word extraction pass checks intersection against all table bounding boxes using `is_inside_any_bbox()`.
3. Any words falling within table regions are filtered out of the general line stream.
4. Tables are inserted into the element stream as distinct `TableBlock` objects at their exact vertical position.

### 2.2 Adaptive Font Hierarchy Clustering
Rather than hardcoding arbitrary font sizes, `docbench` dynamically profiles the font distribution across the document:
- The dominant frequency font size (typically 8.5–9.5 pt) is established as `body_font_size`.
- **Level 1 Headings (`#`)**: Font size $\ge 1.45 \times \text{body\_size}$ with bold weight.
- **Level 2 Headings (`##`)**: Font size $\ge 1.22 \times \text{body\_size}$ and $< 1.45 \times \text{body\_size}$ with bold weight.
- **Level 3 Headings (`###`)**: Font size $\ge 1.05 \times \text{body\_size}$ and $< 1.22 \times \text{body\_size}$ with bold weight.

### 2.3 Paragraph Leading and Wrapping
PDF files store text as positioned glyphs without explicit paragraph markup. `docbench` tracks vertical gaps between consecutive lines:
- When the gap between the baseline of line $i$ and the top of line $i+1$ is small ($\le 5.5$ pt), lines are merged with a space to form continuous wrapped paragraphs.
- When the vertical gap exceeds the paragraph threshold ($> 5.5$ pt), a paragraph boundary (`\n\n`) is emitted.

### 2.4 Strict GFM Table Formatting
Tables are rendered as standard GitHub Flavored Markdown (GFM):
```markdown
| Column Header 1 | Column Header 2 |
| --- | --- |
| Row 1 Value | Row 1 Value |
```
Internal pipe characters (`|`) inside cell text are automatically escaped to `\|` to preserve table syntax.

---

## 3. Data Structures and AST Model

The ingestion engine represents documents using Pydantic data models defined in `docbench.ingestion.models`:
- `HeadingItem`: Level, normalized text, page number.
- `TableBlock`: Table index, headers list, 2D matrix of cell rows, page number.
- `ListItem`: Text, list type (`bullet` or `numbered`), nesting depth, page number.
- `DiagnosticMessage`: Severity level (`INFO`, `WARNING`, `ERROR`), message, context dict.
- `IngestionResult`: PDF SHA-256, Markdown SHA-256, duration in milliseconds, page count, extracted elements, diagnostics.
- `DocumentEvaluation`: Per-document scores across all 5 evaluation dimensions plus composite score.
