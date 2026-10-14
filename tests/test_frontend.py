"""
Automated tests for the DocBench Interactive Frontend Dashboard.
Verifies HTML structure, static file serving, DOM element IDs,
XSS escaping guarantees, and sample PDF delivery.
"""

from fastapi.testclient import TestClient
import pytest
from docbench.api.app import create_app


@pytest.fixture(scope="module")
def client():
    """Create test client with static files mounted."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_dashboard_root_serves_html(client: TestClient):
    """Test GET / serves the interactive HTML dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    content = response.text
    assert "<!DOCTYPE html>" in content
    assert "DocBench" in content
    assert 'id="dropzone"' in content
    assert 'id="file-input"' in content
    assert 'id="btn-ingest"' in content
    assert 'id="btn-evaluate"' in content
    assert 'id="btn-refresh-summary"' in content
    assert 'id="reference-select"' in content
    assert 'id="code-extracted"' in content
    assert 'id="code-reference"' in content
    assert 'id="btn-copy-md"' in content
    assert 'id="btn-download-md"' in content


def test_static_css_and_js_served(client: TestClient):
    """Test that static CSS and JavaScript files are served correctly."""
    css_resp = client.get("/static/css/styles.css")
    assert css_resp.status_code == 200
    assert "text/css" in css_resp.headers.get("content-type", "")
    assert "--bg-page" in css_resp.text

    js_resp = client.get("/static/js/app.js")
    assert js_resp.status_code == 200
    assert "application/javascript" in js_resp.headers.get("content-type", "") or "text/javascript" in js_resp.headers.get("content-type", "")
    assert "performIngestion" in js_resp.text
    assert "performEvaluation" in js_resp.text


def test_sample_pdf_endpoint(client: TestClient):
    """Test downloading synthetic sample PDFs for quick frontend testing."""
    for sample_id in ["contract", "tabular_report", "multipage_report", "edge_cases"]:
        resp = client.get(f"/v1/benchmark/samples/{sample_id}")
        assert resp.status_code == 200
        assert resp.headers.get("content-type") == "application/pdf"
        assert resp.content.startswith(b"%PDF-")


def test_sample_pdf_not_found(client: TestClient):
    """Test that requesting an unknown sample document returns 404."""
    resp = client.get("/v1/benchmark/samples/unknown_doc_xyz")
    assert resp.status_code == 404
    assert "Sample document 'unknown_doc_xyz' not found" in resp.json()["detail"]


def test_references_endpoints(client: TestClient):
    """Test GET /v1/references and GET /v1/references/{id}."""
    list_resp = client.get("/v1/references")
    assert list_resp.status_code == 200
    refs = list_resp.json()
    assert isinstance(refs, list)
    ref_ids = [r["id"] for r in refs]
    assert "contract" in ref_ids
    assert "tabular_report" in ref_ids

    detail_resp = client.get("/v1/references/contract")
    assert detail_resp.status_code == 200
    data = detail_resp.json()
    assert data["reference_id"] == "contract"
    assert "Master Services Agreement" in data["reference_markdown"]
    assert "manifest" in data


def test_xss_prevention_guarantee():
    """
    Verify that JavaScript application logic strictly avoids innerHTML injection
    when displaying untrusted Markdown or document text.
    """
    from pathlib import Path
    app_js_path = Path("src/docbench/frontend/js/app.js")
    assert app_js_path.exists()
    content = app_js_path.read_text(encoding="utf-8")

    # Verify that code elements strictly use textContent for Markdown rendering
    assert "el.codeExtracted.textContent = state.currentMarkdown;" in content
    assert "el.codeRaw.textContent = state.currentMarkdown;" in content
    assert "el.codeReference.textContent = state.currentReferenceMarkdown;" in content

    # Verify no dangerous innerHTML assignment with arbitrary user text
    assert "codeExtracted.innerHTML" not in content
    assert "codeRaw.innerHTML" not in content
    assert "codeReference.innerHTML" not in content


def test_missing_reference_flow_guard():
    """
    Verify frontend logic protects against calling evaluation endpoint
    with missing or null reference IDs, and contains the required completion message.
    """
    from pathlib import Path
    app_js_path = Path("src/docbench/frontend/js/app.js")
    assert app_js_path.exists()
    content = app_js_path.read_text(encoding="utf-8")

    # Verify trusted reference array
    assert "const TRUSTED_REFERENCES = ['contract', 'tabular_report', 'multipage_report', 'edge_cases'];" in content

    # Verify reference resolution function
    assert "getResolvedReferenceId()" in content

    # Verify exact required message when no trusted reference exists
    expected_msg = "Conversion completed. Accuracy evaluation is unavailable because no trusted reference exists for this document."
    assert expected_msg in content

    # Verify that missing reference routes to callIngestApi and renderNoReferenceState
    assert "renderNoReferenceState" in content
    assert "callIngestApi" in content
