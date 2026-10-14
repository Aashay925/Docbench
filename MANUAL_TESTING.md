# DocBench Manual Verification & Testing Guide

This guide provides step-by-step instructions to manually test and verify every component of the **DocBench** project so you can be completely assured that the ingestion engine, evaluation metrics, FastAPI backend, and interactive frontend dashboard work as intended.

---

## 1. Quick Access: Live Running Project

The server is **currently running locally**:

| Interface | URL | Description |
| :--- | :--- | :--- |
| **Interactive Dashboard** | **`http://127.0.0.1:8080/`** | Visual web UI for ingestion, evaluation, and side-by-side inspection |
| **OpenAPI Documentation** | **`http://127.0.0.1:8080/docs`** | Interactive Swagger UI for exploring and executing REST endpoints |
| **ReDoc Specification** | **`http://127.0.0.1:8080/redoc`** | Alternative OpenAPI schema viewer |
| **Health Check Endpoint** | **`http://127.0.0.1:8080/health`** | Live JSON operational status check |

> **Note on Port:** The server is bound to port **8080** (`http://127.0.0.1:8080/`) to prevent conflicts with other services on your machine.
> If you ever restart it manually, run:
> ```bash
> docbench serve --host 127.0.0.1 --port 8080
> ```

---

## 2. Interactive Web Dashboard Testing (Step-by-Step)

Open your web browser and navigate to **`http://127.0.0.1:8080/`**. Follow these steps:

### Test Step 1: Verify API Connection & Corpus Health
1. Look at the top right header:
   - You should see a green glowing dot with **`Online (Xms)`** and a version badge **`v1 (v0.1.0)`**.
2. Look at the **Corpus Benchmark Performance** card:
   - Composite score displays **`100.0 / 100`** with a green **`ALL PASS`** badge.
   - A purple badge indicates **`Cached`** (results loaded instantly from `outputs/benchmark_report.json` without re-running an expensive full benchmark).
   - In the document table, confirm that all 4 canonical topologies are listed: `contract`, `tabular_report`, `multipage_report`, and `edge_cases`.
3. Click the **Refresh** button next to "Cached". The button will briefly disable and reload the latest statistics smoothly.

---

### Test Step 2: Test One-Click Synthetic Sample Loading
In the **Document Ingestion & Evaluation** card, find the **"Quick Test Synthetic Samples"** row:
1. Click the **`Contract`** button.
   - Notice the green notification: *"Loaded synthetic sample 'contract.pdf' (2.9 KB). Ready to convert or evaluate."*
   - A file banner appears showing the file name (`contract.pdf`), size, and a remove (`✕`) button.
   - The "Ground-Truth Reference Manifest" dropdown automatically pre-selects `contract - Master Services Agreement`.
2. Try clicking **`Tabular Report`**, **`Multi-Page Spec`**, or **`Stress Test`**. Each one loads the respective binary PDF directly into the browser state.

---

### Test Step 3: Test Plain Conversion to Markdown (`/v1/ingest`)
1. Click **`Contract`** to load the sample.
2. Click the **`Convert to Markdown`** button (secondary button).
3. Observe the flow:
   - A spinner appears with *"Streaming PDF to backend parser..."*.
   - Within ~50 ms, the alert turns green: *"Successfully ingested 'contract.pdf' in ~50 ms."*
   - The page smoothly scrolls to the **Extracted Markdown & Side-by-Side Comparison** section.
4. Verify the metadata strip:
   - **Document:** `contract.pdf`
   - **Pages:** `1`
   - **Duration:** sub-100ms
   - **Usable Text:** `Yes (Usable Text)`
   - **Markdown SHA-256:** Truncated 16-character checksum (hovering shows full 64-hex string).
5. View the extracted Markdown in the left column:
   - Confirm `# Master Services Agreement` heading.
   - Confirm bullet points for scope of work.
   - Confirm the clean GFM table under `## 5. Signatures and Execution`.

---

