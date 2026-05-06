using ClientConsolApp.Models;
using ClientConsolApp.Services;
using System.Runtime.Versioning;

namespace ClientConsolApp.Display;

/// <summary>
/// Full-screen auto-refreshing live portfolio dashboard.
///
/// Dark theme — navy header, colour-coded P&amp;L, sector bar charts.
/// Press Q or Escape at any time to return to the main menu.
///
/// Layout (top → bottom):
///   ┌ Header bar ─────────────────────────────────────────────┐
///   │ Portfolio Summary panel                                 │
///   │ Top Movers panel  (gainers + losers)                    │
///   │ Active Alerts panel                                     │
///   │ Exchange Allocation bar chart panel                     │
///   └ Footer ─ countdown timer, last-updated, [Q] hint ──────┘
/// </summary>
[SupportedOSPlatform("windows")]
public static class LiveDashboard
{
    // ── Config ────────────────────────────────────────────────────────────
    private const int DefaultRefreshSeconds = 5;
    private const int MinRefreshSeconds     = 3;  // below 3s Upstox rate-limits portfolio endpoints

    // ── Dark colour scheme ────────────────────────────────────────────────
    private const ConsoleColor Accent    = ConsoleColor.Cyan;
    private const ConsoleColor Dim       = ConsoleColor.DarkCyan;
    private const ConsoleColor Label     = ConsoleColor.DarkGray;
    private const ConsoleColor ValueFg   = ConsoleColor.White;
    private const ConsoleColor GainFg    = ConsoleColor.Green;
    private const ConsoleColor LossFg    = ConsoleColor.Red;
    private const ConsoleColor WarnFg    = ConsoleColor.Yellow;
    private const ConsoleColor BarFg     = ConsoleColor.DarkGreen;
    private const ConsoleColor BarEmpty  = ConsoleColor.DarkGray;

    // ── Mutable render state ──────────────────────────────────────────────
    private static int _footerRow  = 0;
    private static int _statusRow  = 0;

    // ── Public entry point ────────────────────────────────────────────────

    /// <summary>
    /// Launches the live dashboard. Blocks until the user presses Q/Escape.
    /// </summary>
    public static async Task RunAsync(
        PortfolioService portfolio,
        string broker,
        int refreshSeconds = DefaultRefreshSeconds,
        // Note: refreshSeconds is clamped to MinRefreshSeconds (3s) internally.
        CancellationToken outerCt = default)
    {
        var origFg      = Console.ForegroundColor;
        var origBg      = Console.BackgroundColor;
        var origTitle   = Console.Title;
        var origCursor  = true;
        try { origCursor = Console.CursorVisible; } catch { }

        // Clamp to minimum — below 3s Upstox portfolio endpoints rate-limit
        refreshSeconds = Math.Max(refreshSeconds, MinRefreshSeconds);

        try
        {
            Console.Title         = $"Sujin's Investment  ─  Live [{broker.ToUpper()}]  [{refreshSeconds}s]";
            Console.CursorVisible = false;

            using var cts = CancellationTokenSource.CreateLinkedTokenSource(outerCt);

            // Background key-listener — exits on Q / Escape
            _ = Task.Run(() =>
            {
                while (!cts.IsCancellationRequested)
                {
                    if (Console.KeyAvailable)
                    {
                        var k = Console.ReadKey(intercept: true);
                        if (k.Key is ConsoleKey.Q or ConsoleKey.Escape)
                        {
                            cts.Cancel();
                            return;
                        }
                    }
                    Thread.Sleep(80);
                }
            }, CancellationToken.None);

            // ── First load ────────────────────────────────────────────────
            SetDark();
            Console.Clear();
            DrawHeader(broker);
            WritAt(4, "  ⏳  Fetching portfolio data...", WarnFg);

            var (analysis, summary, fetchError) = await FetchAsync(portfolio, broker, cts.Token);

            // ── Main loop ─────────────────────────────────────────────────
            while (!cts.IsCancellationRequested)
            {
                var fetchedAt = DateTime.Now;
                Redraw(broker, summary, analysis, fetchedAt, fetchError);

                // Countdown — updates footer once per second
                for (int rem = refreshSeconds; rem >= 0; rem--)
                {
                    if (cts.IsCancellationRequested) break;
                    UpdateFooter(fetchedAt, rem);
                    try   { await Task.Delay(1000, cts.Token); }
                    catch (OperationCanceledException) { break; }
                }

                if (cts.IsCancellationRequested) break;

                // Trigger refresh — invalidate backend cache first so the
                // server fetches live prices from the broker API, not stale cached data.
                PaintStatus("  🔄  Invalidating cache...");
                try
                {
                    await portfolio.InvalidateCacheAsync(broker, cts.Token);
                }
                catch (OperationCanceledException) { break; }
                catch { /* non-fatal — proceed with fetch anyway */ }

                PaintStatus("  ⏳  Fetching live data from broker...");
                try
                {
                    (analysis, summary, fetchError) = await FetchAsync(portfolio, broker, cts.Token);
                }
                catch (OperationCanceledException) { break; }
                catch (Exception ex)
                {
                    fetchError = $"Refresh failed: {ex.Message}";
                    PaintStatus($"  ✗  {fetchError}");
                    await Task.Delay(3_000, CancellationToken.None);
                }
            }
        }
        catch (OperationCanceledException) { /* normal Q/Esc exit */ }
        finally
        {
            Console.CursorVisible = origCursor;
            Console.BackgroundColor = origBg;
            Console.ForegroundColor = origFg;
            Console.Title = origTitle;
            Console.Clear();
        }
    }

