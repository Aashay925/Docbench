# Evaluation Methodology and Metric Formulations (Hardened Phase 2)

## 1. Overview and Design Principles

The `document-ingestion-benchmark` (`docbench`) suite provides a rigorous, objective evaluation framework for measuring the structural fidelity, textual completeness, and operational determinism of PDF-to-Markdown document ingestion pipelines.

Rather than relying on qualitative human inspection or stochastic LLM-based grading, `docbench` evaluates extraction quality against **independent, ground-truth reference manifests** and **reference Markdown documents** generated deterministically from known source specifications.

In **Phase 2**, all metrics were audited and hardened against 14 adversarial corruption scenarios to ensure defects (such as dropped sections, duplicated text, transposed tables, reordered paragraphs, and nesting depth errors) cannot pass undetected.

---

## 2. Benchmark Corpus Design

The benchmark corpus targets four foundational document topologies:

| Document ID | Topology | Key Structural Characteristics | Pages | Primary Challenges |
| :--- | :--- | :--- | :---: | :--- |
| `contract` | Legal Agreement | Strict section hierarchy (H1, H2), bulleted deliverables, signature block | 1 | Inline entity wrapping, bullet marker parsing, signature matrix |
| `tabular_report` | Financial Report | Multi-column tabular data, currency symbols, percentages, growth rates | 1 | Exact cell alignment, table bounding box isolation, numeric preservation |
| `multipage_report` | Architecture Doc | Multi-level headings (H1, H2, H3), ordered lists, multi-page layout | 3 | Cross-page reading order, page boundaries, nested header hierarchy |
| `edge_cases` | Stress Test | International currencies, math symbols, nested lists, punctuation | 1 | Unicode accents, nested list depths, border error matrix, inline code |

---

## 3. Mathematical Metric Formulations (Phase 2 Hardened)

### 3.1 Heading Structure Preservation & Sequential Order

Headings are evaluated across precision, recall, harmonic F1, and sequential order. A true positive ($TP$) match requires both **exact heading level equality** ($L_{ext} = L_{exp}$) and **normalized text equality**:

$$\text{Precision} = \frac{TP}{\max(|H_{ext}|, 1)}, \quad \text{Recall} = \frac{TP}{\max(|H_{exp}|, 1)}$$

$$\text{Raw } F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

To detect heading reordering, the Longest Increasing Subsequence ($\text{LIS}$) of matched heading positions is calculated:

$$\text{Order Accuracy} = \frac{\text{len}(\text{LIS}(\text{ExtractedIndices}))}{\max(TP, 1)}$$

$$\text{Structural } F_1 = \text{Raw } F_1 \times (0.80 + 0.20 \cdot \text{Order Accuracy})$$

If a document has no headings in ground truth, `is_applicable = False` is set and the metric is excluded from composite weighting.

### 3.2 Table Cell Preservation Accuracy & Alignment

To prevent fragile index-based errors when tables are omitted or reordered, extracted tables are first aligned with expected tables using **Header-Jaccard Bipartite Matching**:

$$\text{Jaccard}(H_{exp}, H_{ext}) = \frac{|H_{exp} \cap H_{ext}|}{|H_{exp} \cup H_{ext}|}$$

Once paired, cell-by-cell coordinate matching $(r, c)$ evaluates both header and data cells:

$$\text{Cell Accuracy} = \frac{M_{cells}}{\max(N_{exp\_cells}, N_{ext\_cells}, 1)}$$

Where:
- $M_{cells}$ is the number of cells matching across header and data rows at exact coordinate $(r, c)$.
- $N_{exp\_cells}$ is the total number of cells in the ground-truth table manifest.
- $N_{ext\_cells}$ is the total number of cells in the extracted table block.

Extra rows or columns increase $N_{ext\_cells}$ and penalize the denominator; omitted rows reduce $M_{cells}$. If a document contains no tables, `is_applicable = False`.

### 3.3 Verbatim Text Completeness (Duplication-Penalized)

In Phase 1, text completeness only measured recall, allowing 3x–5x duplicated text to achieve high scores. In Phase 2, **token precision**, **harmonic token F1**, and **length ratio penalties** were introduced:

1. **Character Recall**:
   $$\text{Char Recall} = \frac{\sum_{c} \min(\text{count}_{ext}(c), \text{count}_{ref}(c))}{\sum_{c} \text{count}_{ref}(c)}$$

