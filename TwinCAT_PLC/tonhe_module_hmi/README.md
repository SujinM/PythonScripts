# TONHE Module HMI

PyQt6 HMI for monitoring and controlling TONHE V1.3 CAN charging modules via a **TwinCAT 3 PLC** using the ADS (AMS/TCP) protocol.

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
pyads ≥ 3.0  (TwinCAT ADS route configured on the host PC)
PyQt6 ≥ 6.6
pyqtgraph ≥ 0.13  (future graph panel)
```

## Quick start

```powershell
# From the tonhe_module_hmi/ folder:
pip install -r requirements.txt
python app.py

# MOCK ADS (PowerShell)
$env:MOCK_ADS=1; python app.py

# Build
scripts\build_cx.bat              # build exe tree
scripts\build_cx.bat clean        # clean build exe tree
scripts\build_cx.bat msi          # exe + MSI installer
scripts\build_cx.bat clean msi    # clean rebuild + MSI
```

1. Choose **File → Open Config…** and select `config/tone_config.xml`  
   (or edit the XML first with your TwinCAT AMS Net ID / IP address).
2. Click **Connect** in the Connection panel.
3. The HMI starts polling every 300 ms automatically.

## Config file

Edit `config/tone_config.xml` to match your TwinCAT host:

```xml
<Connection>
    <AMSNetID>5.1.204.160.1.1</AMSNetID>   <!-- AMS Net ID of TC3 runtime -->
    <IPAddress>192.168.0.100</IPAddress>    <!-- IP of TwinCAT host PC     -->
    <Port>851</Port>                        <!-- PLC runtime 1             -->
</Connection>
```

## PLC variable mapping

All variables map to the `ThoneModuleTest` TwinCAT project:

| XML Name | PLC Symbol | Type | Direction |
|---|---|---|---|
| `GVL.nModuleVoltage` | GVL output voltage | REAL | Read |
| `GVL.nModuleCurrent` | GVL output current | REAL | Read |
| `GVL.nModuleStatus` | M_C_1 status byte | BYTE | Read |
| `GVL.wModuleFaults` | fault bit-field | UINT | Read |
| `GVL.wModuleExtFaultWarningBits` | extended faults | UINT | Read |
| `GVL.nPhaseVoltageA/B/C` | AC phase voltages | REAL | Read |
| `GVL.nAmbientTemperature` | module temperature | INT | Read |
| `MAIN.bStartModule` | start command | BOOL | Write |
| `MAIN.bStopModule` | stop command | BOOL | Write |
| `MAIN.bClearFault` | clear fault | BOOL | Write |
| `MAIN.nTargetVoltage` | voltage setpoint (0.1 V/bit) | UINT | Read/Write |
| `MAIN.nTargetCurrent` | current setpoint (0.01 A/bit) | UINT | Read/Write |
| `MAIN.bUpdateVI` | apply setpoint pulse | BOOL | Write |

## Project structure

```
tonhe_module_hmi/
├── app.py                          Entry point
├── requirements.txt
├── config/
│   └── tone_config.xml             ADS + variable configuration
├── resources/
│   └── styles/
│       ├── dark.qss
│       └── light.qss
└── src/
    └── tone_hmi/
        ├── constants.py            App-wide constants + PLC symbol names
        ├── app_context.py          Service container (loads plc_ads_project backend)
        ├── controllers/
        │   ├── app_controller.py   Top-level orchestrator
        │   ├── connection_controller.py
        │   └── module_controller.py  Poll loop + command writes
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
        │   ├── log_panel.py
        │   └── about_dialog.py
        └── workers/
            ├── connect_worker.py
            ├── disconnect_worker.py
            └── poll_worker.py
```

## Future: Voltage & Current Graph

The `pyqtgraph` dependency is already included. To add the graph panel:

1. Create `src/tone_hmi/views/graph_panel.py` using `pyqtgraph.PlotWidget`
2. Buffer the last N voltage/current samples in `ModuleController._on_polled`
3. Add the panel to `MainWindow._build_central_widget` as a new tab or splitter pane

## Themes

Switch between dark (default) and light via:
- **View → Dark theme / Light theme**, or
- **🌙 / ☀** toolbar buttons
