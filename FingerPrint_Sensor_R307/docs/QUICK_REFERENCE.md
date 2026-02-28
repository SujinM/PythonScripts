# Quick Reference Guide

## Installation

```bash
pip install -e .
# or
bash scripts/install.sh
```

## Command Line

```bash
# Admin mode (enroll/delete users)
fingerprint-admin

# Reader mode (verify fingerprints)
fingerprint-reader

# Using Python module
python -m fingerprint_r307 admin
python -m fingerprint_r307 reader
```

## Python API - Common Tasks

### Initialize Sensor
```python
from fingerprint_r307 import FingerprintSensor
sensor = FingerprintSensor(port='/dev/ttyUSB0', baudrate=57600)
```

### Enroll User
```python
from fingerprint_r307.admin import UserManager
from fingerprint_r307.utils import ConfigManager

config = ConfigManager()
manager = UserManager(sensor, config)
manager.enroll_user("username")
```

### Verify Fingerprint
```python
from fingerprint_r307.reader import FingerprintVerifier

verifier = FingerprintVerifier(sensor, config)
result = verifier.verify()
```

### List All Users
```python
users = config.get_all_users()
for user in users:
    print(f"{user['position']}: {user['name']}")
```

### Delete User
```python
manager.delete_user(position=5)
```

### GPIO Control
```python
from fingerprint_r307.reader import GPIOHandler

gpio = GPIOHandler(pin=24)
gpio.trigger(duration=5.0)  # High for 5 seconds
gpio.cleanup()
```

## Configuration

**Default config location**: `~/.fingerprint_config.ini`

**Custom config**:
```python
config = ConfigManager(config_path='/custom/path/config.ini')
```

## Logging

**Default log location**: `~/.fingerprint_log.txt`

**Custom logging**:
```python
from fingerprint_r307.utils.logger import setup_logging
import logging

setup_logging(
    log_file='/custom/path/app.log',
    level=logging.DEBUG,
    console=True
)
```

## Serial Ports

| Platform | Common Ports |
|----------|--------------|
| Linux USB | `/dev/ttyUSB0` |
| Linux UART | `/dev/ttyAMA0` |
| Raspberry Pi | `/dev/serial0` |
| Windows | `COM3`, `COM4` |

## Error Handling

```python
from fingerprint_r307 import (
    FingerprintSensorError,
    EnrollmentError,
    VerificationError
)

try:
    sensor = FingerprintSensor()
except FingerprintSensorError as e:
    print(f"Error: {e}")
```

## Sensor Info

```python
info = sensor.get_sensor_info()
# Returns: {
#     'port': '/dev/ttyUSB0',
#     'baudrate': 57600,
#     'templates_used': 10,
#     'storage_capacity': 1000
# }
```

## Common Operations

### Check if user exists
```python
if config.user_exists(position):
    user = config.get_user(position)
```

### Get user count
```python
count = config.get_user_count()
```

### Clear all users
```python
config.clear_all()
```

### Read image
```python
if sensor.read_image():
    sensor.convert_image()
    position, accuracy = sensor.search_template()
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/fingerprint_r307

# Run specific test
pytest tests/test_sensor.py
```

## File Structure

```
~/.fingerprint_config.ini   # User database
~/.fingerprint_log.txt      # Application log
```

## Permissions (Linux)

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Or temporary permission
sudo chmod 666 /dev/ttyUSB0
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied | Add user to dialout group |
| Sensor not found | Check connections, verify port |
| Import error | Install dependencies: `pip install -r requirements.txt` |
| GPIO not working | Install RPi.GPIO: `pip install RPi.GPIO` |

## Admin Password

Default: `9510`

Change in: `src/fingerprint_r307/admin/cli.py`

## Examples

See `examples/` directory:
- `basic_usage.py` - Basic sensor operations
- `complete_workflow.py` - Full enrollment/verification
- `gpio_control.py` - GPIO integration

## Documentation

- [Installation Guide](INSTALLATION.md)
- [Usage Guide](USAGE.md)
- [Hardware Setup](HARDWARE_SETUP.md)
- [API Documentation](API.md)
