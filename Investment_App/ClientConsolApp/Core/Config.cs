namespace ClientConsolApp.Core;

/// <summary>
/// Strongly-typed settings bound from ApiSettings section in appsettings.json.
/// Override any value with environment variables: ApiSettings__BaseUrl=http://...
/// Never put secrets (tokens, keys) in this file — use environment variables.
/// </summary>
public class ApiSettings
{
    public const string SectionName = "ApiSettings";

    /// <summary>FastAPI backend base URL, e.g. http://localhost:8000</summary>
    public string BaseUrl { get; set; } = "http://localhost:8000";

    /// <summary>HTTP request timeout in seconds.</summary>
    public int TimeoutSeconds { get; set; } = 30;

    /// <summary>Maximum number of retry attempts on transient failures.</summary>
    public int MaxRetries { get; set; } = 3;

    /// <summary>Base delay in milliseconds between retries (multiplied by attempt number).</summary>
    public int RetryDelayMs { get; set; } = 500;
}
