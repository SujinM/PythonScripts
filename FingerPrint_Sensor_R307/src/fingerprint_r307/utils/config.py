"""
Configuration management for fingerprint sensor.
Handles user enrollment data and sensor settings.
"""
import os
import configparser
from typing import Optional, Dict, List
from pathlib import Path

from fingerprint_r307.core.exceptions import ConfigurationError
from fingerprint_r307.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """
    Manages configuration file for fingerprint users.
    
    Stores user enrollment data in INI format:
    [position_number]
    Name = user_id
    Enrolled = True
    """
    
    DEFAULT_CONFIG_PATH = os.path.expanduser("~/.fingerprint_config.ini")
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file (uses default if None)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = configparser.ConfigParser()
        self._load()
    
    def _load(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                self.config.read(self.config_path)
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.warning(f"Config file not found, creating new: {self.config_path}")
                self._save()
        except configparser.Error as e:
            logger.error(f"Configuration read error: {e}")
            raise ConfigurationError(f"Failed to read configuration: {e}") from e
    
    def _save(self):
        """Save configuration to file."""
        try:
            # Ensure directory exists
            config_dir = os.path.dirname(self.config_path)
            if config_dir:
                Path(config_dir).mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as configfile:
                self.config.write(configfile)
            logger.info(f"Configuration saved to {self.config_path}")
        except (IOError, configparser.Error) as e:
            logger.error(f"Configuration write error: {e}")
            raise ConfigurationError(f"Failed to write configuration: {e}") from e
    
    def add_user(self, position: int, name: str) -> bool:
        """
        Add user to configuration.
        
        Args:
            position: Template position number
            name: User identifier
            
        Returns:
            True if user added successfully
        """
        try:
            position_str = str(position)
            
            if self.config.has_section(position_str):
                logger.warning(f"User already exists at position {position}")
                return False
            
            self.config.add_section(position_str)
            self.config.set(position_str, 'Name', name)
            self.config.set(position_str, 'Enrolled', 'True')
            self._save()
            
            logger.info(f"User '{name}' added at position {position}")
            return True
        except Exception as e:
            logger.error(f"Failed to add user: {e}")
            raise ConfigurationError(f"Failed to add user: {e}") from e
    
    def remove_user(self, position: int) -> bool:
        """
        Remove user from configuration.
        
        Args:
            position: Template position number
            
        Returns:
            True if user removed successfully
        """
        try:
            position_str = str(position)
            
            if not self.config.has_section(position_str):
                logger.warning(f"User not found at position {position}")
                return False
            
            user_name = self.config.get(position_str, 'Name', fallback='Unknown')
            self.config.remove_section(position_str)
            self._save()
            
            logger.info(f"User '{user_name}' removed from position {position}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove user: {e}")
            raise ConfigurationError(f"Failed to remove user: {e}") from e
    
    def get_user(self, position: int) -> Optional[Dict[str, str]]:
        """
        Get user information by position.
        
        Args:
            position: Template position number
            
        Returns:
            Dictionary with user info or None if not found
        """
        position_str = str(position)
        
        if not self.config.has_section(position_str):
            return None
        
        return {
            'position': position_str,
            'name': self.config.get(position_str, 'Name', fallback='Unknown'),
            'enrolled': self.config.get(position_str, 'Enrolled', fallback='False'),
        }
    
    def get_all_users(self) -> List[Dict[str, str]]:
        """
        Get all enrolled users.
        
        Returns:
            List of dictionaries with user information
        """
        users = []
        for position in self.config.sections():
            users.append({
                'position': position,
                'name': self.config.get(position, 'Name', fallback='Unknown'),
                'enrolled': self.config.get(position, 'Enrolled', fallback='False'),
            })
        return users
    
    def user_exists(self, position: int) -> bool:
        """
        Check if user exists at position.
        
        Args:
            position: Template position number
            
        Returns:
            True if user exists
        """
        return self.config.has_section(str(position))
    
    def get_user_count(self) -> int:
        """
        Get total number of enrolled users.
        
        Returns:
            Number of users in configuration
        """
        return len(self.config.sections())
    
    def reload(self):
        """Reload configuration from file."""
        self._load()
    
    def clear_all(self) -> bool:
        """
        Clear all users from configuration.
        
        Returns:
            True if cleared successfully
        """
        try:
            for section in self.config.sections():
                self.config.remove_section(section)
            self._save()
            logger.info("All users cleared from configuration")
            return True
        except Exception as e:
            logger.error(f"Failed to clear configuration: {e}")
            return False
