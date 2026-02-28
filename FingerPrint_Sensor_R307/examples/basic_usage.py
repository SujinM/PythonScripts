"""
Example: Basic sensor usage
Demonstrates basic sensor initialization and operations.
"""
from fingerprint_r307 import FingerprintSensor

def main():
    print("=== Basic Sensor Usage Example ===\n")
    
    # Initialize sensor with default settings
    print("Initializing sensor...")
    try:
        sensor = FingerprintSensor(
            port='/dev/ttyUSB0',  # Change to your port
            baudrate=57600
        )
        print("✓ Sensor initialized successfully\n")
    except Exception as e:
        print(f"✗ Failed to initialize sensor: {e}")
        return
    
    # Get sensor information
    info = sensor.get_sensor_info()
    print("Sensor Information:")
    print(f"  Port: {info['port']}")
    print(f"  Baud Rate: {info['baudrate']}")
    print(f"  Templates Used: {info['templates_used']}")
    print(f"  Storage Capacity: {info['storage_capacity']}")
    print(f"  Available Slots: {info['storage_capacity'] - info['templates_used']}")
    print()
    
    # Read and search for fingerprint
    print("Place finger on sensor to test...")
    try:
        if sensor.read_image():
            print("✓ Fingerprint image captured")
            
            # Convert image to characteristics
            sensor.convert_image()
            print("✓ Image converted to characteristics")
            
            # Search for matching template
            position, accuracy = sensor.search_template()
            
            if position >= 0:
                print(f"✓ Match found!")
                print(f"  Position: #{position}")
                print(f"  Accuracy: {accuracy}")
            else:
                print("✗ No match found")
        else:
            print("✗ Failed to capture fingerprint")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
