using System.Text.Json.Serialization;

namespace ClientConsolApp.Models;

/// <summary>
/// Full analysis result from GET /api/v1/{broker}/analysis.
/// </summary>
public class AnalysisResult
{
    [JsonPropertyName("broker")]
    public string Broker { get; set; } = string.Empty;

    [JsonPropertyName("holdings_count")]
    public int HoldingsCount { get; set; }

    [JsonPropertyName("total_invested")]
    public double TotalInvested { get; set; }

    [JsonPropertyName("total_current_value")]
    public double TotalCurrentValue { get; set; }

    [JsonPropertyName("total_pnl")]
    public double TotalPnl { get; set; }

    [JsonPropertyName("overall_return_pct")]
    public double OverallReturnPct { get; set; }

    [JsonPropertyName("top_gainers")]
    public List<Holding> TopGainers { get; set; } = new();

    [JsonPropertyName("top_losers")]
    public List<Holding> TopLosers { get; set; } = new();

    [JsonPropertyName("alerts")]
    public List<Alert> Alerts { get; set; } = new();

    [JsonPropertyName("sector_allocation")]
    public List<SectorAllocation> SectorAllocation { get; set; } = new();
}

/// <summary>A P&amp;L alert for a holding outside the normal range.</summary>
public class Alert
{
    [JsonPropertyName("symbol")]
    public string Symbol { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [JsonPropertyName("return_pct")]
    public double ReturnPct { get; set; }

    [JsonPropertyName("message")]
    public string Message { get; set; } = string.Empty;
}

/// <summary>Investment weight per exchange/sector.</summary>
public class SectorAllocation
{
    [JsonPropertyName("exchange")]
    public string Exchange { get; set; } = string.Empty;

    [JsonPropertyName("current_value")]
    public double CurrentValue { get; set; }

    [JsonPropertyName("weight_pct")]
    public double WeightPct { get; set; }
}
