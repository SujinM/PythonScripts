"""
CLI entry point — Upstox Investment Analyzer.

Commands
--------
  auth            Authenticate via OAuth2 and obtain an access token.
  request-token   Request an Access Token directly (v3, no browser redirect).
  holdings        Display long-term holdings with P&L breakdown.
  positions       Display current open positions.
  trades          Display today's executed trades.
  summary         Full portfolio report (holdings + positions + trades).
  alerts          Show holdings that breached gain/loss thresholds.
  analytics       Read-only market analytics (Analytics Token required).

Usage
-----
  python -m app                         # shows help
  python -m app auth
  python -m app request-token
  python -m app holdings --top 10
  python -m app summary
  python -m app alerts --gain 25 --loss -15
  python -m app analytics ltp "NSE_EQ|INE009A01021"
"""

import sys
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.rule import Rule
from rich.table import Table

from app.api.analytics_client import AnalyticsAPIError, AnalyticsClient, AnalyticsTokenError
from app.api.upstox_client import UpstoxAPIError, UpstoxAuthError, UpstoxClient
from app.core.config import Config, ConfigError
from app.core.logger import get_logger
from app.services.analysis_service import AnalysisService
from app.services.analytics_service import AnalyticsService
from app.services.portfolio_service import PortfolioService
from app.utils.helpers import format_currency, format_percentage, pnl_color, truncate

# ---------------------------------------------------------------------------
app = typer.Typer(
    name="upstox-analyzer",
    help="Upstox Investment Portfolio Analyzer  —  Phase 1",
    add_completion=False,
    no_args_is_help=True,
)

# Analytics sub-app — uses the long-lived Analytics Token (read-only)
analytics_app = typer.Typer(
    name="analytics",
    help=(
        "Read-only market analytics using the Upstox Analytics Token.\n\n"
        "Requires UPSTOX_ANALYTICS_TOKEN in your .env file.\n"
        "Generate one from the Upstox Developer Apps page (1-year validity)."
    ),
    no_args_is_help=True,
)
app.add_typer(analytics_app, name="analytics")

console = Console()
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bootstrap(token: Optional[str]) -> tuple[PortfolioService, AnalysisService]:
    """
    Load config, build the client, and return initialized services.
    Exits with a friendly message on configuration or auth errors.
    """
    try:
        config = Config()
    except ConfigError as exc:
        console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    client = UpstoxClient(config)

    # Token precedence: CLI flag > .env UPSTOX_ACCESS_TOKEN
    effective_token = token or config.access_token
    if not effective_token:
        console.print(
            "[bold red]No access token found.[/bold red]  "
            "Run [cyan]python -m app auth[/cyan] first, then add the token to your .env file."
        )
        raise typer.Exit(1)

    client.set_access_token(effective_token)

    portfolio_svc = PortfolioService(client, cache_ttl=config.cache_ttl_seconds)
    analysis_svc = AnalysisService()
    return portfolio_svc, analysis_svc


def _handle_api_error(exc: UpstoxAPIError) -> None:
    """Print a user-friendly error and exit."""
    if isinstance(exc, UpstoxAuthError):
        console.print(
            f"[bold red]Authentication error [{exc.status_code}]:[/bold red] {exc}\n"
            "Your access token may have expired.  Run [cyan]python -m app auth[/cyan] to refresh it."
        )
    else:
        console.print(f"[bold red]API error [{exc.status_code}]:[/bold red] {exc}")
    raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def auth() -> None:
    """Authenticate with Upstox via OAuth2 and obtain an access token."""
    try:
        config = Config()
    except ConfigError as exc:
        console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    client = UpstoxClient(config)
    url = client.get_authorization_url()

    console.print(Rule("[bold cyan]Upstox Authentication[/bold cyan]"))
    console.print("\nOpen this URL in your browser to authorize the application:\n")
    console.print(f"[link={url}]{url}[/link]\n")

    typer.launch(url)

    auth_code = typer.prompt("Paste the authorization code from the redirect URL")

    try:
        token = client.exchange_code_for_token(auth_code.strip())
    except UpstoxAPIError as exc:
        _handle_api_error(exc)
        return  # unreachable — _handle_api_error exits

    console.print(
        "\n[bold green]Authentication successful![/bold green]\n"
        "Add the following line to your [cyan].env[/cyan] file:\n"
    )
    # Display instruction only — do NOT log the token
    console.print(f"  UPSTOX_ACCESS_TOKEN=<your-token-here>\n")
    console.print("[dim](The token has been printed to stdout above — copy it now.)[/dim]")
    # Print actual token last so the user can copy it easily
    print(f"\nUPSTOX_ACCESS_TOKEN={token}\n")


