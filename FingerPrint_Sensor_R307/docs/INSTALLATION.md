# Installation Guide

## Requirements

- Python 3.7 or higher
- R307 Fingerprint Sensor Module
- For Raspberry Pi: RPi.GPIO library
- USB-to-Serial adapter or direct UART connection

## Hardware Setup

### Wiring

Connect the R307 sensor to your device:

- **5V** (or 3.3V) → Power supply
- **GND** → Ground
- **TXD** → RX on your device/USB-Serial adapter
- **RXD** → TX on your device/USB-Serial adapter
- **TOUCH** → Optional: Connect to GPIO for touch detection

### USB-Serial Adapter

If using a USB-Serial adapter:
1. Connect the adapter to your computer
2. Identify the serial port (usually `/dev/ttyUSB0` on Linux)
3. Ensure you have read/write permissions:
   ```bash
   sudo usermod -a -G dialout $USER
   ```

## Software Installation

### Option 1: Install from PyPI (when published)

```bash
pip install fingerprint-r307
```

### Option 2: Install from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fingerprint-r307.git
   cd fingerprint-r307
   ```

2. Install in development mode:
   ```bash
   pip install -e .
   ```

3. Or install with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Option 3: Direct Install

```bash
pip install -r requirements.txt
```

## Raspberry Pi Specific

For Raspberry Pi GPIO support:

```bash
pip install RPi.GPIO
```

Or install with extras:

```bash
pip install "fingerprint-r307[rpi]"
```

## Configuration

1. Copy the configuration template:
   ```bash
   cp config/config.ini.template ~/.fingerprint_config.ini
   ```

2. The configuration file will be automatically created on first run.

## Testing Installation

Test the sensor connection:

```bash
python -m fingerprint_r307 admin
```

This will launch the admin interface. If the sensor initializes successfully, you're ready to go!

## Troubleshooting

### Permission Denied on Serial Port

```bash
sudo chmod 666 /dev/ttyUSB0
# Or add user to dialout group
sudo usermod -a -G dialout $USER
# Then logout and login again
```

### Sensor Not Detected

1. Check physical connections
2. Verify the correct serial port
3. Ensure the sensor is powered (red LED should be on)
4. Try a different USB port or cable

### Import Errors

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

For development:

```bash
pip install -r requirements-dev.txt
```
