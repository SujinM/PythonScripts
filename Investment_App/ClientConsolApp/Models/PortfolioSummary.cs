using System.Text.Json.Serialization;

namespace ClientConsolApp.Models;

/// <summary>
/// Aggregated portfolio summary. Mirrors the FastAPI PortfolioSummary Pydantic model.
/// </summary>
public class PortfolioSummary
{
    [JsonPropertyName("broker")]
    public string Broker { get; set; } = string.Empty;

    [JsonPropertyName("holdings_count")]
    public int HoldingsCount { get; set; }

    [JsonPropertyName("positions_count")]
    public int PositionsCount { get; set; }

    [JsonPropertyName("total_invested")]
    public double TotalInvested { get; set; }

    [JsonPropertyName("total_current_value")]
    public double TotalCurrentValue { get; set; }

    [JsonPropertyName("total_unrealised_pnl")]
    public double TotalUnrealisedPnl { get; set; }

    [JsonPropertyName("total_realised_pnl")]
    public double TotalRealisedPnl { get; set; }

    [JsonPropertyName("overall_return_pct")]
    public double OverallReturnPct { get; set; }

    [JsonPropertyName("top_gainers")]
    public List<Holding> TopGainers { get; set; } = new();

    [JsonPropertyName("top_losers")]
    public List<Holding> TopLosers { get; set; } = new();
}