@app.command()
def holdings(
    token: Optional[str] = typer.Option(
        None, "--token", "-t", help="Override UPSTOX_ACCESS_TOKEN", show_default=False
    ),
    top: int = typer.Option(5, "--top", help="Number of top/bottom holdings to display"),
) -> None:
    """Display long-term holdings with P&L analysis."""
    portfolio_svc, analysis_svc = _bootstrap(token)

    try:
        raw_holdings = portfolio_svc.get_holdings()
    except UpstoxAPIError as exc:
        _handle_api_error(exc)
        return

    summary = analysis_svc.generate_summary(raw_holdings, [], top_n=top)

    # ── Summary panel ──────────────────────────────────────────────────
    console.print(Rule("[bold]Holdings Summary[/bold]"))
    col = pnl_color(summary.total_pnl)
    console.print(f"  Holdings       : [cyan]{summary.holdings_count}[/cyan]")
    console.print(f"  Total Invested : [cyan]{format_currency(summary.total_invested)}[/cyan]")
    console.print(f"  Current Value  : [cyan]{format_currency(summary.total_current_value)}[/cyan]")
    console.print(f"  P&L            : [{col}]{format_currency(summary.total_pnl)}[/{col}]")
    console.print(
        f"  Return         : [{col}]{format_percentage(summary.overall_return_pct)}[/{col}]"
    )
    console.print()

    # ── Holdings table ─────────────────────────────────────────────────
    if not raw_holdings:
        console.print("[italic dim]No holdings found.[/italic dim]")
        return

    table = Table(title="Holdings", box=box.ROUNDED, show_lines=False, highlight=True)
    table.add_column("Symbol", style="cyan", min_width=14)
    table.add_column("Qty", justify="right")
    table.add_column("Avg Price", justify="right")
    table.add_column("LTP", justify="right")
    table.add_column("Invested", justify="right")
    table.add_column("Current", justify="right")
    table.add_column("P&L", justify="right")
    table.add_column("Return %", justify="right")

    for h in sorted(raw_holdings, key=lambda x: x.current_value, reverse=True):
        c = pnl_color(h.unrealised_pnl)
        table.add_row(
            truncate(h.trading_symbol),
            str(h.quantity),
            format_currency(h.average_price),
            format_currency(h.last_price),
            format_currency(h.invested_value),
            format_currency(h.current_value),
            f"[{c}]{format_currency(h.unrealised_pnl)}[/{c}]",
            f"[{c}]{format_percentage(h.return_percentage)}[/{c}]",
        )

    console.print(table)

    # ── Ranked lists ───────────────────────────────────────────────────
    if summary.top_gainers:
        console.print("\n[bold green]Top Gainers[/bold green]")
        for h in summary.top_gainers:
            console.print(
                f"  {h.trading_symbol:<20} [green]{format_percentage(h.return_percentage)}[/green]"
            )

    if summary.top_losers:
        console.print("\n[bold red]Top Losers[/bold red]")
        for h in summary.top_losers:
            console.print(
                f"  {h.trading_symbol:<20} [red]{format_percentage(h.return_percentage)}[/red]"
            )

    console.print()


@app.command()
def positions(
    token: Optional[str] = typer.Option(
        None, "--token", "-t", help="Override UPSTOX_ACCESS_TOKEN", show_default=False
    ),
) -> None:
    """Display current open positions with P&L."""
    portfolio_svc, analysis_svc = _bootstrap(token)

    try:
        raw_positions = portfolio_svc.get_positions()
    except UpstoxAPIError as exc:
        _handle_api_error(exc)
        return

    pnl_data = analysis_svc.analyse_positions_pnl(raw_positions)

    console.print(Rule("[bold]Open Positions[/bold]"))
    c = pnl_color(pnl_data["total_pnl"])
    console.print(f"  Positions    : [cyan]{pnl_data['positions_count']}[/cyan]")
    console.print(f"  Total P&L    : [{c}]{format_currency(pnl_data['total_pnl'])}[/{c}]")
    console.print(f"  Realised     : {format_currency(pnl_data['realised'])}")
    console.print(f"  Unrealised   : {format_currency(pnl_data['unrealised'])}")
    console.print()

    if not raw_positions:
        console.print("[italic dim]No open positions.[/italic dim]")
        return

    table = Table(title="Positions", box=box.ROUNDED, highlight=True)
    table.add_column("Symbol", style="cyan", min_width=14)
    table.add_column("Exchange")
    table.add_column("Product")
    table.add_column("Qty", justify="right")
    table.add_column("Buy Avg", justify="right")
    table.add_column("P&L", justify="right")
    table.add_column("Realised", justify="right")
    table.add_column("Unrealised", justify="right")

    for p in raw_positions:
        c = pnl_color(p.pnl)
        table.add_row(
            truncate(p.trading_symbol),
            p.exchange,
            p.product,
            str(p.quantity),
            format_currency(p.buy_price),
            f"[{c}]{format_currency(p.pnl)}[/{c}]",
            format_currency(p.realised),
            format_currency(p.unrealised),
        )

    console.print(table)


