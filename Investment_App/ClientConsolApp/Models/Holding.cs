using System.Text.Json.Serialization;

namespace ClientConsolApp.Models;

/// <summary>
/// Long-term investment holding. Mirrors the FastAPI Holding Pydantic model.
/// Computed fields (invested_value, current_value, unrealised_pnl, return_pct)
/// are calculated server-side and returned in the JSON.
/// </summary>
public class Holding
{
    [JsonPropertyName("broker")]
    public string Broker { get; set; } = string.Empty;

    [JsonPropertyName("instrument_key")]
    public string InstrumentKey { get; set; } = string.Empty;

    [JsonPropertyName("trading_symbol")]
    public string TradingSymbol { get; set; } = string.Empty;

    [JsonPropertyName("exchange")]
    public string Exchange { get; set; } = string.Empty;

    [JsonPropertyName("isin")]
    public string? Isin { get; set; }

    [JsonPropertyName("quantity")]
    public double Quantity { get; set; }

    [JsonPropertyName("average_price")]
    public double AveragePrice { get; set; }

    [JsonPropertyName("last_price")]
    public double LastPrice { get; set; }

    [JsonPropertyName("close_price")]
    public double ClosePrice { get; set; }

    // ── Computed fields returned by FastAPI ───────────────────────────────

    [JsonPropertyName("invested_value")]
    public double InvestedValue { get; set; }

    [JsonPropertyName("current_value")]
    public double CurrentValue { get; set; }

    [JsonPropertyName("unrealised_pnl")]
    public double UnrealisedPnl { get; set; }

    [JsonPropertyName("return_pct")]
    public double ReturnPct { get; set; }
}
