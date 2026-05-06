using System.Text.Json.Serialization;

namespace ClientConsolApp.Models;

/// <summary>
/// A single price entry inside a tick frame for one instrument.
///
/// Upstox fields  : Ltp (last traded price), Close (previous close).
/// eToro fields   : Bid, Ask, Name (trading symbol).
/// Ts             : Unix epoch seconds (server-side timestamp).
/// </summary>
public class LiveTickEntry
{
    /// <summary>Human-readable name / trading symbol (eToro).</summary>
    [JsonPropertyName("name")]
    public string? Name { get; set; }

    /// <summary>Last traded price (Upstox).</summary>
    [JsonPropertyName("ltp")]
    public double? Ltp { get; set; }

    /// <summary>Previous close price (Upstox).</summary>
    [JsonPropertyName("close")]
    public double? Close { get; set; }

    /// <summary>Bid price (eToro).</summary>
    [JsonPropertyName("bid")]
    public double? Bid { get; set; }

    /// <summary>Ask price (eToro).</summary>
    [JsonPropertyName("ask")]
    public double? Ask { get; set; }

    /// <summary>Last execution / trade price (eToro).</summary>
    [JsonPropertyName("last_exec")]
    public double? LastExec { get; set; }

    /// <summary>
    /// Session change % computed by the server: (current_mid - session_start_mid) / session_start_mid * 100.
    /// Positive = risen since session start; negative = fallen.
    /// </summary>
    [JsonPropertyName("change_pct")]
    public double? ServerChangePct { get; set; }

    /// <summary>Trading volume (eToro, when pushed by the server).</summary>
    [JsonPropertyName("volume")]
    public double? Volume { get; set; }

    /// <summary>Server timestamp (Unix epoch seconds).</summary>
    [JsonPropertyName("ts")]
    public double Ts { get; set; }

    // ── Computed helpers ──────────────────────────────────────────────────

    /// <summary>Best available price: LTP for Upstox, mid of Bid/Ask for eToro.</summary>
    public double? BestPrice => Ltp ?? (Bid.HasValue && Ask.HasValue ? (Bid + Ask) / 2 : Bid ?? Ask);

    /// <summary>Change from previous close (Upstox only).</summary>
    public double? ChangeFromClose =>
        Ltp.HasValue && Close.HasValue && Close.Value != 0
            ? Ltp.Value - Close.Value
            : null;

    /// <summary>Percentage change from previous close (Upstox only).</summary>
    public double? ChangePct =>
        Ltp.HasValue && Close.HasValue && Close.Value != 0
            ? (Ltp.Value - Close.Value) / Close.Value * 100
            : null;
}

/// <summary>
/// A complete tick frame pushed by the server over the WebSocket.
///
/// Success frame from the server::
///   { "broker": "upstox", "ticks": { "NSE_EQ|INE848E01016": { "ltp": 1234.5, ... } }, "ts": 1746567890.1 }
///   { "broker": "etoro",  "ticks": { "100001": { "bid": 1234.5, "ask": 1235.0, ... } }, "ts": 1746567890.1 }
///
/// Error frame::
///   { "broker": "upstox", "error": "...", "ts": 1746567890.1 }
/// </summary>
public class LiveTickFrame
{
    [JsonPropertyName("broker")]
    public string Broker { get; set; } = string.Empty;

    /// <summary>
    /// Map of instrument key → tick entry.
    /// Keys are Upstox instrument_keys ("NSE_EQ|INE848E01016") or
    /// eToro str(instrumentId) ("100001").
    /// Null when the server sent an error frame.
    /// </summary>
    [JsonPropertyName("ticks")]
    public Dictionary<string, LiveTickEntry>? Ticks { get; set; }

    /// <summary>Server error message. Non-null on error frames.</summary>
    [JsonPropertyName("error")]
    public string? Error { get; set; }

    /// <summary>
    /// True on keepalive ping frames emitted when eToro has been silent
    /// for more than the server's keepalive interval (~25 s).
    /// Callers should discard these frames — they carry no price data.
    /// </summary>
    [JsonPropertyName("ping")]
    public bool? Ping { get; set; }

    /// <summary>Server-side Unix epoch timestamp.</summary>
    [JsonPropertyName("ts")]
    public double Ts { get; set; }

    /// <summary>True if the frame carries price data (not an error).</summary>
    public bool HasTicks => Ticks is { Count: > 0 };

    /// <summary>Client-side timestamp of when the frame was received.</summary>
    [JsonIgnore]
    public DateTime ReceivedAt { get; set; } = DateTime.Now;
}
