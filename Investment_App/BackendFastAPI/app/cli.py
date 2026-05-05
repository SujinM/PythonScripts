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
from app.services.analysis_service import build_analysis_result, compute_alerts, sector_allocation
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


# ── positions ─────────────────────────────────────────────────────────────────

@cli.command("positions")
def positions(broker: str = typer.Argument(..., help="Broker ID, e.g. upstox or etoro")):
    """Fetch and display open positions for a broker."""
    svc = _svc()
    data = svc.get_positions(broker)
    if not data:
        console.print(f"[yellow]No open positions found for {broker}[/yellow]")
        return
    table = Table(title=f"{broker.title()} Positions")
    table.add_column("Symbol", style="cyan")
    table.add_column("Exchange")
    table.add_column("Product")
    table.add_column("Qty", justify="right")
    table.add_column("Buy Price", justify="right")
    table.add_column("Sell Price", justify="right")
    table.add_column("P&L", justify="right")
    for p in data:
        pnl_color = "green" if p.total_pnl >= 0 else "red"
        table.add_row(
            p.trading_symbol,
            p.exchange,
            p.product,
            str(p.quantity),
            f"{p.buy_price:.2f}",
            f"{p.sell_price:.2f}",
            f"[{pnl_color}]{p.total_pnl:.2f}[/{pnl_color}]",
        )
    console.print(table)


# ── trades ────────────────────────────────────────────────────────────────────

@cli.command("trades")
def trades(broker: str = typer.Argument(..., help="Broker ID, e.g. upstox or etoro")):
    """Fetch and display today's trades for a broker."""
    svc = _svc()
    data = svc.get_trades(broker)
    if not data:
        console.print(f"[yellow]No trades found for {broker} today[/yellow]")
        return
    table = Table(title=f"{broker.title()} Today's Trades")
    table.add_column("Order ID", style="dim")
    table.add_column("Symbol", style="cyan")
    table.add_column("Exchange")
    table.add_column("Side")
    table.add_column("Qty", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Value", justify="right")
    table.add_column("Time")
    for t in data:
        side_color = "green" if t.side.upper() == "BUY" else "red"
        table.add_row(
            t.order_id,
            t.trading_symbol,
            t.exchange,
            f"[{side_color}]{t.side}[/{side_color}]",
            str(t.quantity),
            f"{t.price:.2f}",
            f"{t.trade_value:.2f}",
            t.trade_time or "—",
        )
    console.print(table)


# ── analysis ──────────────────────────────────────────────────────────────────

@cli.command("analysis")
def analysis(broker: str = typer.Argument(..., help="Broker ID, e.g. upstox or etoro")):
    """Show full portfolio analysis: P&L, alerts, and exchange allocation."""
    svc = _svc()
    summary_data = svc.get_summary(broker)
    holdings_data = svc.get_holdings(broker)
    result = build_analysis_result(summary_data, holdings_data)

    pnl_color = "green" if result["total_pnl"] >= 0 else "red"
    console.print(f"\n[bold]Portfolio Analysis — {broker.title()}[/bold]")
    console.print(f"  Holdings:        {result['holdings_count']}")
    console.print(f"  Invested:        {result['total_invested']:,.2f}")
    console.print(f"  Current Value:   {result['total_current_value']:,.2f}")
    console.print(f"  Total P&L:       [{pnl_color}]{result['total_pnl']:,.2f}[/{pnl_color}]")
    console.print(f"  Return:          [{pnl_color}]{result['overall_return_pct']:.2f}%[/{pnl_color}]")

    if result["top_gainers"]:
        console.print("\n  [bold green]Top Gainers[/bold green]")
        for h in result["top_gainers"]:
            console.print(f"    {h['trading_symbol']:12}  +{h['return_pct']:.2f}%  ({h['unrealised_pnl']:,.2f})")

    if result["top_losers"]:
        console.print("\n  [bold red]Top Losers[/bold red]")
        for h in result["top_losers"]:
            console.print(f"    {h['trading_symbol']:12}  {h['return_pct']:.2f}%  ({h['unrealised_pnl']:,.2f})")

    if result["sector_allocation"]:
        console.print("\n  [bold]Exchange Allocation[/bold]")
        for row in result["sector_allocation"]:
            console.print(f"    {row['exchange']:8}  {row['weight_pct']:.2f}%  ({row['current_value']:,.2f})")

    if result["alerts"]:
        console.print(f"\n  [bold yellow]Alerts ({len(result['alerts'])})[/bold yellow]")
        for a in result["alerts"]:
            color = "red" if a["type"] == "LOSS_ALERT" else "green"
            console.print(f"    [{color}]{a['message']}[/{color}]")
    else:
        console.print("\n  [green]No alerts — all holdings within normal range.[/green]")
    console.print()


# ── alerts ────────────────────────────────────────────────────────────────────

@cli.command("alerts")
def alerts(broker: str = typer.Argument(..., help="Broker ID, e.g. upstox or etoro")):
    """Show active P&L alerts (holdings down >5% or up >20%)."""
    svc = _svc()
    holdings_data = svc.get_holdings(broker)
    active = compute_alerts(holdings_data)
    if not active:
        console.print(f"[green]No alerts for {broker} — all holdings within normal range.[/green]")
        return
    table = Table(title=f"{broker.title()} Alerts")
    table.add_column("Symbol", style="cyan")
    table.add_column("Type")
    table.add_column("Return %", justify="right")
    table.add_column("Message")
    for a in active:
        color = "red" if a["type"] == "LOSS_ALERT" else "green"
        table.add_row(
            a["symbol"],
            f"[{color}]{a['type']}[/{color}]",
            f"[{color}]{a['return_pct']:.2f}%[/{color}]",
            a["message"],
        )
    console.print(table)


# ── invalidate ────────────────────────────────────────────────────────────────

@cli.command("invalidate")
def invalidate(broker: str = typer.Argument(..., help="Broker ID, e.g. upstox or etoro")):
    """Invalidate the cached data for a broker (forces a fresh API fetch)."""
    svc = _svc()
    svc.invalidate(broker)
    console.print(f"[green]Cache cleared for broker: {broker}[/green]")


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
