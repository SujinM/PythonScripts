using System.Text.Json.Serialization;

namespace ClientConsolApp.Models;

/// <summary>
/// Open intraday or F&amp;O position. Mirrors the FastAPI Position Pydantic model.
/// </summary>
public class Position
{
    [JsonPropertyName("broker")]
    public string Broker { get; set; } = string.Empty;

    [JsonPropertyName("instrument_key")]
    public string InstrumentKey { get; set; } = string.Empty;

    [JsonPropertyName("trading_symbol")]
    public string TradingSymbol { get; set; } = string.Empty;

    [JsonPropertyName("exchange")]
    public string Exchange { get; set; } = string.Empty;

    [JsonPropertyName("product")]
    public string Product { get; set; } = string.Empty;

    [JsonPropertyName("quantity")]
    public int Quantity { get; set; }

    [JsonPropertyName("buy_price")]
    public double BuyPrice { get; set; }

    [JsonPropertyName("sell_price")]
    public double SellPrice { get; set; }

    [JsonPropertyName("last_price")]
    public double LastPrice { get; set; }

    [JsonPropertyName("realised_pnl")]
    public double RealisedPnl { get; set; }

    [JsonPropertyName("unrealised_pnl")]
    public double UnrealisedPnl { get; set; }

    [JsonPropertyName("total_pnl")]
    public double TotalPnl { get; set; }
}
