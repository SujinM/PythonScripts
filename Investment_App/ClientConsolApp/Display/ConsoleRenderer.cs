using ClientConsolApp.Models;

namespace ClientConsolApp.Display;

/// <summary>
/// All console output formatting lives here — no rendering logic in services or Program.cs.
/// Uses fixed-width padding for table alignment. No external dependencies required.
/// </summary>
public static class ConsoleRenderer
{
    // ── Colour helpers ────────────────────────────────────────────────────

    private static void WriteColored(string text, ConsoleColor color, bool newLine = true)
    {
        var saved = Console.ForegroundColor;
        Console.ForegroundColor = color;
        if (newLine) Console.WriteLine(text); else Console.Write(text);
        Console.ForegroundColor = saved;
    }

    private static string Cur(string broker) =>
        broker.Equals("etoro", StringComparison.OrdinalIgnoreCase) ? "$" : "\u20b9";

    private static void WritePnl(double value, string format = "N2", string prefix = "")
    {
        var color = value >= 0 ? ConsoleColor.Green : ConsoleColor.Red;
        string sign = value > 0 ? "+" : "";
        string body = value < 0
            ? "-" + prefix + Math.Abs(value).ToString(format)
            : prefix + value.ToString(format);
        WriteColored($"{sign}{body}", color, newLine: false);
    }

    // ── Main menu ─────────────────────────────────────────────────────────

    public static void DrawMainMenu(string broker)
    {
        Console.Clear();
        WriteColored("╔══════════════════════════════════════════════╗", ConsoleColor.DarkCyan);
        WriteColored("║   Investment Portfolio Console Client  v1.0  ║", ConsoleColor.Cyan);
        WriteColored("╚══════════════════════════════════════════════╝", ConsoleColor.DarkCyan);
        Console.WriteLine();
        WriteColored($"  Active broker : {broker.ToUpper()}", ConsoleColor.Yellow);
        Console.WriteLine();
        WriteColored("  ── Portfolio ─────────────────────────────────", ConsoleColor.DarkGray);
        Console.WriteLine("   1.  Portfolio Summary");
        Console.WriteLine("   2.  Holdings");
        Console.WriteLine("   3.  Positions");
        Console.WriteLine("   4.  Trades");
        WriteColored("  ── Analysis ──────────────────────────────────", ConsoleColor.DarkGray);
        Console.WriteLine("   5.  Full Analysis");
        Console.WriteLine("   6.  Active Alerts");
        WriteColored("  ── System ────────────────────────────────────", ConsoleColor.DarkGray);
        Console.WriteLine("   7.  List Brokers");
        Console.WriteLine("   8.  Invalidate Cache");
        Console.WriteLine("   9.  Switch Broker");
        WriteColored("  ── Live ─────────────────────────────────────", ConsoleColor.DarkGray);
        WriteColored("   L.  Live Dashboard  (REST auto-refresh)", ConsoleColor.Yellow);
        WriteColored("   W.  WS Live Prices  (WebSocket, sub-second)", ConsoleColor.Yellow);
        Console.WriteLine("   0.  Exit");
        Console.WriteLine();
        WriteColored("  ───────────────────────────────────────────────", ConsoleColor.DarkGray);
        Console.Write("  Select option: ");
    }

    // ── Portfolio Summary ─────────────────────────────────────────────────

