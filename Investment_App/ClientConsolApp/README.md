# Investment Portfolio Console Client

A **.NET 8 C# console application** that connects to the [FastAPI backend](../BackendFastAPI/README.md),
fetches live portfolio data, and displays it in a formatted interactive menu.

---

## Architecture

```
Program.cs            DI wiring + interactive menu loop
    │
    ├─ Core/
    │   ├─ Config.cs          ApiSettings POCO (BaseUrl, Timeout, Retries)
    │   └─ AppLogger.cs       Colour-coded timestamped console logger
    │
    ├─ Models/                C# mirror of every FastAPI Pydantic model
    │   ├─ ApiResponse.cs     Generic APIResponse<T> + ErrorResponse envelope
    │   ├─ Holding.cs
    │   ├─ Position.cs
    │   ├─ Trade.cs
    │   ├─ PortfolioSummary.cs
    │   ├─ AnalysisResult.cs  (includes Alert + SectorAllocation sub-models)
    │   └─ BrokerInfo.cs
    │
    ├─ Services/
    │   ├─ ApiClient.cs       GET/POST wrapper — retry, error parsing, no hardcoded URLs
    │   └─ PortfolioService.cs one method per REST endpoint
    │
    └─ Display/
        └─ ConsoleRenderer.cs  all formatted output — tables, colour P&L, menus
```

### CLI vs Server

The CLI talks **directly to the FastAPI REST API over HTTP**.
The FastAPI server must be running before you launch this app.

```
ClientConsolApp  ──HTTP──►  FastAPI (BackendFastAPI)  ──►  Broker APIs
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| .NET SDK | 8.0 or later |
| FastAPI backend | Running on http://localhost:8000 |

Install .NET SDK: https://dotnet.microsoft.com/download

---

## Setup

```powershell
# 1. Start the FastAPI backend (in a separate window)
cd ..\BackendFastAPI
.\start-dev.bat

# 2. Navigate to this project
cd ..\ClientConsolApp

# 3. Restore NuGet packages
dotnet restore

# 4. Build
dotnet build
```

### Configure the base URL

Edit `appsettings.json` if your FastAPI server runs on a different port:

```json
{
  "ApiSettings": {
    "BaseUrl": "http://localhost:8000",
    "TimeoutSeconds": 30,
    "MaxRetries": 3,
    "RetryDelayMs": 500
  },
  "DefaultBroker": "upstox"
}
```

Override with an environment variable (no file changes needed):

```powershell
$env:ApiSettings__BaseUrl = "http://localhost:9000"
dotnet run
```

---

## Running

```powershell
dotnet run
```

Or run the compiled binary directly:

```powershell
dotnet build -c Release
.\bin\Release\net8.0\ClientConsolApp.exe
```

---

## Building a Production EXE

### Quick build (EXE only)

```bat
build-release.bat
```

Produces a **self-contained, single-file Windows EXE** — no .NET installation required on the target machine:

```
bin\publish\win-x64\SujinsInvestment.exe   (~36 MB)
```

### With Windows Installer

1. Install **[Inno Setup 6](https://jrsoftware.org/isdl.php)**
2. Run:

```bat
build-release.bat /installer
```

Produces:

```
installer\Output\SujinsInvestment-Setup-1.0.0.exe
```

The installer includes:
- Start Menu shortcut
- Optional desktop shortcut
- Uninstaller (Add/Remove Programs)
- Windows 10 (1809+) version check

### What `build-release.bat` does

| Step | Action |
|------|--------|
| 1 | Regenerates `Assets/app.ico` via `create_icon.py` |
| 2 | `dotnet publish` with the `win-x64` profile (self-contained, ReadyToRun) |
| 3 | Runs Inno Setup compiler (only with `/installer` flag) |

### Publish profile details

The `Properties/PublishProfiles/win-x64.pubxml` profile sets:

| Option | Value |
|--------|-------|
| Runtime | `win-x64` |
| Self-contained | `true` |
| Single file | `true` |
| Compression | `true` |
| ReadyToRun | `true` (faster startup) |
| Debug symbols | stripped |

### EXE metadata (Windows file properties)

| Field | Value |
|-------|-------|
| Product name | Sujin's Investment |
| Version | 1.0.0 |
| Company | Sujin M |
| Description | Portfolio management console — Upstox & eToro |
| Copyright | © 2026 Sujin M |
| Icon | Navy + gold investment chart (`Assets/app.ico`) |

To bump the version, update `<Version>` in `ClientConsolApp.csproj` and the `#define AppVersion` in `installer/SujinsInvestment.iss`.

---

## Interactive Menu

```
╔══════════════════════════════════════════════╗
║   Investment Portfolio Console Client  v1.0  ║
╚══════════════════════════════════════════════╝

  Active broker : UPSTOX

  ── Portfolio ─────────────────────────────────
   1.  Portfolio Summary
   2.  Holdings
   3.  Positions
   4.  Trades
  ── Analysis ──────────────────────────────────
   5.  Full Analysis
   6.  Active Alerts
  ── System ────────────────────────────────────
   7.  List Brokers
   8.  Invalidate Cache
   9.  Switch Broker
   0.  Exit
```

Switch between `upstox` and `etoro` at runtime using option **9**.

---

## API Calls Made

| Menu Option | Method | Endpoint |
|---|---|---|
| Summary | GET | `/api/v1/{broker}/summary` |
| Holdings | GET | `/api/v1/{broker}/holdings` |
| Positions | GET | `/api/v1/{broker}/positions` |
| Trades | GET | `/api/v1/{broker}/trades` |
| Full Analysis | GET | `/api/v1/{broker}/analysis` |
| Active Alerts | GET | `/api/v1/{broker}/analysis/alerts` |
| List Brokers | GET | `/api/v1/brokers` |
| Invalidate Cache | POST | `/api/v1/{broker}/cache/invalidate` |

---

## Security

- **No secrets in code or config files.** API keys and tokens are read by the FastAPI backend from its own `.env` file.
- This client only sends requests to the FastAPI backend — it never touches broker APIs directly.
- Override `BaseUrl` via environment variable (`ApiSettings__BaseUrl`) — never hardcode it.
- `.gitignore` excludes `appsettings.Local.json` and `.env` for local overrides.

---

## Adding a New Endpoint

1. Add the response model to `Models/` (if new)
2. Add one method to `Services/PortfolioService.cs`
3. Add a `case` in `Program.cs`
4. Add a `Render*` method in `Display/ConsoleRenderer.cs`

No changes to `ApiClient.cs` or `Core/` are needed.

---

## Extending to UI (WPF / Blazor)

`PortfolioService` and `ApiClient` are UI-framework agnostic.
To move to a WPF or Blazor frontend:

1. Keep `Core/`, `Models/`, `Services/` as a shared class library
2. Replace `Display/ConsoleRenderer.cs` with your UI bindings
3. Replace `Program.cs` with your UI entry point

---

## License

MIT
