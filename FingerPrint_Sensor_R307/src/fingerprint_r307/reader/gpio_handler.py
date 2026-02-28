"""
GPIO handler for Raspberry Pi GPIO control.
Provides abstraction for GPIO operations with fallback for non-RPi systems.
"""
import time
from typing import Optional

from fingerprint_r307.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import RPi.GPIO
try:
    import RPi.GPIO as GPIO  # type: ignore
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not available - GPIO functionality disabled")


class GPIOHandler:
    """
    Handles GPIO operations for hardware control.
    Safe to use on non-Raspberry Pi systems (will log warnings).
    """
    
    def __init__(self, pin: int = 24, mode: str = 'BCM'):
        """
        Initialize GPIO handler.
        
        Args:
            pin: GPIO pin number
            mode: GPIO mode ('BCM' or 'BOARD')
        """
        self.pin = pin
        self.mode = mode
        self.enabled = GPIO_AVAILABLE
        
        if self.enabled:
            self._setup()
        else:
            logger.warning(f"GPIO handler initialized but GPIO not available")
    
    def _setup(self):
        """Setup GPIO pin."""
        try:
            if self.mode == 'BCM':
                GPIO.setmode(GPIO.BCM)
            else:
                GPIO.setmode(GPIO.BOARD)
            
            GPIO.setup(self.pin, GPIO.OUT)
            GPIO.output(self.pin, GPIO.LOW)
            logger.info(f"GPIO pin {self.pin} initialized ({self.mode} mode)")
        except Exception as e:
            logger.error(f"GPIO setup failed: {e}")
            self.enabled = False
    
    def trigger(self, duration: float = 5.0):
        """
        Trigger GPIO pin high for specified duration.
        
        Args:
            duration: Duration in seconds to keep pin high
        """
        if not self.enabled:
            logger.debug(f"GPIO trigger skipped (not available): pin {self.pin}")
            return
        
        try:
            logger.info(f"Triggering GPIO pin {self.pin} for {duration}s")
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(self.pin, GPIO.LOW)
            logger.debug(f"GPIO pin {self.pin} returned to LOW")
        except Exception as e:
            logger.error(f"GPIO trigger failed: {e}")
    
    def set_high(self):
        """Set GPIO pin to HIGH."""
        if not self.enabled:
            return
        
        try:
            GPIO.output(self.pin, GPIO.HIGH)
            logger.debug(f"GPIO pin {self.pin} set to HIGH")
        except Exception as e:
            logger.error(f"Failed to set GPIO HIGH: {e}")
    
    def set_low(self):
        """Set GPIO pin to LOW."""
        if not self.enabled:
            return
        
        try:
            GPIO.output(self.pin, GPIO.LOW)
            logger.debug(f"GPIO pin {self.pin} set to LOW")
        except Exception as e:
            logger.error(f"Failed to set GPIO LOW: {e}")
    
    def cleanup(self):
        """Cleanup GPIO resources."""
        if not self.enabled:
            return
        
        try:
            GPIO.cleanup()
            logger.info("GPIO cleanup completed")
        except Exception as e:
            logger.error(f"GPIO cleanup failed: {e}")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()