    public static void RenderSummary(PortfolioSummary s)
    {
        Console.WriteLine();
        WriteColored($"  Portfolio Summary — {s.Broker.ToUpper()}", ConsoleColor.Cyan);
        WriteColored($"  {new string('─', 44)}", ConsoleColor.DarkCyan);
        var cur = Cur(s.Broker);
        Console.WriteLine($"  {"Holdings:",-22} {s.HoldingsCount}");
        Console.WriteLine($"  {"Positions:",-22} {s.PositionsCount}");
        Console.WriteLine($"  {"Invested:",-22} {cur}{s.TotalInvested:N2}");
        Console.WriteLine($"  {"Current Value:",-22} {cur}{s.TotalCurrentValue:N2}");
        Console.Write($"  {"Unrealised P&L:",-22} ");
        WritePnl(s.TotalUnrealisedPnl, prefix: cur);
        Console.WriteLine();
        Console.Write($"  {"Realised P&L:",-22} ");
        WritePnl(s.TotalRealisedPnl, prefix: cur);
        Console.WriteLine();
        Console.Write($"  {"Overall Return:",-22} ");
        WritePnl(s.OverallReturnPct, "F2");
        WriteColored("%", s.OverallReturnPct >= 0 ? ConsoleColor.Green : ConsoleColor.Red);

        if (s.TopGainers.Count > 0)
        {
            Console.WriteLine();
            WriteColored("  Top Gainers:", ConsoleColor.Green);
            foreach (var h in s.TopGainers)
                Console.WriteLine($"    {h.TradingSymbol,-20}  {h.ReturnPct:+0.00;-0.00}%   P&L: {cur}{h.UnrealisedPnl:N2}");
        }

        if (s.TopLosers.Count > 0)
        {
            Console.WriteLine();
            WriteColored("  Top Losers:", ConsoleColor.Red);
            foreach (var h in s.TopLosers)
                Console.WriteLine($"    {h.TradingSymbol,-20}  {h.ReturnPct:+0.00;-0.00}%   P&L: {cur}{h.UnrealisedPnl:N2}");
        }
        Console.WriteLine();
    }

    // ── Holdings table ────────────────────────────────────────────────────

    public static void RenderHoldings(List<Holding> holdings, string broker)
    {
        if (holdings.Count == 0)
        {
            WriteColored($"  No holdings found for {broker}.", ConsoleColor.Yellow);
            return;
        }

        Console.WriteLine();
        WriteColored($"  Holdings — {broker.ToUpper()}  ({holdings.Count})", ConsoleColor.Cyan);
        Console.WriteLine();

        const string header = "  {0,-22} {1,-8} {2,10} {3,10} {4,11} {5,12} {6,9}";
        WriteColored(string.Format(header,
            "Symbol", "Exch", "Qty", "Avg Price", "Last Price", "P&L", "Return%"),
            ConsoleColor.DarkGray);
        WriteColored("  " + new string('─', 90), ConsoleColor.DarkGray);

        var cur = Cur(broker);
        foreach (var h in holdings)
        {
            string avgP  = (cur + h.AveragePrice.ToString("N2")).PadLeft(10);
            string lastP = (cur + h.LastPrice.ToString("N2")).PadLeft(11);
            Console.Write(string.Format("  {0,-22} {1,-8} {2,10:N3} {3} {4} ",
                TruncateSymbol(h.TradingSymbol, 22),
                h.Exchange,
                h.Quantity,
                avgP,
                lastP));
            string pnl = h.UnrealisedPnl >= 0
                ? (cur + h.UnrealisedPnl.ToString("N2")).PadLeft(12)
                : ("-" + cur + Math.Abs(h.UnrealisedPnl).ToString("N2")).PadLeft(12);
            WriteColored(pnl, h.UnrealisedPnl >= 0 ? ConsoleColor.Green : ConsoleColor.Red, newLine: false);
            WriteColored($" {h.ReturnPct,8:+0.00;-0.00}%", h.ReturnPct >= 0 ? ConsoleColor.Green : ConsoleColor.Red);
        }
        Console.WriteLine();
    }

    // ── Positions table ───────────────────────────────────────────────────

