"""
Unit tests for fingerprint sensor core functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from fingerprint_r307.core.sensor import FingerprintSensor
from fingerprint_r307.core.exceptions import SensorInitializationError, ImageCaptureError


class TestFingerprintSensor:
    """Test cases for FingerprintSensor class."""
    
    @patch('fingerprint_r307.core.sensor.PyFingerprint')
    def test_sensor_initialization_success(self, mock_pyfingerprint):
        """Test successful sensor initialization."""
        # Arrange
        mock_instance = Mock()
        mock_pyfingerprint.return_value = mock_instance
        
        # Act
        sensor = FingerprintSensor()
        
        # Assert
        assert sensor._sensor is not None
        mock_pyfingerprint.assert_called_once_with(
            '/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000
        )
    
    @patch('fingerprint_r307.core.sensor.PyFingerprint')
    def test_sensor_initialization_failure(self, mock_pyfingerprint):
        """Test sensor initialization failure."""
        # Arrange
        mock_pyfingerprint.side_effect = Exception("Connection failed")
        
        # Act & Assert
        with pytest.raises(SensorInitializationError):
            FingerprintSensor()
    
    @patch('fingerprint_r307.core.sensor.PyFingerprint')
    def test_get_template_count(self, mock_pyfingerprint):
        """Test getting template count."""
        # Arrange
        mock_instance = Mock()
        mock_instance.getTemplateCount.return_value = 5
        mock_pyfingerprint.return_value = mock_instance
        
        sensor = FingerprintSensor()
        
        # Act
        count = sensor.get_template_count()
        
        # Assert
        assert count == 5
        mock_instance.getTemplateCount.assert_called_once()
    
    @patch('fingerprint_r307.core.sensor.PyFingerprint')
    def test_get_storage_capacity(self, mock_pyfingerprint):
        """Test getting storage capacity."""
        # Arrange
        mock_instance = Mock()
        mock_instance.getStorageCapacity.return_value = 1000
        mock_pyfingerprint.return_value = mock_instance
        
        sensor = FingerprintSensor()
        
        # Act
        capacity = sensor.get_storage_capacity()
        
        # Assert
        assert capacity == 1000
    
    @patch('fingerprint_r307.core.sensor.PyFingerprint')
    def test_read_image_success(self, mock_pyfingerprint):
        """Test successful image reading."""
        # Arrange
        mock_instance = Mock()
        mock_instance.readImage.return_value = True
        mock_pyfingerprint.return_value = mock_instance
        
        sensor = FingerprintSensor()
        
        # Act
        result = sensor.read_image()
        
        # Assert
        assert result is True
    
    @patch('fingerprint_r307.core.sensor.PyFingerprint')
    def test_search_template_found(self, mock_pyfingerprint):
        """Test template search when match is found."""
        # Arrange
        mock_instance = Mock()
        mock_instance.searchTemplate.return_value = (5, 200)
        mock_pyfingerprint.return_value = mock_instance
        
        sensor = FingerprintSensor()
        
        # Act
        position, accuracy = sensor.search_template()
        
        # Assert
        assert position == 5
        assert accuracy == 200
    
    @patch('fingerprint_r307.core.sensor.PyFingerprint')
    def test_search_template_not_found(self, mock_pyfingerprint):
        """Test template search when no match found."""
        # Arrange
        mock_instance = Mock()
        mock_instance.searchTemplate.return_value = (-1, 0)
        mock_pyfingerprint.return_value = mock_instance
        
        sensor = FingerprintSensor()
        
        # Act
        position, accuracy = sensor.search_template()
        
        # Assert
        assert position == -1
        assert accuracy == 0
    
    @patch('fingerprint_r307.core.sensor.PyFingerprint')
    def test_delete_template_success(self, mock_pyfingerprint):
        """Test successful template deletion."""
        # Arrange
        mock_instance = Mock()
        mock_instance.deleteTemplate.return_value = True
        mock_pyfingerprint.return_value = mock_instance
        
        sensor = FingerprintSensor()
        
        # Act
        result = sensor.delete_template(5)
        
        # Assert
        assert result is True
        mock_instance.deleteTemplate.assert_called_once_with(5)
    
    @patch('fingerprint_r307.core.sensor.PyFingerprint')
    def test_get_sensor_info(self, mock_pyfingerprint):
        """Test getting sensor information."""
        # Arrange
        mock_instance = Mock()
        mock_instance.getTemplateCount.return_value = 10
        mock_instance.getStorageCapacity.return_value = 1000
        mock_pyfingerprint.return_value = mock_instance
        
        sensor = FingerprintSensor(port='/dev/ttyUSB0', baudrate=57600)
        
        # Act
        info = sensor.get_sensor_info()
        
        # Assert
        assert info['port'] == '/dev/ttyUSB0'
        assert info['baudrate'] == 57600
        assert info['templates_used'] == 10
        assert info['storage_capacity'] == 1000
