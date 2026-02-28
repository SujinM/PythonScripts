"""
Unit tests for configuration management.
"""
import pytest
import tempfile
import os
from pathlib import Path

from fingerprint_r307.utils.config import ConfigManager
from fingerprint_r307.core.exceptions import ConfigurationError


class TestConfigManager:
    """Test cases for ConfigManager class."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as f:
            config_path = f.name
        yield config_path
        # Cleanup
        if os.path.exists(config_path):
            os.remove(config_path)
    
    def test_config_initialization(self, temp_config_file):
        """Test configuration manager initialization."""
        config = ConfigManager(config_path=temp_config_file)
        assert config.config_path == temp_config_file
        assert os.path.exists(temp_config_file)
    
    def test_add_user(self, temp_config_file):
        """Test adding a user."""
        config = ConfigManager(config_path=temp_config_file)
        
        result = config.add_user(position=0, name="TestUser")
        
        assert result is True
        assert config.user_exists(0)
    
    def test_add_duplicate_user(self, temp_config_file):
        """Test adding duplicate user."""
        config = ConfigManager(config_path=temp_config_file)
        
        config.add_user(position=0, name="TestUser")
        result = config.add_user(position=0, name="AnotherUser")
        
        assert result is False
    
    def test_get_user(self, temp_config_file):
        """Test getting user information."""
        config = ConfigManager(config_path=temp_config_file)
        config.add_user(position=5, name="TestUser")
        
        user = config.get_user(5)
        
        assert user is not None
        assert user['name'] == "TestUser"
        assert user['position'] == '5'
        assert user['enrolled'] == 'True'
    
    def test_get_nonexistent_user(self, temp_config_file):
        """Test getting non-existent user."""
        config = ConfigManager(config_path=temp_config_file)
        
        user = config.get_user(99)
        
        assert user is None
    
    def test_remove_user(self, temp_config_file):
        """Test removing a user."""
        config = ConfigManager(config_path=temp_config_file)
        config.add_user(position=0, name="TestUser")
        
        result = config.remove_user(0)
        
        assert result is True
        assert not config.user_exists(0)
    
    def test_remove_nonexistent_user(self, temp_config_file):
        """Test removing non-existent user."""
        config = ConfigManager(config_path=temp_config_file)
        
        result = config.remove_user(99)
        
        assert result is False
    
    def test_get_all_users(self, temp_config_file):
        """Test getting all users."""
        config = ConfigManager(config_path=temp_config_file)
        config.add_user(position=0, name="Alice")
        config.add_user(position=1, name="Bob")
        config.add_user(position=2, name="Charlie")
        
        users = config.get_all_users()
        
        assert len(users) == 3
        names = [u['name'] for u in users]
        assert "Alice" in names
        assert "Bob" in names
        assert "Charlie" in names
    
    def test_get_user_count(self, temp_config_file):
        """Test getting user count."""
        config = ConfigManager(config_path=temp_config_file)
        config.add_user(position=0, name="User1")
        config.add_user(position=1, name="User2")
        
        count = config.get_user_count()
        
        assert count == 2
    
    def test_user_exists(self, temp_config_file):
        """Test checking if user exists."""
        config = ConfigManager(config_path=temp_config_file)
        config.add_user(position=0, name="TestUser")
        
        assert config.user_exists(0) is True
        assert config.user_exists(99) is False
    
    def test_clear_all(self, temp_config_file):
        """Test clearing all users."""
        config = ConfigManager(config_path=temp_config_file)
        config.add_user(position=0, name="User1")
        config.add_user(position=1, name="User2")
        
        result = config.clear_all()
        
        assert result is True
        assert config.get_user_count() == 0
    
    def test_persistence(self, temp_config_file):
        """Test that configuration persists across instances."""
        # Add users with first instance
        config1 = ConfigManager(config_path=temp_config_file)
        config1.add_user(position=0, name="TestUser")
        
        # Load with new instance
        config2 = ConfigManager(config_path=temp_config_file)
        user = config2.get_user(0)
        
        assert user is not None
        assert user['name'] == "TestUser"
