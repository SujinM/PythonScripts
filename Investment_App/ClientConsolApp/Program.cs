using ClientConsolApp.Core;
using ClientConsolApp.Display;
using ClientConsolApp.Services;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

// ── Configuration ──────────────────────────────────────────────────────────────
//
// Load order (later sources override earlier ones):
//   1. appsettings.json
//   2. appsettings.Development.json  (when DOTNET_ENVIRONMENT=Development)
//   3. Environment variables         (use ApiSettings__BaseUrl=http://... syntax)
//
// Never put secrets (API keys, tokens) in appsettings files.
// Set them as environment variables instead.
//
// ──────────────────────────────────────────────────────────────────────────────

var env = Environment.GetEnvironmentVariable("DOTNET_ENVIRONMENT") ?? "Production";

var configuration = new ConfigurationBuilder()
    .SetBasePath(AppContext.BaseDirectory)
    .AddJsonFile("appsettings.json", optional: false, reloadOnChange: false)
    .AddJsonFile($"appsettings.{env}.json", optional: true, reloadOnChange: false)
    .AddEnvironmentVariables()
    .Build();

var apiSettings = configuration.GetSection(ApiSettings.SectionName).Get<ApiSettings>()
    ?? new ApiSettings();

// ── Dependency Injection ───────────────────────────────────────────────────────

var services = new ServiceCollection();

services.Configure<ApiSettings>(configuration.GetSection(ApiSettings.SectionName));

// Register a named HttpClient — base address + timeout set once here.
// All requests go through this single client (connection pooling built-in).
services.AddHttpClient<ApiClient>(client =>
{
    client.BaseAddress = new Uri(apiSettings.BaseUrl);
    client.Timeout = TimeSpan.FromSeconds(apiSettings.TimeoutSeconds);
    client.DefaultRequestHeaders.Add("Accept", "application/json");
});

services.AddTransient<PortfolioService>();

var provider = services.BuildServiceProvider();
var portfolio = provider.GetRequiredService<PortfolioService>();

// ── Startup banner ─────────────────────────────────────────────────────────────

string currentBroker = configuration["DefaultBroker"] ?? "upstox";

// ── Main loop ──────────────────────────────────────────────────────────────────

