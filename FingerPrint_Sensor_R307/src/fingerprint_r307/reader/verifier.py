"""
Fingerprint verification module for continuous authentication.
"""
import sys
import time
from typing import Optional, Callable

from pyfingerprint.pyfingerprint import FINGERPRINT_CHARBUFFER1

from fingerprint_r307.core.sensor import FingerprintSensor
from fingerprint_r307.core.exceptions import FingerprintSensorError, VerificationError
from fingerprint_r307.utils.config import ConfigManager
from fingerprint_r307.utils.logger import get_logger, setup_logging
from fingerprint_r307.reader.gpio_handler import GPIOHandler

logger = get_logger(__name__)


class FingerprintVerifier:
    """
    Handles fingerprint verification and authentication.
    """
    
    def __init__(
        self,
        sensor: FingerprintSensor,
        config: ConfigManager,
        gpio_handler: Optional[GPIOHandler] = None,
        on_success: Optional[Callable] = None
    ):
        """
        Initialize fingerprint verifier.
        
        Args:
            sensor: Fingerprint sensor instance
            config: Configuration manager instance
            gpio_handler: GPIO handler for hardware control (optional)
            on_success: Callback function on successful verification (optional)
        """
        self.sensor = sensor
        self.config = config
        self.gpio_handler = gpio_handler
        self.on_success = on_success
    
    def verify(self) -> bool:
        """
        Verify fingerprint against enrolled templates.
        
        Returns:
            True if verification successful
            
        Raises:
            VerificationError: If verification process fails
        """
        try:
            print('Place finger on the sensor...')
            logger.debug("Waiting for fingerprint scan")
            
            # Wait for finger
            while not self.sensor.read_image():
                pass
            
            # Convert image to characteristics
            self.sensor.convert_image(FINGERPRINT_CHARBUFFER1)
            
            # Search for matching template
            position, accuracy = self.sensor.search_template()
            
            if position == -1:
                print('No match found!')
                logger.warning("Fingerprint verification failed - no match")
                return False
            
            # Get user information
            user_info = self.config.get_user(position)
            
            if user_info:
                user_name = user_info['name']
                print(f"\n✓ User '{user_name}' verified!")
                print(f"  Position: #{position}")
                print(f"  Accuracy: {accuracy}")
                logger.info(f"User '{user_name}' verified (position: {position}, accuracy: {accuracy})")
                
                # Trigger GPIO
                if self.gpio_handler:
                    self.gpio_handler.trigger()
                
                # Call success callback
                if self.on_success:
                    self.on_success(user_name, position, accuracy)
                
                return True
            else:
                print(f'Warning: User found at position #{position} but not in configuration')
                logger.error(f"User at position {position} not found in configuration")
                return False
                
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            raise VerificationError(f"Verification failed: {e}") from e
    
    def run_continuous(self, delay: float = 1.0):
        """
        Run continuous verification loop.
        
        Args:
            delay: Delay between verification attempts in seconds
        """
        print("\n" + "="*50)
        print("FINGERPRINT READER - VERIFICATION MODE")
        print("="*50)
        print("\nReady for fingerprint verification...")
        print("Press Ctrl+C to exit\n")
        
        logger.info("Starting continuous verification mode")
        
        try:
            while True:
                try:
                    self.verify()
                except VerificationError as e:
                    print(f"Error: {e}")
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error(f"Unexpected error during verification: {e}")
                    print(f"Error: {e}")
                
                time.sleep(delay)
                
        except KeyboardInterrupt:
            print("\n\nStopping verification...")
            logger.info("Verification mode stopped by user")


def main():
    """Main entry point for fingerprint reader."""
    try:
        # Setup logging
        setup_logging(console=False)
        
        print("Initializing fingerprint reader...")
        
        # Initialize sensor
        try:
            sensor = FingerprintSensor()
        except FingerprintSensorError as e:
            print(f"Error initializing sensor: {e}")
            logger.error(f"Sensor initialization failed: {e}")
            sys.exit(1)
        
        # Initialize configuration
        config = ConfigManager()
        
        # Initialize GPIO handler
        gpio_handler = GPIOHandler(pin=24)
        
        # Initialize verifier
        verifier = FingerprintVerifier(
            sensor=sensor,
            config=config,
            gpio_handler=gpio_handler
        )
        
        # Run continuous verification
        verifier.run_continuous()
        
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        # Cleanup GPIO
        try:
            if 'gpio_handler' in locals():
                gpio_handler.cleanup()
        except:
            pass


if __name__ == '__main__':
    main()
