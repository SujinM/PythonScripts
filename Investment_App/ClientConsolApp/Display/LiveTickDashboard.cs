using ClientConsolApp.Core;
using ClientConsolApp.Models;
using ClientConsolApp.Services;
using System.Runtime.Versioning;
using System.Text;

namespace ClientConsolApp.Display;

/// <summary>
/// Full-screen WebSocket live price dashboard.
///
/// Connects to <c>WS /api/v1/{broker}/ws/live</c> and renders an
/// auto-updating table of instrument prices as ticks arrive.
/// Press Q or Escape to return to the main menu.
///
/// Layout
/// ──────
///   ┌ Header bar ──────────────────────────────────────────────┐
///   │ Instrument │ LTP / Bid  │ Ask        │ Chg   │ Chg%  │  │
///   ├────────────────────────────────────────────────────────  ┤
///   │ AAPL       │ 1234.50    │ 1234.80    │ +4.50 │ +0.36%│  │
///   │ GTLB       │  832.10    │  832.40    │ -1.20 │ -0.14%│  │
///   │ ...        │ ...        │ ...        │ ...   │ ...   │  │
///   └ Footer — last tick time, frame count, [Q] hint ──────────┘
///
/// Upstox columns : LTP | Close | Chg | Chg%
/// eToro columns  : Bid | Ask   | (spread)
/// </summary>
[SupportedOSPlatform("windows")]
public static class LiveTickDashboard
{
    // ── Colour palette ────────────────────────────────────────────────────
    private const ConsoleColor Accent   = ConsoleColor.Cyan;
    private const ConsoleColor Dim      = ConsoleColor.DarkCyan;
    private const ConsoleColor Label    = ConsoleColor.DarkGray;
    private const ConsoleColor ValueFg  = ConsoleColor.White;
    private const ConsoleColor GainFg   = ConsoleColor.Green;
    private const ConsoleColor LossFg   = ConsoleColor.Red;
    private const ConsoleColor WarnFg   = ConsoleColor.Yellow;

    // ── Column widths ─────────────────────────────────────────────────────
    private const int ColSymbol  = 20;   // Upstox symbol column
    private const int ColEtoroId = 8;    // eToro numeric ID column
    private const int ColEtoroName = 22; // eToro display name column
    private const int ColPrice   = 13;
    private const int ColChg     = 11;
    private const int ColPct     = 10;

    // ── State ─────────────────────────────────────────────────────────────

    /// <summary>Latest tick entry per instrument key.</summary>
    private static readonly Dictionary<string, LiveTickEntry> _latest = new();

    /// <summary>Previous LTP/BestPrice per instrument — for flash highlight.</summary>
    private static readonly Dictionary<string, double> _prev = new();

    private static int _frameCount   = 0;
    private static DateTime _lastTick = DateTime.MinValue;
    private static string   _statusMsg = "  Connecting...";
    private static int      _footerRow = 0;

    // ── Entry point ───────────────────────────────────────────────────────

