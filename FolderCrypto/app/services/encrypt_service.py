"""Encryption service for folder encryption operations."""

import logging
from pathlib import Path
from typing import Optional, Callable

from app.core.crypto_engine import CryptoEngine
from app.core.key_derivation import KeyDerivation
from app.core.file_processor import FileProcessor
from app.core.exceptions import (
    EncryptionError,
    FileProcessingError,
    InvalidPasswordError,
)


logger = logging.getLogger(__name__)


class EncryptService:
    """Service for encrypting folders."""

    def __init__(
        self,
        use_argon2: bool = False,
        verify_password_strength: bool = True,
    ) -> None:
        """Initialize encryption service.

        Args:
            use_argon2: Whether to use Argon2id for key derivation.
            verify_password_strength: Whether to verify password strength.
        """
        self.key_derivation = KeyDerivation(use_argon2=use_argon2)
        self.verify_password_strength = verify_password_strength

    def encrypt_folder(
        self,
        input_path: str,
        output_path: str,
        password: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> None:
        """Encrypt a folder with a password.

        Args:
            input_path: Path to folder to encrypt.
            output_path: Path to output encrypted folder.
            password: Encryption password.
            progress_callback: Optional progress callback.

        Raises:
            InvalidPasswordError: If password is invalid.
            EncryptionError: If encryption fails.
            FileProcessingError: If file processing fails.
        """
        logger.info(f"Starting encryption: {input_path} -> {output_path}")

        # Verify password strength
        if self.verify_password_strength:
            is_valid, message = self.key_derivation.verify_password_strength(password)
            if not is_valid:
                raise InvalidPasswordError(message)
            logger.info(f"Password strength: {message}")

        try:
            # Generate salt
            salt = self.key_derivation.generate_salt()
            logger.debug("Generated salt for key derivation")

            # Derive encryption key
            key = self.key_derivation.derive_key(password, salt)
            logger.debug("Derived encryption key from password")

            # Initialize crypto engine and file processor
            crypto_engine = CryptoEngine(key)
            file_processor = FileProcessor(crypto_engine)

            # Convert paths
            input_path_obj = Path(input_path).resolve()
            output_path_obj = Path(output_path).resolve()

            # Encrypt folder
            logger.info("Encrypting folder contents...")
            file_processor.encrypt_folder(
                input_path_obj,
                output_path_obj,
                progress_callback=progress_callback,
            )

            # Save salt to a separate file
            salt_file = output_path_obj / ".salt"
            with open(salt_file, "wb") as f:
                f.write(salt)

            logger.info("Encryption completed successfully")

        except (InvalidPasswordError, EncryptionError, FileProcessingError):
            raise
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}", exc_info=True)
            raise EncryptionError(f"Encryption failed: {str(e)}") from e
