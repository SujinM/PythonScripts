#!/usr/bin/env python3
"""
Setup script to create initial configuration.
"""
import os
import sys
from pathlib import Path
import shutil


def main():
    """Create initial configuration files."""
    print("=" * 60)
    print("Fingerprint R307 - Configuration Setup")
    print("=" * 60)
    print()
    
    # Determine config paths
    home_dir = Path.home()
    config_file = home_dir / '.fingerprint_config.ini'
    log_file = home_dir / '.fingerprint_log.txt'
    
    # Config file
    if config_file.exists():
        print(f"✓ Configuration file already exists: {config_file}")
        overwrite = input("  Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("  Keeping existing configuration")
        else:
            create_config(config_file)
    else:
        create_config(config_file)
    
    print()
    
    # Log file
    if log_file.exists():
        print(f"✓ Log file already exists: {log_file}")
        size = log_file.stat().st_size
        print(f"  Size: {size} bytes")
        
        if size > 1024 * 1024:  # 1MB
            clear = input("  Clear log file? (y/N): ").strip().lower()
            if clear == 'y':
                log_file.write_text('')
                print("  Log file cleared")
    else:
        log_file.touch()
        print(f"✓ Log file created: {log_file}")
    
    print()
    
    # Serial port configuration
    print("Serial Port Configuration")
    print("-" * 60)
    
    if sys.platform.startswith('linux'):
        print("Common ports on Linux:")
        print("  /dev/ttyUSB0 - USB-Serial adapter")
        print("  /dev/ttyAMA0 - Raspberry Pi UART")
        print("  /dev/ttyS0   - Serial port 1")
        
        # Try to detect USB serial devices
        usb_devices = list(Path('/dev').glob('ttyUSB*'))
        if usb_devices:
            print(f"\nDetected USB serial devices:")
            for dev in usb_devices:
                print(f"  {dev}")
    
    elif sys.platform == 'win32':
        print("Common ports on Windows:")
        print("  COM3, COM4, COM5...")
        print("Check Device Manager for actual port number")
    
    else:
        print("Platform:", sys.platform)
    
    print()
    print("=" * 60)
    print("Configuration setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Connect your R307 sensor")
    print("2. Note the serial port (e.g., /dev/ttyUSB0 or COM3)")
    print("3. Run: fingerprint-admin")
    print()


def create_config(config_path: Path):
    """Create configuration file from template."""
    template_path = Path(__file__).parent.parent / 'config' / 'config.ini.template'
    
    if template_path.exists():
        shutil.copy(template_path, config_path)
        print(f"✓ Configuration created: {config_path}")
    else:
        # Create basic config
        config_path.write_text(
            "# Fingerprint R307 Configuration\n"
            "# Users will be added here automatically\n"
        )
        print(f"✓ Configuration created: {config_path}")


if __name__ == '__main__':
    main()
