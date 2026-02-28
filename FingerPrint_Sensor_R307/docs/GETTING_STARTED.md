# Getting Started with Fingerprint R307

## Welcome!

This guide will help you get started with the Fingerprint R307 Sensor project quickly.

## Prerequisites

- Python 3.7 or higher
- R307 Fingerprint Sensor Module
- USB-to-Serial adapter (or Raspberry Pi with UART)
- Basic knowledge of Python

## Installation Steps

### 1. Install Dependencies

**Option A - Automatic (Recommended)**
```bash
# Linux/Raspberry Pi
bash scripts/install.sh

# Windows
scripts\install.bat
```

**Option B - Manual**
```bash
# Install required packages
pip install -r requirements.txt

# For Raspberry Pi GPIO support
pip install RPi.GPIO

# Install the package
pip install -e .
```

### 2. Connect Hardware

1. Connect R307 sensor to your computer/Raspberry Pi
2. For USB-Serial adapter:
   - VCC → 5V
   - GND → GND
   - TXD → RX
   - RXD → TX

See [docs/HARDWARE_SETUP.md](HARDWARE_SETUP.md) for detailed wiring diagrams.

### 3. Verify Installation

```bash
python -m fingerprint_r307 --version
```

## First Use

### Step 1: Enroll Your First User

```bash
fingerprint-admin
```

1. Enter admin password (default: `9510`)
2. Select option `1` (Enroll New User)
3. Enter a username
4. Follow the on-screen prompts to scan your finger

### Step 2: Test Verification

```bash
fingerprint-reader
```

Place your enrolled finger on the sensor to verify it works!

## Common Tasks

### Manage Users
```bash
fingerprint-admin
```
- Enroll new users
- Delete users
- View all enrolled users
- Check sensor information

### Verify Fingerprints
```bash
fingerprint-reader
```
- Continuous verification mode
- GPIO trigger on success (Raspberry Pi)

## Python API Quick Start

```python
from fingerprint_r307 import FingerprintSensor
from fingerprint_r307.utils import ConfigManager
from fingerprint_r307.admin import UserManager

# Initialize
sensor = FingerprintSensor(port='/dev/ttyUSB0')  # Change port as needed
config = ConfigManager()
manager = UserManager(sensor, config)

# Enroll a user
manager.enroll_user("Alice")

# List all users
manager.view_all_users()
```

## Configuration Files

After first run, these files will be created:

- `~/.fingerprint_config.ini` - User database
- `~/.fingerprint_log.txt` - Application logs

## Port Configuration

### Linux/Raspberry Pi
Common ports:
- `/dev/ttyUSB0` - USB-Serial adapter
- `/dev/ttyAMA0` - Raspberry Pi UART
- `/dev/serial0` - Raspberry Pi serial (symlink)

### Windows
Check Device Manager:
- `COM3`, `COM4`, `COM5`, etc.

To change port in code:
```python
sensor = FingerprintSensor(port='COM3')  # Windows
sensor = FingerprintSensor(port='/dev/ttyUSB0')  # Linux
```

## Troubleshooting

### "Permission denied" on Linux
```bash
sudo usermod -a -G dialout $USER
# Then logout and login again
```

### Sensor Not Found
1. Check physical connections
2. Verify the correct port:
   ```bash
   ls -l /dev/ttyUSB*
   ```
3. Ensure sensor has power (red LED on)

### Import Errors
Install dependencies:
```bash
pip install -r requirements.txt
```

## Next Steps

1. **Read the Documentation**
   - [Usage Guide](USAGE.md) - Detailed usage instructions
   - [API Documentation](API.md) - Complete API reference
   - [Hardware Setup](HARDWARE_SETUP.md) - Wiring diagrams

2. **Explore Examples**
   - Check the `examples/` directory for code samples
   - `basic_usage.py` - Simple sensor operations
   - `complete_workflow.py` - Full enrollment/verification workflow
   - `gpio_control.py` - GPIO integration

3. **Run Tests**
   ```bash
   pip install -r requirements-dev.txt
   pytest
   ```

## Project Structure Overview

```
fingerprint-r307/
├── src/fingerprint_r307/    # Main package
│   ├── core/                # Sensor operations
│   ├── admin/               # User management
│   ├── reader/              # Verification
│   └── utils/               # Config & logging
├── examples/                # Usage examples
├── docs/                    # Documentation
├── tests/                   # Unit tests
└── scripts/                 # Installation scripts
```

## Security Notes

1. **Change Admin Password**: Edit `ADMIN_PASSWORD` in `src/fingerprint_r307/admin/cli.py`
2. **Protect Config File**: Set appropriate permissions on `~/.fingerprint_config.ini`
3. **Review Logs**: Check `~/.fingerprint_log.txt` for security events

## Support & Resources

- **Documentation**: See `docs/` directory
- **Examples**: See `examples/` directory
- **Issues**: Report on GitHub
- **Quick Reference**: [docs/QUICK_REFERENCE.md](QUICK_REFERENCE.md)


## Command Reference

```bash
# Admin mode
fingerprint-admin

# Reader mode
fingerprint-reader

# Using Python module
python -m fingerprint_r307 admin
python -m fingerprint_r307 reader

# Run setup
python scripts/setup_config.py

# Run tests
pytest

# View help
python -m fingerprint_r307 --help
```

