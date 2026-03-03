# TwinCAT 3 PLC Monitor – PyQt6 GUI

A **production-ready PyQt6 desktop application** for monitoring and controlling TwinCAT 3 PLC variables via the ADS protocol.  It wraps the `plc_ads_project` ADS backend and provides a fully functional Windows GUI.

---

## Features

| Feature | Details |
|---|---|
| **MVC architecture** | Models / Views / Controllers separated; each file has a single responsibility |
| **Background workers** | `QRunnable` + `QThread` keep the GUI thread free during ADS I/O |
| **Live variable table** | Configurable polling; sortable and filterable by name |
| **Write dialog** | Type-aware value entry with range validation for all PLC integer types |
| **Log panel** | Real-time Python log stream with level filter and auto-scroll |
| **Dark / Light themes** | QSS stylesheets switchable at runtime; choice persisted in QSettings |
| **Config persistence** | Last-used XML path, theme, window geometry all saved between sessions |
| **JSON export** | One-click snapshot of all variable values to a timestamped JSON file |
| **Windows installer** | `cx_Freeze` builds a self-contained `.exe` and `.msi` installer |

---

## Project Structure

```
plc_gui_project/
│
├── app.py                          # Application entry point
├── setup.py                        # cx_Freeze Windows installer / MSI builder
├── setup.cfg                       # Package metadata & tool configuration
├── MANIFEST.in                     # Source distribution manifest
├── requirements.txt                # Runtime + dev dependencies
│
├── resources/
│   ├── styles/
│   │   ├── dark.qss                # Dark QSS theme
│   │   └── light.qss               # Light QSS theme
│   └── icons/                      # Place app.ico and toolbar icons here
│
└── src/
    └── plc_gui/
        │
        ├── __init__.py             # Package marker + __version__
        ├── constants.py            # Paths, sizes, column indices, QSettings keys
        ├── app_context.py          # Dependency container (ADS services)
        │
        ├── models/                 # Qt data models (no business logic)
        │   ├── variable_table_model.py   # QAbstractTableModel for PLC variables
        │   └── log_table_model.py        # QAbstractTableModel for log records
        │
        ├── views/                  # Purely presentational widgets
        │   ├── main_window.py      # QMainWindow shell + menu + toolbar + splitter
        │   ├── connection_panel.py # AMS Net ID / IP / Port + Connect LED
        │   ├── variable_panel.py   # Variable table + Refresh / Write / Poll toolbar
        │   ├── write_dialog.py     # Modal QDialog for writing a value to the PLC
        │   ├── log_panel.py        # Log stream QTableView with level filter
        │   └── about_dialog.py     # About QDialog
        │
        ├── controllers/            # View ↔ service glue (no Qt widget code)
        │   ├── connection_controller.py  # Open / close ADS; update LED
        │   ├── variable_controller.py    # Polling, refresh, write, JSON export
        │   └── app_controller.py         # Top-level orchestrator
        │
        ├── workers/                # Background Qt threads / runnables
        │   ├── connect_worker.py   # QRunnable – opens ADS connection
        │   ├── disconnect_worker.py# QRunnable – closes ADS connection
        │   └── poll_worker.py      # QThread  – periodic read_all loop
        │
        └── utils/
            ├── qt_log_handler.py   # logging.Handler → pyqtSignal bridge
            └── style_manager.py    # QSS loader + theme persistence
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python ≥ 3.11 | Tested on 3.11 – 3.13 |
| TwinCAT 3 / XAR | Runtime on the target PLC host |
| TwinCAT ADS router | Installed locally (TwinCAT XAE or XAR) |
| AMS Net ID route | Local PC must have a route to the PLC's AMS Net ID |

---

## Installation (development)

```powershell
# 1. Clone / unzip the repository so both sibling folders exist:
#    TwinCAT_PLC/
#    ├── plc_ads_project/   ← existing ADS backend
#    └── plc_gui_project/   ← this GUI project

# 2. Create and activate a virtual environment
cd plc_gui_project
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

---

## Build Windows Installer

```powershell
# Activate the venv (same environment used above)
.venv\Scripts\Activate.ps1

# Build standalone .exe (output → build\exe.win-amd64-<py_ver>\)
python setup.py build

# Build Windows MSI installer (output → dist\PLCMonitor-1.0.0-*.msi)
python setup.py bdist_msi
```

The MSI installer:
- Installs to `C:\Program Files\TwinCAT Tools\PLCMonitor\`
- Creates a **Desktop shortcut** and a **Start Menu shortcut**
- Bundles Python, PyQt6, and pyads — **no Python installation required** on the target PC

---

## Usage

### First run

1. Launch **PLCMonitor.exe** (or `python app.py`).
2. Click **Open Config** (toolbar / File menu) and select your `plc_config.xml`.
3. The connection panel fills in AMS Net ID and IP Address from the XML.
4. Click **Connect** — the LED turns green when the ADS handshake succeeds.
5. Click **▶ Start Poll** to start live variable updates.

### Writing a value

1. Select any row in the variable table.
2. Click **✎ Write**; a dialog opens pre-filled with the current value.
3. Enter the new value and click **Write**.
4. The next poll cycle reflects the updated value.

### Exporting to JSON

Click **⬇ Export JSON** in the variable panel toolbar to save a timestamped snapshot of all variable values.

---

## Architecture Overview

```
app.py
  └─► MainWindow (QMainWindow)
        ├─► AppController
        │     ├─► ConnectionController ──► ConnectWorker / DisconnectWorker (QRunnable)
        │     └─► VariableController   ──► PollWorker (QThread)
        │                              ──► _ReadAllWorker (QRunnable)
        │                              ──► VariableTableModel (QAbstractTableModel)
        ├─► ConnectionPanel (QGroupBox)
        ├─► VariablePanel   (QGroupBox + QTableView)
        └─► LogPanel        (QGroupBox + QTableView)
                                └─► LogTableModel (QAbstractTableModel)

QtLogHandler  ──► LogTableModel.append_record  (cross-thread queued signal)
AppContext     ──► ADSClient ──► plc_ads_project backend
```

---

## Configuration

The application reads the same `plc_config.xml` as `plc_ads_project`.  A copy of the default config is included in `build/config/plc_config.xml` in the installer bundle as a starting-point template.

Edit the XML to point at your PLC::

```xml
<Connection>
    <AMSNetID>5.1.204.160.1.1</AMSNetID>
    <IPAddress>192.168.0.100</IPAddress>
    <Port>851</Port>
</Connection>
```

---

## Theming

QSS files live in `resources/styles/`.  You can customise colours by editing `dark.qss` or `light.qss`.  Themes can be switched at runtime via **View → Dark theme / Light theme**.

---

## License

MIT — see `LICENSE` for details.
