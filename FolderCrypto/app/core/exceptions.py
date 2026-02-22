"""Custom exception classes for the folder encryptor."""

from typing import Optional


class FolderEncryptorError(Exception):
    """Base exception for all folder encryptor errors."""

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message.
            details: Additional error details.
        """
        self.message = message
        self.details = details
        super().__init__(self.message)


class CryptoError(FolderEncryptorError):
    """Raised when cryptographic operation fails."""

    pass


class DecryptionError(CryptoError):
    """Raised when decryption fails (wrong password or corrupted data)."""

    pass


class EncryptionError(CryptoError):
    """Raised when encryption fails."""

    pass


class InvalidPasswordError(FolderEncryptorError):
    """Raised when password validation fails."""

    pass


class FileProcessingError(FolderEncryptorError):
    """Raised when file processing fails."""

    pass


class InvalidMetadataError(FolderEncryptorError):
    """Raised when metadata is invalid or corrupted."""

    pass


class UnsupportedVersionError(FolderEncryptorError):
    """Raised when encrypted data version is not supported."""

    pass