while (true)
{
    ConsoleRenderer.DrawMainMenu(currentBroker);
    string option = Console.ReadLine()?.Trim() ?? "";

    if (option == "0") break;

    using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(apiSettings.TimeoutSeconds * apiSettings.MaxRetries + 30));
    bool suppressPressAnyKey = false;

    try
    {
        switch (option)
        {
            // ── 1: Summary ────────────────────────────────────────────────
            case "1":
                AppLogger.Info($"Fetching portfolio summary for {currentBroker}...");
                var summaryResp = await portfolio.GetSummaryAsync(currentBroker, cts.Token);
                if (summaryResp.Data is not null)
                    ConsoleRenderer.RenderSummary(summaryResp.Data);
                else
                    AppLogger.Warn("No summary data returned.");
                break;

            // ── 2: Holdings ───────────────────────────────────────────────
            case "2":
                AppLogger.Info($"Fetching holdings for {currentBroker}...");
                var holdingsResp = await portfolio.GetHoldingsAsync(currentBroker, cts.Token);
                ConsoleRenderer.RenderHoldings(holdingsResp.Data ?? new(), currentBroker);
                break;

            // ── 3: Positions ──────────────────────────────────────────────
            case "3":
                AppLogger.Info($"Fetching positions for {currentBroker}...");
                var posResp = await portfolio.GetPositionsAsync(currentBroker, cts.Token);
                ConsoleRenderer.RenderPositions(posResp.Data ?? new(), currentBroker);
                break;

            // ── 4: Trades ─────────────────────────────────────────────────
            case "4":
                AppLogger.Info($"Fetching today's trades for {currentBroker}...");
                var tradesResp = await portfolio.GetTradesAsync(currentBroker, cts.Token);
                ConsoleRenderer.RenderTrades(tradesResp.Data ?? new(), currentBroker);
                break;

            // ── 5: Full Analysis ──────────────────────────────────────────
            case "5":
                AppLogger.Info($"Fetching full analysis for {currentBroker}...");
                var analysisResp = await portfolio.GetAnalysisAsync(currentBroker, cts.Token);
                if (analysisResp.Data is not null)
                    ConsoleRenderer.RenderAnalysis(analysisResp.Data);
                else
                    AppLogger.Warn("No analysis data returned.");
                break;

            // ── 6: Alerts ─────────────────────────────────────────────────
            case "6":
                AppLogger.Info($"Fetching alerts for {currentBroker}...");
                var alertsResp = await portfolio.GetAlertsAsync(currentBroker, cts.Token);
                ConsoleRenderer.RenderAlerts(alertsResp.Data ?? new());
                break;

            // ── 7: List Brokers ───────────────────────────────────────────
            case "7":
                AppLogger.Info("Fetching registered brokers...");
                var brokersResp = await portfolio.GetBrokersAsync(cts.Token);
                ConsoleRenderer.RenderBrokers(brokersResp.Data ?? new());
                break;

            // ── 8: Invalidate Cache ───────────────────────────────────────
            case "8":
                AppLogger.Info($"Invalidating cache for {currentBroker}...");
                await portfolio.InvalidateCacheAsync(currentBroker, cts.Token);
                AppLogger.Success($"Cache cleared for {currentBroker}. Next fetch will hit the broker API.");
                break;

            // ── 9: Switch Broker ──────────────────────────────────────────
            case "9":
                Console.Write("  Enter broker ID (upstox / etoro): ");
                string? input = Console.ReadLine()?.Trim().ToLower();
                if (!string.IsNullOrWhiteSpace(input))
                {
                    currentBroker = input;
                    AppLogger.Success($"Switched to broker: {currentBroker}");
                }
                break;

            // ── L: Live Dashboard ─────────────────────────────────────────
            case "l":
            case "L":
                suppressPressAnyKey = true;
                if (System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(System.Runtime.InteropServices.OSPlatform.Windows))
                {
                    Console.Write("  Refresh interval in seconds [5]: ");
                    string? intervalInput = Console.ReadLine()?.Trim();
                    int liveInterval = string.IsNullOrEmpty(intervalInput)
                        ? 5
                        : int.TryParse(intervalInput, out int parsed) ? parsed : 5;
                    if (liveInterval < 3)
                    {
                        AppLogger.Warn($"Minimum is 3s (broker API rate limit). Using 3s.");
                        liveInterval = 3;
                    }
                    await ClientConsolApp.Display.LiveDashboard.RunAsync(portfolio, currentBroker, liveInterval);
                }
                else
                    AppLogger.Warn("Live Dashboard is only supported on Windows.");
                break;

            default:
                AppLogger.Warn("Unknown option. Please enter a number from the menu.");
                break;
        }
    }
    catch (ApiException ex)
    {
        Console.WriteLine();
        AppLogger.Error($"API error [{(int)ex.StatusCode}]: {ex.Message}");
        if (ex.ErrorCode is not null)
            AppLogger.Error($"Error code: {ex.ErrorCode}");
        if (ex.StatusCode == System.Net.HttpStatusCode.ServiceUnavailable ||
            ex.StatusCode == System.Net.HttpStatusCode.BadGateway)
        {
            AppLogger.Warn("Is the FastAPI server running? Start it with: start-dev.bat");
        }
    }
    catch (HttpRequestException ex)
    {
        Console.WriteLine();
        AppLogger.Error($"Cannot reach server at {apiSettings.BaseUrl}: {ex.Message}");
        AppLogger.Warn("Make sure the FastAPI server is running. Start it with: start-dev.bat");
    }
    catch (OperationCanceledException)
    {
        AppLogger.Error("Request timed out.");
    }

    if (!suppressPressAnyKey)
        ConsoleRenderer.PressAnyKey();
}

Console.Clear();
AppLogger.Success("Goodbye!");
