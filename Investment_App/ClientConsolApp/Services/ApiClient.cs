using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using ClientConsolApp.Core;
using ClientConsolApp.Models;
using Microsoft.Extensions.Options;

namespace ClientConsolApp.Services;

/// <summary>
/// Raised when the FastAPI backend returns a non-2xx HTTP response.
/// Never contains raw secrets or tokens.
/// </summary>
public class ApiException : Exception
{
    public HttpStatusCode StatusCode { get; }
    public string? ErrorCode { get; }

    public ApiException(HttpStatusCode status, string message, string? errorCode = null)
        : base(message)
    {
        StatusCode = status;
        ErrorCode = errorCode;
    }
}

/// <summary>
/// Generic HTTP client for the FastAPI backend.
/// - Singleton-safe: injected via IHttpClientFactory.
/// - Retry logic: exponential backoff on transient errors (5xx, network).
/// - Does NOT retry 4xx — those are caller errors.
/// - Parses FastAPI's standard { status, error } error envelope.
/// </summary>
public class ApiClient
{
    private readonly HttpClient _http;
    private readonly ApiSettings _settings;

    private static readonly JsonSerializerOptions _json = new()
    {
        PropertyNameCaseInsensitive = true,
    };

    public ApiClient(HttpClient http, IOptions<ApiSettings> settings)
    {
        _http = http;
        _settings = settings.Value;
    }

    // ── Public methods ────────────────────────────────────────────────────

    public async Task<T> GetAsync<T>(string endpoint, CancellationToken ct = default)
        => await ExecuteWithRetryAsync<T>(() => _http.GetAsync(endpoint, ct), endpoint, ct);

    public async Task<T> PostAsync<T>(string endpoint, object? body = null, CancellationToken ct = default)
        => await ExecuteWithRetryAsync<T>(
            () => _http.PostAsJsonAsync(endpoint, body ?? new { }, _json, ct),
            endpoint, ct);

    // ── Retry wrapper ─────────────────────────────────────────────────────

    private async Task<T> ExecuteWithRetryAsync<T>(
        Func<Task<HttpResponseMessage>> sendRequest,
        string endpoint,
        CancellationToken ct)
    {
        int attempt = 0;
        while (true)
        {
            attempt++;
            try
            {
                var response = await sendRequest();
                return await ParseResponseAsync<T>(response);
            }
            catch (ApiException ex) when ((int)ex.StatusCode < 500)
            {
                // 4xx — client error, do not retry
                throw;
            }
            catch (Exception ex) when (attempt < _settings.MaxRetries)
            {
                int delay = _settings.RetryDelayMs * attempt;
                AppLogger.Warn($"Attempt {attempt}/{_settings.MaxRetries} failed for {endpoint}: {ex.Message}. Retrying in {delay}ms...");
                await Task.Delay(delay, ct);
            }
        }
    }

    // ── Response parser ───────────────────────────────────────────────────

    private static async Task<T> ParseResponseAsync<T>(HttpResponseMessage response)
    {
        if (response.IsSuccessStatusCode)
        {
            var result = await response.Content.ReadFromJsonAsync<T>(_json);
            return result ?? throw new ApiException(response.StatusCode, "Server returned an empty response body.");
        }

        // Attempt to parse FastAPI error envelope
        string raw = await response.Content.ReadAsStringAsync();
        string errorMessage = $"HTTP {(int)response.StatusCode} {response.ReasonPhrase}";
        string? errorCode = null;

        try
        {
            var envelope = JsonSerializer.Deserialize<ErrorResponse>(raw, _json);
            if (envelope?.Error is not null)
            {
                errorCode = envelope.Error.Code;
                errorMessage = envelope.Error.Message;
            }
        }
        catch { /* fall through with raw HTTP status message */ }

        throw new ApiException(response.StatusCode, errorMessage, errorCode);
    }
}
