"""
Reporting package coordinating Markdown, JSON, CSV, and console benchmark reports.
"""

import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from docbench.config import OUTPUTS_DIR, ensure_directories
from docbench.reporting.markdown_report import generate_markdown_report
from docbench.reporting.json_report import generate_json_report
from docbench.reporting.csv_report import generate_csv_report
from docbench.reporting.console_report import print_console_report


def get_system_info() -> Dict[str, Any]:
    """Gather diagnostic runtime system and environment metadata."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
    }


def generate_and_save_all_reports(
    eval_results: Dict[str, Any],
    repeat_results: Dict[str, Any],
    output_dir: Path = OUTPUTS_DIR,
    print_console: bool = True,
) -> Dict[str, Path]:
    """
    Generate all reports (Markdown, JSON, CSV) and save them to output_dir.
    Optionally print to console.
    """
    ensure_directories()
    output_dir.mkdir(parents=True, exist_ok=True)
    system_info = get_system_info()

    # 1. Generate Markdown Report
    md_content = generate_markdown_report(eval_results, repeat_results, system_info)
    md_path = output_dir / "benchmark_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 2. Generate JSON Report
    json_content = generate_json_report(eval_results, repeat_results, system_info)
    json_path = output_dir / "benchmark_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_content)

    # 3. Generate CSV Report
    csv_content = generate_csv_report(eval_results, repeat_results)
    csv_path = output_dir / "benchmark_summary.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(csv_content)

    # 4. Console print
    if print_console:
        print_console_report(eval_results, repeat_results, system_info)

    return {
        "markdown": md_path,
        "json": json_path,
        "csv": csv_path,
    }


__all__ = [
    "generate_markdown_report",
    "generate_json_report",
    "generate_csv_report",
    "print_console_report",
    "generate_and_save_all_reports",
    "get_system_info",
]