    public static void RenderPositions(List<Position> positions, string broker)
    {
        if (positions.Count == 0)
        {
            WriteColored($"  No open positions for {broker}.", ConsoleColor.Yellow);
            return;
        }

        Console.WriteLine();
        WriteColored($"  Positions — {broker.ToUpper()}  ({positions.Count})", ConsoleColor.Cyan);
        Console.WriteLine();

        const string header = "  {0,-22} {1,-8} {2,-6} {3,6} {4,10} {5,10} {6,12}";
        WriteColored(string.Format(header, "Symbol", "Exch", "Prod", "Qty", "Buy", "Sell", "P&L"),
            ConsoleColor.DarkGray);
        WriteColored("  " + new string('─', 82), ConsoleColor.DarkGray);

        var cur = Cur(broker);
        foreach (var p in positions)
        {
            string buyP  = (cur + p.BuyPrice.ToString("N2")).PadLeft(10);
            string sellP = (cur + p.SellPrice.ToString("N2")).PadLeft(10);
            Console.Write(string.Format("  {0,-22} {1,-8} {2,-6} {3,6} {4} {5} ",
                TruncateSymbol(p.TradingSymbol, 22),
                p.Exchange,
                p.Product,
                p.Quantity,
                buyP,
                sellP));
            string pnl = p.TotalPnl >= 0
                ? (cur + p.TotalPnl.ToString("N2")).PadLeft(12)
                : ("-" + cur + Math.Abs(p.TotalPnl).ToString("N2")).PadLeft(12);
            WriteColored(pnl, p.TotalPnl >= 0 ? ConsoleColor.Green : ConsoleColor.Red);
        }
        Console.WriteLine();
    }

    // ── Trades table ──────────────────────────────────────────────────────

    public static void RenderTrades(List<Trade> trades, string broker)
    {
        if (trades.Count == 0)
        {
            WriteColored($"  No trades today for {broker}.", ConsoleColor.Yellow);
            return;
        }

        Console.WriteLine();
        WriteColored($"  Today's Trades — {broker.ToUpper()}  ({trades.Count})", ConsoleColor.Cyan);
        Console.WriteLine();

        const string header = "  {0,-22} {1,-8} {2,-5} {3,8} {4,10} {5,12} {6,-20}";
        WriteColored(string.Format(header, "Symbol", "Exch", "Side", "Qty", "Price", "Value", "Time"),
            ConsoleColor.DarkGray);
        WriteColored("  " + new string('─', 92), ConsoleColor.DarkGray);

        var cur = Cur(broker);
        foreach (var t in trades)
        {
            bool isBuy = t.TransactionType.Equals("BUY", StringComparison.OrdinalIgnoreCase);
            Console.Write(string.Format("  {0,-22} {1,-8} ",
                TruncateSymbol(t.TradingSymbol, 22), t.Exchange));
            WriteColored($"{t.TransactionType,-5}", isBuy ? ConsoleColor.Green : ConsoleColor.Red, newLine: false);
            string price = (cur + t.Price.ToString("N2")).PadLeft(10);
            string val   = (cur + t.TradeValue.ToString("N2")).PadLeft(12);
            Console.WriteLine(string.Format(" {0,8:N3} {1} {2} {3,-20}",
                t.Quantity, price, val,
                t.TradeDate?.ToString("yyyy-MM-dd HH:mm") ?? "—"));
        }
        Console.WriteLine();
    }

    // ── Analysis ──────────────────────────────────────────────────────────

