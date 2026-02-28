#!/bin/bash
# Installation script for Linux/Raspberry Pi

echo "====================================="
echo "Fingerprint R307 Sensor Installation"
echo "====================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Check if running on Raspberry Pi
if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo ""
    echo "Raspberry Pi detected. Installing RPi.GPIO..."
    pip3 install RPi.GPIO
fi

# Create config directory if it doesn't exist
echo ""
echo "Setting up configuration..."
if [ ! -f ~/.fingerprint_config.ini ]; then
    cp config/config.ini.template ~/.fingerprint_config.ini
    echo "Configuration template created at ~/.fingerprint_config.ini"
else
    echo "Configuration file already exists"
fi

# Check serial port permissions
echo ""
echo "Checking serial port permissions..."
if groups | grep -q dialout; then
    echo "User is in dialout group (serial port access granted)"
else
    echo "Adding user to dialout group for serial port access..."
    sudo usermod -a -G dialout $USER
    echo "Please logout and login again for changes to take effect"
fi

# Install package in development mode
echo ""
echo "Installing package..."
pip3 install -e .

echo ""
echo "====================================="
echo "Installation completed!"
echo "====================================="
echo ""
echo "Next steps:"
echo "1. Connect your R307 fingerprint sensor"
echo "2. Run 'fingerprint-admin' to manage users"
echo "3. Run 'fingerprint-reader' for verification"
echo ""
echo "For more information, see docs/INSTALLATION.md"
