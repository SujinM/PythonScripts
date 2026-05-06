using ClientConsolApp.Models;

namespace ClientConsolApp.Services;

/// <summary>
/// Typed client for the Investment Portfolio FastAPI backend.
/// Each method corresponds to exactly one REST endpoint.
/// Easily extendable: add a new method for every new endpoint.
/// </summary>
public class PortfolioService
{
    private readonly ApiClient _client;

    public PortfolioService(ApiClient client)
    {
        _client = client;
    }

    // ── System ────────────────────────────────────────────────────────────

    /// <summary>GET /api/v1/brokers — list all registered broker adapters.</summary>
    public Task<ApiResponse<List<BrokerInfo>>> GetBrokersAsync(CancellationToken ct = default)
        => _client.GetAsync<ApiResponse<List<BrokerInfo>>>("/api/v1/brokers", ct);

    // ── Portfolio ─────────────────────────────────────────────────────────

    /// <summary>GET /api/v1/{broker}/holdings</summary>
    public Task<ApiResponse<List<Holding>>> GetHoldingsAsync(string broker, CancellationToken ct = default)
        => _client.GetAsync<ApiResponse<List<Holding>>>($"/api/v1/{broker}/holdings", ct);

    /// <summary>GET /api/v1/{broker}/positions</summary>
    public Task<ApiResponse<List<Position>>> GetPositionsAsync(string broker, CancellationToken ct = default)
        => _client.GetAsync<ApiResponse<List<Position>>>($"/api/v1/{broker}/positions", ct);

    /// <summary>GET /api/v1/{broker}/trades</summary>
    public Task<ApiResponse<List<Trade>>> GetTradesAsync(string broker, CancellationToken ct = default)
        => _client.GetAsync<ApiResponse<List<Trade>>>($"/api/v1/{broker}/trades", ct);

    /// <summary>GET /api/v1/{broker}/summary</summary>
    public Task<ApiResponse<PortfolioSummary>> GetSummaryAsync(string broker, CancellationToken ct = default)
        => _client.GetAsync<ApiResponse<PortfolioSummary>>($"/api/v1/{broker}/summary", ct);

    // ── Analysis ──────────────────────────────────────────────────────────

    /// <summary>GET /api/v1/{broker}/analysis</summary>
    public Task<ApiResponse<AnalysisResult>> GetAnalysisAsync(string broker, CancellationToken ct = default)
        => _client.GetAsync<ApiResponse<AnalysisResult>>($"/api/v1/{broker}/analysis", ct);

    /// <summary>GET /api/v1/{broker}/analysis/alerts</summary>
    public Task<ApiResponse<List<Alert>>> GetAlertsAsync(string broker, CancellationToken ct = default)
        => _client.GetAsync<ApiResponse<List<Alert>>>($"/api/v1/{broker}/analysis/alerts", ct);

    // ── Cache ─────────────────────────────────────────────────────────────

    /// <summary>POST /api/v1/{broker}/cache/invalidate — force fresh API fetch.</summary>
    public Task<ApiResponse<object>> InvalidateCacheAsync(string broker, CancellationToken ct = default)
        => _client.PostAsync<ApiResponse<object>>($"/api/v1/{broker}/cache/invalidate", null, ct);
}
