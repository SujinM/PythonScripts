"""
eToro Analyzer CLI.

Usage:
    python -m app [command]

Commands:
    positions   Display open positions.
    history     Display closed trade history.
    summary     Display portfolio summary.
    alerts      Show positions that breached gain/loss thresholds.

Authentication:
    No browser flow required. Set ETORO_API_KEY and ETORO_USER_KEY in .env.
    Get keys from: eToro account → Settings → Trading → API Key Management
"""

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from etoro_app.api.etoro_client import EToroAuthError, EToroClient
from etoro_app.core.config import Config, ConfigError
from etoro_app.models.portfolio import ClosedPosition, PortfolioSummary, Position
from etoro_app.services.analysis_service import AnalysisService
from etoro_app.services.portfolio_service import PortfolioService
from etoro_app.utils.helpers import format_currency, format_percentage, pnl_color, truncate

app = typer.Typer(
    name="etoro-analyzer",
    help="eToro portfolio analysis CLI.",
    add_completion=False,
)
console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_service() -> tuple[Config, PortfolioService]:
    """Bootstrap config + client + service; exit on config error."""
    try:
        config = Config()
    except ConfigError as exc:
        console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    client = EToroClient(config)
    service = PortfolioService(client, cache_ttl=0)
    return config, service


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def positions() -> None:
    """Display all open positions."""
    _, service = _get_service()
    try:
        rows = service.get_positions()
    except EToroAuthError as exc:
        console.print(f"[bold red]Auth error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    if not rows:
        console.print("[yellow]No open positions found.[/yellow]")
        return

    table = Table(title="Open Positions", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Instrument", min_width=18)
    table.add_column("Type", width=10)
    table.add_column("Dir", width=5)
    table.add_column("Invested", justify="right")
    table.add_column("Units", justify="right")
    table.add_column("Open Rate", justify="right")
    table.add_column("Current", justify="right")
    table.add_column("P&L", justify="right")
    table.add_column("Return %", justify="right")
    table.add_column("Lev", justify="right", width=5)

    for i, p in enumerate(rows, 1):
        color = pnl_color(p.unrealised_pnl)
        table.add_row(
            str(i),
            truncate(p.instrument_name, 20),
            p.instrument_type,
            p.direction,
            format_currency(p.amount),
            f"{p.units:.4f}",
            f"{p.open_rate:.4f}",
            f"{p.current_rate:.4f}",
            f"[{color}]{format_currency(p.unrealised_pnl)}[/{color}]",
            f"[{color}]{format_percentage(p.return_percentage)}[/{color}]",
            f"{p.leverage}x",
        )

    console.print(table)
    console.print(f"\n[dim]Total open positions: {len(rows)}[/dim]")


@app.command()
def history(
    limit: int = typer.Option(50, "--limit", "-n", help="Max records to show")
) -> None:
    """Display closed trade history."""
    _, service = _get_service()
    try:
        rows = service.get_closed_positions()
    except EToroAuthError as exc:
        console.print(f"[bold red]Auth error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    rows = rows[:limit]
    if not rows:
        console.print("[yellow]No closed positions found.[/yellow]")
        return

    table = Table(title="Closed Trade History", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Instrument", min_width=18)
    table.add_column("Dir", width=5)
    table.add_column("Invested", justify="right")
    table.add_column("Open Rate", justify="right")
    table.add_column("Close Rate", justify="right")
    table.add_column("Realised P&L", justify="right")
    table.add_column("Return %", justify="right")
    table.add_column("Close Date")

    for i, c in enumerate(rows, 1):
        color = pnl_color(c.realised_pnl)
        close_date = c.close_date.strftime("%Y-%m-%d") if c.close_date else "—"
        table.add_row(
            str(i),
            truncate(c.instrument_name, 20),
            c.direction,
            format_currency(c.amount),
            f"{c.open_rate:.4f}",
            f"{c.close_rate:.4f}",
            f"[{color}]{format_currency(c.realised_pnl)}[/{color}]",
            f"[{color}]{format_percentage(c.return_percentage)}[/{color}]",
            close_date,
        )

    console.print(table)
    console.print(f"\n[dim]Showing {len(rows)} closed trade(s).[/dim]")


@app.command()
def summary() -> None:
    """Display portfolio summary with top gainers/losers."""
    _, service = _get_service()
    try:
        open_pos = service.get_positions()
        closed_pos = service.get_closed_positions()
    except EToroAuthError as exc:
        console.print(f"[bold red]Auth error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    analysis = AnalysisService()
    s: PortfolioSummary = analysis.generate_summary(open_pos, closed_pos)

    console.rule("[bold cyan]Portfolio Summary[/bold cyan]")
    color = pnl_color(s.total_pnl)

    console.print(f"  Total Invested     : [bold]{format_currency(s.total_invested)}[/bold]")
    console.print(f"  Current Value      : [bold]{format_currency(s.total_current_value)}[/bold]")
    console.print(f"  Unrealised P&L     : [bold {color}]{format_currency(s.total_pnl)}[/bold {color}]")
    console.print(f"  Overall Return     : [bold {color}]{format_percentage(s.overall_return_pct)}[/bold {color}]")
    console.print(f"  Open Positions     : {s.positions_count}")
    console.print(f"  Closed Positions   : {s.closed_positions_count}")

    if s.top_gainers:
        console.rule("[green]Top Gainers[/green]")
        for p in s.top_gainers:
            console.print(
                f"  {truncate(p.instrument_name, 22):<22} "
                f"[green]{format_percentage(p.return_percentage)}[/green]  "
                f"{format_currency(p.unrealised_pnl)}"
            )

    if s.top_losers:
        console.rule("[red]Top Losers[/red]")
        for p in s.top_losers:
            console.print(
                f"  {truncate(p.instrument_name, 22):<22} "
                f"[red]{format_percentage(p.return_percentage)}[/red]  "
                f"{format_currency(p.unrealised_pnl)}"
            )


@app.command()
def alerts(
    gain: float = typer.Option(20.0, "--gain", help="Gain alert threshold (%)"),
    loss: float = typer.Option(-10.0, "--loss", help="Loss alert threshold (%)"),
) -> None:
    """Show positions that have breached gain or loss thresholds."""
    _, service = _get_service()
    try:
        open_pos = service.get_positions()
    except EToroAuthError as exc:
        console.print(f"[bold red]Auth error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    analysis = AnalysisService()
    triggered = analysis.check_alerts(open_pos, gain_threshold=gain, loss_threshold=loss)

    if not triggered:
        console.print("[green]No alerts triggered.[/green]")
        return

    for a in triggered:
        color = "green" if a["type"] == "GAIN" else "red"
        console.print(f"[bold {color}][{a['type']}][/bold {color}] {a['message']}")


if __name__ == "__main__":
    app()