### Test Step 4: Test Ground-Truth Evaluation & `N/A` Metric Handling (`/v1/evaluate`)
This is the core benchmark capability.

#### A. Test with `contract.pdf`
1. Load **`Contract`** and click **`Ingest & Evaluate`** (primary blue button).
2. Look at the **Structural Evaluation Metrics** card on the right:
   - **Composite Quality Score:** `100.0%` with a green `PASS` badge.
   - **Heading Hierarchy:** `100.0%` (P: 100.0% | R: 100.0% | Level Acc: 100.0%).
   - **Table Cell Accuracy:** `100.0%` (Cells: 8/8 | Det Prec: 100.0%).
   - **Text Completeness:** `100.0%`.
   - **Reading Order:** `100.0%`.
   - **List Preservation:** `100.0%`.
   - **Active Normalized Weight Allocations:** shows `heading_f1: 25%`, `table_cell_accuracy: 25%`, `text_completeness: 30%`, `reading_order: 10%`, `list_preservation: 10%`.

#### B. Test Transparent `N/A` Handling with `tabular_report.pdf` (Critical Check!)
1. Click **`Tabular Report`** and click **`Ingest & Evaluate`**.
2. Examine the **List Preservation** metric card:
   - Notice it displays **`N/A`** in a gray badge instead of a fabricated 100%!
   - Subtext explains: *"Ground-truth contains no lists (weights dynamically re-normalized)"*.
   - Check the **Active Normalized Weight Allocations**: `list_preservation` is omitted, and the weights for headings, tables, and text are dynamically re-allocated so the document is scored fairly without unearned bonus points.

---

### Test Step 5: Test Side-by-Side Comparison & Tabs
Scroll down to the bottom section:
1. **Side-by-Side Comparison Tab** (Default):
   - **Left Column:** *Extracted Markdown Output* (produced by our parser).
   - **Right Column:** *Ground-Truth Reference Markdown* (`contract.ref.md`).
   - Scroll both columns to compare headings, bullet points, and table structures line-by-line.
2. **Raw Markdown Tab**:
   - Click **`Raw Markdown`**.
   - Inspect the pure monospace GitHub-Flavored Markdown text.
3. **Extraction Diagnostics Tab**:
   - Click **`Extraction Diagnostics`**.
   - See cards for Headings Extracted (`6`), Tables Extracted (`1`), List Items Extracted (`4`).
   - Notice the clean log message: *"No diagnostic warnings reported. Extraction completed cleanly."*

---

### Test Step 5B: Testing Arbitrary PDFs (e.g. `Aashay_Resume (1).pdf`)
1. Upload any arbitrary PDF (e.g., your resume).
2. Leave the dropdown on **"Auto-detect from file name"**.
3. **If you click "Convert to Markdown"**:
   - The document is successfully converted to GitHub-Flavored Markdown.
   - Page count, duration, and extracted headings/lists are displayed in the metadata strip.
4. **If you click "Ingest & Evaluate"**:
   - Instead of throwing an error or generating fake scores, the system detects that no trusted reference manifest exists for this document.
   - It completes ingestion cleanly, renders the extracted Markdown, and displays the informative notice:
     *"Conversion completed. Accuracy evaluation is unavailable because no trusted reference exists for this document."*
   - The evaluation scorecard status badge updates to `NO REFERENCE`.

---

### Test Step 6: Test Copy & Download Actions
1. Click the **`Copy Markdown`** button in the top right of the output card:
   - The button text changes to **`Copied!`** for 2 seconds.
   - Open Notepad or any text editor and press `Ctrl+V` to verify the exact Markdown was copied.
2. Click the **`Download .md`** button:
   - Your browser downloads a file named `contract.md` (or `<filename>.md`).
   - Open the downloaded file to verify it matches.

---

### Test Step 7: Test Security Safeguards & File Validation
1. **Invalid File Format Test**:
   - Create a dummy text file named `test.txt` on your desktop or rename an image to `sample.txt`.
   - Drag and drop `test.txt` into the dropzone (or select it via Browse).
   - Notice the immediate error: *"Invalid file format. Only PDF files (.pdf) are permitted."*
   - The file is rejected before any network request is sent.