    // ── Data fetching ─────────────────────────────────────────────────────

    private static async Task<(AnalysisResult?, PortfolioSummary?, string)> FetchAsync(
        PortfolioService portfolio, string broker, CancellationToken ct)
    {
        try
        {
            // Sequential — NOT parallel.
            //
            // Both /analysis and /summary independently call holdings + positions
            // on the backend. If both arrive simultaneously after a cache-clear,
            // neither benefits from the other's cache → broker API is called twice,
            // triggering eToro 429 rate-limit errors.
            //
            // Sequential fetch: /analysis populates the backend cache first;
            // /summary then hits that warm cache at zero broker-API cost.
            var analysisResp = await portfolio.GetAnalysisAsync(broker, ct).ConfigureAwait(false);
            var summaryResp  = await portfolio.GetSummaryAsync(broker, ct).ConfigureAwait(false);
            return (analysisResp.Data, summaryResp.Data, "");
        }
        catch (OperationCanceledException) { throw; }
        catch (Exception ex) { return (null, null, ex.Message); }
    }

    // ── Full-screen redraw ────────────────────────────────────────────────

    private static void Redraw(
        string broker,
        PortfolioSummary? summary,
        AnalysisResult? analysis,
        DateTime fetchedAt,
        string fetchError)
    {
        SetDark();
        Console.SetCursorPosition(0, 0);
        Console.Clear();

        DrawHeader(broker);
        int row = 3;

        if (!string.IsNullOrEmpty(fetchError))
        {
            WritAt(row++, $"  ✗  {fetchError}", LossFg);
            row++;
        }

        row = DrawSummaryPanel(summary, row);
        row = DrawMoversPanel(analysis, row);
        row = DrawAlertsPanel(analysis?.Alerts ?? [], row);
        row = DrawAllocationPanel(analysis?.SectorAllocation ?? [], row);

        // Reserve footer rows
        _statusRow = row + 1;
        _footerRow = row + 2;

        // Draw footer separator
        try
        {
            Console.SetCursorPosition(0, _footerRow - 1);
            Writ("  " + new string('═', W - 4), ConsoleColor.DarkBlue);
            Console.WriteLine();
        }
        catch { /* console too small */ }

        UpdateFooter(fetchedAt, 0);
    }

    // ── Panel: Header ─────────────────────────────────────────────────────

    private static void DrawHeader(string broker)
    {
        int w = W;
        string left  = "  ● SUJIN'S INVESTMENT   LIVE DASHBOARD";
        string right = $"Broker: {broker.ToUpper()}   {DateTime.Now:HH:mm:ss}  ";
        int gap = Math.Max(1, w - left.Length - right.Length);
        string bar = (left + new string(' ', gap) + right).PadRight(w + 1);

        try
        {
            Console.SetCursorPosition(0, 0);
            Console.BackgroundColor = ConsoleColor.DarkBlue;
            Console.ForegroundColor = ConsoleColor.White;
            Console.Write(bar.Length > w + 1 ? bar[..(w + 1)] : bar);
            Console.WriteLine();

            Console.BackgroundColor = ConsoleColor.Black;
            Console.ForegroundColor = ConsoleColor.DarkBlue;
            Console.WriteLine(new string('▄', w + 1));
        }
        finally
        {
            SetDark();
        }
    }

