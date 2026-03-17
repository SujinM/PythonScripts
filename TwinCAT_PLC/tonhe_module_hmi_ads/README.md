# TONHE Module HMI ADS

PyQt6 HMI for monitoring and controlling TONHE V1.3 CAN charging modules via a **TwinCAT 3 PLC** using **ADS device notifications** (push-based, no polling).

Unlike `tonhe_module_hmi` which polls every 300 ms, this version subscribes to PLC variables via `ADSTRANS_SERVERONCHA` — the GUI updates only when a value actually changes, reducing bus load and improving responsiveness.

## Features

| Panel | Description |
|---|---|
| **Module Status** | State badge (OFF / ON / FAULT), live output voltage & current with large digit display, status text from PLC, boolean flag pills |
| **Module Control** | START / STOP / CLEAR FAULT commands; module & master address display; retry counter |
| **Setpoints** | Enter target voltage (V) and current (A), press Apply → writes encoded integers + pulses `bUpdateVI` |
| **Phase Info** | AC input phase voltages (Va, Vb, Vc) and ambient temperature from M_C_3 frames |
| **Fault & Diagnostics** | Decoded fault bits, extended fault/warning bits from M_C_4, PFC fault byte, RX frame count, last COB-ID |
| **Application Log** | All Python log records from every module shown in a scrollable table |

## Prerequisites

```
Python ≥ 3.10
TwinCAT 3 runtime with ThoneModuleTest.plcproj deployed
pyads ≥ 3.3.9  (TwinCAT ADS route configured on the host PC)
PyQt6 ≥ 6.4
pyqtgraph ≥ 0.13
numpy ≥ 1.24
```

## Quick start

```powershell
# From the tonhe_module_hmi_ads/ folder:
pip install -r requirements.txt

# Real PLC
python app.py

# Mock ADS (no hardware needed – PowerShell)
$env:MOCK_ADS = "1"; python app.py

# Remove mock flag when done
Remove-Item Env:MOCK_ADS
```

1. Choose **File → Open Config…** and select `config/tone_config.xml`
   (or edit the XML first with your TwinCAT AMS Net ID / IP address).
2. Click **Connect** in the Connection panel.
3. The HMI subscribes to all PLC variables via ADS notifications automatically.

## Config file

Edit `config/tone_config.xml` to match your TwinCAT host:

```xml
<Connection>
    <AMSNetID>5.1.204.160.1.1</AMSNetID>   <!-- AMS Net ID of TC3 runtime -->
    <IPAddress>192.168.0.100</IPAddress>    <!-- IP of TwinCAT host PC     -->
    <Port>851</Port>                        <!-- PLC runtime 1             -->
</Connection>
```

## ADS notification channels

The ADS router limits each connection to ~499 notification handles. This application automatically manages multiple channels when the number of subscribed variables exceeds that limit:

- Variables are batched into groups of 499 (`NOTIFICATION_CHANNEL_LIMIT`).
- The first batch uses the primary `ConnectionManager`.
- Each additional batch opens a dedicated `ConnectionManager + ADSClient + NotificationManager`.
- All channels are torn down cleanly on disconnect.

With the current 28 subscribed variables this is handled in a single channel.

## PLC variable mapping

All variables map to the `ThoneModuleTest` TwinCAT project:

| XML Name | PLC Symbol | Type | Direction |
|---|---|---|---|
| `GVL.nModuleVoltage` | GVL output voltage | REAL | Read (notified) |
| `GVL.nModuleCurrent` | GVL output current | REAL | Read (notified) |
| `GVL.nModuleStatus` | M_C_1 status byte | BYTE | Read (notified) |
| `GVL.wModuleFaults` | fault bit-field | UINT | Read (notified) |
| `GVL.wModuleExtFaultWarningBits` | extended faults | UINT | Read (notified) |
| `GVL.nPhaseVoltageA/B/C` | AC phase voltages | REAL | Read (notified) |
| `GVL.nAmbientTemperature` | module temperature | INT | Read (notified) |
| `MAIN.bStartModule` | start command | BOOL | Write |
| `MAIN.bStopModule` | stop command | BOOL | Write |
| `MAIN.bClearFault` | clear fault | BOOL | Write |
| `MAIN.nTargetVoltage` | voltage setpoint (0.1 V/bit) | UINT | Read/Write |
| `MAIN.nTargetCurrent` | current setpoint (0.01 A/bit) | UINT | Read/Write |
| `MAIN.bUpdateVI` | apply setpoint pulse | BOOL | Write |

## Project structure

```
tonhe_module_hmi_ads/
├── app.py                          Entry point
├── requirements.txt
├── setup.py                        cx_Freeze build script (exe / MSI)
├── config/
│   └── tone_config.xml             ADS + variable configuration
├── resources/
│   └── styles/
│       ├── dark.qss
│       └── light.qss
└── src/
    └── tone_hmi_ads/
        ├── constants.py            App-wide constants, PLC symbol names,
        │                           NOTIFICATION_CHANNEL_LIMIT = 499
        ├── app_context.py          Service container; setup_notifications()
        │                           opens extra channels if vars > 499
        ├── mock_ads.py             Simulated PLC for testing (MOCK_ADS=1)
        ├── controllers/
        │   ├── app_controller.py   Top-level orchestrator
        │   ├── connection_controller.py
        │   └── module_controller.py  Event-driven; no poll loop
        ├── models/
        │   └── log_table_model.py
        ├── utils/
        │   ├── qt_log_handler.py
        │   └── style_manager.py
        ├── views/
        │   ├── main_window.py
        │   ├── connection_panel.py
        │   ├── module_status_panel.py
        │   ├── module_control_panel.py
        │   ├── setpoint_panel.py
        │   ├── phase_info_panel.py
        │   ├── fault_panel.py
        │   ├── graph_panel.py
        │   ├── log_panel.py
        │   └── about_dialog.py
        └── workers/
            ├── notification_bridge.py  Thread-safe Qt signal bridge
            ├── connect_worker.py
            └── disconnect_worker.py
```

## Architecture: notification flow

```
ADS dispatcher thread
  └─ PLCVariable.change_hook()          (called by pyads on value change)
       └─ NotificationBridge.variable_changed.emit(name)
            │  (Qt auto-queues across threads)
            └─ ModuleController._on_variable_changed(name)   [GUI thread]
                 └─ updates only the panels affected by that variable
```

`NotificationBridge` is a `QObject` — PyQt6 automatically delivers the signal as a queued connection, so no manual locking or `QMetaObject.invokeMethod` is required.

## Build

```powershell
pip install cx_Freeze
python setup.py build        # produces build/exe.win-amd64-*/
python setup.py bdist_msi    # produces dist/ToneHMI_ADS-1.0.0-*.msi
```

## Themes

Switch between dark (default) and light via:
- **View → Dark theme / Light theme**, or
- **🌙 / ☀** toolbar buttons
