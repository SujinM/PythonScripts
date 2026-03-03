# TwinCAT 3 PLC ADS Communication – Python Project

A **production-ready, modular Python project** for bidirectional communication with a TwinCAT 3 PLC using the ADS (Automation Device Specification) protocol via [pyads](https://pyads.readthedocs.io/).

---

## Features

| Feature | Details |
|---|---|
| **OOP / SOLID** | Strict layered architecture; each class has a single responsibility |
| **Thread safety** | All shared state guarded by `threading.RLock`; notifications delivered via a thread-safe queue |
| **Auto-reconnect** | Exponential back-off strategy; configurable max attempts, initial delay, and multiplier |
| **Watchdog** | Heartbeat thread detects silent link drops and triggers the reconnect loop |
| **ADS Notifications** | Device notifications update `PLCVariable` instances without polling |
| **Change hooks** | Register callables on each variable; triggered asynchronously from the dispatcher thread |
| **Data-type safety** | PLC type → pyads type resolution + Python value validation + integer range checks |
| **XML configuration** | All connection parameters, reconnect strategy, and variable definitions in one XML file |
| **JSON export** | Periodic registry snapshots written to timestamped JSON files |
| **Logging** | Rotating file + coloured console; per-module child loggers via `get_logger(__name__)` |
| **Type hints** | `from __future__ import annotations`; all public APIs fully annotated |
| **Tests** | Pytest test suite with mocked ADS I/O (no real PLC needed to run tests) |

---

## Project Structure

```
plc_ads_project/
│
├── main.py                         # Application entry point
│
├── config/
│   ├── plc_config.xml              # XML configuration (connection + variables)
│   └── config_loader.py            # Parses XML → frozen PLCConfig dataclasses
│
├── core/
│   ├── connection_manager.py       # ADS lifecycle, watchdog, auto-reconnect
│   ├── ads_client.py               # Thin façade: read/write/notify via pyads
│   ├── notification_manager.py     # ADS notification subscriptions + async dispatcher
│   └── datatype_converter.py       # PLC type ↔ pyads type + validation + coercion
│
├── models/
│   ├── plc_variable.py             # PLCVariable domain model (thread-safe)
│   └── variable_registry.py        # Central store: register, lookup, iterate variables
│
├── services/
│   ├── plc_read_service.py         # High-level read_variable / read_all
│   └── plc_write_service.py        # High-level write_variable + typed helpers
│
├── utils/
│   ├── logger.py                   # setup_logger() + get_logger() factory
│   └── custom_exceptions.py        # PLCADSBaseError hierarchy
│
├── tests/
│   ├── conftest.py                 # sys.path bootstrap for pytest
│   ├── test_plc_variable.py        # Unit tests – PLCVariable
│   ├── test_config_loader.py       # Unit tests – ConfigLoader + XML validation
│   ├── test_datatype_converter.py  # Unit tests – DataTypeConverter
│   ├── test_read_write_services.py # Unit tests – Read/Write services (mocked ADS)
│   └── test_connection_manager.py  # Unit tests – ConnectionManager (mocked pyads)
│
├── requirements.txt
└── pytest.ini
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python ≥ 3.11 | f-strings, `tomllib`, `match` not required, but 3.11+ is the target |
| TwinCAT 3 / XAR | TwinCAT runtime must be running on the target machine |
| TwinCAT ADS router | Must be installed locally (TwinCAT XAE or XAR installation) |
| AMS Net ID route | The local PC must have a route to the PLC's AMS Net ID |

---

## Installation

```bash
# 1. Clone / copy the project
cd plc_ads_project

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

# 3. Install runtime dependencies
pip install -r requirements.txt

# 4. Install test dependencies (optional)
pip install pytest pytest-cov
```

---

## Configuration

Edit `config/plc_config.xml` to match your TwinCAT installation:

```xml
<PLCConfig>
    <Connection>
        <AMSNetID>5.1.204.160.1.1</AMSNetID>   <!-- Your PLC AMS Net ID -->
        <IPAddress>192.168.0.100</IPAddress>    <!-- Your PLC IP address -->
        <Port>851</Port>                         <!-- TC3 Runtime 1 -->
    </Connection>

    <Reconnect>
        <MaxAttempts>10</MaxAttempts>
        <InitialDelaySeconds>1.0</InitialDelaySeconds>
        <BackoffMultiplier>2.0</BackoffMultiplier>
        <MaxDelaySeconds>60.0</MaxDelaySeconds>
    </Reconnect>

    <Variables>
        <Variable>
            <Name>MAIN.bMotorOn</Name>
            <Type>BOOL</Type>
        </Variable>
        <!-- Add more variables here -->
    </Variables>
</PLCConfig>
```

**Supported PLC types:** `BOOL`, `INT`, `DINT`, `UDINT`, `REAL`, `LREAL`, `STRING`, `ARRAY`

---

## Running

```bash
# Default (INFO logging, polls every 2 s)
python main.py

# Debug mode with custom config and poll rate
python main.py --log-level DEBUG --config config/plc_config.xml --poll-interval 1.0

# Show all options
python main.py --help
```

### What the application does at runtime

1. Loads `plc_config.xml`.
2. Opens the ADS connection (retries automatically if the PLC is not reachable).
3. Registers all configured variables in the `VariableRegistry`.
4. Subscribes to **ADS device notifications** → variable values update automatically when the PLC changes them.
5. Registers a **change hook** on each variable that prints live changes to stdout.
6. Enters the **polling loop**:
   * Reads all variables via ADS polling (complements notifications).
   * Prints a live status table.
   * Performs demo write operations (toggle motor on/off, ramp speed).
   * Exports a JSON snapshot to `exports/`.
7. On `Ctrl+C` or `SIGTERM`: unsubscribes all notifications, closes the ADS connection, stops all threads.

---

## Running Tests

```bash
# From the project root (plc_ads_project/)
pytest

# With coverage report
pytest --cov=. --cov-report=term-missing

# Skip connection-related tests (no PLC needed)
pytest -m "not integration"

python -m pytest tests/ -v --tb=short 2>&1
```

All unit tests use mocked `pyads` I/O and run without a real PLC.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                     main.py                         │
│   (init, orchestration, polling loop, shutdown)     │
└──────────────────────┬──────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │       Services          │
          │  PLCReadService         │
          │  PLCWriteService        │
          └─────────┬───────────────┘
                    │
     ┌──────────────▼──────────────────┐
     │            Core                 │
     │  ADSClient ←── ConnectionManager│
     │  NotificationManager            │
     │  DataTypeConverter              │
     └──────────────┬──────────────────┘
                    │
     ┌──────────────▼──────────────────┐
     │           Models                │
     │  VariableRegistry               │
     │    └── PLCVariable[]            │
     └─────────────────────────────────┘
                    │
     ┌──────────────▼──────────────────┐
     │       Config + Utils            │
     │  ConfigLoader (plc_config.xml)  │
     │  Logger, CustomExceptions       │
     └─────────────────────────────────┘
```

---

## Custom Exception Hierarchy

```
PLCADSBaseError
├── PLCConnectionError
│   └── PLCReconnectExhaustedError
├── PLCReadError
├── PLCWriteError
├── PLCNotificationError
├── PLCVariableNotFoundError
├── DataTypeMismatchError
└── XMLConfigError
```

---

## Key Design Decisions

### Why a two-stage notification pipeline?

The pyads ADS callback runs on an internal ADS thread.  Doing any significant
work inside that callback (logging, calling user hooks, etc.) risks blocking
notification delivery.  Instead, the `NotificationManager` places a minimal
`_NotificationItem` onto a thread-safe `queue.Queue` and returns immediately.
A dedicated daemon thread (`plc-notif-dispatcher`) dequeues items and
applies them to `PLCVariable` instances at its own pace.

### Why frozen dataclasses for configuration?

The `PLCConfig` family of dataclasses is `frozen=True` to make configuration
read-only after loading.  This eliminates an entire class of bugs where
configuration is accidentally mutated at runtime.

### Why `threading.RLock` instead of `threading.Lock`?

`PLCVariable` methods call each other (e.g. `update_value` → `validate_type`).
A non-reentrant lock would deadlock if both acquire the same lock.  The `RLock`
is re-entrant within the same thread, preventing this while maintaining mutual
exclusion between threads.

---

## License

MIT – see [LICENSE](LICENSE) for details.
