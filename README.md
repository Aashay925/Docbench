# Document Ingestion Benchmark (`document-ingestion-benchmark`)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](docs/LICENSES.md)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](pyproject.toml)
[![Tests: 83 Passed](https://img.shields.io/badge/Tests-83%20Passed-success.svg)](tests/)
[![Score: 100%](https://img.shields.io/badge/Benchmark%20Score-100%2F100-emerald.svg)](outputs/benchmark_report.md)
[![Stability: 100% Deterministic](https://img.shields.io/badge/Repeatability-100%25%20Stable-purple.svg)](outputs/benchmark_summary.csv)
[![Validation: Hardened](https://img.shields.io/badge/Validation-14%20Negative%20Scenarios%20Hardened-blueviolet.svg)](docs/VALIDATION.md)
[![REST API: FastAPI](https://img.shields.io/badge/REST%20API-FastAPI%20v1-informational.svg)](docs/API.md)
[![Dashboard: Vanilla JS](https://img.shields.io/badge/Dashboard-HTML5%20%2F%20CSS%20%2F%20JS-blueviolet.svg)](#6-interactive-frontend-dashboard--api-service)

A high-precision, deterministic PDF-to-Markdown document ingestion and structural preservation benchmark suite built for engineering collaboration involving **Zipmd**.

---

## 1. Executive Summary & Motivation

Enterprise document workflows (such as legal contracts, multi-page technical reports, and tabular financial filings) increasingly depend on converting unstructured PDFs into clean, structured Markdown for consumption by LLMs and downstream RAG pipelines.

However, naive PDF extractors suffer from recurring structural failures:
- **Duplicate Table Content**: Text inside tables is often dumped twice—once as fragmented raw lines and once as table rows.
- **Lost Heading Hierarchy**: Document titles and section numbers lose their heading levels (`#`, `##`, `###`), destroying document navigation.
- **Non-Deterministic Extraction**: Stochastic or heuristic converters produce fluctuating outputs for the same input file.
- **Copyleft Licensing Traps**: Popular tools like `PyMuPDF4LLM` rely on `PyMuPDF` (AGPL-3.0), introducing legal and compliance hurdles for commercial distribution.

**`document-ingestion-benchmark` (`docbench`)** solves these problems:
1. **Conservative Determinism**: Uses spatial bounding-box isolation and adaptive font clustering to achieve **100% bitwise repeatable** Markdown output.
2. **Permissive Licensing**: Strictly avoids AGPL/GPL dependencies; built entirely on verified **MIT** and **BSD-3-Clause** libraries.
3. **Hardened Multi-Dimensional Benchmark Metrics**: Evaluates heading precision/recall, table-cell accuracy, verbatim text completeness (with duplication penalties), reading order (Kendall's Tau & LCS), list preservation (depth-strict), and repeatability.
4. **Adversarial Validation**: Hardened against 14 controlled corruption scenarios with dynamic weight re-normalization and critical failure detection.

---

## 2. Hardened Benchmark Results Matrix

Evaluated across four deterministic synthetic document topologies:

| Document ID | Topology | Heading F1 | Table Cell Acc | Text Comp | Reading Order | List F1 | Composite Score | Status | Ingestion Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `contract` | Master Services Agreement | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | **100.0%** | PASS | 48.7 ms |
| `tabular_report` | Q4 Financial Report | 100.0% | 100.0% | 100.0% | 100.0% | N/A | **100.0%** | PASS | 60.7 ms |
| `multipage_report` | 3-Page Architecture Spec | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | **100.0%** | PASS | 65.0 ms |
| `edge_cases` | Stress Test (Accents, Symbols) | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | **100.0%** | PASS | 79.3 ms |
| **CORPUS AVERAGE** | **All Topologies** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **ALL PASS** | **63.4 ms** |

*Note: For `tabular_report`, List F1 is transparently marked `N/A` (no list elements exist in the ground truth), and composite weights are dynamically re-normalized over applicable components rather than granting free points.*

### Repeatability & Latency Jitter (5 Consecutive Runs)

| Document ID | Runs | Bitwise SHA-256 Stability | Mean Latency | Latency Std Dev (Jitter) | Min / Max Latency |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `contract` | 5 | **100.0%** | 55.48 ms | 17.53 ms | 44.9 / 90.4 ms |
| `tabular_report` | 5 | **100.0%** | 60.51 ms | 12.34 ms | 46.2 / 77.2 ms |
| `multipage_report` | 5 | **100.0%** | 82.51 ms | 26.42 ms | 60.9 / 133.5 ms |
| `edge_cases` | 5 | **100.0%** | 62.56 ms | 5.45 ms | 56.5 / 71.8 ms |
| **CORPUS AVERAGE** | 5 | **100.0%** | **65.27 ms** | **15.44 ms** | - |

*Artifacts generated in `outputs/`: [`benchmark_report.md`](outputs/benchmark_report.md), [`benchmark_report.json`](outputs/benchmark_report.json), and [`benchmark_summary.csv`](outputs/benchmark_summary.csv).*

---

## 3. High-Level Architecture

```
                    +------------------------------------+
                    |        Input PDF Document          |
                    +------------------------------------+
                                      |
                                      v
          +-------------------------------------------------------+
          |  Spatial Geometry Isolation (pdfplumber, MIT)         |
          |  - Table Bounding Boxes: (x0, top, x1, bottom)        |
          |  - Table Extraction: Clean 2D Matrix of Cells         |
          |  - Word Filtering: Suppress text inside table BBoxes  |
          +-------------------------------------------------------+
                                      |
                                      v
          +-------------------------------------------------------+
          |  Typography & Reading Order Synthesis                 |
          |  - Dynamic body font size detection                   |
          |  - H1 / H2 / H3 classification from font size & weight|
          |  - Nested list hierarchy recognition                  |
          |  - Vertical leading paragraph gap reconciliation      |
          +-------------------------------------------------------+
                                      |
                                      v
          +-------------------------------------------------------+
          |  Conservative GitHub Flavored Markdown (GFM) Output   |
          |  - SHA-256 Checksums (Input PDF & Output Markdown)    |
          |  - Sub-100ms Ingestion Latency Tracking               |
          |  - Diagnostic Logging (Irregular cells, warnings)     |
          +-------------------------------------------------------+
```

---

## 4. Verified Permissive Dependencies

In adherence to licensing constraints, all dependencies have been audited:

| Package | License | Role |
| :--- | :--- | :--- |
| `pdfplumber` | **MIT** | Table line vector detection & word bounding boxes |
| `pdfminer.six` | **MIT** | Low-level PDF stream parsing & font CMap mapping |
| `pypdf` | **BSD-3-Clause** | PDF metadata normalization & deterministic stream output |
| `reportlab` | **BSD-3-Clause** | Deterministic synthetic PDF generation |
| `click` | **BSD-3-Clause** | Unified Command Line Interface (CLI) |
| `pydantic` | **MIT** | Type-safe manifests, models, and serialization |
| `rich` | **MIT** | Formatted console tables and reports |
| `pytest` | **MIT** | Test automation suite |

*See [`docs/LICENSES.md`](docs/LICENSES.md) for full compliance documentation.*

---

## 5. Installation and Quickstart

### 5.1 Installation

```bash
# Clone and enter the repository
git clone https://github.com/zipmd/document-ingestion-benchmark.git
cd document-ingestion-benchmark

# Install in editable mode
pip install -e .
```

### 5.2 One-Command Full Pipeline

Execute synthetic corpus generation, ingestion evaluation, repeatability benchmarks, and report generation in a single command:

```bash
docbench run-all
```

### 5.3 CLI Subcommands

```bash
# 1. Generate deterministic synthetic PDFs, reference markdown, and manifests
docbench generate-samples

# 2. Ingest and convert a single PDF document
docbench convert data/synthetic/contract.pdf -o outputs/contract.md

# 3. Evaluate ingestion corpus against ground-truth manifests
docbench evaluate

# 4. Run determinism and latency jitter repeatability test
docbench repeatability --runs 5

# 5. Generate benchmark report artifacts (Markdown, JSON, CSV)
docbench report --output-dir outputs/
```

---

---

## 6. Interactive Frontend Dashboard & API Service

DocBench features a clean, responsive web application served directly from the FastAPI service at `/`:
- **Web Dashboard URL**: `http://127.0.0.1:8000/`
- **Interactive OpenAPI Docs**: `http://127.0.0.1:8000/docs`

### Starting the Application

```bash
# Option 1: Start via docbench CLI (defaults to 127.0.0.1:8000)
docbench serve --host 127.0.0.1 --port 8000 --reload

# Option 2: Start via Uvicorn directly
uvicorn docbench.api:app --host 127.0.0.1 --port 8000 --reload
```

Once started, opening `http://127.0.0.1:8000/` in any modern web browser presents the full interactive dashboard:
1. **Corpus Benchmark Performance**: Real-time aggregated corpus score (`100.0 / 100`), status indicator (`ALL_PASS`), cached status indicator, and per-document breakdown.
2. **Document Ingestion & Evaluation Workspace**:
   - Drag-and-drop or browse PDF upload (enforcing `.pdf` format and 5 MB limits).
   - Quick one-click sample loaders (`Contract`, `Tabular Report`, `Multi-Page Spec`, `Stress Test`).
   - Ground-truth reference manifest selector.
   - Dual actions: **"Convert to Markdown"** (`/v1/ingest`) and **"Ingest & Evaluate"** (`/v1/evaluate`).
3. **Structural Evaluation Scorecard**:
   - Composite Quality Score hero gauge (`100.0% PASS`).
   - Detailed metric cards for Headings, Tables, Text Completeness, Reading Order, and Lists.
   - Transparent **`N/A`** handling for non-applicable components (e.g. `tabular_report` has no lists, so lists are cleanly marked `N/A` and weights are dynamically normalized).
4. **Side-by-Side Comparison Workspace**:
   - **Side-by-Side Tab**: Left column shows extracted Markdown from the ingestion engine; Right column displays ground-truth reference Markdown.
   - **Raw Markdown Tab**: Preformatted monospace view with line numbers.
   - **Extraction Diagnostics Tab**: Heading hierarchy counts, table dimensions, list items, and parser warnings.
   - One-click **"Copy Markdown"** and **"Download .md"** actions.
   - **Strict XSS Immunity**: Zero executable HTML rendering; document text is safely populated via `textContent`.

### Programmatic REST Ingestion Examples

```bash
# 1. Plain ingestion to Markdown
curl -X POST "http://127.0.0.1:8000/v1/ingest" \
  -H "accept: application/json" \
  -F "file=@data/synthetic/contract.pdf"

# 2. Evaluation against ground truth
curl -X POST "http://127.0.0.1:8000/v1/evaluate" \
  -H "accept: application/json" \
  -F "file=@data/synthetic/contract.pdf" \
  -F "reference_id=contract"
```

For full endpoint documentation, schema details, error codes, and curl examples, see **[API Documentation](docs/API.md)**.

---

## 7. Running the Test Suite

The test suite contains **83 automated tests** covering PDF generation, ingestion pipelines, AST converters, metric evaluation, all 14 negative validation corruption scenarios, report format consistency, the complete FastAPI REST API service layer, and frontend static assets/DOM guarantees:

```bash
pytest -v
```

Expected output:
```
============================= 83 passed in ~6.9s ==============================
```

---

## 8. Project Structure

```
document-ingestion-benchmark/
├── src/
│   └── docbench/
│       ├── __init__.py          # Version and package definitions
│       ├── cli.py               # Unified Click CLI (7 subcommands including serve)
│       ├── config.py            # Global paths, weights, and sample definitions
│       ├── api/                 # FastAPI REST Service Layer (Phase 3)
│       │   ├── app.py           # Application factory, static mounting, CORS, error handlers
│       │   ├── config.py        # Environment settings (upload size, temp dir, log level)
│       │   ├── schemas.py       # Pydantic request and response schemas
│       │   ├── security.py      # Bounded chunk streaming, PDF header check, filename sanitization
│       │   ├── service.py       # Thread-pool offloading for CPU parsing & trusted reference mapping
│       │   └── routes/          # REST route controllers (/health, /version, /ingest, /evaluate, /summary)
│       ├── frontend/            # Interactive Web Dashboard (Phase 4)
│       │   ├── index.html       # Clean, accessible HTML5 dashboard structure
│       │   ├── css/styles.css   # Modern, restrained responsive dark-slate design
│       │   └── js/app.js        # Vanilla JS application logic & safe DOM manipulation
│       ├── generator/           # Deterministic synthetic PDF generator
│       │   ├── contract.py      # Legal Master Services Agreement
│       │   ├── tabular.py       # Tabular business and financial report
│       │   ├── multipage.py     # 3-page distributed architecture spec
│       │   ├── edgecases.py     # Accents, currencies, symbols, nested lists
│       │   └── runner.py        # Coordinated generator with PyPDF normalizer
│       ├── ingestion/           # Document Ingestion Engine
│       │   ├── models.py        # Hardened Pydantic data schemas
│       │   ├── parser.py        # Spatial table isolation & line bucketing
│       │   ├── converter.py     # Conservative GFM synthesis & font clustering
│       │   └── pipeline.py      # End-to-end ingestion with SHA-256 and profiling
│       ├── metrics/             # Hardened Evaluation Subsystem
│       │   ├── headings.py      # Heading Precision, Recall, F1, and Order Acc
│       │   ├── tables.py        # Header-Jaccard alignment & cell-level accuracy
│       │   ├── text.py          # Verbatim recall, precision, Token F1, length ratio
│       │   ├── reading_order.py # Longest Increasing Subsequence & Kendall's Tau
│       │   ├── lists.py         # Bullet/numbered preservation, depth strictness, order
│       │   └── evaluator.py     # Dynamic weight re-normalization & critical failure alerts
│       ├── repeatability/       # Determinism & Jitter Profiler
│       │   └── runner.py        # Bitwise hash stability across N runs
│       └── reporting/           # Report Generators
│           ├── markdown_report.py
│           ├── json_report.py
│           ├── csv_report.py
│           └── console_report.py
├── data/
│   ├── synthetic/               # Generated deterministic PDFs (.pdf)
│   ├── references/              # Independent reference Markdown (.ref.md)
│   └── manifests/               # Ground-truth JSON manifests (.manifest.json)
├── outputs/                     # Benchmark artifacts (.md, .json, .csv)
├── docs/
│   ├── API.md                   # REST API documentation, schemas, and curl examples
│   ├── METHODOLOGY.md           # Hardened metric formulas, weighting, and rationale
│   ├── ARCHITECTURE.md          # Ingestion architecture and dataflow
│   ├── LIMITATIONS.md           # Scope boundaries and known edge-case limits
│   ├── LICENSES.md              # Permissive dependency license audit
│   └── VALIDATION.md            # Phase 2 audit findings, 14 corruption scenarios, and fixes
├── tests/                       # 78 unit, integration, negative validation, and API tests
│   ├── test_api.py              # FastAPI endpoint, security boundary, and concurrency tests
│   └── test_frontend.py         # Dashboard HTML, static assets, and XSS safety tests
├── pyproject.toml               # Package configuration
└── README.md                    # Project portfolio presentation
```

---

## 9. Documentation Index

- **[REST API Specification](docs/API.md)**: Endpoints, request/response models, curl examples, upload security, and error responses.
- **[Validation & Hardening Report](docs/VALIDATION.md)**: Phase 2 adversarial corruption test results, defect investigations, and fixes.
- **[Evaluation Methodology](docs/METHODOLOGY.md)**: Full mathematical definitions for all metrics and weighting rationale.
- **[System Architecture](docs/ARCHITECTURE.md)**: Pipeline design, spatial bounding box isolation, and font hierarchy heuristics.
- **[Scope & Limitations](docs/LIMITATIONS.md)**: OCR-free boundary, complex multi-column layouts, and roadmap.
- **[License Audit](docs/LICENSES.md)**: Verified SPDX compliance and rationale for excluding AGPL libraries.

---

## 10. Phase Status & Roadmap

- **Phase 1: Core Benchmark** — Complete.
- **Phase 2: Validation & Quality Hardening** — Complete (55 tests passing, 14 corruption scenarios verified, metrics hardened).
- **Phase 3: FastAPI REST Service Layer** — Complete (72 tests passing, async streaming, security boundaries, live verified).
- **Phase 4: Interactive Frontend Dashboard** — Complete (78 tests passing, responsive UI, side-by-side comparison, sample loaders, XSS safe).
- **Phase 5 (Next)**: Packaging, containerization, and public deployment for Zipmd portfolio review.