@app.command()
def trades(
    token: Optional[str] = typer.Option(
        None, "--token", "-t", help="Override UPSTOX_ACCESS_TOKEN", show_default=False
    ),
) -> None:
    """Display today's executed trades."""
    portfolio_svc, analysis_svc = _bootstrap(token)

    try:
        raw_trades = portfolio_svc.get_trades()
    except UpstoxAPIError as exc:
        _handle_api_error(exc)
        return

    vol = analysis_svc.analyse_trade_volume(raw_trades)

    console.print(Rule("[bold]Today's Trades[/bold]"))
    console.print(f"  Total Trades : [cyan]{vol['total_trades']}[/cyan]")
    console.print(
        f"  Buys         : [green]{vol['buy_trades']}[/green]  "
        f"({format_currency(vol['buy_value'])})"
    )
    console.print(
        f"  Sells        : [red]{vol['sell_trades']}[/red]  "
        f"({format_currency(vol['sell_value'])})"
    )
    console.print()

    if not raw_trades:
        console.print("[italic dim]No trades executed today.[/italic dim]")
        return

    table = Table(title="Trades", box=box.ROUNDED, highlight=True)
    table.add_column("Symbol", style="cyan", min_width=14)
    table.add_column("Type")
    table.add_column("Product")
    table.add_column("Qty", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Value", justify="right")
    table.add_column("Time")

    for t in raw_trades:
        c = "green" if t.transaction_type == "BUY" else "red"
        table.add_row(
            truncate(t.trading_symbol),
            f"[{c}]{t.transaction_type}[/{c}]",
            t.product,
            str(t.quantity),
            format_currency(t.price),
            format_currency(t.trade_value),
            t.trade_date.strftime("%H:%M:%S") if t.trade_date else "—",
        )

    console.print(table)


@app.command()
def summary(
    token: Optional[str] = typer.Option(
        None, "--token", "-t", help="Override UPSTOX_ACCESS_TOKEN", show_default=False
    ),
    top: int = typer.Option(5, "--top", help="Number of top/bottom holdings to display"),
) -> None:
    """Full portfolio report: holdings, positions, and today's trades."""
    portfolio_svc, analysis_svc = _bootstrap(token)

    try:
        raw_holdings = portfolio_svc.get_holdings()
        raw_positions = portfolio_svc.get_positions()
        raw_trades = portfolio_svc.get_trades()
    except UpstoxAPIError as exc:
        _handle_api_error(exc)
        return

    port_summary = analysis_svc.generate_summary(raw_holdings, raw_positions, raw_trades, top_n=top)
    pos_pnl = analysis_svc.analyse_positions_pnl(raw_positions)
    trade_vol = analysis_svc.analyse_trade_volume(raw_trades)

    console.print(Rule("[bold underline]Full Portfolio Report[/bold underline]"))

    # Holdings
    c1 = pnl_color(port_summary.total_pnl)
    console.print("\n[bold]Long-Term Holdings[/bold]")
    console.print(f"  Count          : [cyan]{port_summary.holdings_count}[/cyan]")
    console.print(f"  Invested       : [cyan]{format_currency(port_summary.total_invested)}[/cyan]")
    console.print(f"  Current Value  : [cyan]{format_currency(port_summary.total_current_value)}[/cyan]")
    console.print(f"  P&L            : [{c1}]{format_currency(port_summary.total_pnl)}[/{c1}]")
    console.print(
        f"  Return         : [{c1}]{format_percentage(port_summary.overall_return_pct)}[/{c1}]"
    )

    # Positions
    c2 = pnl_color(pos_pnl["total_pnl"])
    console.print("\n[bold]Open Positions[/bold]")
    console.print(f"  Count          : [cyan]{pos_pnl['positions_count']}[/cyan]")
    console.print(f"  Total P&L      : [{c2}]{format_currency(pos_pnl['total_pnl'])}[/{c2}]")
    console.print(f"  Realised       : {format_currency(pos_pnl['realised'])}")
    console.print(f"  Unrealised     : {format_currency(pos_pnl['unrealised'])}")

    # Trades
    console.print("\n[bold]Today's Activity[/bold]")
    console.print(f"  Trades         : [cyan]{trade_vol['total_trades']}[/cyan]")
    console.print(
        f"  Buy Value      : [green]{format_currency(trade_vol['buy_value'])}[/green]"
    )
    console.print(
        f"  Sell Value     : [red]{format_currency(trade_vol['sell_value'])}[/red]"
    )

    console.print()


@app.command()
def alerts(
    token: Optional[str] = typer.Option(
        None, "--token", "-t", help="Override UPSTOX_ACCESS_TOKEN", show_default=False
    ),
    gain: float = typer.Option(20.0, "--gain", help="Profit alert threshold (%)"),
    loss: float = typer.Option(-10.0, "--loss", help="Loss alert threshold (%)"),
) -> None:
    """Show holdings that have breached profit or loss thresholds."""
    portfolio_svc, analysis_svc = _bootstrap(token)

    try:
        raw_holdings = portfolio_svc.get_holdings()
    except UpstoxAPIError as exc:
        _handle_api_error(exc)
        return

    triggered = analysis_svc.check_alerts(raw_holdings, gain_threshold=gain, loss_threshold=loss)

    console.print(Rule("[bold]Portfolio Alerts[/bold]"))
    console.print(
        f"  Thresholds: [green]Gain ≥ {format_percentage(gain)}[/green]  |  "
        f"[red]Loss ≤ {format_percentage(loss)}[/red]\n"
    )

    if not triggered:
        console.print("[italic dim]No alerts triggered.[/italic dim]")
        return

    table = Table(title="Triggered Alerts", box=box.ROUNDED, highlight=True)
    table.add_column("Symbol", style="cyan", min_width=14)
    table.add_column("Return %", justify="right")
    table.add_column("Alert Type")

    for alert in triggered:
        is_profit = alert["alert_type"] == "PROFIT_TARGET"
        c = "green" if is_profit else "red"
        table.add_row(
            str(alert["symbol"]),
            f"[{c}]{format_percentage(float(alert['return_pct']))}[/{c}]",
            f"[{c}]{alert['alert_type']}[/{c}]",
        )

    console.print(table)


# ===========================================================================
# Analytics sub-app commands
# Uses the Analytics Token — no OAuth2 required, strictly read-only.
# ===========================================================================


def _bootstrap_analytics() -> AnalyticsService:
    """
    Load config, build AnalyticsClient, return AnalyticsService.
    Exits with a friendly message if the analytics token is missing.
    """
    try:
        config = Config()
    except ConfigError as exc:
        console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    try:
        client = AnalyticsClient(config)
    except AnalyticsTokenError as exc:
        console.print(f"[bold red]Analytics token missing:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    return AnalyticsService(client, cache_ttl=config.cache_ttl_seconds)


def _handle_analytics_error(exc: AnalyticsAPIError) -> None:
    console.print(f"[bold red]Analytics API error [{exc.status_code}]:[/bold red] {exc}")
    raise typer.Exit(1)


# ---------------------------------------------------------------------------
# analytics ltp
# ---------------------------------------------------------------------------


@analytics_app.command("ltp")
def analytics_ltp(
    instrument_keys: list[str] = typer.Argument(
        ..., help="Instrument keys, e.g. NSE_EQ|INE009A01021"
    ),
) -> None:
    """Last Traded Price for one or more instruments."""
    svc = _bootstrap_analytics()
    try:
        results = svc.get_ltp(instrument_keys)
    except AnalyticsAPIError as exc:
        _handle_analytics_error(exc)
        return

    table = Table(title="Last Traded Price", box=box.ROUNDED, highlight=True)
    table.add_column("Instrument Key", style="cyan")
    table.add_column("Symbol")
    table.add_column("LTP", justify="right")

    for q in results:
        table.add_row(q.instrument_token, q.trading_symbol, format_currency(q.last_price))

    console.print(table)


# ---------------------------------------------------------------------------
# analytics quotes
# ---------------------------------------------------------------------------


@analytics_app.command("quotes")
def analytics_quotes(
    instrument_keys: list[str] = typer.Argument(
        ..., help="Instrument keys, e.g. NSE_EQ|INE009A01021"
    ),
) -> None:
    """Full market quotes with OHLCV, circuit limits, and 52-week range."""
    svc = _bootstrap_analytics()
    try:
        results = svc.get_quotes(instrument_keys)
    except AnalyticsAPIError as exc:
        _handle_analytics_error(exc)
        return

    for q in results:
        c = pnl_color(q.net_change)
        console.print(Rule(f"[bold cyan]{q.trading_symbol}[/bold cyan] ({q.exchange})"))
        console.print(f"  LTP            : [{c}]{format_currency(q.last_price)}[/{c}]")
        console.print(
            f"  Change         : [{c}]{format_currency(q.net_change)} "
            f"({format_percentage(q.net_change_pct)})[/{c}]"
        )
        console.print(
            f"  OHLC           : {format_currency(q.open_price)} / "
            f"{format_currency(q.high_price)} / "
            f"{format_currency(q.low_price)} / "
            f"{format_currency(q.close_price)}"
        )
        console.print(f"  Volume         : [cyan]{q.volume:,}[/cyan]")
        console.print(f"  Avg Price      : {format_currency(q.average_price)}")
        console.print(f"  Bid / Ask      : {format_currency(q.bid_price)} / {format_currency(q.ask_price)}")
        console.print(
            f"  Circuit        : [red]{format_currency(q.lower_circuit_limit)}[/red] "
            f"— [green]{format_currency(q.upper_circuit_limit)}[/green]"
        )
        console.print(
            f"  52W H/L        : [green]{format_currency(q.week_52_high)}[/green] "
            f"/ [red]{format_currency(q.week_52_low)}[/red]"
        )
        console.print()


# ---------------------------------------------------------------------------
# analytics ohlc
# ---------------------------------------------------------------------------

# Friendly aliases → API interval codes accepted by /v3/market-quote/ohlc
_OHLC_INTERVAL_ALIASES: dict[str, str] = {
    "day": "1d",
    "1day": "1d",
    "1minute": "I1",
    "1min": "I1",
    "30minute": "I30",
    "30min": "I30",
}


@analytics_app.command("ohlc")
def analytics_ohlc(
    instrument_keys: list[str] = typer.Argument(
        ..., help="Instrument keys, e.g. NSE_EQ|INE009A01021"
    ),
    interval: str = typer.Option(
        "1d",
        "--interval",
        "-i",
        help="Interval: 1d (day), I1 (1 min), I30 (30 min). Aliases: 30minute, 1minute, day.",
    ),
) -> None:
    """OHLC quotes for one or more instruments."""
    svc = _bootstrap_analytics()
    api_interval = _OHLC_INTERVAL_ALIASES.get(interval, interval)
    try:
        results = svc.get_ohlc(instrument_keys, interval=api_interval)
    except AnalyticsAPIError as exc:
        _handle_analytics_error(exc)
        return

    table = Table(title=f"OHLC  [{api_interval}]", box=box.ROUNDED, highlight=True)
    table.add_column("Symbol", style="cyan")
    table.add_column("Open", justify="right")
    table.add_column("High", justify="right", style="green")
    table.add_column("Low", justify="right", style="red")
    table.add_column("Close", justify="right")
    table.add_column("LTP", justify="right")
    table.add_column("vs Open", justify="right")

    for q in results:
        c = pnl_color(q.change_from_open)
        table.add_row(
            truncate(q.trading_symbol),
            format_currency(q.open_price),
            format_currency(q.high_price),
            format_currency(q.low_price),
            format_currency(q.close_price),
            f"[{c}]{format_currency(q.last_price)}[/{c}]",
            f"[{c}]{format_percentage(q.change_from_open / q.open_price * 100 if q.open_price else 0)}[/{c}]",
        )

    console.print(table)


# ---------------------------------------------------------------------------
# analytics candles
# ---------------------------------------------------------------------------


@analytics_app.command("candles")
def analytics_candles(
    instrument_key: str = typer.Argument(..., help="Instrument key, e.g. NSE_EQ|INE009A01021"),
    interval: str = typer.Option("day", "--interval", "-i", help="1minute|30minute|day|week|month"),
    from_date: str = typer.Option(..., "--from", help="Start date YYYY-MM-DD"),
    to_date: str = typer.Option(..., "--to", help="End date YYYY-MM-DD"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max rows to display"),
) -> None:
    """Historical OHLCV candle data for an instrument."""
    svc = _bootstrap_analytics()
    try:
        candles = svc.get_historical_candles(instrument_key, interval, from_date, to_date)
    except AnalyticsAPIError as exc:
        _handle_analytics_error(exc)
        return

    if not candles:
        console.print("[italic dim]No candles returned for the given range.[/italic dim]")
        return

    console.print(
        Rule(
            f"[bold]{truncate(instrument_key, 30)}[/bold]  "
            f"[dim]{interval} candles  {from_date} → {to_date}[/dim]"
        )
    )
    console.print(f"  Total candles : [cyan]{len(candles)}[/cyan]  (showing last {min(limit, len(candles))})\n")

    table = Table(box=box.SIMPLE, highlight=True)
    table.add_column("Date/Time", style="dim")
    table.add_column("Open", justify="right")
    table.add_column("High", justify="right", style="green")
    table.add_column("Low", justify="right", style="red")
    table.add_column("Close", justify="right")
    table.add_column("Volume", justify="right")
    table.add_column("OI", justify="right")
    table.add_column("Dir")

    for candle in candles[-limit:]:
        c = "green" if candle.is_bullish else "red"
        table.add_row(
            candle.timestamp.strftime("%Y-%m-%d %H:%M") if candle.timestamp else "—",
            format_currency(candle.open_price),
            format_currency(candle.high_price),
            format_currency(candle.low_price),
            f"[{c}]{format_currency(candle.close_price)}[/{c}]",
            f"{candle.volume:,}",
            f"{candle.open_interest:,}",
            f"[{c}]{'▲' if candle.is_bullish else '▼'}[/{c}]",
        )

    console.print(table)


# ---------------------------------------------------------------------------
# analytics market-status
# ---------------------------------------------------------------------------


@analytics_app.command("market-status")
def analytics_market_status(
    exchange: Optional[str] = typer.Option(
        None, "--exchange", "-e", help="Filter by exchange: NSE, BSE, MCX, etc."
    ),
) -> None:
    """Current trading status for all market segments."""
    svc = _bootstrap_analytics()
    try:
        statuses = svc.get_market_status(exchange)
    except AnalyticsAPIError as exc:
        _handle_analytics_error(exc)
        return

    if not statuses:
        console.print("[italic dim]No market status data returned.[/italic dim]")
        return

    table = Table(title="Market Status", box=box.ROUNDED, highlight=True)
    table.add_column("Exchange", style="cyan")
    table.add_column("Segment")
    table.add_column("Status")

    for s in statuses:
        c = "green" if s.is_open else "red"
        table.add_row(s.exchange, s.segment, f"[{c}]{s.trading_status}[/{c}]")

    console.print(table)


# ---------------------------------------------------------------------------
# analytics option-chain
# ---------------------------------------------------------------------------


@analytics_app.command("option-chain")
def analytics_option_chain(
    instrument_key: str = typer.Argument(
        ..., help="Underlying key, e.g. NSE_INDEX|Nifty 50"
    ),
    expiry: str = typer.Option(..., "--expiry", "-e", help="Expiry date YYYY-MM-DD"),
    strikes: int = typer.Option(10, "--strikes", "-n", help="ATM strikes to show on each side"),
) -> None:
    """Put/Call option chain for an underlying and expiry."""
    svc = _bootstrap_analytics()
    try:
        chain = svc.get_option_chain(instrument_key, expiry)
    except AnalyticsAPIError as exc:
        _handle_analytics_error(exc)
        return

    if not chain:
        console.print("[italic dim]No option chain data returned.[/italic dim]")
        return

    # Find ATM strike (closest to spot)
    spot = chain[0].underlying_spot_price if chain else 0.0
    sorted_chain = sorted(chain, key=lambda e: abs(e.strike_price - spot))
    atm_entries = sorted_chain[: strikes * 2]
    display = sorted(atm_entries, key=lambda e: e.strike_price)

    console.print(Rule(f"[bold]Option Chain[/bold]  [dim]{instrument_key} | Expiry: {expiry}[/dim]"))
    console.print(f"  Spot Price : [cyan]{format_currency(spot)}[/cyan]\n")

    table = Table(box=box.SIMPLE, highlight=True)
    # Call side (left) | Strike | Put side (right)
    table.add_column("CE LTP", justify="right", style="green")
    table.add_column("CE IV", justify="right")
    table.add_column("CE OI", justify="right")
    table.add_column("Strike", justify="center", style="bold cyan")
    table.add_column("PE OI", justify="right")
    table.add_column("PE IV", justify="right")
    table.add_column("PE LTP", justify="right", style="red")

    for entry in display:
        ce = entry.call
        pe = entry.put
        atm_marker = " ◀ ATM" if abs(entry.strike_price - spot) == min(
            abs(e.strike_price - spot) for e in display
        ) else ""
        table.add_row(
            format_currency(ce.ltp) if ce else "—",
            f"{ce.iv:.1f}%" if ce else "—",
            f"{ce.open_interest:,}" if ce else "—",
            f"{entry.strike_price:,.0f}{atm_marker}",
            f"{pe.open_interest:,}" if pe else "—",
            f"{pe.iv:.1f}%" if pe else "—",
            format_currency(pe.ltp) if pe else "—",
        )

    console.print(table)


# ---------------------------------------------------------------------------
# analytics option-greeks
# ---------------------------------------------------------------------------


@analytics_app.command("option-greeks")
def analytics_option_greeks(
    instrument_key: str = typer.Argument(
        ..., help="Underlying key, e.g. NSE_INDEX|Nifty 50"
    ),
    expiry: str = typer.Option(..., "--expiry", "-e", help="Expiry date YYYY-MM-DD"),
    option_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Filter: CE or PE"
    ),
) -> None:
    """Option Greeks (Δ Γ Θ Vega ρ IV) for all contracts of an expiry."""
    svc = _bootstrap_analytics()
    try:
        greeks_list = svc.get_option_greeks(instrument_key, expiry)
    except AnalyticsAPIError as exc:
        _handle_analytics_error(exc)
        return

    if option_type:
        greeks_list = [g for g in greeks_list if g.option_type.upper() == option_type.upper()]

    if not greeks_list:
        console.print("[italic dim]No Greeks data returned.[/italic dim]")
        return

    table = Table(title=f"Option Greeks  [{expiry}]", box=box.ROUNDED, highlight=True)
    table.add_column("Symbol", style="cyan", min_width=20)
    table.add_column("Type")
    table.add_column("Strike", justify="right")
    table.add_column("IV %", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("Gamma", justify="right")
    table.add_column("Theta", justify="right")
    table.add_column("Vega", justify="right")
    table.add_column("Rho", justify="right")
    table.add_column("Theor. Price", justify="right")

    for g in greeks_list:
        c = "green" if g.option_type == "CE" else "red"
        table.add_row(
            truncate(g.trading_symbol, 22),
            f"[{c}]{g.option_type}[/{c}]",
            f"{g.strike_price:,.0f}",
            f"{g.iv:.2f}",
            f"{g.delta:+.4f}",
            f"{g.gamma:.6f}",
            f"{g.theta:+.4f}",
            f"{g.vega:.4f}",
            f"{g.rho:+.4f}",
            format_currency(g.theoretical_price),
        )

    console.print(table)


# ---------------------------------------------------------------------------
# analytics search
# ---------------------------------------------------------------------------


@analytics_app.command("search")
def analytics_search(
    query: str = typer.Argument(..., help="Search term: symbol, name, or ISIN"),
    asset_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Filter: equity|futures|options|index"
    ),
) -> None:
    """Search for instruments by name, symbol, or ISIN."""
    svc = _bootstrap_analytics()
    try:
        results = svc.search_instruments(query, asset_type=asset_type)
    except AnalyticsAPIError as exc:
        _handle_analytics_error(exc)
        return

    if not results:
        console.print(f"[italic dim]No results for '{query}'.[/italic dim]")
        return

    table = Table(title=f"Instrument Search: '{query}'", box=box.ROUNDED, highlight=True)
    table.add_column("Instrument Key", style="cyan")
    table.add_column("Symbol")
    table.add_column("Name")
    table.add_column("Exchange")
    table.add_column("Type")
    table.add_column("ISIN")
    table.add_column("Lot", justify="right")

    for r in results:
        table.add_row(
            r.instrument_key,
            r.trading_symbol,
            truncate(r.name, 25),
            r.exchange,
            r.instrument_type,
            r.isin or "—",
            str(r.lot_size),
        )

    console.print(table)


# ---------------------------------------------------------------------------
# analytics feed-url
# ---------------------------------------------------------------------------


@analytics_app.command("feed-url")
def analytics_feed_url() -> None:
    """
    Obtain a signed WebSocket URL for the V3 Market Data Feed.

    Connect the returned WSS URL with any WebSocket client to receive
    real-time Level-1 and Level-2 streaming market data.
    """
    svc = _bootstrap_analytics()
    try:
        auth = svc.authorize_market_feed()
    except AnalyticsAPIError as exc:
        _handle_analytics_error(exc)
        return

    console.print(Rule("[bold]Market Data Feed V3 — Authorization[/bold]"))
    console.print("\n  [bold green]WSS URL (valid for a short window):[/bold green]\n")
    print(auth.authorized_redirect_uri)
    console.print(
        "\n[dim]Connect with any WebSocket client, e.g.:\n"
        "  wscat -c '<url>'\n"
        "  python -m websockets '<url>'[/dim]\n"
    )


# ---------------------------------------------------------------------------
# analytics brokerage
# ---------------------------------------------------------------------------


@analytics_app.command("brokerage")
def analytics_brokerage(
    instrument_token: str = typer.Argument(..., help="Instrument key, e.g. NSE_EQ|INE009A01021"),
    qty: int = typer.Option(..., "--qty", "-q", help="Number of shares"),
    price: float = typer.Option(..., "--price", "-p", help="Trade price"),
    product: str = typer.Option("D", "--product", help="D=Delivery I=Intraday CO OCO"),
    tx: str = typer.Option("BUY", "--tx", help="BUY or SELL"),
    exchange: str = typer.Option("NSE", "--exchange", "-x", help="NSE|BSE|MCX"),
) -> None:
    """Calculate brokerage and statutory charges for a hypothetical trade."""
    svc = _bootstrap_analytics()
    try:
        detail = svc.get_brokerage(
            instrument_token=instrument_token,
            quantity=qty,
            price=price,
            product=product,
            transaction_type=tx.upper(),
            exchange=exchange.upper(),
        )
    except AnalyticsAPIError as exc:
        _handle_analytics_error(exc)
        return

    console.print(Rule("[bold]Brokerage Calculator[/bold]"))
    console.print(f"  Instrument     : [cyan]{instrument_token}[/cyan]")
    console.print(f"  Trade          : [cyan]{tx.upper()} {qty} × {format_currency(price)}[/cyan]")
    console.print(f"  Trade Value    : {format_currency(detail.trade_value)}")
    console.print()
    console.print(f"  Brokerage      : {format_currency(detail.brokerage)}")
    console.print(f"  STT / CTT      : {format_currency(detail.stt_ctt)}")
    console.print(f"  Exchange Chrgs : {format_currency(detail.exchange_transaction_charges)}")
    console.print(f"  GST            : {format_currency(detail.gst)}")
    console.print(f"  SEBI Charges   : {format_currency(detail.sebi_charges)}")
    console.print(f"  Stamp Duty     : {format_currency(detail.stamp_duty)}")
    console.print(Rule(style="dim"))
    console.print(f"  [bold]Total Charges  : [red]{format_currency(detail.total_charges)}[/red][/bold]")
    console.print(f"  Effective Rate : [red]{format_percentage(detail.effective_rate_pct)}[/red] of trade value")
    console.print(f"  [bold]Net Cost       : {format_currency(detail.net_cost)}[/bold]")
    console.print()


# ---------------------------------------------------------------------------
# request-token  (v3 direct — no browser redirect)
# ---------------------------------------------------------------------------


@app.command("request-token")
def request_token() -> None:
    """
    Request an Access Token directly using your API key and secret.

    Calls POST /v3/login/auth/token/request/{client_id} — no browser needed.
    Requires UPSTOX_API_KEY and UPSTOX_API_SECRET in .env.

    Add the printed token to your .env file:

        UPSTOX_ACCESS_TOKEN=<token>
    """
    try:
        config = Config()
    except ConfigError as exc:
        console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    client = UpstoxClient(config)
    try:
        token = client.request_access_token()
    except UpstoxAPIError as exc:
        _handle_api_error(exc)
        return

    console.print(Rule("[bold cyan]Access Token (v3 Direct)[/bold cyan]"))
    console.print("\n[bold green]Access Token obtained successfully![/bold green]\n")
    console.print("[bold]Add the following line to your [cyan].env[/cyan] file:[/bold]\n")
    print(f"UPSTOX_ACCESS_TOKEN={token}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
