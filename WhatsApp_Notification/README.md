# WhatsApp Notification System

A production-grade Python notification system that sends WhatsApp messages
periodically or in response to trigger events.

Both **Twilio WhatsApp API** and **Meta WhatsApp Cloud API** are supported and
selectable via a single config line — no code changes required.

---

## Architecture overview

```
WhatsApp_Notification/
│
├── main.py                     ← Composition root / entry point
│
├── .env                        ← Your real secrets (NEVER commit — in .gitignore)
├── .env.template               ← Safe placeholder template (commit this)
├── .gitignore                  ← Excludes .env and config/config.ini
│
├── config/
│   ├── config.ini              ← Runtime config using ${ENV_VAR} refs (NEVER commit)
│   └── config.ini.template     ← Safe placeholder template (commit this)
│
├── core/
│   ├── notifier.py             ← Formats events and dispatches messages
│   ├── scheduler.py            ← Heartbeat loop (SIGINT-safe)
│   └── trigger_manager.py      ← Registers, lifecycles and polls triggers
│
├── services/
│   ├── base_service.py         ← Abstract notification service interface
│   └── whatsapp_service.py     ← Twilio + CloudAPI implementations + factory
│
├── triggers/
│   ├── base_trigger.py         ← Abstract trigger interface + TriggerEvent
│   ├── time_trigger.py         ← Periodic interval trigger
│   ├── file_trigger.py         ← File/directory change trigger
│   └── custom_trigger.py       ← User-extensible triggers + ThresholdTrigger
│
├── utils/
│   ├── logger.py               ← Centralised logging (console + rotating file)
│   └── config_loader.py        ← Typed INI config loader with validation
│
├── tests/                      ← Unit test suite
│   ├── __init__.py
│   ├── test_config_loader.py
│   ├── test_notifier.py
│   ├── test_triggers.py
│   └── test_scheduler.py
│
└── requirements.txt
```

---

## Installation

### Prerequisites

- Python 3.10 or later
- Works on **Linux**, **Windows**, **macOS**, and **Raspberry Pi**

### Steps

```bash
# 1. Clone / copy the project
cd WhatsApp_Notification

# 2. Create and activate a virtual environment
python -m venv .venv

# Linux / macOS / Raspberry Pi
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your secrets file from the template
cp .env.template .env
# Open .env and fill in your real Twilio / Cloud API credentials

# 5. Create your config file from the template
cp config/config.ini.template config/config.ini
# config.ini already uses ${ENV_VAR} references — no edits needed
# unless you want to change intervals, triggers, or log settings

# 6. Validate everything loads correctly (no messages sent)
python main.py --dry-run
```

---

## Secrets management

**Credentials must never be stored in `config.ini` or committed to Git.**
The system uses a `.env` file to hold secrets and `${ENV_VAR}` placeholders
in `config.ini` that are expanded at startup.

### File responsibilities

| File | Contains | Committed? |
|---|---|---|
| `.env` | Real API keys, tokens, phone numbers | **NO** — in `.gitignore` |
| `.env.template` | Placeholder variable names only | ✅ Yes |
| `config/config.ini` | Settings with `${VAR}` refs, no secrets | **NO** — in `.gitignore` |
| `config/config.ini.template` | Placeholder template | ✅ Yes |

### `.env` example

```dotenv
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_real_auth_token
TWILIO_FROM_NUMBER=whatsapp:+14155238886
TWILIO_TO_NUMBERS=whatsapp:+1234567890
```

### How `config.ini` references them

```ini
[whatsapp]
provider     = twilio
account_sid  = ${TWILIO_ACCOUNT_SID}
auth_token   = ${TWILIO_AUTH_TOKEN}
from_number  = ${TWILIO_FROM_NUMBER}
to_numbers   = ${TWILIO_TO_NUMBERS}
```

At startup `config_loader.py` loads `.env` automatically (using
`python-dotenv` when installed, falling back to a built-in parser),
then substitutes every `${VAR}` before any value reaches the application.
If a referenced variable is missing, a clear `KeyError` is raised
naming the exact variable that needs to be set.

### Deploying to a server / CI

Instead of a `.env` file, export the variables directly in the shell or
use your platform's secret store:

```bash
# Linux / macOS
export TWILIO_ACCOUNT_SID=ACxxxx
export TWILIO_AUTH_TOKEN=xxxx
export TWILIO_FROM_NUMBER=whatsapp:+14155238886
export TWILIO_TO_NUMBERS=whatsapp:+1234567890

python main.py
```