2. **Token Recall, Precision, and F1**:
   $$\text{Token Recall} = \frac{\sum_{t} \min(\text{count}_{ext}(t), \text{count}_{ref}(t))}{\text{len}(Tokens_{ref})}$$
   $$\text{Token Precision} = \frac{\sum_{t} \min(\text{count}_{ext}(t), \text{count}_{ref}(t))}{\text{len}(Tokens_{ext})}$$
   $$\text{Token } F_1 = \frac{2 \cdot \text{Token Precision} \cdot \text{Token Recall}}{\text{Token Precision} + \text{Token Recall}}$$

3. **Sequence Similarity**:
   $$\text{Sequence Ratio} = \frac{2 M}{|S_{ref}| + |S_{ext}|}$$
   Computed via Ratcliff-Obershelp gestalt pattern matching on normalized whitespace text.

4. **Length Ratio Penalty**:
   $$\text{Length Ratio} = \frac{\min(\text{len}(S_{ext}), \text{len}(S_{ref}))}{\max(\text{len}(S_{ext}), \text{len}(S_{ref}), 1)}$$

5. **Hardened Composite Text Score**:
   $$\text{Composite Text} = 0.30 \cdot \text{Sequence Ratio} + 0.35 \cdot \text{Token } F_1 + 0.20 \cdot \text{Char Recall} + 0.15 \cdot \text{Length Ratio}$$

If either string is empty while the other is non-empty, all text scores return `0.0`.

### 3.4 Reading Order Accuracy (Fixed Empty-Text Bug)

Let $A = [a_1, a_2, \dots, a_k]$ be ordered landmark anchors throughout the document. Let $P = [p(a_1), p(a_2), \dots]$ be the character positions of **only the found anchors**:

- If $\text{len}(P) == 0$, $\text{Composite Order} = 0.0$ (fixes Phase 1 bug where empty text scored 100%).
- **LCS Ratio**:
  $$\text{LCS Ratio} = \frac{\text{len}(\text{LIS}(P))}{|A|}$$
  Normalized against the *total expected anchors*, penalizing omitted sections.
- **Kendall's Tau ($\tau$)**:
  Calculated across pairs of found anchors and scaled by anchor recall:
  $$\text{Anchor Recall} = \frac{\text{len}(P)}{|A|}$$
  $$\tau_{normalized} = \frac{\tau_{raw} + 1.0}{2.0}$$
  $$\text{Effective Tau} = \tau_{normalized} \times \text{Anchor Recall}$$
- **Composite Order Score**:
  $$\text{Composite Order} = 0.50 \cdot \text{LCS Ratio} + 0.50 \cdot \text{Effective Tau}$$

### 3.5 List Preservation (Depth-Strict and Order-Aware)

A true positive match requires exact equality on `list_type` (bullet vs numbered), normalized `text`, AND hierarchical nesting `depth`:

$$\text{Precision} = \frac{TP_{exact}}{\max(|L_{ext}|, 1)}, \quad \text{Recall} = \frac{TP_{exact}}{\max(|L_{exp}|, 1)}$$
$$\text{Raw } F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

- **Depth Accuracy**:
  $$\text{Depth Accuracy} = \frac{TP_{exact}}{\max(TP_{text\_and\_type}, 1)}$$
- **Order Accuracy**:
  $$\text{Order Accuracy} = \frac{\text{len}(\text{LIS}(\text{ExtractedIndices}))}{\max(TP_{text\_and\_type}, 1)}$$
- **Hardened List Score**:
  $$\text{List } F_1 = \text{Raw } F_1 \times (0.80 + 0.20 \cdot \text{Order Accuracy})$$

### 3.6 Dynamic Weight Re-normalization for Applicable Components

In Phase 1, documents without certain features (e.g. `tabular_report` has no lists) scored 1.0 on that component, granting unearned points. In Phase 2, weights are dynamically re-normalized over **only applicable components**:

$$\mathcal{K}_{applicable} = \{k \in \mathcal{K} \mid \text{is\_applicable}(k) = \text{True}\}$$
$$W_{sum} = \sum_{k \in \mathcal{K}_{applicable}} w_k$$
$$w_{k, normalized} = \frac{w_k}{W_{sum}}$$
$$\text{Composite Score} = \sum_{k \in \mathcal{K}_{applicable}} w_{k, normalized} \cdot S_k$$

### 3.7 Critical Component Failure Detection

An aggregate score can conceal a catastrophic failure in a single dimension (e.g., table destruction resulting in 0% cell accuracy while text scores 100%). Phase 2 introduces:

$$\text{Critical Failure} = \left(\min_{k \in \mathcal{K}_{applicable}} S_k < 0.40\right)$$

If triggered, reports prominently flag `CRITICAL FAIL` regardless of whether the composite score is high.
