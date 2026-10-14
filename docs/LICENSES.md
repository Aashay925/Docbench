# Dependency License Audit and Compliance Documentation

## 1. Compliance Statement

`document-ingestion-benchmark` (`docbench`) is engineered specifically for **unrestricted public GitHub distribution and commercial enterprise collaboration**.

All direct and transitive dependencies have been rigorously audited for software license compatibility. **No copyleft, AGPL, or GPL dependencies are included or imported.**

---

## 2. Direct Dependency License Registry

The following table details every direct runtime and development dependency used in `docbench`, along with its verified SPDX license identifier and copyright holder:

| Package | Version | Verified License | SPDX Identifier | Purpose in Project |
| :--- | :--- | :--- | :--- | :--- |
| `pdfplumber` | 0.11.10 | MIT License | `MIT` | Explicit table detection and spatial word geometry extraction |
| `pypdf` | 6.20.1 | BSD 3-Clause License | `BSD-3-Clause` | PDF metadata normalization and deterministic byte stream writing |
| `reportlab` | 5.0.1 | BSD License | `BSD-3-Clause` | Programmatic synthetic PDF generation engine |
| `click` | 8.3.2 | BSD 3-Clause License | `BSD-3-Clause` | Command-line interface (CLI) dispatch and argument parsing |
| `pydantic` | 2.13.3 | MIT License | `MIT` | Data models, manifest schemas, and serialization |
| `rich` | 15.0.0 | MIT License | `MIT` | Terminal rendering, table styling, and console reports |
| `pytest` | 9.1.1 | MIT License | `MIT` | Test suite runner and assertion engine |
| `fastapi` | 0.115.11 | MIT License | `MIT` | Asynchronous REST API web framework |
| `uvicorn` | 0.34.0 | BSD 3-Clause License | `BSD-3-Clause` | Lightning-fast ASGI web server implementation |
| `python-multipart` | 0.0.20 | Apache 2.0 License | `Apache-2.0` | Streaming multipart/form-data parser for file uploads |
| `httpx` | 0.28.1 | BSD 3-Clause License | `BSD-3-Clause` | Next-generation asynchronous HTTP client for testing |

---

## 3. Transitive Dependency Audit

| Transitive Dependency | Parent Package | Verified License | SPDX Identifier | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `pdfminer.six` | `pdfplumber` | MIT License | `MIT` | Low-level PDF stream parsing and CMap decoding |
| `pypdfium2` | `pdfplumber` | BSD-3-Clause / Apache-2.0 | `BSD-3-Clause` | Permissively licensed PDFium Python binding |
| `pillow` | `reportlab` | Historical Permission Notice | `HPND` | Permissive image manipulation library |
| `cryptography` | `pdfminer.six` | Apache-2.0 / BSD-3-Clause | `Apache-2.0` | Standard cryptography primitives for PDF streams |

---

## 4. Exclusion of AGPL / GPL Dependencies (e.g. PyMuPDF / PyMuPDF4LLM)

### Why PyMuPDF4LLM Was Explicitly Avoided
`PyMuPDF` (and the `PyMuPDF4LLM` wrapper built on top of it) is distributed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. Under AGPL-3.0:
1. Any proprietary or commercial project that links against or imports the library must make its entire source code available under the AGPL-3.0 when operated over a network (e.g. SaaS, API backends, or collaborative commercial software).
2. Enterprise commercial distribution typically requires expensive commercial licensing agreements.

### Architectural Alternative Implemented in DocBench
By architecting the pipeline around **`pdfplumber` (MIT)**, **`pdfminer.six` (MIT)**, and **`pypdf` (BSD-3-Clause)**:
- Full commercial and open-source freedom is preserved.
- Code can be published on public GitHub, packaged as a PyPI library, or integrated into proprietary cloud services without legal friction.
- Deterministic control over bounding boxes, font clustering, and GFM markdown synthesis is maintained natively within our codebase.
