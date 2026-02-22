"""Command-line interface for folder encryption/decryption."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from app.services.encrypt_service import EncryptService
from app.services.decrypt_service import DecryptService
from app.core.exceptions import (
    FolderEncryptorError,
    InvalidPasswordError,
    DecryptionError,
)
from app.utils.logger import setup_logging
from app.utils.helpers import (
    validate_path,
    format_size,
    get_folder_size,
    confirm_action,
)
from app.utils.config import ConfigManager
from app.utils.password_input import get_password_interactive


logger = logging.getLogger(__name__)


class ProgressBar:
    """Progress bar wrapper (uses tqdm if available)."""

    def __init__(self, total: int, desc: str = "Processing"):
        """Initialize progress bar.

        Args:
            total: Total number of items.
            desc: Description text.
        """
        self.total = total
        self.desc = desc
        self.current = 0

        if TQDM_AVAILABLE:
            self.pbar = tqdm(
                total=total,
                desc=desc,
                unit="files",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            )
        else:
            self.pbar = None
            print(f"{desc}: 0/{total}")

    def update(self, filename: str) -> None:
        """Update progress bar.

        Args:
            filename: Current file being processed.
        """
        self.current += 1

        if self.pbar:
            self.pbar.set_postfix_str(f"{Path(filename).name[:30]}")
            self.pbar.update(1)
        else:
            # Simple text progress
            if self.current % 10 == 0 or self.current == self.total:
                print(f"{self.desc}: {self.current}/{self.total}")

    def close(self) -> None:
        """Close progress bar."""
        if self.pbar:
            self.pbar.close()


def encrypt_command(args: argparse.Namespace, config: ConfigManager) -> int:
    """Handle encrypt command.

    Args:
        args: Parsed command-line arguments.
        config: Configuration manager.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Validate paths
        input_path = validate_path(args.input, must_exist=True)
        output_path = validate_path(args.output, must_exist=False)

        if not input_path.is_dir():
            logger.error(f"Input path is not a directory: {args.input}")
            return 1

        if output_path.exists():
            if not args.force:
                if not confirm_action(
                    f"Output path '{args.output}' already exists. Overwrite?"
                ):
                    logger.info("Operation cancelled by user")
                    return 0
            logger.warning(f"Overwriting existing output: {args.output}")

        # Get password
        if args.password:
            password = args.password
            logger.warning("WARNING: Password provided via command line (insecure)")
        else:
            try:
                password = get_password_interactive(mode="encrypt")
            except ValueError as e:
                logger.error(str(e))
                return 1
            except KeyboardInterrupt:
                logger.info("\n\nOperation cancelled by user")
                return 0

        # Display info
        folder_size = get_folder_size(input_path)
        logger.info(f"Input folder: {input_path}")
        logger.info(f"Output folder: {output_path}")
        logger.info(f"Total size: {format_size(folder_size)}")

        # Initialize service (use config values if not specified in args)
        use_argon2 = args.use_argon2 or config.get_bool("Security", "use_argon2", False)
        verify_password = not args.skip_password_check and config.get_bool(
            "Security", "verify_password_strength", True
        )
        
        encrypt_service = EncryptService(
            use_argon2=use_argon2,
            verify_password_strength=verify_password,
        )

        # Progress callback
        progress_bar: Optional[ProgressBar] = None
        show_progress = not args.no_progress and config.get_bool("UI", "show_progress", True)

        def progress_callback(filename: str, current: int, total: int) -> None:
            nonlocal progress_bar
            if progress_bar is None:
                progress_bar = ProgressBar(total, "Encrypting")
            progress_bar.update(filename)

        # Encrypt
        logger.info("Starting encryption...")
        encrypt_service.encrypt_folder(
            str(input_path),
            str(output_path),
            password,
            progress_callback=progress_callback if show_progress else None,
        )

        if progress_bar:
            progress_bar.close()

        # Save last used paths
        config.update_last_paths(str(input_path), str(output_path))

        logger.info("Encryption completed successfully")
        return 0

    except InvalidPasswordError as e:
        logger.error(f"Invalid password: {e.message}")
        return 1
    except FolderEncryptorError as e:
        logger.error(f"Encryption failed: {e.message}")
        if e.details:
            logger.debug(f"Details: {e.details}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=args.verbose)
        return 1


def decrypt_command(args: argparse.Namespace, config: ConfigManager) -> int:
    """Handle decrypt command.

    Args:
        args: Parsed command-line arguments.
        config: Configuration manager.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Validate paths
        input_path = validate_path(args.input, must_exist=True)
        output_path = validate_path(args.output, must_exist=False)

        if not input_path.is_dir():
            logger.error(f"Input path is not a directory: {args.input}")
            return 1

        if output_path.exists():
            if not args.force:
                if not confirm_action(
                    f"Output path '{args.output}' already exists. Overwrite?"
                ):
                    logger.info("Operation cancelled by user")
                    return 0
            logger.warning(f"Overwriting existing output: {args.output}")

        # Get password
        if args.password:
            password = args.password
            logger.warning("WARNING: Password provided via command line (insecure)")
        else:
            try:
                password = get_password_interactive(mode="decrypt")
            except ValueError as e:
                logger.error(str(e))
                return 1
            except KeyboardInterrupt:
                logger.info("\n\nOperation cancelled by user")
                return 0

        # Display info
        logger.info(f"Input folder: {input_path}")
        logger.info(f"Output folder: {output_path}")

        # Initialize service (use config values if not specified in args)
        use_argon2 = args.use_argon2 or config.get_bool("Security", "use_argon2", False)
        
        decrypt_service = DecryptService(use_argon2=use_argon2)

        # Progress callback
        progress_bar: Optional[ProgressBar] = None
        show_progress = not args.no_progress and config.get_bool("UI", "show_progress", True)

        def progress_callback(filename: str, current: int, total: int) -> None:
            nonlocal progress_bar
            if progress_bar is None:
                progress_bar = ProgressBar(total, "Decrypting")
            progress_bar.update(filename)

        # Decrypt
        logger.info("Starting decryption...")
        decrypt_service.decrypt_folder(
            str(input_path),
            str(output_path),
            password,
            progress_callback=progress_callback if show_progress else None,
        )

        if progress_bar:
            progress_bar.close()

        # Save last used paths
        config.update_last_paths(str(input_path), str(output_path))

        logger.info("Decryption completed successfully")
        return 0

    except DecryptionError as e:
        logger.error(f"Decryption failed: {e.message}")
        logger.error("This may be caused by:")
        logger.error("  - Wrong password")
        logger.error("  - Corrupted encrypted data")
        logger.error("  - Tampered files")
        if e.details:
            logger.debug(f"Details: {e.details}")
        return 1
    except FolderEncryptorError as e:
        logger.error(f"Decryption failed: {e.message}")
        if e.details:
            logger.debug(f"Details: {e.details}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=args.verbose)
        return 1


def main() -> int:
    """Main entry point for CLI.

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        description="Secure folder encryption and decryption tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Encrypt a folder
  python -m app.cli.main encrypt -i ./data -o ./encrypted

  # Decrypt a folder
  python -m app.cli.main decrypt -i ./encrypted -o ./restored

  # Use Argon2id for key derivation (requires argon2-cffi)
  python -m app.cli.main encrypt -i ./data -o ./encrypted --use-argon2
  
  # Use custom config file
  python -m app.cli.main encrypt -i ./data -o ./encrypted --config ./my-config.ini
        """,
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output (debug logging)",
    )

    parser.add_argument(
        "--log-file",
        type=str,
        help="Write logs to file",
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (default: ~/.folder-encryptor/config.ini)",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Folder Encryptor v1.0.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Encrypt command
    encrypt_parser = subparsers.add_parser(
        "encrypt",
        help="Encrypt a folder",
    )
    encrypt_parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input folder path to encrypt",
    )
    encrypt_parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output folder path for encrypted data",
    )
    encrypt_parser.add_argument(
        "-p", "--password",
        help="Encryption password (if not provided, will prompt securely)",
    )
    encrypt_parser.add_argument(
        "--use-argon2",
        action="store_true",
        help="Use Argon2id for key derivation (requires argon2-cffi)",
    )
    encrypt_parser.add_argument(
        "--skip-password-check",
        action="store_true",
        help="Skip password strength validation",
    )
    encrypt_parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar",
    )
    encrypt_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite output folder if it exists",
    )

    # Decrypt command
    decrypt_parser = subparsers.add_parser(
        "decrypt",
        help="Decrypt a folder",
    )
    decrypt_parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input encrypted folder path",
    )
    decrypt_parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output folder path for decrypted data",
    )
    decrypt_parser.add_argument(
        "-p", "--password",
        help="Decryption password (if not provided, will prompt securely)",
    )
    decrypt_parser.add_argument(
        "--use-argon2",
        action="store_true",
        help="Use Argon2id for key derivation (must match encryption)",
    )
    decrypt_parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar",
    )
    decrypt_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite output folder if it exists",
    )

    # Parse arguments
    args = parser.parse_args()

    # Setup logging
    setup_logging(
        verbose=args.verbose,
        log_file=args.log_file,
    )

    # Initialize configuration
    config_path = Path(args.config) if args.config else None
    config = ConfigManager(config_path)
    
    if args.verbose:
        logger.debug(f"Configuration loaded from: {config.config_path}")

    # Check command
    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    if args.command == "encrypt":
        return encrypt_command(args, config)
    elif args.command == "decrypt":
        return decrypt_command(args, config)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