    public static void RenderAnalysis(AnalysisResult a)
    {
        Console.WriteLine();
        WriteColored($"  Full Analysis — {a.Broker.ToUpper()}", ConsoleColor.Cyan);
        WriteColored($"  {new string('─', 44)}", ConsoleColor.DarkCyan);
        var cur = Cur(a.Broker);
        Console.WriteLine($"  {"Holdings:",-26} {a.HoldingsCount}");
        Console.WriteLine($"  {"Invested:",-26} {cur}{a.TotalInvested:N2}");
        Console.WriteLine($"  {"Current Value:",-26} {cur}{a.TotalCurrentValue:N2}");
        Console.Write($"  {"Total P&L:",-26} ");
        WritePnl(a.TotalPnl, prefix: cur);
        Console.WriteLine();
        Console.Write($"  {"Overall Return:",-26} ");
        WritePnl(a.OverallReturnPct, "F2");
        WriteColored("%", a.OverallReturnPct >= 0 ? ConsoleColor.Green : ConsoleColor.Red);

        // Exchange allocation
        if (a.SectorAllocation.Count > 0)
        {
            Console.WriteLine();
            WriteColored("  Exchange Allocation:", ConsoleColor.DarkCyan);
            foreach (var s in a.SectorAllocation)
                Console.WriteLine($"    {s.Exchange,-10}  {s.WeightPct,6:N2}%   {cur}{s.CurrentValue:N2}");
        }

        // Top gainers
        if (a.TopGainers.Count > 0)
        {
            Console.WriteLine();
            WriteColored("  Top Gainers:", ConsoleColor.Green);
            foreach (var h in a.TopGainers)
                Console.WriteLine($"    {h.TradingSymbol,-22}  {h.ReturnPct:+0.00;-0.00}%   {cur}{h.UnrealisedPnl:N2}");
        }

        // Top losers
        if (a.TopLosers.Count > 0)
        {
            Console.WriteLine();
            WriteColored("  Top Losers:", ConsoleColor.Red);
            foreach (var h in a.TopLosers)
                Console.WriteLine($"    {h.TradingSymbol,-22}  {h.ReturnPct:+0.00;-0.00}%   {cur}{h.UnrealisedPnl:N2}");
        }

        // Alerts
        RenderAlerts(a.Alerts);
        Console.WriteLine();
    }

    // ── Alerts ────────────────────────────────────────────────────────────

    public static void RenderAlerts(List<Alert> alerts)
    {
        Console.WriteLine();
        if (alerts.Count == 0)
        {
            WriteColored("  No alerts — all holdings within normal range.", ConsoleColor.Green);
            return;
        }

        WriteColored($"  Active Alerts ({alerts.Count}):", ConsoleColor.Yellow);
        WriteColored("  " + new string('─', 60), ConsoleColor.DarkGray);
        foreach (var a in alerts)
        {
            bool isLoss = a.Type.Equals("LOSS_ALERT", StringComparison.OrdinalIgnoreCase);
            var color = isLoss ? ConsoleColor.Red : ConsoleColor.Green;
            Console.Write($"  [{(isLoss ? "LOSS" : "GAIN")}] {a.Symbol,-18} ");
            WritePnl(a.ReturnPct, "F2");
            WriteColored("%  " + a.Message, color);
        }
        Console.WriteLine();
    }

    // ── Brokers table ─────────────────────────────────────────────────────

    public static void RenderBrokers(List<BrokerInfo> brokers)
    {
        Console.WriteLine();
        WriteColored("  Registered Brokers", ConsoleColor.Cyan);
        WriteColored("  " + new string('─', 40), ConsoleColor.DarkGray);
        WriteColored(string.Format("  {0,-12} {1,-20} {2}", "ID", "Name", "Configured"),
            ConsoleColor.DarkGray);
        WriteColored("  " + new string('─', 40), ConsoleColor.DarkGray);
        foreach (var b in brokers)
        {
            Console.Write($"  {b.Id,-12} {b.Name,-20} ");
            WriteColored(b.Configured ? "Yes" : "No",
                b.Configured ? ConsoleColor.Green : ConsoleColor.Red);
        }
        Console.WriteLine();
    }

    // ── Helpers ───────────────────────────────────────────────────────────

    private static string TruncateSymbol(string s, int max)
        => s.Length <= max ? s : s[..(max - 1)] + "…";

    public static void PressAnyKey()
    {
        WriteColored("  Press any key to return to menu...", ConsoleColor.DarkGray);
        Console.ReadKey(intercept: true);
    }
}
