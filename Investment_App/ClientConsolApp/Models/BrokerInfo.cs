using System.Text.Json.Serialization;

namespace ClientConsolApp.Models;

/// <summary>A registered broker adapter entry from GET /api/v1/brokers.</summary>
public class BrokerInfo
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("configured")]
    public bool Configured { get; set; }
}
