"""
Command-line interface (CLI) for document-ingestion-benchmark.
"""

import sys
from pathlib import Path
import click
from rich.console import Console

from docbench.config import (
    SYNTHETIC_DIR,
    REFERENCES_DIR,
    MANIFESTS_DIR,
    OUTPUTS_DIR,
    DEFAULT_REPEATABILITY_RUNS,
    ensure_directories,
)
from docbench.generator.runner import generate_all
from docbench.ingestion.pipeline import ingest_document
from docbench.metrics.evaluator import evaluate_corpus
from docbench.repeatability.runner import run_repeatability_test
from docbench.reporting import generate_and_save_all_reports, print_console_report, get_system_info

# Initialize console with safe ASCII replacement on Windows legacy consoles
console = Console(safe_box=True)


@click.group()
@click.version_option(version="0.1.0", prog_name="docbench")
def main():
    """DocBench: PDF-to-Markdown Ingestion & Structural Preservation Benchmark."""
    ensure_directories()


@main.command("generate-samples")
@click.option(
    "--synthetic-dir",
    type=click.Path(path_type=Path),
    default=SYNTHETIC_DIR,
    help="Directory to save synthetic PDFs.",
)
@click.option(
    "--references-dir",
    type=click.Path(path_type=Path),
    default=REFERENCES_DIR,
    help="Directory to save reference Markdown.",
)
@click.option(
    "--manifests-dir",
    type=click.Path(path_type=Path),
    default=MANIFESTS_DIR,
    help="Directory to save manifest JSON files.",
)
def generate_samples_cmd(synthetic_dir: Path, references_dir: Path, manifests_dir: Path):
    """Generate 4 deterministic synthetic PDFs, reference Markdown, and ground-truth manifests."""
    console.print("[bold cyan]Generating synthetic benchmark documents...[/bold cyan]")
    summary = generate_all(
        synthetic_dir=synthetic_dir,
        references_dir=references_dir,
        manifests_dir=manifests_dir,
    )
    for doc_id, info in summary.items():
        console.print(
            f" [green][OK][/green] [bold]{doc_id}[/bold]: "
            f"PDF ({info['pdf_size_bytes']} bytes, SHA256: [yellow]{info['pdf_sha256'][:12]}...[/yellow]) | "
            f"Pages: {info['page_count']} | Headings: {info['headings_count']} | Tables: {info['tables_count']} | Lists: {info['lists_count']}"
        )
    console.print("[bold green]All synthetic samples successfully generated.[/bold green]")


@main.command("convert")
@click.argument("pdf_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional output Markdown file path.",
)
@click.option(
    "--doc-id",
    type=str,
    default=None,
    help="Explicit document ID identifier.",
)
def convert_cmd(pdf_path: Path, output: Path, doc_id: str):
    """Ingest a single PDF file and convert to conservative Markdown."""
    console.print(f"[bold cyan]Ingesting document:[/bold cyan] {pdf_path}")
    res = ingest_document(str(pdf_path), doc_id=doc_id, output_md_path=str(output) if output else None)

    console.print(f"  Doc ID: [bold]{res.doc_id}[/bold]")
    console.print(f"  Input PDF SHA-256: [yellow]{res.pdf_sha256}[/yellow]")
    console.print(f"  Output MD SHA-256: [yellow]{res.markdown_sha256}[/yellow]")
    console.print(f"  Pages: {res.page_count} | Duration: [green]{res.duration_ms:.2f} ms[/green]")
    console.print(f"  Extracted: {len(res.extracted_headings)} headings, {len(res.extracted_tables)} tables, {len(res.extracted_lists)} list items")

    if output:
        console.print(f"[bold green]Saved markdown to:[/bold green] {output}")
    else:
        console.print("\n[bold]Converted Markdown Output:[/bold]\n")
        console.print(res.markdown_content)


@main.command("evaluate")
@click.option(
    "--synthetic-dir",
    type=click.Path(exists=True, path_type=Path),
    default=SYNTHETIC_DIR,
    help="Directory containing synthetic PDFs.",
)
@click.option(
    "--references-dir",
    type=click.Path(exists=True, path_type=Path),
    default=REFERENCES_DIR,
    help="Directory containing reference Markdown.",
)
@click.option(
    "--manifests-dir",
    type=click.Path(exists=True, path_type=Path),
    default=MANIFESTS_DIR,
    help="Directory containing manifest JSON files.",
)
def evaluate_cmd(synthetic_dir: Path, references_dir: Path, manifests_dir: Path):
    """Evaluate ingestion quality against ground-truth manifests across the corpus."""
    console.print("[bold cyan]Evaluating document ingestion corpus against ground truth...[/bold cyan]")
    eval_results = evaluate_corpus(
        synthetic_dir=synthetic_dir,
        references_dir=references_dir,
        manifests_dir=manifests_dir,
    )
    repeat_results = run_repeatability_test(runs=3, synthetic_dir=synthetic_dir)
    system_info = get_system_info()
    print_console_report(eval_results, repeat_results, system_info)


