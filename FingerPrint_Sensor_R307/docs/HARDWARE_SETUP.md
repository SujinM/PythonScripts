# Hardware Setup Guide

## R307 Fingerprint Sensor Module

### Overview

The R307 is a professional fingerprint sensor module with:
- TTL UART interface
- 500 DPI resolution
- Built-in image processing
- Low power consumption
- Support for 1:1 and 1:N matching modes

### Specifications

- **Voltage**: 3.3V or 5V DC
- **Current**: 
  - Working: < 120mA
  - Peak: < 150mA
  - Standby: < 10mA
- **Interface**: UART (TTL level)
- **Baud Rate**: 9600 - 115200 bps (default 57600)
- **Storage Capacity**: Typically 1000 fingerprints
- **Matching Time**: < 1 second
- **False Accept Rate (FAR)**: < 0.001%
- **False Reject Rate (FRR)**: < 1.0%

## Pinout

The R307 sensor has 6 pins:

1. **VCC (5V)**: Power supply (3.3V or 5V)
2. **GND**: Ground
3. **TXD**: Transmit data (sensor → device)
4. **RXD**: Receive data (device → sensor)
5. **TOUCH**: Touch detection output (active LOW)
6. **3.3V**: Alternative 3.3V power input

## Connection Diagrams

### Option 1: USB-to-Serial Adapter (Recommended for PC)

```
R307 Sensor          USB-Serial Adapter
-----------          ------------------
VCC (5V)      →      5V (or 3.3V)
GND           →      GND
TXD           →      RX
RXD           →      TX
TOUCH         →      (Optional: to GPIO)
```

**USB Cable Connections** (if using USB interface):
- Red: 5V
- White: D+
- Green: D-
- Black: GND

### Option 2: Raspberry Pi Direct UART

```
R307 Sensor          Raspberry Pi
-----------          ------------
VCC (5V)      →      Pin 2 (5V) or Pin 1 (3.3V)
GND           →      Pin 6 (GND)
TXD           →      Pin 10 (RXD/GPIO15)
RXD           →      Pin 8 (TXD/GPIO14)
TOUCH         →      Pin 18 (GPIO24) - Optional
```

**Important for Raspberry Pi:**
1. Disable serial console (if using GPIO UART):
   ```bash
   sudo raspi-config
   # Interface Options → Serial → 
   # Login shell: No
   # Serial hardware: Yes
   ```

2. Add to `/boot/config.txt`:
   ```
   enable_uart=1
   ```

3. Reboot:
   ```bash
   sudo reboot
   ```

### Option 3: Arduino

```
R307 Sensor          Arduino
-----------          -------
VCC (5V)      →      5V
GND           →      GND
TXD           →      RX (Pin 0) or SoftwareSerial RX
RXD           →      TX (Pin 1) or SoftwareSerial TX
```

Note: Use SoftwareSerial library to avoid conflicting with USB serial.

## Hardware Setup Steps

### 1. Physical Connection

1. **Power OFF** your device before making connections
2. Connect wires according to the diagram above
3. Ensure correct voltage (3.3V or 5V)
4. Double-check TX → RX and RX → TX (crossed connections)

### 2. Power LED Indicator

When powered correctly:
- **Red LED** should illuminate continuously
- **Blue LED** may flash when sensor is active

### 3. Testing Connection

#### Linux/Raspberry Pi:

Check if device is detected:
```bash
ls -l /dev/ttyUSB*
# or
ls -l /dev/ttyAMA0
```

Check permissions:
```bash
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB0
```

#### Windows:

Check Device Manager for COM port number.

### 4. Sensor Position

- Mount sensor at comfortable height for finger placement
- Ensure clean, dry environment
- Avoid direct sunlight on sensor window
- Keep sensor surface clean

## GPIO Configuration (Optional)

If using TOUCH output or GPIO control:

### Raspberry Pi GPIO

```python
from fingerprint_r307.reader import GPIOHandler

# Default pin 24 (BCM mode)
gpio = GPIOHandler(pin=24, mode='BCM')

# Or use BOARD mode
gpio = GPIOHandler(pin=18, mode='BOARD')
```

### Common GPIO Pins (BCM numbering):

- GPIO 24 (Pin 18)
- GPIO 23 (Pin 16)
- GPIO 25 (Pin 22)
- GPIO 17 (Pin 11)

## Troubleshooting

### No Response from Sensor

1. **Check LED**: Red LED should be ON
   - If OFF: Check power connections and voltage
2. **Check Serial Port**: 
   ```bash
   ls -l /dev/tty*
   ```
3. **Verify Baud Rate**: Default is 57600
4. **Swap TX/RX**: Try reversing TX and RX connections

### Poor Reading Quality

1. **Clean Sensor**: Use soft, dry cloth
2. **Finger Position**: Center finger on sensor
3. **Finger Pressure**: Apply moderate pressure
4. **Dry Fingers**: Moisture affects reading

### Permission Errors

Linux:
```bash
sudo usermod -a -G dialout $USER
# Logout and login again
```

Or temporary fix:
```bash
sudo chmod 666 /dev/ttyUSB0
```

### Raspberry Pi UART Issues

1. Disable Bluetooth (uses UART):
   ```bash
   sudo systemctl disable hciuart
   ```

2. Or use alternate UART:
   Add to `/boot/config.txt`:
   ```
   dtoverlay=pi3-miniuart-bt
   ```

## Best Practices

1. **Power Supply**: Use stable power source (avoid USB hubs)
2. **Cable Length**: Keep serial cables short (< 1 meter)
3. **Shielding**: Use shielded cables in noisy environments
4. **ESD Protection**: Handle sensor with ESD precautions
5. **Environmental**: Operating temp 0°C to 40°C, humidity < 90%

## Maintenance

1. **Clean Sensor Window**: Monthly with soft, dry cloth
2. **Check Connections**: Periodically verify wire integrity
3. **Update Firmware**: If available from manufacturer
4. **Backup Configuration**: Regular backups of `~/.fingerprint_config.ini`
