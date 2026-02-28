"""
Core sensor wrapper for R307 Fingerprint Sensor.
Provides a high-level interface to the pyfingerprint library.
"""
from typing import Optional, Tuple
from pyfingerprint.pyfingerprint import PyFingerprint, FINGERPRINT_CHARBUFFER1, FINGERPRINT_CHARBUFFER2

from fingerprint_r307.core.exceptions import (
    SensorInitializationError,
    ImageCaptureError,
    TemplateError
)
from fingerprint_r307.utils.logger import get_logger

logger = get_logger(__name__)


class FingerprintSensor:
    """
    High-level wrapper for R307 fingerprint sensor operations.
    
    Attributes:
        port (str): Serial port for sensor communication
        baudrate (int): Baud rate for serial communication
        address (int): Sensor address
        password (int): Sensor password
    """
    
    DEFAULT_PORT = '/dev/ttyUSB0'
    DEFAULT_BAUDRATE = 57600
    DEFAULT_ADDRESS = 0xFFFFFFFF
    DEFAULT_PASSWORD = 0x00000000
    
    def __init__(
        self,
        port: str = DEFAULT_PORT,
        baudrate: int = DEFAULT_BAUDRATE,
        address: int = DEFAULT_ADDRESS,
        password: int = DEFAULT_PASSWORD
    ):
        """
        Initialize the fingerprint sensor.
        
        Args:
            port: Serial port path
            baudrate: Communication baud rate
            address: Sensor address
            password: Sensor password
            
        Raises:
            SensorInitializationError: If sensor cannot be initialized
        """
        self.port = port
        self.baudrate = baudrate
        self.address = address
        self.password = password
        self._sensor: Optional[PyFingerprint] = None
        
        self._initialize()
    
    def _initialize(self):
        """Initialize the underlying PyFingerprint sensor."""
        try:
            self._sensor = PyFingerprint(
                self.port,
                self.baudrate,
                self.address,
                self.password
            )
            logger.info(f"Fingerprint sensor initialized on {self.port}")
        except Exception as e:
            logger.error(f"Sensor initialization failed: {e}")
            raise SensorInitializationError(
                f"Could not initialize fingerprint sensor: {e}"
            ) from e
    
    @property
    def sensor(self) -> PyFingerprint:
        """Get the underlying sensor instance."""
        if self._sensor is None:
            raise SensorInitializationError("Sensor not initialized")
        return self._sensor
    
    def get_template_count(self) -> int:
        """Get the number of stored templates."""
        try:
            return self.sensor.getTemplateCount()
        except Exception as e:
            logger.error(f"Failed to get template count: {e}")
            return 0
    
    def get_storage_capacity(self) -> int:
        """Get the maximum storage capacity."""
        try:
            return self.sensor.getStorageCapacity()
        except Exception as e:
            logger.error(f"Failed to get storage capacity: {e}")
            return 0
    
    def read_image(self, timeout: int = 10) -> bool:
        """
        Read fingerprint image from sensor.
        
        Args:
            timeout: Timeout in seconds for reading (not used currently)
            
        Returns:
            True if image read successfully, False otherwise
        """
        try:
            return self.sensor.readImage()
        except Exception as e:
            logger.error(f"Failed to read image: {e}")
            raise ImageCaptureError(f"Image capture failed: {e}") from e
    
    def convert_image(self, char_buffer: int = FINGERPRINT_CHARBUFFER1):
        """
        Convert captured image to characteristics.
        
        Args:
            char_buffer: Buffer to store characteristics (1 or 2)
        """
        try:
            self.sensor.convertImage(char_buffer)
        except Exception as e:
            logger.error(f"Failed to convert image: {e}")
            raise ImageCaptureError(f"Image conversion failed: {e}") from e
    
    def search_template(self) -> Tuple[int, int]:
        """
        Search for matching template.
        
        Returns:
            Tuple of (position_number, accuracy_score)
            position_number is -1 if no match found
        """
        try:
            result = self.sensor.searchTemplate()
            return result[0], result[1]
        except Exception as e:
            logger.error(f"Template search failed: {e}")
            return -1, 0
    
    def compare_characteristics(self) -> int:
        """
        Compare characteristics in buffer 1 and 2.
        
        Returns:
            Accuracy score (0 if no match)
        """
        try:
            return self.sensor.compareCharacteristics()
        except Exception as e:
            logger.error(f"Characteristic comparison failed: {e}")
            return 0
    
    def create_template(self):
        """Create template from characteristics."""
        try:
            self.sensor.createTemplate()
        except Exception as e:
            logger.error(f"Template creation failed: {e}")
            raise TemplateError(f"Failed to create template: {e}") from e
    
    def store_template(self, position: int = -1) -> int:
        """
        Store template at specified position.
        
        Args:
            position: Position to store template (-1 for next available)
            
        Returns:
            Position number where template was stored
        """
        try:
            return self.sensor.storeTemplate(position)
        except Exception as e:
            logger.error(f"Template storage failed: {e}")
            raise TemplateError(f"Failed to store template: {e}") from e
    
    def delete_template(self, position: int) -> bool:
        """
        Delete template at specified position.
        
        Args:
            position: Position of template to delete
            
        Returns:
            True if deletion successful
        """
        try:
            return self.sensor.deleteTemplate(position)
        except Exception as e:
            logger.error(f"Template deletion failed: {e}")
            return False
    
    def download_image(self, destination: str):
        """
        Download captured fingerprint image to file.
        
        Args:
            destination: File path to save image
        """
        try:
            self.sensor.downloadImage(destination)
            logger.info(f"Image saved to {destination}")
        except Exception as e:
            logger.error(f"Image download failed: {e}")
            raise ImageCaptureError(f"Failed to download image: {e}") from e
    
    def get_sensor_info(self) -> dict:
        """
        Get sensor information.
        
        Returns:
            Dictionary with sensor information
        """
        return {
            'port': self.port,
            'baudrate': self.baudrate,
            'templates_used': self.get_template_count(),
            'storage_capacity': self.get_storage_capacity(),
        }
