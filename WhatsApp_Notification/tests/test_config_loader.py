"""
Unit tests for ConfigLoader.
"""

import configparser
import os
import tempfile

import pytest

# Ensure project root is on path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.config_loader import ConfigLoader, AppConfig


_VALID_INI = """
[whatsapp]
provider     = twilio
account_sid  = ACtest123
auth_token   = token123
from_number  = whatsapp:+14155238886
to_numbers   = whatsapp:+1234567890

[notification]
interval_minutes     = 5
retry_attempts       = 3
retry_delay_seconds  = 10
message_template     = [{severity}] {source} @ {timestamp} | {message}

[triggers]
enable_time_trigger   = true
enable_file_trigger   = false
enable_custom_trigger = false
watch_path            = /tmp

[logging]
level        = INFO
log_file     =
max_bytes    = 5242880
backup_count = 3
"""


def _write_ini(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False)
    f.write(content)
    f.close()
    return f.name


class TestConfigLoader:
    def test_load_valid_config(self):
        path = _write_ini(_VALID_INI)
        try:
            cfg: AppConfig = ConfigLoader(config_path=path).load()
            assert cfg.whatsapp.provider == "twilio"
            assert cfg.whatsapp.account_sid == "ACtest123"
            assert cfg.notification.interval_minutes == 5
            assert cfg.trigger.enable_time_trigger is True
            assert cfg.trigger.enable_file_trigger is False
            assert cfg.logging.level == "INFO"
            assert cfg.logging.log_file is None
        finally:
            os.unlink(path)

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            ConfigLoader(config_path="/nonexistent/path/config.ini").load()

    def test_missing_required_field_raises(self):
        bad_ini = _VALID_INI.replace("account_sid  = ACtest123", "account_sid  =")
        path = _write_ini(bad_ini)
        try:
            with pytest.raises(ValueError, match="account_sid"):
                ConfigLoader(config_path=path).load()
        finally:
            os.unlink(path)

    def test_to_numbers_parsed_as_list(self):
        multi = _VALID_INI.replace(
            "to_numbers   = whatsapp:+1234567890",
            "to_numbers   = whatsapp:+1111111111, whatsapp:+2222222222",
        )
        path = _write_ini(multi)
        try:
            cfg = ConfigLoader(config_path=path).load()
            assert len(cfg.whatsapp.to_numbers) == 2
        finally:
            os.unlink(path)