@main.command("repeatability")
@click.option(
    "-n", "--runs",
    type=int,
    default=DEFAULT_REPEATABILITY_RUNS,
    help=f"Number of consecutive ingestion runs per document (default: {DEFAULT_REPEATABILITY_RUNS}).",
)
@click.option(
    "--synthetic-dir",
    type=click.Path(exists=True, path_type=Path),
    default=SYNTHETIC_DIR,
    help="Directory containing synthetic PDFs.",
)
def repeatability_cmd(runs: int, synthetic_dir: Path):
    """Run repeatability and determinism test across consecutive ingestion executions."""
    console.print(f"[bold cyan]Running repeatability benchmark ({runs} runs per document)...[/bold cyan]")
    rep = run_repeatability_test(runs=runs, synthetic_dir=synthetic_dir)
    console.print(f"Overall Bitwise Hash Stability: [bold green]{rep['overall_identical_rate']*100:.1f}%[/bold green]")
    console.print(f"Mean Execution Latency: [bold cyan]{rep['avg_mean_duration_ms']:.2f} ms[/bold cyan]")
    console.print(f"Latency Standard Deviation (Jitter): [bold yellow]{rep['avg_std_duration_ms']:.2f} ms[/bold yellow]")


@main.command("report")
@click.option(
    "-n", "--runs",
    type=int,
    default=DEFAULT_REPEATABILITY_RUNS,
    help="Number of repeatability runs.",
)
@click.option(
    "-o", "--output-dir",
    type=click.Path(path_type=Path),
    default=OUTPUTS_DIR,
    help="Directory to save report artifacts.",
)
def report_cmd(runs: int, output_dir: Path):
    """Generate Markdown, JSON, CSV, and console benchmark reports."""
    console.print("[bold cyan]Generating full benchmark evaluation and reports...[/bold cyan]")
    eval_results = evaluate_corpus()
    repeat_results = run_repeatability_test(runs=runs)
    saved_files = generate_and_save_all_reports(
        eval_results=eval_results,
        repeat_results=repeat_results,
        output_dir=output_dir,
        print_console=True,
    )
    console.print("\n[bold green]Reports generated successfully:[/bold green]")
    for fmt, p in saved_files.items():
        console.print(f"  - {fmt.upper()}: [cyan]{p}[/cyan]")


@main.command("run-all")
@click.option(
    "-n", "--runs",
    type=int,
    default=DEFAULT_REPEATABILITY_RUNS,
    help="Number of repeatability runs (default: 5).",
)
@click.option(
    "-o", "--output-dir",
    type=click.Path(path_type=Path),
    default=OUTPUTS_DIR,
    help="Directory to save report artifacts.",
)
def run_all_cmd(runs: int, output_dir: Path):
    """Execute complete Phase 1 pipeline: generation, evaluation, repeatability, and reporting."""
    console.print("[bold green]=== Step 1: Generating Deterministic Synthetic Corpus ===[/bold green]")
    generate_all()

    console.print("\n[bold green]=== Step 2: Evaluating Ingestion & Structural Preservation ===[/bold green]")
    eval_results = evaluate_corpus()

    console.print(f"\n[bold green]=== Step 3: Running Repeatability Benchmark ({runs} runs) ===[/bold green]")
    repeat_results = run_repeatability_test(runs=runs)

    console.print("\n[bold green]=== Step 4: Generating Benchmark Artifacts (MD, JSON, CSV) ===[/bold green]")
    saved_files = generate_and_save_all_reports(
        eval_results=eval_results,
        repeat_results=repeat_results,
        output_dir=output_dir,
        print_console=True,
    )

    console.print("\n[bold green]=== Benchmark Complete ===[/bold green]")
    for fmt, p in saved_files.items():
        console.print(f"  [green][OK][/green] {fmt.upper()}: [cyan]{p}[/cyan]")


@main.command("serve")
@click.option("--host", type=str, default="127.0.0.1", help="Host interface to bind to.")
@click.option("--port", type=int, default=8000, help="Port to bind to.")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload for local development.")
def serve_cmd(host: str, port: int, reload: bool):
    """Start local FastAPI REST service via Uvicorn."""
    import uvicorn
    console.print(f"[bold cyan]Starting DocBench API service at http://{host}:{port}...[/bold cyan]")
    uvicorn.run("docbench.api.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
