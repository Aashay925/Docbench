"""
Comprehensive unit and integration tests for the DocBench FastAPI REST Service layer.
Tests health, version, ingestion, evaluation, benchmark summary,
security boundaries, upload size limits, MIME validation, corrupt files,
temporary file lifecycle cleanup, and request tracing.
"""

import io
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient

from docbench.config import SYNTHETIC_DIR, OUTPUTS_DIR
from docbench.api.app import create_app
from docbench.api.config import api_settings


@pytest.fixture(scope="module")
def client():
    """Create a test client instance."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client: TestClient):
    """Test GET /health returns operational status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert response.headers.get("x-request-id") is not None


def test_version_endpoint(client: TestClient):
    """Test GET /version returns semantic application version."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "document-ingestion-benchmark"
    assert data["app_version"] == "0.1.0"
    assert data["api_version"] == "v1"


def test_ingest_valid_pdf(client: TestClient):
    """Test POST /v1/ingest successfully processes a real synthetic contract PDF."""
    contract_path = SYNTHETIC_DIR / "contract.pdf"
    assert contract_path.exists(), "Synthetic contract.pdf must exist"

    with open(contract_path, "rb") as f:
        response = client.post(
            "/v1/ingest",
            files={"file": ("contract.pdf", f, "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "contract.pdf"
    assert data["page_count"] == 1
    assert data["duration_ms"] > 0
    assert len(data["pdf_sha256"]) == 64
    assert len(data["markdown_sha256"]) == 64
    assert data["has_usable_text"] is True
    assert "Master Services Agreement" in data["markdown_content"]
    assert data["extracted_headings_count"] > 0


def test_evaluate_valid_pdf_explicit_ref(client: TestClient):
    """Test POST /v1/evaluate with explicit reference_id."""
    tabular_path = SYNTHETIC_DIR / "tabular_report.pdf"
    assert tabular_path.exists(), "Synthetic tabular_report.pdf must exist"

    with open(tabular_path, "rb") as f:
        response = client.post(
            "/v1/evaluate",
            files={"file": ("custom_named_report.pdf", f, "application/pdf")},
            data={"reference_id": "tabular_report"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "custom_named_report.pdf"
    assert data["reference_id"] == "tabular_report"
    assert data["composite_score"] > 0.90
    assert data["status"] == "PASS"
    assert data["critical_failure"] is False
    assert "table_cell_accuracy" in data["applicable_weights"]
    assert data["table_score"]["is_applicable"] is True
    assert data["table_score"]["cell_accuracy"] > 0.90


def test_evaluate_valid_pdf_inferred_ref(client: TestClient):
    """Test POST /v1/evaluate automatically infers reference ID from filename."""
    contract_path = SYNTHETIC_DIR / "contract.pdf"

    with open(contract_path, "rb") as f:
        response = client.post(
            "/v1/evaluate",
            files={"file": ("contract.pdf", f, "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["reference_id"] == "contract"
    assert data["composite_score"] > 0.90
    assert data["critical_failure"] is False


def test_benchmark_summary(client: TestClient):
    """Test GET /v1/benchmark/summary returns aggregated corpus scores."""
    response = client.get("/v1/benchmark/summary")
    assert response.status_code == 200
    data = response.json()
    assert "overall_benchmark_score" in data
    assert "status" in data
    assert "aggregates" in data
    assert "document_summaries" in data
    assert isinstance(data["document_summaries"], list)


def test_security_reject_invalid_extension(client: TestClient):
    """Test rejecting files without a .pdf extension."""
    fake_txt = io.BytesIO(b"Hello world text document")
    response = client.post(
        "/v1/ingest",
        files={"file": ("document.txt", fake_txt, "application/pdf")},
    )
    assert response.status_code == 415
    assert "Unsupported file type" in response.json()["detail"]


def test_security_reject_invalid_content_type(client: TestClient):
    """Test rejecting uploads with an invalid MIME type."""
    fake_pdf = io.BytesIO(b"%PDF-1.4 dummy")
    response = client.post(
        "/v1/ingest",
        files={"file": ("document.pdf", fake_pdf, "text/plain")},
    )
    assert response.status_code == 415
    assert "Unsupported Content-Type" in response.json()["detail"]


def test_security_reject_empty_file(client: TestClient):
    """Test rejecting an empty 0-byte file."""
    empty_stream = io.BytesIO(b"")
    response = client.post(
        "/v1/ingest",
        files={"file": ("document.pdf", empty_stream, "application/pdf")},
    )
    # Empty file has no %PDF- header -> triggers 400
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Empty file" in detail or "Invalid PDF signature" in detail


def test_security_reject_invalid_magic_header(client: TestClient):
    """Test rejecting non-PDF content even if named .pdf."""
    fake_stream = io.BytesIO(b"NOT A REAL PDF FILE AT ALL")
    response = client.post(
        "/v1/ingest",
        files={"file": ("document.pdf", fake_stream, "application/pdf")},
    )
    assert response.status_code == 400
    assert "Invalid PDF signature" in response.json()["detail"]


def test_security_oversized_upload(client: TestClient, monkeypatch):
    """Test rejecting files that exceed the configured size limit."""
    # Set limit to 256 bytes for testing
    monkeypatch.setattr(api_settings, "max_upload_size_bytes", 256)

    oversized_data = b"%PDF-1.4 " + (b"A" * 1024)
    stream = io.BytesIO(oversized_data)
    response = client.post(
        "/v1/ingest",
        files={"file": ("large.pdf", stream, "application/pdf")},
    )
    assert response.status_code == 413
    assert "Upload exceeded maximum permitted file size" in response.json()["detail"]


def test_security_filename_sanitization(client: TestClient):
    """Test that path traversal attempts in filenames are safely sanitized."""
    contract_path = SYNTHETIC_DIR / "contract.pdf"
    with open(contract_path, "rb") as f:
        response = client.post(
            "/v1/ingest",
            files={"file": ("../../../../dangerous_name.pdf", f, "application/pdf")},
        )
    assert response.status_code == 200
    sanitized = response.json()["filename"]
    assert "/" not in sanitized
    assert "\\" not in sanitized
    assert ".." not in sanitized
    assert sanitized.endswith(".pdf")


def test_evaluate_missing_or_unknown_reference(client: TestClient):
    """Test evaluate endpoint returns clear 400 error when reference ID is unknown."""
    contract_path = SYNTHETIC_DIR / "contract.pdf"
    with open(contract_path, "rb") as f:
        response = client.post(
            "/v1/evaluate",
            files={"file": ("unknown_file.pdf", f, "application/pdf")},
            data={"reference_id": "non_existent_reference_id"},
        )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Unknown or missing reference document ID" in detail
    assert "contract" in detail


def test_evaluate_corrupt_pdf_fails_safely(client: TestClient):
    """Test that a corrupt PDF produces a 422 error without leaking internal filesystem details."""
    corrupt_content = b"%PDF-1.4\nCorrupt header and damaged xref table \x00\xff garbage"
    stream = io.BytesIO(corrupt_content)
    response = client.post(
        "/v1/ingest",
        files={"file": ("corrupt.pdf", stream, "application/pdf")},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "Failed to parse and extract PDF" in detail
    # Verify no raw temporary disk paths leaked in message
    assert "outputs\\temp" not in detail
    assert "outputs/temp" not in detail


def test_temporary_file_cleanup_on_success_and_failure(client: TestClient):
    """Verify that temp directory has no leftover files after requests."""
    temp_dir = api_settings.temp_dir
    api_settings.ensure_temp_dir()
    initial_files = set(temp_dir.glob("upload_*"))

    # 1. Success request
    contract_path = SYNTHETIC_DIR / "contract.pdf"
    with open(contract_path, "rb") as f:
        client.post("/v1/ingest", files={"file": ("test_clean.pdf", f, "application/pdf")})
    post_success_files = set(temp_dir.glob("upload_*"))
    assert post_success_files == initial_files, "Temporary file was not cleaned up after success"

    # 2. Failure request (corrupt PDF)
    corrupt_stream = io.BytesIO(b"%PDF-1.4 damaged data \x00\x00")
    client.post("/v1/ingest", files={"file": ("corrupt_clean.pdf", corrupt_stream, "application/pdf")})
    post_failure_files = set(temp_dir.glob("upload_*"))
    assert post_failure_files == initial_files, "Temporary file was not cleaned up after failure"


def test_cors_and_request_id_headers(client: TestClient):
    """Test CORS header handling and request-id propagation."""
    custom_req_id = "trace-uuid-987654"
    response = client.get(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "X-Request-ID": custom_req_id,
        },
    )
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == custom_req_id
    assert response.headers.get("access-control-allow-origin") == "*"


def test_concurrent_uploads_isolation(client: TestClient):
    """Verify that concurrent requests run cleanly without colliding or interfering."""
    contract_path = SYNTHETIC_DIR / "contract.pdf"
    content = contract_path.read_bytes()

    def make_request(idx: int):
        stream = io.BytesIO(content)
        resp = client.post(
            "/v1/ingest",
            files={"file": (f"concurrent_{idx}.pdf", stream, "application/pdf")},
        )
        return resp.status_code, resp.json()["filename"]

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(make_request, i) for i in range(6)]
        results = [f.result() for f in futures]

    for status_code, filename in results:
        assert status_code == 200
        assert filename.startswith("concurrent_")


def test_ingest_arbitrary_pdf_filename(client: TestClient):
    """Test POST /v1/ingest succeeds for an arbitrary PDF like 'Aashay_Resume (1).pdf'."""
    contract_path = SYNTHETIC_DIR / "contract.pdf"
    content = contract_path.read_bytes()
    stream = io.BytesIO(content)

    response = client.post(
        "/v1/ingest",
        files={"file": ("Aashay_Resume (1).pdf", stream, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["has_usable_text"] is True
    assert "Aashay_Resume" in data["filename"]
    assert data["page_count"] >= 1
    assert data["markdown_content"]


def test_evaluate_arbitrary_pdf_without_reference_fails(client: TestClient):
    """Test POST /v1/evaluate rejects an arbitrary PDF when no matching reference exists."""
    contract_path = SYNTHETIC_DIR / "contract.pdf"
    content = contract_path.read_bytes()
    stream = io.BytesIO(content)

    response = client.post(
        "/v1/evaluate",
        files={"file": ("Aashay_Resume (1).pdf", stream, "application/pdf")},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Unknown or missing reference document ID" in detail
    assert "contract" in detail


def test_evaluate_arbitrary_pdf_with_explicit_reference(client: TestClient):
    """Test POST /v1/evaluate succeeds when an arbitrary PDF explicitly specifies a trusted reference."""
    contract_path = SYNTHETIC_DIR / "contract.pdf"
    content = contract_path.read_bytes()
    stream = io.BytesIO(content)

    response = client.post(
        "/v1/evaluate",
        files={"file": ("Aashay_Resume (1).pdf", stream, "application/pdf")},
        data={"reference_id": "contract"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reference_id"] == "contract"
    assert "composite_score" in data


def test_evaluate_all_supported_synthetic_references(client: TestClient):
    """Verify benchmark evaluation is enabled and working for all 4 supported synthetic references."""
    supported = ["contract", "tabular_report", "multipage_report", "edge_cases"]
    for ref_id in supported:
        pdf_path = SYNTHETIC_DIR / f"{ref_id}.pdf"
        assert pdf_path.exists(), f"Synthetic {ref_id}.pdf must exist"
        with open(pdf_path, "rb") as f:
            resp = client.post(
                "/v1/evaluate",
                files={"file": (f"{ref_id}.pdf", f, "application/pdf")},
                data={"reference_id": ref_id},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["reference_id"] == ref_id
        assert data["composite_score"] > 0.80
        assert data["critical_failure"] is False

