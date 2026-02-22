"""Decryption service for folder decryption operations."""

import logging
from pathlib import Path
from typing import Optional, Callable

from app.core.crypto_engine import CryptoEngine
from app.core.key_derivation import KeyDerivation
from app.core.file_processor import FileProcessor
from app.core.exceptions import (
    DecryptionError,
    FileProcessingError,
    InvalidPasswordError,
)


logger = logging.getLogger(__name__)


class DecryptService:
    """Service for decrypting folders."""

    def __init__(self, use_argon2: bool = False) -> None:
        """Initialize decryption service.

        Args:
            use_argon2: Whether to use Argon2id for key derivation.
        """
        self.key_derivation = KeyDerivation(use_argon2=use_argon2)

    def decrypt_folder(
        self,
        input_path: str,
        output_path: str,
        password: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> None:
        """Decrypt a folder with a password.

        Args:
            input_path: Path to encrypted folder.
            output_path: Path to output decrypted folder.
            password: Decryption password.
            progress_callback: Optional progress callback.

        Raises:
            InvalidPasswordError: If password is invalid.
            DecryptionError: If decryption fails (wrong password or corrupted data).
            FileProcessingError: If file processing fails.
        """
        logger.info(f"Starting decryption: {input_path} -> {output_path}")

        try:
            # Convert paths
            input_path_obj = Path(input_path).resolve()
            output_path_obj = Path(output_path).resolve()

            # Load salt
            salt_file = input_path_obj / ".salt"
            if not salt_file.exists():
                raise DecryptionError("Salt file not found. Invalid encrypted folder.")

            with open(salt_file, "rb") as f:
                salt = f.read()

            if len(salt) != KeyDerivation.SALT_SIZE:
                raise DecryptionError("Invalid salt file. Corrupted encrypted folder.")

            logger.debug("Loaded salt from encrypted folder")

            # Derive decryption key
            try:
                key = self.key_derivation.derive_key(password, salt)
                logger.debug("Derived decryption key from password")
            except InvalidPasswordError as e:
                raise DecryptionError(f"Invalid password: {str(e)}") from e

            # Initialize crypto engine and file processor
            crypto_engine = CryptoEngine(key)
            file_processor = FileProcessor(crypto_engine)

            # Decrypt folder
            logger.info("Decrypting folder contents...")
            file_processor.decrypt_folder(
                input_path_obj,
                output_path_obj,
                progress_callback=progress_callback,
            )

            logger.info("Decryption completed successfully")

        except (DecryptionError, FileProcessingError):
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}", exc_info=True)
            raise DecryptionError(f"Decryption failed: {str(e)}") from e
