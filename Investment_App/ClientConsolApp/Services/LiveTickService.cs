using System.Net.WebSockets;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using ClientConsolApp.Core;
using ClientConsolApp.Models;
using Microsoft.Extensions.Options;

namespace ClientConsolApp.Services;

/// <summary>
/// WebSocket client that connects to the FastAPI live feed endpoint and
/// streams <see cref="LiveTickFrame"/> objects to the caller.
///
/// Endpoint consumed: <c>WS /api/v1/{broker}/ws/live[?instruments=KEY1,KEY2,...]</c>
///
/// The base HTTP URL from <see cref="ApiSettings.BaseUrl"/> is automatically
/// converted to a WebSocket URL (http → ws, https → wss).
///
/// Usage::
///
///   await foreach (var frame in svc.StreamAsync("upstox", ct))
///   {
///       if (frame.HasTicks) Console.WriteLine(frame.Ticks!["NSE_EQ|INE848E01016"].Ltp);
///   }
///
/// The stream reconnects automatically on transient network errors until the
/// <paramref name="ct"/> is cancelled or the caller stops iterating.
/// </summary>
public class LiveTickService
{
    private const int ReconnectDelayMs = 3_000;
    private const int ReceiveBufferBytes = 16_384;  // 16 KB per message

    private readonly ApiSettings _settings;

    private static readonly JsonSerializerOptions _json = new()
    {
        PropertyNameCaseInsensitive = true,
    };

    public LiveTickService(IOptions<ApiSettings> settings)
    {
        _settings = settings.Value;
    }

    // ── Public API ────────────────────────────────────────────────────────

    /// <summary>
    /// Yield <see cref="LiveTickFrame"/> objects from the live WebSocket feed.
    ///
    /// Auto-resolves instrument keys from the broker's current holdings when
    /// <paramref name="instruments"/> is empty.
    ///
    /// Reconnects automatically on transient errors. Stops cleanly when
    /// <paramref name="ct"/> is cancelled.
    /// </summary>
    /// <param name="broker">Broker identifier: "upstox" or "etoro".</param>
    /// <param name="instruments">
    /// Optional comma-separated instrument keys.
    /// Upstox: "NSE_EQ|INE848E01016,NSE_EQ|INE002A01018"
    /// eToro : "100001,1001"
    /// Leave empty to auto-resolve from holdings.
    /// </param>
    /// <param name="ct">Cancellation token — cancel to stop streaming.</param>
    public async IAsyncEnumerable<LiveTickFrame> StreamAsync(
        string broker,
        string instruments = "",
        [EnumeratorCancellation] CancellationToken ct = default)
    {
        var uri = BuildUri(broker, instruments);

        while (!ct.IsCancellationRequested)
        {
            using var ws = new ClientWebSocket();
            ws.Options.SetRequestHeader("User-Agent", "SujinsInvestment/1.0");

            // Connect — failure logs a warning and triggers reconnect delay
            bool connected = await TryConnectAsync(ws, uri, ct);
            if (!connected)
            {
                try   { await Task.Delay(ReconnectDelayMs, ct); }
                catch (OperationCanceledException) { yield break; }
                continue;
            }

            // Stream frames — ReceiveFramesAsync catches all internal errors
            // and ends cleanly so yield is never inside a try/catch here
            await foreach (var frame in ReceiveFramesAsync(ws, ct))
                yield return frame;

            if (ct.IsCancellationRequested) yield break;

            // Brief pause before reconnect
            try   { await Task.Delay(ReconnectDelayMs, ct); }
            catch (OperationCanceledException) { yield break; }
        }
    }

    // ── Internals ─────────────────────────────────────────────────────────

    /// <summary>Connect to the WebSocket URI. Returns false on failure.</summary>
    private static async Task<bool> TryConnectAsync(ClientWebSocket ws, Uri uri, CancellationToken ct)
    {
        try
        {
            await ws.ConnectAsync(uri, ct);
            AppLogger.Info($"WS connected \u2192 {uri}");
            return true;
        }
        catch (OperationCanceledException) { return false; }
        catch (WebSocketException ex)
        {
            AppLogger.Warn($"WS connect failed ({ex.Message}). Retrying in {ReconnectDelayMs / 1000}s...");
            return false;
        }
        catch (Exception ex)
        {
            AppLogger.Warn($"WS connect error: {ex.Message}. Retrying in {ReconnectDelayMs / 1000}s...");
            return false;
        }
    }

    /// <summary>
    /// Read WebSocket text frames and deserialise each into a <see cref="LiveTickFrame"/>.
    /// Handles fragmented frames (multi-part WS messages) transparently.
    /// All network/protocol errors are caught internally; the iterator ends cleanly.
    /// </summary>
    private static async IAsyncEnumerable<LiveTickFrame> ReceiveFramesAsync(
        ClientWebSocket ws,
        [EnumeratorCancellation] CancellationToken ct)
    {
        var buffer = new byte[ReceiveBufferBytes];
        var messageBuffer = new MemoryStream(ReceiveBufferBytes);

        while (ws.State == WebSocketState.Open && !ct.IsCancellationRequested)
        {
            messageBuffer.SetLength(0);
            WebSocketReceiveResult result;

            // Accumulate all fragments — catch network errors and end cleanly
            try
            {
                do
                {
                    result = await ws.ReceiveAsync(new ArraySegment<byte>(buffer), ct);

                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        // Server closed the connection — let caller reconnect
                        try { await ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "server close", ct); } catch { }
                        yield break;
                    }

                    if (result.MessageType != WebSocketMessageType.Text)
                        continue;

                    await messageBuffer.WriteAsync(buffer.AsMemory(0, result.Count), ct);
                }
                while (!result.EndOfMessage);
            }
            catch (OperationCanceledException) { yield break; }
            catch (WebSocketException ex)
            {
                AppLogger.Warn($"WS connection lost: {ex.Message}");
                yield break;
            }

            if (messageBuffer.Length == 0) continue;

            // Deserialise
            LiveTickFrame? frame = null;
            try
            {
                messageBuffer.Position = 0;
                frame = await JsonSerializer.DeserializeAsync<LiveTickFrame>(messageBuffer, _json, ct);
            }
            catch (JsonException ex)
            {
                AppLogger.Warn($"WS parse error: {ex.Message}");
                continue;
            }

            if (frame is not null)
            {
                frame.ReceivedAt = DateTime.Now;
                yield return frame;
            }
        }
    }

    /// <summary>
    /// Convert the HTTP base URL to a WebSocket URL and append the live path.
    /// http://host → ws://host/api/v1/{broker}/ws/live
    /// https://host → wss://host/api/v1/{broker}/ws/live
    /// </summary>
    private Uri BuildUri(string broker, string instruments)
    {
        var baseUrl = _settings.BaseUrl.TrimEnd('/');

        // Replace scheme: http → ws, https → wss
        if (baseUrl.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
            baseUrl = "wss://" + baseUrl["https://".Length..];
        else if (baseUrl.StartsWith("http://", StringComparison.OrdinalIgnoreCase))
            baseUrl = "ws://" + baseUrl["http://".Length..];

        var path = $"{baseUrl}/api/v1/{broker}/ws/live";
        if (!string.IsNullOrWhiteSpace(instruments))
            path += $"?instruments={Uri.EscapeDataString(instruments)}";

        return new Uri(path);
    }
}
