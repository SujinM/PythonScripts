"""
Unit tests for user management functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from fingerprint_r307.admin.user_manager import UserManager
from fingerprint_r307.core.exceptions import EnrollmentError, DeletionError


class TestUserManager:
    """Test cases for UserManager class."""
    
    @pytest.fixture
    def mock_sensor(self):
        """Create mock sensor."""
        sensor = Mock()
        sensor.read_image.return_value = True
        sensor.search_template.return_value = (-1, 0)
        sensor.compare_characteristics.return_value = 150
        sensor.store_template.return_value = 0
        return sensor
    
    @pytest.fixture
    def mock_config(self):
        """Create mock config manager."""
        config = Mock()
        config.get_user.return_value = None
        config.add_user.return_value = True
        return config
    
    @pytest.fixture
    def user_manager(self, mock_sensor, mock_config):
        """Create UserManager instance with mocks."""
        return UserManager(mock_sensor, mock_config)
    
    def test_enroll_user_success(self, user_manager, mock_sensor, mock_config):
        """Test successful user enrollment."""
        # Arrange
        user_id = "TestUser"
        
        # Act
        with patch.object(user_manager, '_download_fingerprint_image'):
            result = user_manager.enroll_user(user_id)
        
        # Assert
        assert result is True
        mock_config.add_user.assert_called_once()
    
    def test_enroll_user_already_exists(self, user_manager, mock_sensor, mock_config):
        """Test enrolling fingerprint that already exists."""
        # Arrange
        user_id = "TestUser"
        mock_sensor.search_template.return_value = (5, 200)  # Already enrolled
        mock_config.get_user.return_value = {'name': 'ExistingUser'}
        
        # Act
        result = user_manager.enroll_user(user_id)
        
        # Assert
        assert result is False
    
    def test_delete_user_success(self, user_manager, mock_sensor, mock_config):
        """Test successful user deletion."""
        # Arrange
        position = 5
        mock_config.get_user.return_value = {'name': 'TestUser', 'enrolled': 'True'}
        mock_sensor.delete_template.return_value = True
        
        # Act
        result = user_manager.delete_user(position)
        
        # Assert
        assert result is True
        mock_sensor.delete_template.assert_called_once_with(position)
        mock_config.remove_user.assert_called_once_with(position)
    
    def test_delete_user_not_found(self, user_manager, mock_sensor, mock_config):
        """Test deleting non-existent user."""
        # Arrange
        position = 5
        mock_config.get_user.return_value = None
        
        # Act
        result = user_manager.delete_user(position)
        
        # Assert
        assert result is False
    
    def test_view_all_users_empty(self, user_manager, mock_config, capsys):
        """Test viewing users when none enrolled."""
        # Arrange
        mock_config.get_all_users.return_value = []
        
        # Act
        user_manager.view_all_users()
        captured = capsys.readouterr()
        
        # Assert
        assert "No users enrolled" in captured.out
    
    def test_view_all_users_with_data(self, user_manager, mock_config, capsys):
        """Test viewing multiple enrolled users."""
        # Arrange
        mock_config.get_all_users.return_value = [
            {'position': '0', 'name': 'Alice', 'enrolled': 'True'},
            {'position': '1', 'name': 'Bob', 'enrolled': 'True'},
        ]
        
        # Act
        user_manager.view_all_users()
        captured = capsys.readouterr()
        
        # Assert
        assert "Alice" in captured.out
        assert "Bob" in captured.out
        assert "Total users: 2" in captured.out
