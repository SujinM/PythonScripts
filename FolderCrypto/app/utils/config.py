"""Configuration file handler for folder encryption application."""

import configparser
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manage application configuration from INI file."""

    DEFAULT_CONFIG = {
        "Folders": {
            "default_input": "",
            "default_output": "",
            "last_input": "",
            "last_output": "",
        },
        "Security": {
            "use_argon2": "false",
            "verify_password_strength": "true",
            "min_password_length": "12",
        },
        "UI": {
            "show_progress": "true",
            "verbose": "false",
            "confirm_overwrite": "true",
        },
        "Performance": {
            "chunk_size": "65536",  # 64KB
        },
    }

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            # Use user's home directory or current directory
            try:
                self.config_path = Path.home() / ".folder-encryptor" / "config.ini"
            except RuntimeError:
                # Fallback for systems where home directory is not available
                self.config_path = Path("config.ini")
        else:
            self.config_path = Path(config_path)

        self.config = configparser.ConfigParser()
        self.load()

    def load(self) -> None:
        """Load configuration from file. Create default if missing."""
        if self.config_path.exists():
            try:
                self.config.read(self.config_path)
                logger.debug(f"Loaded configuration from {self.config_path}")
                
                # Ensure all default sections exist
                self._ensure_defaults()
            except Exception as e:
                logger.warning(f"Failed to load config: {e}. Using defaults.")
                self._create_default()
        else:
            logger.info(f"Config file not found. Creating default at {self.config_path}")
            self._create_default()

    def _ensure_defaults(self) -> None:
        """Ensure all default sections and keys exist."""
        modified = False
        for section, options in self.DEFAULT_CONFIG.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
                modified = True
            
            for key, value in options.items():
                if not self.config.has_option(section, key):
                    self.config.set(section, key, value)
                    modified = True
        
        if modified:
            self.save()

    def _create_default(self) -> None:
        """Create default configuration file."""
        for section, options in self.DEFAULT_CONFIG.items():
            self.config.add_section(section)
            for key, value in options.items():
                self.config.set(section, key, value)
        
        self.save()

    def save(self) -> None:
        """Save configuration to file."""
        try:
            # Create directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, "w") as f:
                self.config.write(f)
            
            logger.debug(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get(self, section: str, key: str, fallback: Optional[str] = None) -> str:
        """Get configuration value.

        Args:
            section: Configuration section.
            key: Configuration key.
            fallback: Fallback value if key doesn't exist.

        Returns:
            Configuration value.
        """
        return self.config.get(section, key, fallback=fallback)

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get boolean configuration value.

        Args:
            section: Configuration section.
            key: Configuration key.
            fallback: Fallback value if key doesn't exist.

        Returns:
            Boolean configuration value.
        """
        return self.config.getboolean(section, key, fallback=fallback)

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get integer configuration value.

        Args:
            section: Configuration section.
            key: Configuration key.
            fallback: Fallback value if key doesn't exist.

        Returns:
            Integer configuration value.
        """
        return self.config.getint(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: str) -> None:
        """Set configuration value.

        Args:
            section: Configuration section.
            key: Configuration key.
            value: Configuration value.
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, key, str(value))

    def get_all(self, section: str) -> Dict[str, str]:
        """Get all configuration values in a section.

        Args:
            section: Configuration section.

        Returns:
            Dictionary of configuration values.
        """
        if self.config.has_section(section):
            return dict(self.config.items(section))
        return {}

    def update_last_paths(self, input_path: str, output_path: str) -> None:
        """Update last used paths.

        Args:
            input_path: Last input path.
            output_path: Last output path.
        """
        self.set("Folders", "last_input", input_path)
        self.set("Folders", "last_output", output_path)
        self.save()

    def get_default_input(self) -> Optional[str]:
        """Get default input folder.

        Returns:
            Default input folder path or None.
        """
        value = self.get("Folders", "default_input", "")
        return value if value else None

    def get_default_output(self) -> Optional[str]:
        """Get default output folder.

        Returns:
            Default output folder path or None.
        """
        value = self.get("Folders", "default_output", "")
        return value if value else None

    def get_last_input(self) -> Optional[str]:
        """Get last used input folder.

        Returns:
            Last input folder path or None.
        """
        value = self.get("Folders", "last_input", "")
        return value if value else None

    def get_last_output(self) -> Optional[str]:
        """Get last used output folder.

        Returns:
            Last output folder path or None.
        """
        value = self.get("Folders", "last_output", "")
        return value if value else None
