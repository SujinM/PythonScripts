using System.Text.Json.Serialization;

namespace ClientConsolApp.Models;

/// <summary>
/// An executed trade. Mirrors the FastAPI Trade Pydantic model.
/// </summary>
public class Trade
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

    [JsonPropertyName("transaction_type")]
    public string TransactionType { get; set; } = string.Empty;

    [JsonPropertyName("quantity")]
    public double Quantity { get; set; }

    [JsonPropertyName("price")]
    public double Price { get; set; }

    [JsonPropertyName("trade_date")]
    public DateTime? TradeDate { get; set; }

    [JsonPropertyName("trade_value")]
    public double TradeValue { get; set; }
}
