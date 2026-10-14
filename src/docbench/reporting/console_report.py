"""
Console report generator using rich tables with applicability awareness.
"""

from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from docbench.ingestion.models import DocumentEvaluation, RepeatabilityScore


def print_console_report(
    eval_results: Dict[str, Any],
    repeat_results: Dict[str, Any],
    system_info: Dict[str, Any],
):
    """
    Render formatted benchmark results to stdout with N/A support and critical failure alerts.
    """
    console = Console(safe_box=True)

    evaluations: List[DocumentEvaluation] = eval_results["evaluations"]
    aggregates: Dict[str, float] = eval_results["aggregates"]
    overall_score = eval_results["overall_benchmark_score"]
    repeat_scores: List[RepeatabilityScore] = repeat_results["scores"]
    ingest_map = {r.doc_id: r for r in eval_results.get("ingestion_results", [])}
    crit_count = aggregates.get("critical_failures_count", 0)

    # Header Panel
    header_text = Text()
    header_text.append("Document Ingestion & Structural Preservation Benchmark\n", style="bold cyan")
    header_text.append(f"Overall Score: {overall_score:.2f} / 100  |  ", style="bold green")
    header_text.append(f"Determinism Stability: {repeat_results['overall_identical_rate']*100:.1f}%  |  ", style="bold yellow")
    header_text.append(f"Avg Latency: {aggregates['avg_ingestion_duration_ms']:.1f} ms", style="bold magenta")
    if crit_count > 0:
        header_text.append(f"  |  Critical Failures: {crit_count}", style="bold red")
    console.print(Panel(header_text, border_style="cyan"))

    # Evaluation Matrix Table
    table = Table(title="Corpus Ingestion Benchmark Matrix", show_header=True, header_style="bold blue")
    table.add_column("Document", style="cyan", no_wrap=True)
    table.add_column("Heading F1", justify="right")
    table.add_column("Table Acc", justify="right")
    table.add_column("Text Comp", justify="right")
    table.add_column("Order Acc", justify="right")
    table.add_column("List F1", justify="right")
    table.add_column("Composite", justify="right", style="bold green")
    table.add_column("Status", justify="center")
    table.add_column("Duration", justify="right")

    for ev in evaluations:
        dur = ingest_map[ev.doc_id].duration_ms if ev.doc_id in ingest_map else 0.0
        h_str = f"{ev.heading_score.f1*100:.1f}%" if ev.heading_score.is_applicable else "N/A"
        t_str = f"{ev.table_score.cell_accuracy*100:.1f}%" if ev.table_score.is_applicable else "N/A"
        l_str = f"{ev.list_score.f1*100:.1f}%" if ev.list_score.is_applicable else "N/A"
        status_str = "[green]PASS[/green]" if not ev.critical_failure else "[bold red]FAIL[/bold red]"

        table.add_row(
            ev.doc_id,
            h_str,
            t_str,
            f"{ev.text_score.composite_text_score*100:.1f}%",
            f"{ev.reading_order_score.composite_order_score*100:.1f}%",
            l_str,
            f"{ev.composite_score*100:.1f}%",
            status_str,
            f"{dur:.1f} ms",
        )

    table.add_section()
    table.add_row(
        "CORPUS AVERAGE",
        f"{aggregates['avg_heading_f1']*100:.1f}%",
        f"{aggregates['avg_table_cell_accuracy']*100:.1f}%",
        f"{aggregates['avg_text_completeness']*100:.1f}%",
        f"{aggregates['avg_reading_order_accuracy']*100:.1f}%",
        f"{aggregates['avg_list_preservation_f1']*100:.1f}%",
        f"{aggregates['avg_composite_score']*100:.1f}%",
        "[green]ALL PASS[/green]" if crit_count == 0 else f"[red]{crit_count} FAILS[/red]",
        f"{aggregates['avg_ingestion_duration_ms']:.1f} ms",
        style="bold white on navy_blue",
    )
    console.print(table)
    console.print()

    # Repeatability Table
    rep_table = Table(title=f"Repeatability & Determinism Stability ({repeat_results['runs']} Runs)", show_header=True, header_style="bold magenta")
    rep_table.add_column("Document", style="cyan")
    rep_table.add_column("Runs", justify="right")
    rep_table.add_column("SHA-256 Stability", justify="right", style="bold green")
    rep_table.add_column("Mean Latency", justify="right")
    rep_table.add_column("Std Dev (Jitter)", justify="right")
    rep_table.add_column("Min / Max", justify="right")

    for rs in repeat_scores:
        rep_table.add_row(
            rs.doc_id,
            str(rs.runs),
            f"{rs.sha256_identical_rate*100:.1f}%",
            f"{rs.mean_duration_ms:.2f} ms",
            f"{rs.std_duration_ms:.2f} ms",
            f"{rs.min_duration_ms:.1f} / {rs.max_duration_ms:.1f} ms",
        )

    rep_table.add_section()
    rep_table.add_row(
        "AVERAGE",
        str(repeat_results['runs']),
        f"{repeat_results['overall_identical_rate']*100:.1f}%",
        f"{repeat_results['avg_mean_duration_ms']:.2f} ms",
        f"{repeat_results['avg_std_duration_ms']:.2f} ms",
        "-",
        style="bold white on dark_magenta",
    )
    console.print(rep_table)
