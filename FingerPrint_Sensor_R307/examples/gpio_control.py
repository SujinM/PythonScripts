"""
Example: Custom verification with GPIO control
Demonstrates advanced GPIO integration.
"""
import time
from fingerprint_r307.core.sensor import FingerprintSensor
from fingerprint_r307.utils.config import ConfigManager
from fingerprint_r307.reader.verifier import FingerprintVerifier
from fingerprint_r307.reader.gpio_handler import GPIOHandler


def main():
    print("=== GPIO Control Example ===\n")
    
    # Initialize sensor and config
    sensor = FingerprintSensor()
    config = ConfigManager()
    
    # Initialize GPIO handler (pin 24, BCM mode)
    gpio = GPIOHandler(pin=24, mode='BCM')
    
    # Custom success callback with detailed actions
    def on_access_granted(user_name, position, accuracy):
        """Custom callback when fingerprint is verified."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\n{'='*60}")
        print(f"ACCESS GRANTED - {timestamp}")
        print(f"{'='*60}")
        print(f"  User: {user_name}")
        print(f"  Position: #{position}")
        print(f"  Accuracy: {accuracy}/255")
        print(f"  Match Quality: {(accuracy/255)*100:.1f}%")
        print(f"{'='*60}")
        
        # Optional: Additional actions
        # - Log to database
        # - Send notification
        # - Unlock door
        # - Turn on lights
        print("\n  → Triggering GPIO output...")
        print("  → Door unlocked for 5 seconds")
    
    # Create verifier with GPIO and custom callback
    verifier = FingerprintVerifier(
        sensor=sensor,
        config=config,
        gpio_handler=gpio,
        on_success=on_access_granted
    )
    
    print("Fingerprint Access Control System")
    print("GPIO Pin 24 will be triggered on successful verification")
    print("\nReady for fingerprint scans...")
    print("Press Ctrl+C to exit\n")
    
    try:
        # Run continuous verification
        verifier.run_continuous(delay=0.5)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        # Cleanup GPIO
        gpio.cleanup()
        print("GPIO cleaned up. Goodbye!")


if __name__ == '__main__':
    main()
