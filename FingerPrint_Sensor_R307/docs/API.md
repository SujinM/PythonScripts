# API Documentation

## Core Module

### FingerprintSensor

Main sensor interface class.

```python
from fingerprint_r307 import FingerprintSensor
```

#### Constructor

```python
FingerprintSensor(
    port: str = '/dev/ttyUSB0',
    baudrate: int = 57600,
    address: int = 0xFFFFFFFF,
    password: int = 0x00000000
)
```

**Parameters:**
- `port`: Serial port path
- `baudrate`: Communication baud rate
- `address`: Sensor address
- `password`: Sensor password

**Raises:**
- `SensorInitializationError`: If sensor cannot be initialized

#### Methods

##### get_template_count() -> int
Get the number of stored fingerprint templates.

##### get_storage_capacity() -> int
Get the maximum storage capacity of the sensor.

##### read_image() -> bool
Read fingerprint image from the sensor.

**Returns:** True if image captured successfully

##### convert_image(char_buffer: int = 1)
Convert captured image to characteristics.

**Parameters:**
- `char_buffer`: Buffer number (1 or 2)

##### search_template() -> Tuple[int, int]
Search for matching fingerprint template.

**Returns:** Tuple of (position_number, accuracy_score)
- position_number is -1 if no match found

##### compare_characteristics() -> int
Compare characteristics in buffers 1 and 2.

**Returns:** Accuracy score (0 if no match)

##### create_template()
Create template from characteristics in buffers.

##### store_template(position: int = -1) -> int
Store template at specified position.

**Parameters:**
- `position`: Position to store (-1 for next available)

**Returns:** Position where template was stored

##### delete_template(position: int) -> bool
Delete template at specified position.

**Parameters:**
- `position`: Template position number

**Returns:** True if successful

##### download_image(destination: str)
Download fingerprint image to a file.

**Parameters:**
- `destination`: File path to save image

##### get_sensor_info() -> dict
Get sensor information.

**Returns:** Dictionary with sensor details

## Admin Module

### UserManager

Manages user enrollment and deletion.

```python
from fingerprint_r307.admin import UserManager
```

#### Constructor

```python
UserManager(sensor: FingerprintSensor, config: ConfigManager)
```

#### Methods

##### enroll_user(user_id: str) -> bool
Enroll a new user fingerprint.

**Parameters:**
- `user_id`: User identifier

**Returns:** True if enrollment successful

**Raises:**
- `EnrollmentError`: If enrollment fails

##### delete_user(position: int) -> bool
Delete enrolled user.

**Parameters:**
- `position`: Template position number

**Returns:** True if deletion successful

##### view_all_users()
Display all enrolled users.

## Reader Module

### FingerprintVerifier

Handles fingerprint verification.

```python
from fingerprint_r307.reader import FingerprintVerifier
```

#### Constructor

```python
FingerprintVerifier(
    sensor: FingerprintSensor,
    config: ConfigManager,
    gpio_handler: Optional[GPIOHandler] = None,
    on_success: Optional[Callable] = None
)
```

**Parameters:**
- `sensor`: Fingerprint sensor instance
- `config`: Configuration manager
- `gpio_handler`: GPIO handler (optional)
- `on_success`: Callback on successful verification (optional)

#### Methods

##### verify() -> bool
Verify a fingerprint.

**Returns:** True if verification successful

**Raises:**
- `VerificationError`: If verification fails

##### run_continuous(delay: float = 1.0)
Run continuous verification loop.

**Parameters:**
- `delay`: Delay between attempts in seconds

### GPIOHandler

Manages GPIO operations.

```python
from fingerprint_r307.reader import GPIOHandler
```

#### Constructor

```python
GPIOHandler(pin: int = 24, mode: str = 'BCM')
```

**Parameters:**
- `pin`: GPIO pin number
- `mode`: GPIO mode ('BCM' or 'BOARD')

#### Methods

##### trigger(duration: float = 5.0)
Trigger GPIO pin high for specified duration.

**Parameters:**
- `duration`: Duration in seconds

##### set_high()
Set GPIO pin to HIGH.

##### set_low()
Set GPIO pin to LOW.

##### cleanup()
Cleanup GPIO resources.

## Utils Module

### ConfigManager

Manages user configuration file.

```python
from fingerprint_r307.utils import ConfigManager
```

#### Constructor

```python
ConfigManager(config_path: Optional[str] = None)
```

**Parameters:**
- `config_path`: Path to config file (uses default if None)

#### Methods

##### add_user(position: int, name: str) -> bool
Add user to configuration.

##### remove_user(position: int) -> bool
Remove user from configuration.

##### get_user(position: int) -> Optional[Dict[str, str]]
Get user information by position.

##### get_all_users() -> List[Dict[str, str]]
Get all enrolled users.

##### user_exists(position: int) -> bool
Check if user exists at position.

##### get_user_count() -> int
Get total number of enrolled users.

## Exceptions

All custom exceptions inherit from `FingerprintSensorError`.

```python
from fingerprint_r307 import (
    FingerprintSensorError,
    EnrollmentError,
    VerificationError,
    ConfigurationError
)
```

### Exception Hierarchy

- `FingerprintSensorError` - Base exception
  - `SensorInitializationError` - Sensor init failed
  - `EnrollmentError` - Enrollment failed
  - `VerificationError` - Verification failed
  - `ConfigurationError` - Config operation failed
  - `DeletionError` - Deletion failed
  - `ImageCaptureError` - Image capture failed
  - `TemplateError` - Template operation failed