    // ── Panel: Portfolio Summary ──────────────────────────────────────────

    private static int DrawSummaryPanel(PortfolioSummary? s, int startRow)
    {
        int w = W;
        BoxTop("PORTFOLIO SUMMARY", w, startRow);
        int r = startRow + 1;

        if (s is null)
        {
            WritAt(r++, "    No data.", Label);
        }
        else
        {
            // Row 1 — counts
            Console.SetCursorPosition(0, r++);
            Writ("    ", ValueFg);
            Writ("Holdings:  ", Label); Writ($"{s.HoldingsCount,-5}  ", Accent);
            Writ("Positions:  ", Label); Writ($"{s.PositionsCount,-5}  ", Accent);
            Writ("Overall Return:  ", Label);
            Writ($"{s.OverallReturnPct:+0.00;-0.00}%", s.OverallReturnPct >= 0 ? GainFg : LossFg);
            Console.WriteLine();

            // Row 2 — value
            Console.SetCursorPosition(0, r++);
            Writ("    ", ValueFg);
            Writ("Invested:  ", Label);  Writ($"{s.TotalInvested,16:N2}     ", Accent);
            Writ("Current Value:  ", Label); Writ($"{s.TotalCurrentValue,16:N2}", Accent);
            Console.WriteLine();

            // Row 3 — P&L
            Console.SetCursorPosition(0, r++);
            Writ("    ", ValueFg);
            Writ("Unrealised P&L:  ", Label);
            WritPnl(s.TotalUnrealisedPnl);
            Writ("     Realised P&L:  ", Label);
            WritPnl(s.TotalRealisedPnl);
            Console.WriteLine();
        }

        BoxBot(w, r++);
        return r + 1;
    }

    // ── Panel: Top Movers (gainers + losers) ──────────────────────────────

    private static int DrawMoversPanel(AnalysisResult? a, int startRow)
    {
        if (a is null || (a.TopGainers.Count == 0 && a.TopLosers.Count == 0))
            return startRow;

        int w = W;
        BoxTop("TOP MOVERS", w, startRow);
        int r = startRow + 1;

        // Column header
        Console.SetCursorPosition(0, r++);
        Writ($"    {"Symbol",-20} {"Last Price",12} {"P&L",14} {"Return",9}", Label);
        Console.WriteLine();
        WritAt(r++, "    " + new string('─', w - 8), Dim);

        if (a.TopGainers.Count > 0)
        {
            WritAt(r++, "    GAINERS", GainFg);
            foreach (var h in a.TopGainers.Take(3))
            {
                Console.SetCursorPosition(0, r++);
                string sym = Trunc(h.TradingSymbol, 20);
                Writ($"      {sym,-20} ", ValueFg);
                Writ($"{h.LastPrice,12:N2} ", ValueFg);
                WritPnl(h.UnrealisedPnl, 14);
                Writ($" {h.ReturnPct,8:+0.00;-0.00}%", GainFg);
                Console.WriteLine();
            }
        }

        if (a.TopLosers.Count > 0)
        {
            WritAt(r++, "    LOSERS", LossFg);
            foreach (var h in a.TopLosers.Take(3))
            {
                Console.SetCursorPosition(0, r++);
                string sym = Trunc(h.TradingSymbol, 20);
                Writ($"      {sym,-20} ", ValueFg);
                Writ($"{h.LastPrice,12:N2} ", ValueFg);
                WritPnl(h.UnrealisedPnl, 14);
                Writ($" {h.ReturnPct,8:+0.00;-0.00}%", LossFg);
                Console.WriteLine();
            }
        }

        BoxBot(w, r++);
        return r + 1;
    }

    // ── Panel: Active Alerts ──────────────────────────────────────────────