    /// <summary>
    /// Launch the WebSocket live price dashboard. Blocks until Q / Esc.
    /// </summary>
    public static async Task RunAsync(
        LiveTickService liveTickService,
        string broker,
        string instruments = "",
        CancellationToken outerCt = default)
    {
        var origFg     = Console.ForegroundColor;
        var origBg     = Console.BackgroundColor;
        var origTitle  = Console.Title;
        bool origCursor = true;
        try { origCursor = Console.CursorVisible; } catch { }

        _latest.Clear();
        _prev.Clear();
        _frameCount = 0;
        _lastTick   = DateTime.MinValue;
        _statusMsg  = "  Connecting to WebSocket...";

        try
        {
            Console.Title         = $"Sujin's Investment  ─  WS Live [{broker.ToUpper()}]";
            Console.CursorVisible = false;
            Console.BackgroundColor = ConsoleColor.Black;
            Console.Clear();

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
                    Thread.Sleep(60);
                }
            }, CancellationToken.None);

            // Draw initial skeleton
            DrawHeader(broker);
            DrawTableHeader(broker);
            _footerRow = Console.CursorTop + 1;
            PaintStatus(_statusMsg);

            // ── WebSocket stream loop ─────────────────────────────────────
            await foreach (var frame in liveTickService.StreamAsync(broker, instruments, cts.Token))
            {
                if (frame.Error is not null)
                {
                    _statusMsg = $"  Server error: {frame.Error}";
                    PaintStatus(_statusMsg);
                    continue;
                }

                if (!frame.HasTicks) continue;

                // Merge new ticks into _latest — only overwrite non-null fields so
                // that a partial update (e.g. eToro sending only Bid, or an
                // update with no price) never erases a previously known value.
                foreach (var (key, newEntry) in frame.Ticks!)
                {
                    if (_latest.TryGetValue(key, out var existing))
                    {
                        if (newEntry.Name   is not null) existing.Name  = newEntry.Name;
                        if (newEntry.Bid.HasValue)       existing.Bid   = newEntry.Bid;
                        if (newEntry.Ask.HasValue)       existing.Ask   = newEntry.Ask;
                        if (newEntry.Ltp.HasValue)       existing.Ltp   = newEntry.Ltp;
                        if (newEntry.Close.HasValue)     existing.Close = newEntry.Close;
                        existing.Ts = newEntry.Ts;
                    }
                    else
                    {
                        _latest[key] = newEntry;
                    }
                }

                _frameCount++;
                _lastTick = frame.ReceivedAt;
                _statusMsg = string.Empty;

                // Full redraw on each tick
                RedrawTable(broker);
                PaintFooter(broker);
            }
        }
        catch (OperationCanceledException) { /* Q / Esc or outer token */ }
        finally
        {
            Console.CursorVisible  = origCursor;
            Console.BackgroundColor = origBg;
            Console.ForegroundColor = origFg;
            Console.Title          = origTitle;
            Console.Clear();
        }
    }

    // ── Header ────────────────────────────────────────────────────────────

    private static void DrawHeader(string broker)
    {
        Console.SetCursorPosition(0, 0);
        var title = $"  WS Live Prices  ─  {broker.ToUpper()}  ─  Press Q to exit";
        WriteLn(title.PadRight(Console.WindowWidth - 1), Accent, ConsoleColor.DarkBlue);
        WriteLn(new string('─', Console.WindowWidth - 1), Dim);
    }

    // ── Table header ──────────────────────────────────────────────────────

    private static void DrawTableHeader(string broker)
    {
        Console.SetCursorPosition(0, 2);
        if (broker == "etoro")
        {
            var hdr = "  " + "ID".PadRight(ColEtoroId) + " " +
                      "Name".PadRight(ColEtoroName) + " " +
                      "Bid".PadLeft(ColPrice) + " " +
                      "Ask".PadLeft(ColPrice) + " " +
                      "Spread".PadLeft(ColChg);
            WriteLn(hdr.PadRight(Console.WindowWidth - 1), Label);
        }
        else
        {
            var hdr = "  " + "Instrument".PadRight(ColSymbol) + " " +
                      "LTP".PadLeft(ColPrice) + " " +
                      "Close".PadLeft(ColPrice) + " " +
                      "Change".PadLeft(ColChg) + " " +
                      "Chg%".PadLeft(ColPct);
            WriteLn(hdr.PadRight(Console.WindowWidth - 1), Label);
        }
        WriteLn(new string('─', Console.WindowWidth - 1), Dim);
    }

    // ── Table body ────────────────────────────────────────────────────────

    private static void RedrawTable(string broker)
    {
        // Snapshot the window width ONCE so every calculation in this
        // method uses a consistent value even if the terminal is resized
        // mid-draw, which would cause misaligned rows.
        int w = Math.Max(80, Console.WindowWidth);

        DrawHeader(broker);
        DrawTableHeader(broker);

        // Pre-clear the entire table body area so rows that were drawn in a
        // previous frame but are no longer needed never bleed through.
        int maxBodyRow = Math.Min(4 + _latest.Count + 6, Console.WindowHeight - 2);
        string blankLine = new string(' ', w - 1);
        for (int r = 4; r <= maxBodyRow; r++)
        {
            Console.SetCursorPosition(0, r);
            Console.Write(blankLine);
        }

        int row = 4;
        foreach (var (key, entry) in _latest.OrderBy(k => k.Key))
        {
            Console.SetCursorPosition(0, row++);

            // For Upstox: take segment after last '|' (e.g. "INE848E01016" from "NSE_EQ|INE848E01016").
            // For eToro : use the Name field (trading symbol) served by the backend;
            //             fall back to the numeric ID if name is not yet received.
            string symbol;
            string etoroId = string.Empty;
            if (broker == "etoro")
            {
                etoroId = key.Length > ColEtoroId ? key[..ColEtoroId] : key;
                symbol  = entry.Name ?? key;  // Name = "Apple", "Ethereum", etc.
                symbol  = symbol.Length > ColEtoroName ? symbol[..ColEtoroName] : symbol;
            }
            else
            {
                symbol = key.Contains('|') ? key[(key.LastIndexOf('|') + 1)..] : key;
                symbol = symbol.Length > ColSymbol ? symbol[..ColSymbol] : symbol;
            }

            double? current = entry.BestPrice;
            bool   priceUp  = false;
            bool   priceDn  = false;

            if (current.HasValue)
            {
                if (_prev.TryGetValue(key, out double prev))
                {
                    priceUp = current.Value > prev;
                    priceDn = current.Value < prev;
                }
                _prev[key] = current.Value;
            }

            var priceFg = priceUp ? GainFg : priceDn ? LossFg : ValueFg;

            Console.Write("  ");
            if (broker == "etoro")
            {
                WriteField(etoroId.PadRight(ColEtoroId), Label);
                Console.Write(" ");
                WriteField(symbol.PadRight(ColEtoroName), ValueFg);
            }
            else
            {
                WriteField(symbol.PadRight(ColSymbol), ValueFg);
            }
            Console.Write(" ");

            if (broker == "etoro")
            {
                WriteField(FormatPrice(entry.Bid, "$").PadLeft(ColPrice), priceFg);
                Console.Write(" ");
                WriteField(FormatPrice(entry.Ask, "$").PadLeft(ColPrice), priceFg);
                Console.Write(" ");

                // Only compute spread when both sides are known; a one-sided
                // quote would produce a negative value which is misleading.
                double? spread = entry.Bid.HasValue && entry.Ask.HasValue
                    ? entry.Ask.Value - entry.Bid.Value
                    : (double?)null;
                string spreadStr = spread.HasValue
                    ? ("$" + spread.Value.ToString("F4")).PadLeft(ColChg)
                    : FormatPrice(null).PadLeft(ColChg);   // "─"
                WriteField(spreadStr, spread is null || spread == 0 ? Label : ValueFg);
            }
            else
            {
                WriteField(FormatPrice(entry.Ltp, "\u20b9").PadLeft(ColPrice), priceFg);
                Console.Write(" ");
                WriteField(FormatPrice(entry.Close, "\u20b9").PadLeft(ColPrice), Label);
                Console.Write(" ");

                var chg = entry.ChangeFromClose;
                var pct = entry.ChangePct;
                var chgFg = chg.HasValue && chg.Value >= 0 ? GainFg : LossFg;
                var sign  = chg.HasValue && chg.Value > 0 ? "+" : "";

                WriteField((sign + FormatPrice(chg, "\u20b9")).PadLeft(ColChg), chgFg);
                Console.Write(" ");
                WriteField((sign + (pct.HasValue ? pct.Value.ToString("F2") : "\u2500") + "%").PadLeft(ColPct + 1), chgFg);
            }

            // Pad the rest of the row so the cursor always ends at exactly
            // column w-1 — this prevents any residual character from a wider
            // previous value showing at the end of the line, and ensures the
            // next SetCursorPosition starts from a clean column 0.
            int rowPad = w - 1 - Console.CursorLeft;
            if (rowPad > 0)  Console.Write(new string(' ', rowPad));
            else if (rowPad < 0) Console.SetCursorPosition(w - 1, Console.CursorTop);
        }

        _footerRow = row + 1;
    }

    // ── Footer ────────────────────────────────────────────────────────────

    private static void PaintFooter(string broker)
    {
        int targetRow = _footerRow;
        if (targetRow >= Console.WindowHeight - 1) targetRow = Console.WindowHeight - 2;

        Console.SetCursorPosition(0, targetRow);
        WriteLn(new string('─', Console.WindowWidth - 1), Dim);

        var msg = _lastTick == DateTime.MinValue
            ? "  Waiting for first tick..."
            : $"  Last tick: {_lastTick:HH:mm:ss.fff}   Frames: {_frameCount}   [Q] Exit";

        Console.SetCursorPosition(0, targetRow + 1);
        WriteField(msg.PadRight(Console.WindowWidth - 1), Label);
    }

    private static void PaintStatus(string msg)
    {
        if (string.IsNullOrEmpty(msg)) return;
        int row = _footerRow > 0 ? _footerRow + 2 : Console.WindowHeight - 2;
        if (row >= Console.WindowHeight) row = Console.WindowHeight - 1;
        Console.SetCursorPosition(0, row);
        WriteField(msg.PadRight(Console.WindowWidth - 1), WarnFg);
    }

    // ── Helpers ───────────────────────────────────────────────────────────

    private static string FormatPrice(double? price, string prefix = "")
        => price.HasValue ? prefix + price.Value.ToString("N2") : "─";

    private static void WriteField(string text, ConsoleColor fg)
    {
        var saved = Console.ForegroundColor;
        Console.ForegroundColor = fg;
        Console.Write(text);
        Console.ForegroundColor = saved;
    }

    private static void WriteLn(string text, ConsoleColor fg, ConsoleColor? bg = null)
    {
        var savedFg = Console.ForegroundColor;
        var savedBg = Console.BackgroundColor;
        Console.ForegroundColor = fg;
        if (bg.HasValue) Console.BackgroundColor = bg.Value;
        Console.WriteLine(text);
        Console.ForegroundColor = savedFg;
        Console.BackgroundColor = savedBg;
    }
}
