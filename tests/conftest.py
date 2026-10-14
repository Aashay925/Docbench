"""
Pytest fixtures and configuration for DocBench tests.
"""

import pytest
from pathlib import Path
from docbench.config import (
    SYNTHETIC_DIR,
    REFERENCES_DIR,
    MANIFESTS_DIR,
    ensure_directories,
)
from docbench.generator.runner import generate_all


@pytest.fixture(scope="session", autouse=True)
def setup_benchmark_data():
    """Ensure benchmark directories and synthetic samples are generated before running tests."""
    ensure_directories()
    generate_all()