2. **Oversized File Test**:
   - Try uploading any PDF larger than 5 MB.
   - Notice the immediate warning: *"File size exceeds the maximum permitted limit of 5.0 MB."*
3. **XSS / HTML Injection Defense Verification**:
   - Notice that document text containing characters like `#`, `*`, `|`, `<` or `>` is strictly displayed as plain text. The dashboard never uses executable `innerHTML` for document content, preventing script injection.

---

## 3. Command-Line (CLI) Manual Testing

You can also test the benchmark engine directly in your terminal:

### 1. View Help and Subcommands
```bash
python -m docbench.cli --help
```

### 2. Ingest a Single PDF to Markdown
```bash
python -m docbench.cli convert data/synthetic/contract.pdf --output-dir outputs/
```
Output: Generates `outputs/contract.md` and displays SHA-256 and duration in terminal.

### 3. Evaluate a Document Against Ground Truth
```bash
python -m docbench.cli evaluate data/synthetic/contract.pdf --manifest data/manifests/contract.manifest.json --reference data/references/contract.ref.md
```
Output: Displays a rich formatted table in your console with scores for Heading F1, Table Cell Accuracy, Text Completeness, Reading Order, and List Preservation.

### 4. Run the 5-Iteration Determinism & Repeatability Test
```bash
python -m docbench.cli repeatability --iterations 5
```
Output: Tests 5 consecutive runs across all 4 documents, verifying **100% bitwise SHA-256 stability** and measuring latency jitter.

### 5. Generate Full Benchmark Reports
```bash
python -m docbench.cli report --output-dir outputs/
```
Output: Refreshes `outputs/benchmark_report.md`, `outputs/benchmark_report.json`, and `outputs/benchmark_summary.csv`.

---

## 4. REST API Testing via Terminal (Curl / PowerShell)

While the server is running on `http://127.0.0.1:8080`:

### Health Check:
```bash
curl -s http://127.0.0.1:8080/health
```

### Ingest PDF:
```bash
curl -X POST "http://127.0.0.1:8080/v1/ingest" -F "file=@data/synthetic/contract.pdf"
```

### Evaluate PDF:
```bash
curl -X POST "http://127.0.0.1:8080/v1/evaluate" -F "file=@data/synthetic/contract.pdf" -F "reference_id=contract"
```

### Benchmark Summary:
```bash
curl -s http://127.0.0.1:8080/v1/benchmark/summary
```

---

## 5. Automated Test Suite Verification

To verify that all 78 unit, integration, adversarial, and frontend tests pass:

```bash
python -m pytest tests/ -v
```

Expected output:
```
============================= 78 passed in ~6.5s ==============================
```

---

## Summary Checklist for Verification

- [ ] **Web Dashboard**: Navigated to `http://127.0.0.1:8080/` and saw the dark-slate dashboard.
- [ ] **Corpus Summary**: Confirmed overall score 100.0/100, `ALL_PASS`, and cached badge.
- [ ] **One-Click Samples**: Clicked `Contract` and `Tabular Report` buttons to auto-load sample PDFs.
- [ ] **Conversion**: Clicked "Convert to Markdown" and saw generated GFM with metadata and SHA-256.
- [ ] **Evaluation**: Clicked "Ingest & Evaluate" and verified composite score, metric cards, and weights.
- [ ] **N/A Handling**: Verified `tabular_report` correctly displays `N/A` for lists (not 100%).
- [ ] **Side-by-Side Comparison**: Inspected the two split columns (Extracted Markdown vs Reference Markdown).
- [ ] **Copy & Download**: Tested "Copy Markdown" and "Download .md" buttons.
- [ ] **Validation Guardrails**: Tested uploading a non-PDF file and confirmed it is safely rejected.
- [ ] **Test Suite**: Ran `python -m pytest tests/` and verified all 78 tests pass.
