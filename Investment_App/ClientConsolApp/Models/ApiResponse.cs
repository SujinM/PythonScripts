using System.Text.Json.Serialization;

namespace ClientConsolApp.Models;

/// <summary>
/// Standard success envelope returned by every FastAPI endpoint.
/// Maps to: { "status": "success", "data": ... }
/// </summary>
public class ApiResponse<T>
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    [JsonPropertyName("data")]
    public T? Data { get; set; }
}

/// <summary>Error detail inside the error envelope.</summary>
public class ErrorDetail
{
    [JsonPropertyName("code")]
    public string Code { get; set; } = string.Empty;

    [JsonPropertyName("message")]
    public string Message { get; set; } = string.Empty;

    [JsonPropertyName("broker")]
    public string? Broker { get; set; }
}

/// <summary>
/// Error envelope returned on 4xx / 5xx responses.
/// Maps to: { "status": "error", "error": { "code": "...", "message": "..." } }
/// </summary>
public class ErrorResponse
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "error";

    [JsonPropertyName("error")]
    public ErrorDetail? Error { get; set; }
}
