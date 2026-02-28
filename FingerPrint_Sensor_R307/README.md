# Fingerprint R307 Sensor - Python Interface

Python library for interfacing with the R307 Fingerprint Sensor Module. Provides easy-to-use APIs for fingerprint enrollment, verification, and user management with GPIO integration support.

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Features

-  **Secure Authentication** - Biometric fingerprint verification
-  **User Management** - Easy enrollment and deletion of users
-  **GPIO Integration** - Raspberry Pi GPIO control for hardware integration
-  **Comprehensive Logging** - Track all authentication events
-  **High Accuracy** - Up to 500 DPI resolution
-  **Modular Design** - Clean, maintainable code architecture
-  **Well Documented** - Extensive documentation and examples
-  **Tested** - Unit tests with pytest

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/fingerprint-r307.git
cd fingerprint-r307

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

Or use the installation scripts:

```bash
# Linux/Raspberry Pi
bash scripts/install.sh

# Windows
scripts\install.bat
```

### Basic Usage

**Admin Mode** - Manage users:
```bash
fingerprint-admin
```

**Reader Mode** - Verify fingerprints:
```bash
fingerprint-reader
```

**Python API**:
```python
from fingerprint_r307 import FingerprintSensor

# Initialize sensor
sensor = FingerprintSensor(port='/dev/ttyUSB0')

# Get sensor info
info = sensor.get_sensor_info()
print(f"Templates: {info['templates_used']}/{info['storage_capacity']}")
```

## Hardware Information

### R307 Fingerprint Sensor Specifications

- **Resolution**: 500 DPI
- **Voltage**: 3.3V or 5V DC
- **Interface**: UART (TTL level)
- **Baud Rate**: 9600-115200 bps (default: 57600)
- **Storage**: Up to 1000 fingerprints
- **Matching Time**: < 1 second
- **False Accept Rate**: < 0.001%

### Pinout

| Pin | Description | Connection |
|-----|-------------|------------|
| VCC | 5V Power | 5V or 3.3V |
| GND | Ground | GND |
| TXD | Transmit | RX on device |
| RXD | Receive | TX on device |
| TOUCH | Touch detection | GPIO (optional) |

See [docs/HARDWARE_SETUP.md](docs/HARDWARE_SETUP.md) for detailed wiring diagrams.

## Documentation

-  [Installation Guide](docs/INSTALLATION.md) - Detailed installation instructions
-  [Usage Guide](docs/USAGE.md) - How to use the library
-  [Hardware Setup](docs/HARDWARE_SETUP.md) - Wiring and connections
-  [API Documentation](docs/API.md) - Complete API reference

## Project Structure

```
fingerprint-r307/
├── src/fingerprint_r307/      # Main package
│   ├── core/                  # Core sensor functionality
│   ├── admin/                 # User management
│   ├── reader/                # Verification & GPIO
│   └── utils/                 # Utilities (config, logging)
├── tests/                     # Unit tests
├── examples/                  # Usage examples
├── docs/                      # Documentation
├── scripts/                   # Installation scripts
└── config/                    # Configuration templates
```

## Examples

### Enroll a User

```python
from fingerprint_r307.core.sensor import FingerprintSensor
from fingerprint_r307.utils.config import ConfigManager
from fingerprint_r307.admin.user_manager import UserManager

sensor = FingerprintSensor()
config = ConfigManager()
manager = UserManager(sensor, config)

manager.enroll_user("JohnDoe")
```

### Verify Fingerprint with GPIO

```python
from fingerprint_r307.reader import FingerprintVerifier, GPIOHandler

gpio = GPIOHandler(pin=24)
verifier = FingerprintVerifier(sensor, config, gpio_handler=gpio)
verifier.run_continuous()
```

See [examples/](examples/) directory for more examples.

## Testing

Run tests with pytest:

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=src/fingerprint_r307 --cov-report=html
```

## Requirements

- Python 3.7+
- pyfingerprint library
- Raspberry Pi (optional, for GPIO)
- R307 Fingerprint Sensor Module


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on top of the [pyfingerprint](https://github.com/bastianraschke/pyfingerprint) library
- Hardware specifications from R307 datasheet


---

**Note**: This project requires an R307 Fingerprint Sensor Module. Ensure proper hardware connections before use. See [docs/HARDWARE_SETUP.md](docs/HARDWARE_SETUP.md) for details.