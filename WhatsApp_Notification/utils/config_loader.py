"""
Configuration loader for the WhatsApp Notification System.

Reads config.ini and exposes typed accessor properties so the rest of
the application never has to deal with raw configparser strings.

Secret values (API keys, tokens, phone numbers) are kept out of config.ini
by referencing environment variables with the ${VAR_NAME} syntax::

    account_sid = ${TWILIO_ACCOUNT_SID}

At startup, _load_dotenv() loads a .env file (if present) so that these
variables are available without setting them in the OS environment manually.
.env is listed in .gitignore and must never be committed.
"""

import configparser
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "config.ini"
)

_ENV_VAR_RE = re.compile(r"\$\{([^}]+)\}")


# ---------------------------------------------------------------------------
# .env loader (no third-party deps required)
# ---------------------------------------------------------------------------


def _load_dotenv(dotenv_path: Optional[str] = None) -> None:
    """
    Load a .env file into os.environ.

    Uses python-dotenv when installed; falls back to a simple built-in
    parser so no extra dependency is required.

    The .env file is looked for (in order):
      1. ``dotenv_path`` argument if provided.
      2. A ``.env`` file next to the project root (parent of utils/).
    """
    if dotenv_path is None:
        dotenv_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".env"
        )

    if not os.path.isfile(dotenv_path):
        return  # silently skip — .env is optional

    # Try the well-known python-dotenv library first
    try:
        from dotenv import load_dotenv  # type: ignore[import]
        load_dotenv(dotenv_path=dotenv_path, override=False)
        logger.debug(".env loaded via python-dotenv: %s", dotenv_path)
        return
    except ImportError:
        pass

    # Fallback: minimal built-in parser
    with open(dotenv_path, encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # Only set if not already in the environment (override=False)
            os.environ.setdefault(key, value)

    logger.debug(".env loaded via built-in parser: %s", dotenv_path)


# ---------------------------------------------------------------------------
# Typed configuration data-classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WhatsAppConfig:
    provider: str           # "twilio" | "cloud_api"
    account_sid: str        # Twilio Account SID  /  Cloud API phone-number-id
    auth_token: str         # Twilio Auth Token   /  Cloud API bearer token
    from_number: str        # Twilio: whatsapp:+1415...  /  Cloud API: numeric id
    to_numbers: List[str]   # One or more recipient numbers


@dataclass(frozen=True)
class NotificationConfig:
    interval_minutes: int
    retry_attempts: int
    retry_delay_seconds: int
    message_template: str


@dataclass(frozen=True)
class TriggerConfig:
    enable_time_trigger: bool
    enable_file_trigger: bool
    enable_custom_trigger: bool
    watch_path: str
    custom_trigger_module: Optional[str]


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    log_file: Optional[str]
    max_bytes: int
    backup_count: int


@dataclass
class AppConfig:
    whatsapp: WhatsAppConfig
    notification: NotificationConfig
    trigger: TriggerConfig
    logging: LoggingConfig


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


class ConfigLoader:
    """
    Loads and validates application configuration from a .ini file.

    Responsibilities:
      - Parse the INI file.
      - Provide typed, validated access to every configuration value.
      - Raise clear errors for missing required fields.

    Usage::

        loader = ConfigLoader("/path/to/config.ini")
        cfg: AppConfig = loader.load()
    """

    def __init__(self, config_path: str = _DEFAULT_CONFIG_PATH) -> None:
        self._config_path = config_path
        self._parser = configparser.ConfigParser(
            interpolation=configparser.BasicInterpolation()
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> AppConfig:
        """Parse the config file and return a validated AppConfig."""        # Load .env first so ${VAR} references in config.ini are resolvable
        _load_dotenv()
        if not os.path.isfile(self._config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {self._config_path}\n"
                "Copy config/config.ini.template → config/config.ini and fill in your credentials."
            )

        self._parser.read(self._config_path, encoding="utf-8")
        logger.debug("Configuration loaded from: %s", self._config_path)

        return AppConfig(
            whatsapp=self._load_whatsapp(),
            notification=self._load_notification(),
            trigger=self._load_trigger(),
            logging=self._load_logging(),
        )

    # ------------------------------------------------------------------
    # Private section loaders
    # ------------------------------------------------------------------

    def _load_whatsapp(self) -> WhatsAppConfig:
        sec = "whatsapp"
        self._require_section(sec)

        raw_to = self._get(sec, "to_numbers", fallback="")
        to_numbers = [n.strip() for n in raw_to.split(",") if n.strip()]
        if not to_numbers:
            raise ValueError("[whatsapp] to_numbers must contain at least one number.")

        return WhatsAppConfig(
            provider=self._get(sec, "provider", fallback="twilio"),
            account_sid=self._require(sec, "account_sid"),
            auth_token=self._require(sec, "auth_token"),
            from_number=self._require(sec, "from_number"),
            to_numbers=to_numbers,
        )

    def _load_notification(self) -> NotificationConfig:
        sec = "notification"
        self._require_section(sec)
        return NotificationConfig(
            interval_minutes=self._getint(sec, "interval_minutes", fallback=5),
            retry_attempts=self._getint(sec, "retry_attempts", fallback=3),
            retry_delay_seconds=self._getint(sec, "retry_delay_seconds", fallback=10),
            message_template=self._get(
                sec,
                "message_template",
                fallback="[{timestamp}] {message}",
            ),
        )

    def _load_trigger(self) -> TriggerConfig:
        sec = "triggers"
        self._require_section(sec)
        return TriggerConfig(
            enable_time_trigger=self._getbool(sec, "enable_time_trigger", fallback=True),
            enable_file_trigger=self._getbool(sec, "enable_file_trigger", fallback=False),
            enable_custom_trigger=self._getbool(sec, "enable_custom_trigger", fallback=False),
            watch_path=self._get(sec, "watch_path", fallback="."),
            custom_trigger_module=self._get(sec, "custom_trigger_module", fallback=None),
        )

    def _load_logging(self) -> LoggingConfig:
        sec = "logging"
        self._require_section(sec)
        raw_log_file = self._get(sec, "log_file", fallback="").strip()
        return LoggingConfig(
            level=self._get(sec, "level", fallback="INFO").upper(),
            log_file=raw_log_file if raw_log_file else None,
            max_bytes=self._getint(sec, "max_bytes", fallback=5 * 1024 * 1024),
            backup_count=self._getint(sec, "backup_count", fallback=3),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _require_section(self, section: str) -> None:
        if not self._parser.has_section(section):
            raise KeyError(f"Missing required config section: [{section}]")

    def _require(self, section: str, key: str) -> str:
        value = self._get(section, key, fallback="").strip()
        if not value:
            raise ValueError(f"[{section}] {key} is required but not set.")
        return value

    def _get(self, section: str, key: str, fallback: Optional[str] = None) -> str:
        raw = self._parser.get(section, key, fallback=fallback or "")
        return self._expand_env_vars(raw)

    @staticmethod
    def _expand_env_vars(value: str) -> str:
        """
        Replace ``${VAR_NAME}`` placeholders with the corresponding
        environment variable value.

        Raises:
            KeyError: If a referenced variable is not set in the environment.
        """
        def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
            var_name = match.group(1)
            env_value = os.environ.get(var_name)
            if env_value is None:
                raise KeyError(
                    f"Environment variable '{var_name}' referenced in config.ini "
                    "is not set.  Add it to your .env file."
                )
            return env_value

        return _ENV_VAR_RE.sub(_replace, value)

    def _getint(self, section: str, key: str, fallback: int = 0) -> int:
        try:
            return self._parser.getint(section, key, fallback=fallback)
        except ValueError as exc:
            raise ValueError(f"[{section}] {key} must be an integer: {exc}") from exc

    def _getbool(self, section: str, key: str, fallback: bool = False) -> bool:
        try:
            return self._parser.getboolean(section, key, fallback=fallback)
        except ValueError as exc:
            raise ValueError(f"[{section}] {key} must be a boolean: {exc}") from exc
