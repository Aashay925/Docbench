# DocBench REST API Specification (Phase 3)

The `document-ingestion-benchmark` (`docbench`) REST API provides programmatic access to conservative PDF-to-Markdown document conversion, structural evaluation against verified ground-truth references, and corpus benchmark summaries.

Built with **FastAPI** and **Uvicorn**, the service features asynchronous chunked upload streaming, strict security boundary validation, thread-pool offloading for CPU-bound parsing, and guaranteed temporary file isolation and cleanup.

---

## 1. Quickstart & Local Execution

### Starting the Server

You can launch the API service using either Uvicorn directly or the built-in CLI command:

```bash
# Option 1: Via Uvicorn directly
uvicorn docbench.api:app --host 127.0.0.1 --port 8000 --reload

# Option 2: Via DocBench CLI
python -m docbench.cli serve --host 127.0.0.1 --port 8000 --reload
```

Interactive OpenAPI documentation is automatically available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## 2. Configuration & Environment Variables

The service can be configured using environment variables:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DOCBENCH_MAX_UPLOAD_SIZE_MB` | `5` | Maximum upload size in megabytes (enforced in 64 KB chunks). |
| `DOCBENCH_MAX_UPLOAD_SIZE_BYTES` | `5242880` | Maximum upload size in exact bytes (overrides MB setting if set). |
| `DOCBENCH_TEMP_DIR` | `outputs/temp` | Directory where uploads are temporarily staged during streaming. |
| `DOCBENCH_CORS_ORIGINS` | `*` | Comma-delimited list of allowed CORS origins (e.g. `http://localhost:3000`). |
| `DOCBENCH_LOG_LEVEL` | `INFO` | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## 3. Security Safeguards

