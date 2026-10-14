"""
Unit tests for DocBench Click CLI commands.
"""

from pathlib import Path
from click.testing import CliRunner
from docbench.cli import main
from docbench.config import SYNTHETIC_DIR


def test_cli_help():
    """Verify top-level CLI help command displays available commands."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "DocBench" in result.output
    assert "generate-samples" in result.output
    assert "convert" in result.output
    assert "evaluate" in result.output
    assert "repeatability" in result.output
    assert "report" in result.output
    assert "run-all" in result.output


def test_cli_convert_command(tmp_path: Path):
    """Verify CLI convert command processes a PDF and outputs markdown."""
    runner = CliRunner()
    pdf_path = SYNTHETIC_DIR / "contract.pdf"
    out_md = tmp_path / "cli_contract.md"

    result = runner.invoke(main, ["convert", str(pdf_path), "-o", str(out_md)])
    assert result.exit_code == 0
    assert out_md.exists()
    assert "Master Services Agreement" in out_md.read_text(encoding="utf-8")


def test_cli_repeatability_command():
    """Verify CLI repeatability command runs successfully."""
    runner = CliRunner()
    result = runner.invoke(main, ["repeatability", "-n", "2"])
    assert result.exit_code == 0
    assert "100.0%" in result.output


def test_cli_evaluate_command():
    """Verify CLI evaluate command runs corpus evaluation."""
    runner = CliRunner()
    result = runner.invoke(main, ["evaluate"])
    assert result.exit_code == 0
    assert "Corpus Ingestion Benchmark Matrix" in result.output
