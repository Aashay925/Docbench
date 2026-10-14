# Document Ingestion & Structural Preservation Benchmark Report

**Overall Benchmark Score**: `100.00 / 100`  
**Corpus Determinism Stability**: `100.0%`  
**Average Ingestion Duration**: `72.15 ms`  
**Critical Failures Count**: `0`  
**Timestamp**: `2026-10-14T21:06:51.368507+00:00`  

---

## 1. Executive Summary

This benchmark evaluates conservative, deterministic PDF-to-Markdown ingestion across a four-document synthetic corpus designed to test foundational document layout structures: contracts, tabular financial statements, multi-page hierarchical reports, and structural edge-case documents.

All dependencies are strictly verified for permissive licensing (MIT/BSD/Apache-2.0), avoiding AGPL/GPL dependencies (e.g. PyMuPDF4LLM) to ensure unrestricted public and commercial distribution.

## 2. Document Evaluation Summary Matrix

| Document ID | Heading F1 | Table Cell Acc | Text Comp | Reading Order | List F1 | Composite | Status | Duration (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `contract` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | **100.0%** | **PASS** | 52.1 |
| `tabular_report` | 100.0% | 100.0% | 100.0% | 100.0% | N/A | **100.0%** | **PASS** | 46.9 |
| `multipage_report` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | **100.0%** | **PASS** | 73.0 |
| `edge_cases` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | **100.0%** | **PASS** | 116.6 |
| **CORPUS AVERAGE** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | - | **72.2** |

## 3. Repeatability and Determinism Stability

Repeatability was evaluated across `5` consecutive runs per document. Bitwise hash stability verifies that the output Markdown SHA-256 remains 100% deterministic with zero stochastic fluctuation.

| Document ID | Runs | SHA-256 Stability | Mean Latency (ms) | Std Dev (ms) | Min / Max (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `contract` | 5 | **100.0%** | 79.59 | 25.86 | 47.4 / 118.8 |
| `tabular_report` | 5 | **100.0%** | 63.29 | 12.41 | 49.7 / 79.6 |
| `multipage_report` | 5 | **100.0%** | 99.38 | 11.11 | 85.6 / 115.3 |
| `edge_cases` | 5 | **100.0%** | 82.76 | 24.19 | 56.3 / 119.9 |
| **AVERAGE** | 5 | **100.0%** | **81.25** | **18.39** | - |

## 4. Per-Document Ingestion Details and Metrics

### Document: `contract`

- **Heading Structure**: Precision `100.0%`, Recall `100.0%`, F1 `100.0%`, Order Acc `100.0%` (Matched: 6/6)
- **Table Preservation**: Cell Accuracy `100.0%`, Detection Precision `100.0%`, Detection Recall `100.0%` (Matched Cells: 12/12)
- **Text Completeness**: Token Recall `100.0%`, Token Precision `100.0%`, Token F1 `100.0%`, Sequence Similarity `100.0%`, Length Ratio `100.0%`
- **Reading Order**: LCS Ratio `100.0%`, Kendall's Tau `100.0%` (Found: 9/9)
- **List Preservation**: Precision `100.0%`, Recall `100.0%`, F1 `100.0%`, Depth Acc `100.0%`, Order Acc `100.0%` (Matched Items: 4/4)
- **Overall Document Composite Score**: `100.0%`
- **Applicable Weight Distribution**: `{'text_completeness': 0.25, 'reading_order_accuracy': 0.15, 'heading_f1': 0.2, 'table_cell_accuracy': 0.25, 'list_preservation_f1': 0.15}`

### Document: `tabular_report`

- **Heading Structure**: Precision `100.0%`, Recall `100.0%`, F1 `100.0%`, Order Acc `100.0%` (Matched: 5/5)
- **Table Preservation**: Cell Accuracy `100.0%`, Detection Precision `100.0%`, Detection Recall `100.0%` (Matched Cells: 50/50)
- **Text Completeness**: Token Recall `100.0%`, Token Precision `100.0%`, Token F1 `100.0%`, Sequence Similarity `100.0%`, Length Ratio `100.0%`
- **Reading Order**: LCS Ratio `100.0%`, Kendall's Tau `100.0%` (Found: 7/7)
- **List Preservation**: N/A (No list items in document)
- **Overall Document Composite Score**: `100.0%`
- **Applicable Weight Distribution**: `{'text_completeness': 0.2941, 'reading_order_accuracy': 0.1765, 'heading_f1': 0.2353, 'table_cell_accuracy': 0.2941}`

### Document: `multipage_report`

- **Heading Structure**: Precision `100.0%`, Recall `100.0%`, F1 `100.0%`, Order Acc `100.0%` (Matched: 7/7)
- **Table Preservation**: Cell Accuracy `100.0%`, Detection Precision `100.0%`, Detection Recall `100.0%` (Matched Cells: 20/20)
- **Text Completeness**: Token Recall `100.0%`, Token Precision `100.0%`, Token F1 `100.0%`, Sequence Similarity `100.0%`, Length Ratio `100.0%`
- **Reading Order**: LCS Ratio `100.0%`, Kendall's Tau `100.0%` (Found: 10/10)
- **List Preservation**: Precision `100.0%`, Recall `100.0%`, F1 `100.0%`, Depth Acc `100.0%`, Order Acc `100.0%` (Matched Items: 7/7)
- **Overall Document Composite Score**: `100.0%`
- **Applicable Weight Distribution**: `{'text_completeness': 0.25, 'reading_order_accuracy': 0.15, 'heading_f1': 0.2, 'table_cell_accuracy': 0.25, 'list_preservation_f1': 0.15}`

### Document: `edge_cases`

- **Heading Structure**: Precision `100.0%`, Recall `100.0%`, F1 `100.0%`, Order Acc `100.0%` (Matched: 6/6)
- **Table Preservation**: Cell Accuracy `100.0%`, Detection Precision `100.0%`, Detection Recall `100.0%` (Matched Cells: 20/20)
- **Text Completeness**: Token Recall `100.0%`, Token Precision `100.0%`, Token F1 `100.0%`, Sequence Similarity `100.0%`, Length Ratio `100.0%`
- **Reading Order**: LCS Ratio `100.0%`, Kendall's Tau `100.0%` (Found: 10/10)
- **List Preservation**: Precision `100.0%`, Recall `100.0%`, F1 `100.0%`, Depth Acc `100.0%`, Order Acc `100.0%` (Matched Items: 5/5)
- **Overall Document Composite Score**: `100.0%`
- **Applicable Weight Distribution**: `{'text_completeness': 0.25, 'reading_order_accuracy': 0.15, 'heading_f1': 0.2, 'table_cell_accuracy': 0.25, 'list_preservation_f1': 0.15}`

## 5. Execution Environment

- **Python Version**: `3.12.0`
- **Platform / OS**: `Windows-11-10.0.26200-SP0`
- **Core Parser**: `pdfplumber 0.11.10` (MIT License) / `pdfminer.six` (MIT License)
- **PDF Generator**: `reportlab 5.0.1` (BSD License) / `pypdf 6.20.1` (BSD-3-Clause)

