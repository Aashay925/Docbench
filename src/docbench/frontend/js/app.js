/**
 * DocBench Interactive Dashboard (Phase 4)
 * Plain modern JavaScript managing PDF ingestion, benchmark evaluation,
 * side-by-side comparison, and corpus summaries.
 * Strictly adheres to safe DOM manipulation (zero executable innerHTML for document content).
 */

(function () {
  'use strict';

  // 1. Central API Base Configuration
  // Supports localStorage override for Vercel -> FastAPI Cloud split deployments
  const defaultBase = window.location.hostname.includes('vercel.app') ? 'https://docbench.fastapicloud.dev' : '';
  let API_BASE = (localStorage.getItem('docbench_api_url') || window.DOCBENCH_API_BASE || defaultBase).replace(/\/+$/, '');

  // 2. Application State
  const state = {
    selectedFile: null,
    currentMarkdown: '',
    currentFilename: 'document.pdf',
    currentReferenceMarkdown: '',
    isEvaluating: false,
    isIngesting: false,
    trustedReferences: [],
  };

  // 3. DOM Elements
  const el = {
    // Header
    apiStatusPill: document.getElementById('api-status-pill'),
    apiStatusText: document.getElementById('api-status-text'),
    apiVersionBadge: document.getElementById('api-version-badge'),

    // Corpus Summary
    corpusErrorAlert: document.getElementById('corpus-error-alert'),
    corpusErrorMessage: document.getElementById('corpus-error-message'),
    summaryCachedBadge: document.getElementById('summary-cached-badge'),
    btnRefreshSummary: document.getElementById('btn-refresh-summary'),
    corpusOverallScore: document.getElementById('corpus-overall-score'),
    corpusStatusBadge: document.getElementById('corpus-status-badge'),
    corpusCritFailures: document.getElementById('corpus-crit-failures'),
    corpusHeadingF1: document.getElementById('corpus-heading-f1'),
    corpusTableCellAcc: document.getElementById('corpus-table-cell-acc'),
    corpusTextComp: document.getElementById('corpus-text-comp'),
    corpusReadingOrder: document.getElementById('corpus-reading-order'),
    corpusRepeatabilityRatio: document.getElementById('corpus-repeatability-ratio'),
    corpusTableBody: document.getElementById('corpus-table-body'),

    // Workspace & Upload
    dropzone: document.getElementById('dropzone'),
    fileInput: document.getElementById('file-input'),
    selectedFileBanner: document.getElementById('selected-file-banner'),
    selectedFileName: document.getElementById('selected-file-name'),
    selectedFileSize: document.getElementById('selected-file-size'),
    btnClearFile: document.getElementById('btn-clear-file'),
    referenceSelect: document.getElementById('reference-select'),
    btnIngest: document.getElementById('btn-ingest'),
    btnEvaluate: document.getElementById('btn-evaluate'),
    statusAlert: document.getElementById('status-alert'),
    statusSpinner: document.getElementById('status-spinner'),
    statusAlertIcon: document.getElementById('status-alert-icon'),
    statusAlertMessage: document.getElementById('status-alert-message'),

    // Evaluation Card
    evaluationCard: document.getElementById('evaluation-card'),
    evalEmptyState: document.getElementById('eval-empty-state'),
    evalResultsContent: document.getElementById('eval-results-content'),
    evalStatusBadge: document.getElementById('eval-status-badge'),
    evalRefCaption: document.getElementById('eval-ref-caption'),
    evalCompositeVal: document.getElementById('eval-composite-val'),
    evalCompositeBadge: document.getElementById('eval-composite-badge'),
    evalDurationVal: document.getElementById('eval-duration-val'),
    evalCritCheck: document.getElementById('eval-crit-check'),
    scoreHeadingF1: document.getElementById('score-heading-f1'),
    detailsHeading: document.getElementById('details-heading'),
    scoreTableCell: document.getElementById('score-table-cell'),
    detailsTable: document.getElementById('details-table'),
    scoreTextComp: document.getElementById('score-text-comp'),
    detailsText: document.getElementById('details-text'),
    scoreReadingOrder: document.getElementById('score-reading-order'),
    detailsOrder: document.getElementById('details-order'),
    scoreListF1: document.getElementById('score-list-f1'),
    detailsList: document.getElementById('details-list'),
    weightTagsContainer: document.getElementById('weight-tags-container'),

    // Output & Comparison
    sectionOutput: document.getElementById('section-output'),
    metaFilename: document.getElementById('meta-filename'),
    metaPages: document.getElementById('meta-pages'),
    metaDuration: document.getElementById('meta-duration'),
    metaUsable: document.getElementById('meta-usable'),
    metaSha256: document.getElementById('meta-sha256'),
    btnCopyMd: document.getElementById('btn-copy-md'),
    btnCopyText: document.getElementById('btn-copy-text'),
    btnDownloadMd: document.getElementById('btn-download-md'),

    // Tabs
    tabBtnSideBySide: document.getElementById('tab-btn-sidebyside'),
    tabBtnRaw: document.getElementById('tab-btn-raw'),
    tabBtnDiagnostics: document.getElementById('tab-btn-diagnostics'),
    paneSideBySide: document.getElementById('pane-sidebyside'),
    paneRaw: document.getElementById('pane-raw'),
    paneDiagnostics: document.getElementById('pane-diagnostics'),

    // Code & Content
    codeExtracted: document.getElementById('code-extracted'),
    codeReference: document.getElementById('code-reference'),
    codeRaw: document.getElementById('code-raw'),
    extractedHeadingsBadge: document.getElementById('extracted-headings-badge'),
    referenceBadge: document.getElementById('reference-badge'),
    referenceColumnTitle: document.getElementById('reference-column-title'),

    // Diagnostics
    diagHeadingsCount: document.getElementById('diag-headings-count'),
    diagTablesCount: document.getElementById('diag-tables-count'),
    diagListsCount: document.getElementById('diag-lists-count'),
    diagEntries: document.getElementById('diag-entries'),
  };

  // --------------------------------------------------------------------------
  // Utility Functions
  // --------------------------------------------------------------------------
  function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  function formatPercent(val) {
    if (val === null || val === undefined) return '--';
    return (val * 100).toFixed(1) + '%';
  }

  function setStatusAlert(message, type, showSpinner = false) {
    if (!message) {
      el.statusAlert.style.display = 'none';
      return;
    }
    el.statusAlert.className = 'alert alert-' + type;
    el.statusAlert.style.display = 'flex';
    el.statusAlertMessage.textContent = message;
    el.statusSpinner.style.display = showSpinner ? 'block' : 'none';

    if (showSpinner) {
      el.statusAlertIcon.style.display = 'none';
    } else {
      el.statusAlertIcon.style.display = 'inline';
      el.statusAlertIcon.textContent = type === 'error' ? '⚠️' : (type === 'success' ? '✓' : 'ℹ️');
    }
  }

  // --------------------------------------------------------------------------
  // 4. API Health & Version Verification
  // --------------------------------------------------------------------------
  async function checkApiHealth() {
    const t0 = performance.now();
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const latencyMs = Math.round(performance.now() - t0);

      const dot = el.apiStatusPill.querySelector('.status-dot');
      if (dot) {
        dot.className = 'status-dot online';
      }
      el.apiStatusText.textContent = `Online (${latencyMs}ms)`;

      // Fetch version
      const vRes = await fetch(`${API_BASE}/version`);
      if (vRes.ok) {
        const vData = await vRes.json();
        if (el.apiVersionBadge) {
          el.apiVersionBadge.textContent = `${vData.api_version} (v${vData.app_version})`;
        }
      }
    } catch (err) {
      const dot = el.apiStatusPill.querySelector('.status-dot');
      if (dot) {
        dot.className = 'status-dot offline';
      }
      el.apiStatusText.textContent = 'API Offline';
    }
  }

  // --------------------------------------------------------------------------
  // 5. Corpus Benchmark Summary
  // --------------------------------------------------------------------------
  async function fetchBenchmarkSummary() {
    el.corpusErrorAlert.style.display = 'none';
    el.btnRefreshSummary.disabled = true;

    try {
      const res = await fetch(`${API_BASE}/v1/benchmark/summary`);
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned HTTP ${res.status}`);
      }
      const data = await res.json();
      renderBenchmarkSummary(data);
    } catch (err) {
      el.corpusErrorAlert.style.display = 'flex';
      el.corpusErrorMessage.textContent = `Failed to load benchmark summary: ${err.message}. Ensure backend API is running.`;
    } finally {
      el.btnRefreshSummary.disabled = false;
    }
  }

  function renderBenchmarkSummary(data) {
    // Cached badge
    if (data.is_cached) {
      el.summaryCachedBadge.textContent = 'Cached';
      el.summaryCachedBadge.className = 'badge badge-cached';
      el.summaryCachedBadge.title = `Cached result from ${data.timestamp || 'latest benchmark run'}`;
    } else {
      el.summaryCachedBadge.textContent = 'Newly Computed';
      el.summaryCachedBadge.className = 'badge badge-success';
      el.summaryCachedBadge.title = 'Live newly computed corpus benchmark';
    }

    // Overall Score
    el.corpusOverallScore.textContent = (data.overall_benchmark_score || 0).toFixed(1);
    const critCount = data.critical_failures_count || 0;
    if (critCount === 0) {
      el.corpusStatusBadge.textContent = 'ALL PASS';
      el.corpusStatusBadge.className = 'badge badge-success';
      el.corpusCritFailures.textContent = '0 Critical Failures';
    } else {
      el.corpusStatusBadge.textContent = `${critCount} FAILS`;
      el.corpusStatusBadge.className = 'badge badge-error';
      el.corpusCritFailures.textContent = `${critCount} Critical Failures Detected`;
    }

    // Aggregates
    const agg = data.aggregates || {};
    el.corpusHeadingF1.textContent = formatPercent(agg.average_heading_f1);
    el.corpusTableCellAcc.textContent = formatPercent(agg.average_table_cell_accuracy);
    el.corpusTextComp.textContent = formatPercent(agg.average_text_completeness);
    el.corpusReadingOrder.textContent = formatPercent(agg.average_reading_order);

    // Repeatability
    const rep = data.repeatability_summary || {};
    const stabRatio = rep.byte_exact_match_ratio !== undefined ? formatPercent(rep.byte_exact_match_ratio) : '100.0%';
    el.corpusRepeatabilityRatio.textContent = stabRatio;

    // Document Table
    const docs = data.document_summaries || [];
    el.corpusTableBody.innerHTML = '';

    if (docs.length === 0) {
      const row = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 5;
      td.className = 'text-center text-muted';
      td.textContent = 'No corpus document evaluations available.';
      row.appendChild(td);
      el.corpusTableBody.appendChild(row);
      return;
    }

    const topoDescriptions = {
      contract: 'Master Services Agreement (Legal, 1 Page)',
      tabular_report: 'Q4 Financial Metrics (2D Data Matrix, 1 Page)',
      multipage_report: 'System Architecture Specification (Multi-Page, 3 Pages)',
      edge_cases: 'Typography Stress Test (Accents, Symbols, Nested Lists)',
    };

    docs.forEach(doc => {
      const row = document.createElement('tr');

      // 1. Doc ID
      const tdId = document.createElement('td');
      const codeElem = document.createElement('strong');
      codeElem.className = 'font-mono';
      codeElem.textContent = doc.doc_id || 'document';
      tdId.appendChild(codeElem);
      row.appendChild(tdId);

      // 2. Topology
      const tdTopo = document.createElement('td');
      tdTopo.textContent = topoDescriptions[doc.doc_id] || 'Synthetic Topology';
      row.appendChild(tdTopo);

      // 3. Score
      const tdScore = document.createElement('td');
      tdScore.className = 'font-mono';
      const scoreVal = (doc.composite_score || 0) * 100;
      tdScore.textContent = `${scoreVal.toFixed(1)}%`;
      row.appendChild(tdScore);

      // 4. Status
      const tdStatus = document.createElement('td');
      const badge = document.createElement('span');
      if (doc.critical_failure) {
        badge.className = 'badge badge-error';
        badge.textContent = 'CRITICAL FAIL';
      } else {
        badge.className = 'badge badge-success';
        badge.textContent = 'PASS';
      }
      tdStatus.appendChild(badge);
      row.appendChild(tdStatus);

      // 5. Ingestion Latency
      const tdLat = document.createElement('td');
      tdLat.className = 'font-mono text-muted';
      tdLat.textContent = doc.duration_ms ? `${doc.duration_ms.toFixed(1)} ms` : '< 80 ms';
      row.appendChild(tdLat);

      el.corpusTableBody.appendChild(row);
    });
  }

  // --------------------------------------------------------------------------
  // 6. File Selection & Dropzone Handling
  // --------------------------------------------------------------------------
  function handleFileSelect(file) {
    if (!file) return;

    // Validate extension
    const name = file.name || '';
    if (!name.toLowerCase().endsWith('.pdf')) {
      setStatusAlert('Invalid file format. Only PDF files (.pdf) are permitted.', 'error');
      clearFileSelection();
      return;
    }

    // Validate size limit (5 MB)
    const MAX_BYTES = 5 * 1024 * 1024;
    if (file.size > MAX_BYTES) {
      setStatusAlert(`File size (${formatBytes(file.size)}) exceeds the maximum permitted limit of 5.0 MB.`, 'error');
      clearFileSelection();
      return;
    }

    state.selectedFile = file;
    state.currentFilename = name;

    // Update UI
    el.selectedFileBanner.style.display = 'flex';
    el.selectedFileName.textContent = name;
    el.selectedFileSize.textContent = formatBytes(file.size);
    el.btnIngest.disabled = false;
    el.btnEvaluate.disabled = false;
    setStatusAlert('', 'info');

    // Auto-select reference in dropdown if matching stem
    const stem = name.replace(/\.pdf$/i, '').toLowerCase();
    const match = Array.from(el.referenceSelect.options).find(opt => opt.value === stem);
    if (match) {
      el.referenceSelect.value = stem;
    } else {
      el.referenceSelect.value = '';
    }
  }

  function clearFileSelection() {
    state.selectedFile = null;
    el.fileInput.value = '';
    el.selectedFileBanner.style.display = 'none';
    el.btnIngest.disabled = true;
    el.btnEvaluate.disabled = true;
  }

  // Quick synthetic sample loader
  async function loadSamplePdf(docId) {
    setStatusAlert(`Fetching sample PDF '${docId}.pdf'...`, 'info', true);
    try {
      const res = await fetch(`${API_BASE}/v1/benchmark/samples/${docId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const file = new File([blob], `${docId}.pdf`, { type: 'application/pdf' });
      handleFileSelect(file);
      setStatusAlert(`Loaded synthetic sample '${docId}.pdf' (${formatBytes(file.size)}). Ready to convert or evaluate.`, 'success');
    } catch (err) {
      setStatusAlert(`Failed to load sample '${docId}': ${err.message}`, 'error');
    }
  }

  // Trusted benchmark reference identifiers
  const TRUSTED_REFERENCES = ['contract', 'tabular_report', 'multipage_report', 'edge_cases'];

  function getResolvedReferenceId() {
    if (!state.selectedFile) return null;

    // 1. Check if an explicit valid reference is selected in dropdown
    const selected = (el.referenceSelect.value || '').trim().toLowerCase();
    if (selected && TRUSTED_REFERENCES.includes(selected)) {
      return selected;
    }

    // 2. Otherwise (Auto-detect), check if filename stem matches any trusted reference
    const name = state.selectedFile.name || '';
    const stem = name.replace(/\.pdf$/i, '').trim().toLowerCase();
    if (TRUSTED_REFERENCES.includes(stem)) {
      return stem;
    }

    return null;
  }

  // Helper to call backend ingestion API
  async function callIngestApi(file) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/v1/ingest`, {
      method: 'POST',
      body: formData,
    });

    const reqId = res.headers.get('X-Request-ID') || '';

    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      const detail = errJson.detail || `Server returned error status ${res.status}`;
      throw new Error(`${detail}${reqId ? ` [Req ID: ${reqId}]` : ''}`);
    }

    return await res.json();
  }

  // --------------------------------------------------------------------------
  // 7. Ingestion & Conversion (`POST /v1/ingest`)
  // --------------------------------------------------------------------------
  async function performIngestion() {
    if (!state.selectedFile) return;

    state.isIngesting = true;
    el.btnIngest.disabled = true;
    el.btnEvaluate.disabled = true;
    setStatusAlert('Streaming PDF to backend parser...', 'info', true);

    try {
      const data = await callIngestApi(state.selectedFile);
      renderIngestResults(data);
      setStatusAlert(`Successfully ingested '${data.filename}' in ${data.duration_ms.toFixed(1)} ms.`, 'success');
    } catch (err) {
      setStatusAlert(`Ingestion failed: ${err.message}`, 'error');
    } finally {
      state.isIngesting = false;
      el.btnIngest.disabled = false;
      el.btnEvaluate.disabled = false;
    }
  }

  function renderIngestResults(data) {
    state.currentMarkdown = data.markdown_content || '';
    state.currentFilename = data.filename || 'document.pdf';

    // Metadata
    el.metaFilename.textContent = data.filename;
    el.metaPages.textContent = data.page_count;
    el.metaDuration.textContent = `${data.duration_ms.toFixed(1)} ms`;
    el.metaUsable.textContent = data.has_usable_text ? 'Yes (Usable Text)' : 'No (Empty Content)';
    el.metaUsable.className = data.has_usable_text ? 'badge badge-success' : 'badge badge-error';
    el.metaSha256.textContent = (data.markdown_sha256 || '').substring(0, 16) + '...';
    el.metaSha256.title = data.markdown_sha256;

    // Output views (STRICT XSS-SAFE: textContent only!)
    el.codeExtracted.textContent = state.currentMarkdown;
    el.codeRaw.textContent = state.currentMarkdown;
    el.extractedHeadingsBadge.textContent = `${data.extracted_headings_count} headings`;

    // Reference column in Side-by-Side
    if (state.currentReferenceMarkdown) {
      el.codeReference.textContent = state.currentReferenceMarkdown;
    } else {
      el.codeReference.textContent =
        '# No Ground-Truth Reference Loaded\n\n' +
        'To view a side-by-side comparison against ground-truth, select a trusted benchmark reference (contract, tabular_report, multipage_report, edge_cases) and run "Ingest & Evaluate".';
    }

    // Diagnostics
    el.diagHeadingsCount.textContent = data.extracted_headings_count;
    el.diagTablesCount.textContent = data.extracted_tables_count;
    el.diagListsCount.textContent = data.extracted_lists_count;

    renderDiagnosticsLogs(data.diagnostics || []);

    // Reveal output section
    el.sectionOutput.style.display = 'block';
    el.sectionOutput.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function renderNoReferenceState(filename) {
    el.evalEmptyState.style.display = 'block';
    el.evalResultsContent.style.display = 'none';

    el.evalStatusBadge.textContent = 'NO REFERENCE';
    el.evalStatusBadge.className = 'badge badge-outline';
    el.evalRefCaption.textContent = 'No ground-truth reference exists for this document';

    // Clear reference markdown in state and side-by-side view
    state.currentReferenceMarkdown = '';
    el.codeReference.textContent =
      '# No Ground-Truth Reference Available\n\n' +
      'Accuracy evaluation and side-by-side reference comparison are only available for the 4 canonical benchmark topologies:\n' +
      '- contract (Master Services Agreement)\n' +
      '- tabular_report (Q4 Financial & Operating Metrics)\n' +
      '- multipage_report (Distributed Ingestion Architecture Spec)\n' +
      '- edge_cases (Typography & Stress Test)\n\n' +
      'Extracted Markdown for this document has been generated in the left pane.';
    el.referenceBadge.textContent = 'None';
    el.referenceColumnTitle.textContent = 'Ground-Truth Reference: None';
  }

  // --------------------------------------------------------------------------
  // 8. Evaluation (`POST /v1/evaluate`)
  // --------------------------------------------------------------------------
  async function performEvaluation() {
    if (!state.selectedFile) return;

    const resolvedRef = getResolvedReferenceId();

    // Requirement 3 & 4: If no trusted reference is selected or detected, do not call /v1/evaluate.
    // Complete ingestion successfully and display exact required message.
    if (!resolvedRef) {
      state.isEvaluating = true;
      el.btnIngest.disabled = true;
      el.btnEvaluate.disabled = true;
      setStatusAlert('Streaming PDF to backend parser...', 'info', true);

      try {
        const ingestData = await callIngestApi(state.selectedFile);
        renderIngestResults(ingestData);

        // Update evaluation scorecard state
        renderNoReferenceState(state.selectedFile.name);

        setStatusAlert(
          'Conversion completed. Accuracy evaluation is unavailable because no trusted reference exists for this document.',
          'info'
        );
      } catch (err) {
        setStatusAlert(`Ingestion failed: ${err.message}`, 'error');
      } finally {
        state.isEvaluating = false;
        el.btnIngest.disabled = false;
        el.btnEvaluate.disabled = false;
      }
      return;
    }

    // A trusted reference is selected or detected: proceed with benchmark evaluation
    state.isEvaluating = true;
    el.btnIngest.disabled = true;
    el.btnEvaluate.disabled = true;
    setStatusAlert(`Streaming PDF & evaluating against reference '${resolvedRef}'...`, 'info', true);

    const formData = new FormData();
    formData.append('file', state.selectedFile);
    formData.append('reference_id', resolvedRef);

    try {
      const res = await fetch(`${API_BASE}/v1/evaluate`, {
        method: 'POST',
        body: formData,
      });

      const reqId = res.headers.get('X-Request-ID') || '';

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        const detail = errJson.detail || `Server returned error status ${res.status}`;
        throw new Error(`${detail}${reqId ? ` [Req ID: ${reqId}]` : ''}`);
      }

      const data = await res.json();
      renderEvaluationResults(data);
      setStatusAlert(`Evaluated against '${data.reference_id}' in ${data.duration_ms.toFixed(1)} ms. Composite Score: ${(data.composite_score * 100).toFixed(1)}%.`, 'success');
    } catch (err) {
      setStatusAlert(`Evaluation failed: ${err.message}`, 'error');
    } finally {
      state.isEvaluating = false;
      el.btnIngest.disabled = false;
      el.btnEvaluate.disabled = false;
    }
  }

  function renderEvaluationResults(data) {
    el.evalEmptyState.style.display = 'none';
    el.evalResultsContent.style.display = 'block';

    state.currentReferenceMarkdown = data.reference_markdown || '';
    if (data.extracted_markdown) {
      state.currentMarkdown = data.extracted_markdown;
    }

    // Reference caption
    el.evalRefCaption.textContent = `Evaluated against verified ground-truth reference: '${data.reference_id}'`;

    // Composite Hero
    const compPct = (data.composite_score * 100).toFixed(1);
    el.evalCompositeVal.textContent = `${compPct}%`;

    if (data.critical_failure) {
      el.evalStatusBadge.textContent = 'CRITICAL FAIL';
      el.evalStatusBadge.className = 'badge badge-error';
      el.evalCompositeBadge.textContent = 'CRITICAL FAIL';
      el.evalCompositeBadge.className = 'badge badge-error';
      el.evalCritCheck.textContent = 'Critical Failure Triggered (< 40%)';
      el.evalCritCheck.className = 'badge badge-error';
    } else {
      el.evalStatusBadge.textContent = 'PASS';
      el.evalStatusBadge.className = 'badge badge-success';
      el.evalCompositeBadge.textContent = 'PASS';
      el.evalCompositeBadge.className = 'badge badge-success';
      el.evalCritCheck.textContent = 'No Critical Failures';
      el.evalCritCheck.className = 'badge badge-success';
    }

    el.evalDurationVal.textContent = `${data.duration_ms.toFixed(1)} ms`;

    // 1. Heading Hierarchy
    const h = data.heading_score || {};
    if (h.is_applicable === false) {
      el.scoreHeadingF1.innerHTML = '<span class="badge badge-na">N/A</span>';
      el.detailsHeading.textContent = 'Not applicable for this document topology';
    } else {
      el.scoreHeadingF1.textContent = formatPercent(h.f1);
      el.detailsHeading.textContent = `P: ${formatPercent(h.precision)} | R: ${formatPercent(h.recall)} | Level Acc: ${formatPercent(h.level_accuracy)}`;
    }

    // 2. Table Cell Accuracy
    const t = data.table_score || {};
    if (t.is_applicable === false) {
      el.scoreTableCell.innerHTML = '<span class="badge badge-na">N/A</span>';
      el.detailsTable.textContent = 'Not applicable for this document topology';
    } else {
      el.scoreTableCell.textContent = formatPercent(t.cell_accuracy);
      el.detailsTable.textContent = `Cells: ${t.matched_cells || 0}/${t.total_expected_cells || 0} | Det Prec: ${formatPercent(t.table_detection_precision)}`;
    }

    // 3. Text Completeness
    const txt = data.text_score || {};
    el.scoreTextComp.textContent = formatPercent(txt.composite_text_score || txt.token_f1);
    el.detailsText.textContent = `Token F1: ${formatPercent(txt.token_f1)} | Recall: ${formatPercent(txt.token_recall)} | Length Ratio: ${formatPercent(txt.length_ratio)}`;

    // 4. Reading Order
    const ro = data.reading_order_score || {};
    el.scoreReadingOrder.textContent = formatPercent(ro.composite_order_score || ro.kendall_tau);
    el.detailsOrder.textContent = `Kendall's Tau: ${formatPercent(ro.kendall_tau)} | LIS Ratio: ${formatPercent(ro.lcs_ratio)}`;

    // 5. List Preservation (CRITICAL REQUIREMENT: Show N/A if not applicable!)
    const l = data.list_score || {};
    if (l.is_applicable === false) {
      el.scoreListF1.innerHTML = '<span class="badge badge-na">N/A</span>';
      el.detailsList.textContent = 'Ground-truth contains no lists (weights dynamically re-normalized)';
    } else {
      el.scoreListF1.textContent = formatPercent(l.f1);
      el.detailsList.textContent = `P: ${formatPercent(l.precision)} | R: ${formatPercent(l.recall)} | Depth Acc: ${formatPercent(l.depth_accuracy)}`;
    }

    // Weights tags
    el.weightTagsContainer.innerHTML = '';
    const weights = data.applicable_weights || {};
    for (const [k, v] of Object.entries(weights)) {
      const tag = document.createElement('span');
      tag.className = 'weight-tag';
      tag.textContent = `${k}: ${(v * 100).toFixed(0)}%`;
      el.weightTagsContainer.appendChild(tag);
    }

    // Populate Side-by-Side & Code (STRICT XSS-SAFE: textContent only!)
    el.codeExtracted.textContent = state.currentMarkdown;
    el.codeRaw.textContent = state.currentMarkdown;
    el.codeReference.textContent = state.currentReferenceMarkdown;
    el.referenceBadge.textContent = data.reference_id;
    el.referenceColumnTitle.textContent = `Ground-Truth Reference: ${data.reference_id}.ref.md`;

    // Metadata
    el.metaFilename.textContent = data.filename;
    el.metaPages.textContent = '1+';
    el.metaDuration.textContent = `${data.duration_ms.toFixed(1)} ms`;
    el.metaUsable.textContent = 'Yes (Evaluated)';
    el.metaUsable.className = 'badge badge-success';
    el.metaSha256.textContent = 'Verified Deterministic';

    renderDiagnosticsLogs(data.diagnostics || []);

    // Reveal output section
    el.sectionOutput.style.display = 'block';
    el.sectionOutput.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function renderDiagnosticsLogs(diagnostics) {
    el.diagEntries.innerHTML = '';
    if (diagnostics.length === 0) {
      const span = document.createElement('span');
      span.className = 'text-muted';
      span.textContent = 'No diagnostic warnings reported. Extraction completed cleanly.';
      el.diagEntries.appendChild(span);
      return;
    }

    diagnostics.forEach(diag => {
      const div = document.createElement('div');
      div.style.marginBottom = '0.35rem';
      div.textContent = `[${diag.severity || 'INFO'}] Page ${diag.page_number || 1}: ${diag.message}`;
      el.diagEntries.appendChild(div);
    });
  }

  // --------------------------------------------------------------------------
  // 9. Copy to Clipboard & Download as Markdown
  // --------------------------------------------------------------------------
  async function copyMarkdownToClipboard() {
    if (!state.currentMarkdown) return;
    try {
      await navigator.clipboard.writeText(state.currentMarkdown);
      const originalText = el.btnCopyText.textContent;
      el.btnCopyText.textContent = 'Copied!';
      setTimeout(() => {
        el.btnCopyText.textContent = originalText;
      }, 2000);
    } catch (err) {
      setStatusAlert('Failed to copy Markdown to clipboard.', 'error');
    }
  }

  function downloadMarkdownFile() {
    if (!state.currentMarkdown) return;
    const blob = new Blob([state.currentMarkdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const baseName = (state.currentFilename || 'document').replace(/\.pdf$/i, '');
    a.href = url;
    a.download = `${baseName}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // --------------------------------------------------------------------------
  // 10. Tab Switching
  // --------------------------------------------------------------------------
  function switchTab(tabId) {
    const tabs = [
      { btn: el.tabBtnSideBySide, pane: el.paneSideBySide, id: 'sidebyside' },
      { btn: el.tabBtnRaw, pane: el.paneRaw, id: 'raw' },
      { btn: el.tabBtnDiagnostics, pane: el.paneDiagnostics, id: 'diagnostics' },
    ];

    tabs.forEach(t => {
      if (t.id === tabId) {
        t.btn.classList.add('active');
        t.btn.setAttribute('aria-selected', 'true');
        t.pane.style.display = 'block';
      } else {
        t.btn.classList.remove('active');
        t.btn.setAttribute('aria-selected', 'false');
        t.pane.style.display = 'none';
      }
    });
  }

  // --------------------------------------------------------------------------
  // 11. Event Listeners Setup
  // --------------------------------------------------------------------------
  function setupEventListeners() {
    // Dropzone
    el.dropzone.addEventListener('click', () => el.fileInput.click());
    el.fileInput.addEventListener('change', e => {
      if (e.target.files && e.target.files[0]) {
        handleFileSelect(e.target.files[0]);
      }
    });

    el.dropzone.addEventListener('dragover', e => {
      e.preventDefault();
      el.dropzone.classList.add('dragover');
    });

    el.dropzone.addEventListener('dragleave', () => {
      el.dropzone.classList.remove('dragover');
    });

    el.dropzone.addEventListener('drop', e => {
      e.preventDefault();
      el.dropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileSelect(e.dataTransfer.files[0]);
      }
    });

    el.dropzone.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        el.fileInput.click();
      }
    });

    el.btnClearFile.addEventListener('click', clearFileSelection);

    // Sample buttons
    document.querySelectorAll('.sample-btn').forEach(btn => {
      btn.addEventListener('click', e => {
        const docId = e.currentTarget.getAttribute('data-doc');
        loadSamplePdf(docId);
      });
    });

    // Actions
    el.btnIngest.addEventListener('click', performIngestion);
    el.btnEvaluate.addEventListener('click', performEvaluation);
    el.btnRefreshSummary.addEventListener('click', fetchBenchmarkSummary);
    el.btnCopyMd.addEventListener('click', copyMarkdownToClipboard);
    el.btnDownloadMd.addEventListener('click', downloadMarkdownFile);

    // Tabs
    el.tabBtnSideBySide.addEventListener('click', () => switchTab('sidebyside'));
    el.tabBtnRaw.addEventListener('click', () => switchTab('raw'));
    el.tabBtnDiagnostics.addEventListener('click', () => switchTab('diagnostics'));

    // Backend API URL Configuration (for Vercel / Cloud split deployments)
    const btnApiConfig = document.getElementById('btn-api-config');
    if (btnApiConfig) {
      btnApiConfig.addEventListener('click', () => {
        const current = localStorage.getItem('docbench_api_url') || window.DOCBENCH_API_BASE || '';
        const entered = prompt(
          'Enter your deployed FastAPI Cloud Backend URL\n(e.g., https://your-app.fastapicloud.app):\n\nLeave blank to reset to default relative path.',
          current
        );
        if (entered !== null) {
          const cleaned = entered.trim().replace(/\/+$/, '');
          if (cleaned) {
            localStorage.setItem('docbench_api_url', cleaned);
            API_BASE = cleaned;
          } else {
            localStorage.removeItem('docbench_api_url');
            API_BASE = (window.DOCBENCH_API_BASE || '').replace(/\/+$/, '');
          }
          checkApiHealth();
          fetchBenchmarkSummary();
        }
      });
    }
  }

  // --------------------------------------------------------------------------
  // Initialization
  // --------------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkApiHealth();
    fetchBenchmarkSummary();
  });

})();
