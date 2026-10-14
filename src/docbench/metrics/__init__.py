"""
Evaluation metrics package.
"""

from docbench.metrics.headings import evaluate_headings
from docbench.metrics.tables import evaluate_tables
from docbench.metrics.text import evaluate_text_completeness
from docbench.metrics.reading_order import evaluate_reading_order
from docbench.metrics.lists import evaluate_lists
from docbench.metrics.evaluator import evaluate_document, evaluate_corpus

__all__ = [
    "evaluate_headings",
    "evaluate_tables",
    "evaluate_text_completeness",
    "evaluate_reading_order",
    "evaluate_lists",
    "evaluate_document",
    "evaluate_corpus",
]
