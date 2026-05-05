"""
app/cli.py
──────────
Typer CLI for the Investment Portfolio API.
Run:  python -m app.cli --help
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

# Import broker adapters to trigger self-registration
import app.brokers.upstox  # noqa: F401
import app.brokers.etoro   # noqa: F401

from app.brokers.registry import registry
from app.core.cache import get_cache
from app.core.config import get_settings
from app.services.portfolio_service import PortfolioService

cli = typer.Typer(help="Investment Portfolio API — CLI tool")
console = Console()


def _svc() -> PortfolioService:
    return PortfolioService(registry=registry, cache=get_cache())


# ── brokers ───────────────────────────────────────────────────────────────────

@cli.command("brokers")
def list_brokers():
    """List all registered broker adapters."""
    svc = _svc()
    table = Table(title="Registered Brokers")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Configured", style="green")
    for b in svc.list_brokers():
        table.add_row(b["id"], b["name"], "[green]Yes[/green]" if b["configured"] else "[red]No[/red]")
    console.print(table)


# ── holdings ──────────────────────────────────────────────────────────────────

@cli.command("holdings")
def holdings(broker: str = typer.Argument(..., help="Broker ID, e.g. upstox")):
    """Fetch and display holdings for a broker."""
    svc = _svc()
    data = svc.get_holdings(broker)
    if not data:
        console.print(f"[yellow]No holdings found for {broker}[/yellow]")
        return
    table = Table(title=f"{broker.title()} Holdings")
    table.add_column("Symbol", style="cyan")
    table.add_column("Exchange")
    table.add_column("Qty", justify="right")
    table.add_column("Avg Price", justify="right")
    table.add_column("Last Price", justify="right")
    table.add_column("P&L", justify="right")
    table.add_column("Return %", justify="right")
    for h in data:
        pnl_color = "green" if h.unrealised_pnl >= 0 else "red"
        table.add_row(
            h.trading_symbol,
            h.exchange,
            str(h.quantity),
            f"{h.average_price:.2f}",
            f"{h.last_price:.2f}",
            f"[{pnl_color}]{h.unrealised_pnl:.2f}[/{pnl_color}]",
            f"[{pnl_color}]{h.return_pct:.2f}%[/{pnl_color}]",
        )
    console.print(table)


# ── summary ───────────────────────────────────────────────────────────────────

@cli.command("summary")
def summary(broker: str = typer.Argument(..., help="Broker ID, e.g. upstox")):
    """Display portfolio summary for a broker."""
    svc = _svc()
    s = svc.get_summary(broker)
    pnl_color = "green" if s.total_unrealised_pnl >= 0 else "red"
    console.print(f"\n[bold]Portfolio Summary — {s.broker.title()}[/bold]")
    console.print(f"  Holdings:        {s.holdings_count}")
    console.print(f"  Positions:       {s.positions_count}")
    console.print(f"  Invested:        {s.total_invested:,.2f}")
    console.print(f"  Current Value:   {s.total_current_value:,.2f}")
    console.print(f"  Unrealised P&L:  [{pnl_color}]{s.total_unrealised_pnl:,.2f}[/{pnl_color}]")
    console.print(f"  Return:          [{pnl_color}]{s.overall_return_pct:.2f}%[/{pnl_color}]\n")


# ── serve ─────────────────────────────────────────────────────────────────────

@cli.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to bind"),
    reload: bool = typer.Option(False, help="Enable hot-reload (development only)"),
):
    """Start the FastAPI server with uvicorn."""
    import uvicorn

    settings = get_settings()
    console.print(f"[bold green]Starting server on {host}:{port}[/bold green]")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    cli()
