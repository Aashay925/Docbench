"""
Configuration and default paths for document-ingestion-benchmark.
"""

from pathlib import Path
from typing import Dict

# Base project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
REFERENCES_DIR = DATA_DIR / "references"
MANIFESTS_DIR = DATA_DIR / "manifests"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DOCS_DIR = PROJECT_ROOT / "docs"

# Benchmark document definitions
SAMPLE_DOCUMENTS = [
    "contract",
    "tabular_report",
    "multipage_report",
    "edge_cases",
]

# Benchmark scoring weights
DEFAULT_METRIC_WEIGHTS: Dict[str, float] = {
    "heading_f1": 0.20,
    "table_cell_accuracy": 0.25,
    "text_completeness": 0.25,
    "reading_order_accuracy": 0.15,
    "list_preservation_f1": 0.15,
}

# Repeatability defaults
DEFAULT_REPEATABILITY_RUNS = 5

def ensure_directories():
    """Ensure all required runtime directories exist."""
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