The config loader reads `os.environ` after the `.env` step, so all
platform-injected variables (Docker `--env`, GitHub Actions secrets,
systemd `EnvironmentFile`, etc.) work without any changes.

---

## Configuration

Open `config/config.ini` and set the values for your environment.

### Twilio provider

Add to `.env`:

```dotenv
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=whatsapp:+14155238886
TWILIO_TO_NUMBERS=whatsapp:+1234567890
```

`config.ini` (already set up by template):

```ini
[whatsapp]
provider     = twilio
account_sid  = ${TWILIO_ACCOUNT_SID}
auth_token   = ${TWILIO_AUTH_TOKEN}
from_number  = ${TWILIO_FROM_NUMBER}
to_numbers   = ${TWILIO_TO_NUMBERS}
```

Get credentials at <https://console.twilio.com>.  
For the sandbox, use `whatsapp:+14155238886` as `TWILIO_FROM_NUMBER`.

### Meta WhatsApp Cloud API provider

Add to `.env`:

```dotenv
WA_PHONE_NUMBER_ID=123456789012345
WA_BEARER_TOKEN=EAAxxxxxxxxxxxxxxx
WA_TO_NUMBERS=+1234567890
```

`config.ini`:

```ini
[whatsapp]
provider     = cloud_api
account_sid  = ${WA_PHONE_NUMBER_ID}
auth_token   = ${WA_BEARER_TOKEN}
from_number  = ${WA_PHONE_NUMBER_ID}
to_numbers   = ${WA_TO_NUMBERS}
```

Get credentials at <https://developers.facebook.com/apps/> → WhatsApp → API Setup.

### Notification interval

```ini
[notification]
interval_minutes = 5
```

### Triggers

```ini
[triggers]
enable_time_trigger   = true
enable_file_trigger   = false
enable_custom_trigger = false
watch_path            = /path/to/watch
```

---

## Running

```bash
# Standard run (blocking)
python main.py

# Custom config path
python main.py --config /etc/myapp/config.ini

# Validate config without sending any messages
python main.py --dry-run

# Faster polling tick (useful when testing file triggers)
python main.py --tick 5
```

Stop with **Ctrl-C** — the system shuts down gracefully.

---

## Adding a custom trigger

Create a Python file, e.g. `my_plc_trigger.py`:

```python
from triggers.custom_trigger import ThresholdTrigger

def build_triggers(cfg):
    """Return a list of BaseTrigger instances."""
    return [
        ThresholdTrigger(
            name_label   = "PLCPressureAlarm",
            value_getter = lambda: read_plc_register("DB1.DBD0"),
            threshold    = 95.0,
            above        = True,
            unit         = " bar",
            cooldown_seconds = 120,
        )
    ]
```

Then in `config.ini`:

```ini
[triggers]
enable_custom_trigger  = true
custom_trigger_module  = /absolute/path/my_plc_trigger.py
```

No other file needs to change.

---

## Extending the notification channel

Implement `BaseNotificationService` from `services/base_service.py`:

```python
from services.base_service import BaseNotificationService, SendResult, SendStatus

class SlackService(BaseNotificationService):
    @property
    def name(self): return "Slack"

    def validate_config(self): ...

    def send_message(self, to: str, body: str) -> SendResult:
        # your HTTP call here
        return SendResult(status=SendStatus.SUCCESS, provider_id="msg_id")
```

Pass an instance to `Notifier(service=SlackService(...), ...)` in `main.py`.

---

## Running tests

```bash
pytest tests/ -v
```

---

## Supported use-cases

| Scenario | Trigger class | Example |
|---|---|---|
| Periodic status ping | `TimeTrigger` | Every 5 minutes |
| Log / data file arrival | `FileTrigger` | New CSV in `/data` |
| PLC alarm | `ThresholdTrigger` | Register value > threshold |
| CPU / memory alert | `ThresholdTrigger` | `psutil.cpu_percent()` |
| Raspberry Pi sensor | `ThresholdTrigger` | ADC / temperature reading |
| Database row threshold | `ThresholdTrigger` | `SELECT COUNT(*)` |
| Sentinel file detection | `LambdaTrigger` | `/tmp/alert.flag` exists |
| Any custom logic | `CustomTrigger` subclass | Subclass `_evaluate()` |

---

## License

MIT