    private static int DrawAlertsPanel(List<Alert> alerts, int startRow)
    {
        int w = W;
        BoxTop("ACTIVE ALERTS", w, startRow);
        int r = startRow + 1;

        if (alerts.Count == 0)
        {
            WritAt(r++, "    ✓  All holdings within normal range — no alerts.", GainFg);
        }
        else
        {
            foreach (var a in alerts)
            {
                Console.SetCursorPosition(0, r++);
                bool loss  = a.Type.Contains("LOSS", StringComparison.OrdinalIgnoreCase);
                var  color = loss ? LossFg : GainFg;
                string badge = loss ? "[LOSS]" : "[GAIN]";
                string pct   = $"{a.ReturnPct:+0.00;-0.00}%";
                string msg   = $"    {badge,-7}  {a.Symbol,-18}  {pct,8}   {a.Message}";
                if (msg.Length > w - 2) msg = msg[..(w - 5)] + "…";
                Writ(msg, color);
                Console.WriteLine();
            }
        }

        BoxBot(w, r++);
        return r + 1;
    }

    // ── Panel: Exchange / Sector Allocation ───────────────────────────────

    private static int DrawAllocationPanel(List<SectorAllocation> alloc, int startRow)
    {
        if (alloc.Count == 0) return startRow;

        int w   = W;
        int barW = Math.Max(20, w - 52);
        BoxTop("EXCHANGE ALLOCATION", w, startRow);
        int r = startRow + 1;

        foreach (var s in alloc)
        {
            Console.SetCursorPosition(0, r++);
            int filled = (int)(s.WeightPct / 100.0 * barW);
            int empty  = barW - filled;
            Writ($"    {s.Exchange,-6}  {s.WeightPct,6:N1}%  ", Label);
            Writ(new string('█', filled), BarFg);
            Writ(new string('░', empty),  BarEmpty);
            Writ($"  {s.CurrentValue,14:N2}", Accent);
            Console.WriteLine();
        }

        BoxBot(w, r++);
        return r + 1;
    }

    // ── Footer helpers ─────────────────────────────────────────────────────

    private static void UpdateFooter(DateTime fetchedAt, int remaining)
    {
        if (_footerRow == 0) return;
        try
        {
            Console.SetCursorPosition(0, _footerRow);
            string timer = remaining > 0
                ? $"⏱  Next live refresh in {remaining,3}s"
                : "🔄  Refreshing live data...  ";
            string msg = $"  {timer}    │    Last fetched: {fetchedAt:HH:mm:ss}  (live)    │    [Q] / [Esc]  Exit";
            Writ((msg.Length > W ? msg[..W] : msg).PadRight(W), WarnFg);
        }
        catch { /* console too small */ }
    }

    private static void PaintStatus(string msg)
    {
        if (_statusRow == 0) return;
        try
        {
            Console.SetCursorPosition(0, _statusRow);
            Writ((msg.Length > W ? msg[..W] : msg).PadRight(W), WarnFg);
        }
        catch { /* console too small */ }
    }

    // ── Drawing primitives ────────────────────────────────────────────────

    private static int W => Math.Max(80, Math.Min(Console.WindowWidth - 1, 120));

    private static void SetDark()
    {
        Console.BackgroundColor = ConsoleColor.Black;
        Console.ForegroundColor = ValueFg;
    }

    private static void BoxTop(string title, int w, int row)
    {
        string border = $"  ┌─ {title} {new string('─', Math.Max(0, w - title.Length - 8))}┐";
        WritAt(row, border, Dim);
    }

    private static void BoxBot(int w, int row)
        => WritAt(row, "  └" + new string('─', Math.Max(0, w - 5)) + "┘", Dim);

    private static void WritAt(int row, string text, ConsoleColor color)
    {
        try
        {
            Console.SetCursorPosition(0, row);
            Writ(text, color);
            Console.WriteLine();
        }
        catch { /* row out of range */ }
    }

    private static void Writ(string text, ConsoleColor color)
    {
        var saved = Console.ForegroundColor;
        Console.ForegroundColor = color;
        Console.Write(text);
        Console.ForegroundColor = saved;
    }

    private static void WritPnl(double value, int width = 0)
    {
        string s    = value >= 0 ? $"+{value:N2}" : $"{value:N2}";
        var    color = value >= 0 ? GainFg : LossFg;
        Writ(width > 0 ? s.PadLeft(width) : s, color);
    }

    private static string Trunc(string s, int max)
        => s.Length <= max ? s : s[..(max - 1)] + "…";
}