1. **Strict File Type & Extension Validation**: Only files ending in `.pdf` with MIME type `application/pdf`, `application/x-pdf`, or `application/octet-stream` are permitted. Other extensions or media types return `415 Unsupported Media Type`.
2. **PDF Header Magic Bytes Verification**: Streams verify the presence of `%PDF-` within the initial 1024 bytes. Uploads with missing signatures return `400 Bad Request`. *(Note: Header verification validates file structure format, but does not guarantee protection against all binary exploits).*
3. **Bounded Chunked Uploads**: Incoming uploads are read in 64 KB chunks. If cumulative bytes exceed the maximum upload limit, transmission is aborted immediately with `413 Request Entity Too Large` before memory exhaustion occurs.
4. **Filesystem Path Traversal Defense**: All user-provided filenames are sanitized: null bytes (`\x00`), control characters, directory separators (`/`, `\`), and relative path patterns (`..`) are stripped.
5. **Temporary File Isolation & Guaranteed Cleanup**: Uploads are written to isolated, UUID-tagged temporary files (`upload_<uuid>.pdf`) and are unconditionally removed in an asynchronous `finally` block upon completion or exception.
6. **Information Disclosure Prevention**: Error responses never return raw internal server file paths or Python tracebacks. Unhandled exceptions return generic `500 Internal Server Error` payloads with a correlated `request_id`.
7. **Thread Pool Execution**: CPU-bound PDF extraction and evaluation routines run in background threads (`asyncio.to_thread`) to prevent blocking the asynchronous event loop.

---

## 4. REST Endpoints

### 4.1. System & Dashboard Endpoints

#### `GET /`
Serves the interactive DocBench HTML5 dashboard and static web assets.

**Example Request:**
```bash
curl -X GET "http://127.0.0.1:8000/"
```

**Response (`200 OK`):**
Returns HTML document containing the complete interactive dashboard.

---

#### `GET /health`
Returns operational health status.

**Example Request:**
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

**Response (`200 OK`):**
```json
{
  "status": "ok",
  "timestamp": "2026-10-15T02:45:49.601860+00:00"
}
```

---

#### `GET /version`
Returns application and API semantic version information.

**Example Request:**
```bash
curl -X GET "http://127.0.0.1:8000/version"
```

**Response (`200 OK`):**
```json
{
  "app_name": "document-ingestion-benchmark",
  "app_version": "0.1.0",
  "api_version": "v1"
}
```

---

### 4.2. Ingestion Endpoint

#### `POST /v1/ingest`
Accepts a binary PDF file upload via `multipart/form-data`, extracts text, tables, and headings, and synthesizes conservative GitHub-Flavored Markdown.

**Request Parameters:**
- `file` (form-data, required): Binary PDF document.

**Example Request (using synthetic contract):**
```bash
curl -X POST "http://127.0.0.1:8000/v1/ingest" \
  -H "accept: application/json" \
  -F "file=@data/synthetic/contract.pdf"
```

**Response (`200 OK`):**
```json
{
  "filename": "contract.pdf",
  "page_count": 1,
  "duration_ms": 64.86,
  "pdf_sha256": "47fa0d2e5a6a9b5f...",
  "markdown_sha256": "8064cfbcf76a8d79...",
  "markdown_content": "# Master Services Agreement\n\nThis Master Services Agreement...",
  "has_usable_text": true,
  "extracted_headings_count": 6,
  "extracted_tables_count": 1,
  "extracted_lists_count": 4,
  "diagnostics": [
    {
      "code": "INFO_PAGE_CONVERTED",
      "message": "Page 1 converted: 6 headings, 1 tables, 4 list items.",
      "page_number": 1,
      "severity": "INFO"
    }
  ]
}
```

---

### 4.3. Evaluation Endpoint

#### `POST /v1/evaluate`
Accepts a PDF upload and evaluates extraction quality against an existing, trusted ground-truth reference manifest.

> **Ground Truth Integrity Note:** Arbitrary uploaded reference manifests are **not** accepted as ground truth. The evaluation endpoint strictly verifies documents against canonical reference manifests (`contract`, `tabular_report`, `multipage_report`, `edge_cases`).

**Request Parameters:**
- `file` (form-data, required): Binary PDF document.
- `reference_id` (form-data, optional): Identifier of the trusted reference document (`contract`, `tabular_report`, `multipage_report`, `edge_cases`). If omitted, the reference ID is inferred from the uploaded file's stem.

**Example Request:**
```bash
curl -X POST "http://127.0.0.1:8000/v1/evaluate" \
  -H "accept: application/json" \
  -F "file=@data/synthetic/contract.pdf" \
  -F "reference_id=contract"
```

**Response (`200 OK`):**
```json
{
  "filename": "contract.pdf",
  "reference_id": "contract",
  "composite_score": 1.0,
  "status": "PASS",
  "critical_failure": false,
  "min_component_score": 1.0,
  "applicable_weights": {
    "heading_f1": 0.25,
    "table_cell_accuracy": 0.25,
    "text_completeness": 0.3,
    "reading_order": 0.1,
    "list_preservation": 0.1
  },
  "heading_score": {
    "precision": 1.0,
    "recall": 1.0,
    "f1": 1.0,
    "level_accuracy": 1.0,
    "order_accuracy": 1.0,
    "is_applicable": true
  },
  "table_score": {
    "table_detection_precision": 1.0,
    "table_detection_recall": 1.0,
    "cell_accuracy": 1.0,
    "matched_cells": 8,
    "total_expected_cells": 8,
    "total_extracted_cells": 8,
    "is_applicable": true
  },
  "text_score": {
    "char_recall": 1.0,
    "token_recall": 1.0,
    "token_precision": 1.0,
    "token_f1": 1.0,
    "sequence_similarity": 1.0,
    "jaccard_similarity": 1.0,
    "composite_text_score": 1.0
  },
  "reading_order_score": {
    "lcs_ratio": 1.0,
    "kendall_tau": 1.0,
    "anchor_count_expected": 15,
    "anchor_count_found": 15,
    "composite_order_score": 1.0
  },
  "list_score": {
    "precision": 1.0,
    "recall": 1.0,
    "f1": 1.0,
    "depth_accuracy": 1.0,
    "order_accuracy": 1.0,
    "is_applicable": true
  },
  "duration_ms": 62.16,
  "diagnostics": []
}
```

---

### 4.4. Benchmark Summary Endpoint

#### `GET /v1/benchmark/summary`
Returns the latest available benchmark evaluation summary across the corpus. Reads cached results (`outputs/benchmark_report.json`) when available to avoid full benchmark re-execution on every request.

**Example Request:**
```bash
curl -X GET "http://127.0.0.1:8000/v1/benchmark/summary"
```

**Response (`200 OK`):**
```json
{
  "is_cached": true,
  "timestamp": "2026-10-15T02:00:00Z",
  "overall_benchmark_score": 100.0,
  "status": "ALL_PASS",
  "critical_failures_count": 0,
  "aggregates": {
    "average_heading_f1": 1.0,
    "average_table_cell_accuracy": 1.0,
    "average_text_completeness": 1.0,
    "average_reading_order": 1.0,
    "average_list_preservation": 1.0,
    "critical_failures_count": 0
  },
  "repeatability_summary": {
    "runs_evaluated": 5,
    "max_score_deviation": 0.0,
    "byte_exact_match_ratio": 1.0
  },
  "document_summaries": [
    {
      "doc_id": "contract",
      "composite_score": 1.0,
      "critical_failure": false
    }
  ]
}
```

---

### 4.5. Reference & Synthetic Sample Endpoints

#### `GET /v1/references`
Returns a list of all trusted reference documents registered in the system with their human-readable titles.

**Response (`200 OK`):**
```json
[
  { "id": "contract", "title": "Master Services Agreement (Contract)" },
  { "id": "tabular_report", "title": "Q4 Financial & Operating Metrics (Tabular Report)" },
  { "id": "multipage_report", "title": "Distributed Ingestion Engine Architecture (Multi-Page)" },
  { "id": "edge_cases", "title": "Typography & Stress Test (Accents, Symbols, Nested Lists)" }
]
```

#### `GET /v1/references/{reference_id}`
Returns reference markdown and manifest structure for a canonical document.

#### `GET /v1/benchmark/samples/{doc_id}`
Streams a synthetic binary PDF (`application/pdf`) for interactive testing.

---

## 5. Error Responses

The API uses standard HTTP status codes and structured JSON error objects:

| Status Code | Description | Typical Cause |
| :--- | :--- | :--- |
| `400 Bad Request` | Invalid input or format | Uploaded file is empty, lacks `%PDF-` signature, or specifies an unknown `reference_id`. |
| `413 Request Entity Too Large` | Size boundary exceeded | File exceeds upload size limit (default 5 MB). |
| `415 Unsupported Media Type` | Invalid extension or MIME | Upload is not a `.pdf` file or has invalid `Content-Type`. |
| `422 Unprocessable Entity` | Parser failure | PDF has corrupt internal binary structures or xref tables. |
| `500 Internal Server Error` | Server execution error | Ground truth reference manifest unreadable or server fault. |

**Example Error Payload:**
```json
{
  "error": "HTTP_415",
  "detail": "Unsupported file type. Only PDF files (.pdf) are permitted. Received: 'document.txt'",
  "request_id": "c7484e90d330"
}
```

---

## 6. Known Limitations

1. **No OCR Support**: The ingestion engine extracts digital text and vector elements. Scanned image-only PDFs will produce empty Markdown content (`has_usable_text: false`).
2. **Encrypted/Password-Protected PDFs**: Password-protected PDFs are not decrypted and will fail with `422 Unprocessable Entity`.
3. **Reference Association**: The `/v1/evaluate` endpoint only benchmarks against the canonical 4 synthetic documents in `data/manifests/`. Arbitrary user-uploaded ground-truth manifests are intentionally disallowed to prevent benchmark manipulation.
