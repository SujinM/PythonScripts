# Usage Guide

## Quick Start

### Admin Mode - Enroll Users

To manage users (enroll, delete, view):

```bash
fingerprint-admin
```

Or using Python module:

```bash
python -m fingerprint_r307 admin
```

#### Enrolling a New User

1. Start admin mode
2. Enter admin password (default: `9510`)
3. Select option `1` (Enroll New User)
4. Enter a user ID/name
5. Place finger on sensor when prompted
6. Remove finger
7. Place same finger again
8. User will be enrolled and assigned a registration number

#### Deleting a User

1. Start admin mode
2. Select option `2` (Delete User)
3. Enter the registration number to delete
4. User will be removed from sensor and configuration

#### Viewing All Users

1. Start admin mode
2. Select option `3` (View All Users)
3. All enrolled users will be displayed

### Reader Mode - Verify Fingerprints

To run the fingerprint reader for authentication:

```bash
fingerprint-reader
```

Or:

```bash
python -m fingerprint_r307 reader
```

This will continuously scan for fingerprints and verify against enrolled users.

## Python API Usage

### Basic Sensor Operations

```python
from fingerprint_r307 import FingerprintSensor

# Initialize sensor
sensor = FingerprintSensor(port='/dev/ttyUSB0', baudrate=57600)

# Get sensor info
info = sensor.get_sensor_info()
print(f"Templates: {info['templates_used']}/{info['storage_capacity']}")

# Read and search fingerprint
if sensor.read_image():
    sensor.convert_image()
    position, accuracy = sensor.search_template()
    if position >= 0:
        print(f"Match found at position {position} with accuracy {accuracy}")
```

### User Management

```python
from fingerprint_r307.core.sensor import FingerprintSensor
from fingerprint_r307.utils.config import ConfigManager
from fingerprint_r307.admin.user_manager import UserManager

# Initialize components
sensor = FingerprintSensor()
config = ConfigManager()
user_manager = UserManager(sensor, config)

# Enroll a user
user_manager.enroll_user("JohnDoe")

# Delete a user
user_manager.delete_user(position=0)

# View all users
user_manager.view_all_users()
```

### Verification with GPIO

```python
from fingerprint_r307.core.sensor import FingerprintSensor
from fingerprint_r307.utils.config import ConfigManager
from fingerprint_r307.reader.verifier import FingerprintVerifier
from fingerprint_r307.reader.gpio_handler import GPIOHandler

# Initialize components
sensor = FingerprintSensor()
config = ConfigManager()
gpio = GPIOHandler(pin=24)

# Custom callback on successful verification
def on_verified(user_name, position, accuracy):
    print(f"Welcome, {user_name}!")
    # Custom logic here

# Create verifier
verifier = FingerprintVerifier(
    sensor=sensor,
    config=config,
    gpio_handler=gpio,
    on_success=on_verified
)

# Run continuous verification
verifier.run_continuous()
```

### Configuration Management

```python
from fingerprint_r307.utils.config import ConfigManager

# Initialize config manager
config = ConfigManager()

# Add user
config.add_user(position=5, name="JohnDoe")

# Get user info
user_info = config.get_user(5)
print(user_info['name'])

# Get all users
all_users = config.get_all_users()

# Remove user
config.remove_user(5)

# Get user count
count = config.get_user_count()
```

### Custom Logging

```python
from fingerprint_r307.utils.logger import setup_logging
import logging

# Setup logging with custom path and console output
setup_logging(
    log_file="/custom/path/fingerprint.log",
    level=logging.DEBUG,
    console=True
)
```

## Configuration File

The configuration file is stored at `~/.fingerprint_config.ini` by default.

Format:
```ini
[position_number]
Name = user_id
Enrolled = True
```

Example:
```ini
[0]
Name = JohnDoe
Enrolled = True

[1]
Name = JaneSmith
Enrolled = True
```

## Command Line Options

### Admin Interface

```bash
fingerprint-admin
```

Interactive menu with options:
1. Enroll New User
2. Delete User
3. View All Users
4. Sensor Information
5. Exit

### Reader Interface

```bash
fingerprint-reader
```

Runs continuous verification mode.

## Security Considerations

1. **Change Admin Password**: Modify `ADMIN_PASSWORD` in `admin/cli.py`
2. **Secure Configuration**: Protect `~/.fingerprint_config.ini` with appropriate permissions
3. **Log Files**: Regularly rotate and secure log files at `~/.fingerprint_log.txt`
4. **Physical Security**: Ensure the sensor is physically protected from tampering

## Customization

### Custom Serial Port

```python
sensor = FingerprintSensor(port='/dev/ttyAMA0')
```

### Custom GPIO Pin

```python
gpio = GPIOHandler(pin=18)
```

### Custom Config Path

```python
config = ConfigManager(config_path='/custom/path/config.ini')
```
