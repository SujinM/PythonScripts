"""
WhatsApp Notification System — application entry point.

Wires all components together following the Composition Root pattern:
  1. Load configuration.
  2. Initialise logging.
  3. Build the WhatsApp service.
  4. Build and register triggers (based on config flags).
  5. Start the scheduler.

To add a new trigger without editing this file see the README section
"Adding a custom trigger".
"""

from __future__ import annotations

import argparse
import sys
import os

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path when running as a script
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.notifier import Notifier
from core.scheduler import Scheduler
from core.trigger_manager import TriggerManager
from services.whatsapp_service import create_whatsapp_service
from triggers.file_trigger import FileTrigger
from triggers.time_trigger import TimeTrigger
from utils.config_loader import AppConfig, ConfigLoader
from utils.logger import get_logger, setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WhatsApp Notification System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        default=os.path.join(_PROJECT_ROOT, "config", "config.ini"),
        help="Path to the configuration file.",
    )
    parser.add_argument(
        "--tick",
        type=int,
        default=30,
        help="Scheduler polling interval in seconds.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load config and validate; do not send any messages.",
    )
    return parser.parse_args()


def build_trigger_manager(cfg: AppConfig) -> TriggerManager:
    """
    Construct and register triggers based on the [triggers] config section.

    Extend this function (or call manager.register() from your own code)
    to add PLC / sensor / database triggers without touching any other module.
    """
    manager = TriggerManager()

    if cfg.trigger.enable_time_trigger:
        manager.register(
            TimeTrigger(
                interval_minutes=cfg.notification.interval_minutes,
                message="Scheduled status notification.",
            )
        )

    if cfg.trigger.enable_file_trigger:
        manager.register(
            FileTrigger(
                watch_path=cfg.trigger.watch_path,
                message_prefix="File system change detected",
            )
        )

    if cfg.trigger.enable_custom_trigger:
        # Dynamically load a custom trigger module specified in config.
        # The module must expose a ``build_triggers(cfg)`` function that
        # returns a list of BaseTrigger instances.
        module_path = cfg.trigger.custom_trigger_module
        if module_path:
            import importlib.util

            spec = importlib.util.spec_from_file_location("_custom_trigger", module_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[attr-defined]
                if hasattr(mod, "build_triggers"):
                    for trigger in mod.build_triggers(cfg):
                        manager.register(trigger)
                else:
                    get_logger(__name__).warning(
                        "Custom trigger module '%s' has no build_triggers() function.",
                        module_path,
                    )

    return manager


def main() -> int:
    args = parse_args()

    # ------------------------------------------------------------------
    # 1. Load configuration
    # ------------------------------------------------------------------
    try:
        loader = ConfigLoader(config_path=args.config)
        cfg: AppConfig = loader.load()
    except (FileNotFoundError, KeyError, ValueError) as exc:
        # Logging not yet set up — print directly
        print(f"[FATAL] Configuration error: {exc}", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # 2. Initialise logging (needs config values)
    # ------------------------------------------------------------------
    setup_logging(
        level=cfg.logging.level,
        log_file=cfg.logging.log_file,
        max_bytes=cfg.logging.max_bytes,
        backup_count=cfg.logging.backup_count,
    )
    logger = get_logger(__name__)
    logger.info("=" * 60)
    logger.info("WhatsApp Notification System starting…")
    logger.info("Config: %s", args.config)
    logger.info("Provider: %s", cfg.whatsapp.provider)
    logger.info("Recipients: %s", ", ".join(cfg.whatsapp.to_numbers))
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # 3. Build the WhatsApp service
    # ------------------------------------------------------------------
    try:
        service = create_whatsapp_service(
            config=cfg.whatsapp,
            retry_attempts=cfg.notification.retry_attempts,
            retry_delay_seconds=cfg.notification.retry_delay_seconds,
        )
    except ValueError as exc:
        logger.critical("Service configuration error: %s", exc)
        return 1

    if args.dry_run:
        logger.info("--dry-run mode: configuration OK, exiting without sending.")
        return 0

    # ------------------------------------------------------------------
    # 4. Assemble the notification pipeline
    # ------------------------------------------------------------------
    notifier = Notifier(
        service=service,
        wa_config=cfg.whatsapp,
        notif_config=cfg.notification,
    )

    trigger_manager = build_trigger_manager(cfg)

    if not trigger_manager.trigger_names:
        logger.warning(
            "No triggers are enabled.  "
            "Enable at least one trigger in [triggers] section of config.ini."
        )

    scheduler = Scheduler(
        trigger_manager=trigger_manager,
        notifier=notifier,
        tick_seconds=args.tick,
    )

    # ------------------------------------------------------------------
    # 5. Run (blocking call — returns on SIGINT / SIGTERM)
    # ------------------------------------------------------------------
    scheduler.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
