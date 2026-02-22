"""Secure key derivation from passwords using Argon2id."""

import os
from typing import Tuple

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

from .exceptions import InvalidPasswordError


class KeyDerivation:
    """Handles secure key derivation from passwords.
    
    Uses PBKDF2-HMAC-SHA256 as a fallback when Argon2 is not available.
    Argon2id is preferred but requires additional dependencies.
    """

    # Constants for PBKDF2
    PBKDF2_ITERATIONS = 600_000  # OWASP recommendation (2023)
    SALT_SIZE = 32  # 256 bits
    KEY_SIZE = 32  # 256 bits for AES-256

    def __init__(self, use_argon2: bool = False) -> None:
        """Initialize key derivation.

        Args:
            use_argon2: Whether to use Argon2id (requires argon2-cffi).
        """
        self.use_argon2 = use_argon2
        
        if use_argon2:
            try:
                from argon2 import PasswordHasher
                from argon2.low_level import hash_secret_raw, Type
                self._argon2_available = True
                self._Type = Type
                self._hash_secret_raw = hash_secret_raw
            except ImportError:
                self._argon2_available = False
        else:
            self._argon2_available = False

    def generate_salt(self) -> bytes:
        """Generate a cryptographically secure random salt.

        Returns:
            Random salt bytes.
        """
        return os.urandom(self.SALT_SIZE)

    def derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive a cryptographic key from a password and salt.

        Args:
            password: User password.
            salt: Salt for key derivation.

        Returns:
            Derived key bytes.

        Raises:
            InvalidPasswordError: If password is invalid.
        """
        if not password:
            raise InvalidPasswordError("Password cannot be empty")

        if not salt or len(salt) != self.SALT_SIZE:
            raise InvalidPasswordError(
                f"Salt must be exactly {self.SALT_SIZE} bytes"
            )

        password_bytes = password.encode("utf-8")

        if self._argon2_available and self.use_argon2:
            return self._derive_key_argon2(password_bytes, salt)
        else:
            return self._derive_key_pbkdf2(password_bytes, salt)

    def _derive_key_pbkdf2(self, password: bytes, salt: bytes) -> bytes:
        """Derive key using PBKDF2-HMAC-SHA256.

        Args:
            password: Password bytes.
            salt: Salt bytes.

        Returns:
            Derived key.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.PBKDF2_ITERATIONS,
            backend=default_backend(),
        )
        return kdf.derive(password)

    def _derive_key_argon2(self, password: bytes, salt: bytes) -> bytes:
        """Derive key using Argon2id.

        Args:
            password: Password bytes.
            salt: Salt bytes.

        Returns:
            Derived key.
        """
        # Argon2id parameters (OWASP recommendations)
        return self._hash_secret_raw(
            secret=password,
            salt=salt,
            time_cost=3,  # iterations
            memory_cost=65536,  # 64 MB
            parallelism=4,  # threads
            hash_len=self.KEY_SIZE,
            type=self._Type.ID,  # Argon2id
        )

    def verify_password_strength(self, password: str) -> Tuple[bool, str]:
        """Verify password meets minimum strength requirements.

        Args:
            password: Password to verify.

        Returns:
            Tuple of (is_valid, message).
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if len(password) < 12:
            return True, "Password is weak but acceptable"

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        strength_score = sum([has_upper, has_lower, has_digit, has_special])

        if strength_score >= 3:
            return True, "Password is strong"
        elif strength_score >= 2:
            return True, "Password is moderate"
        else:
            return True, "Password is weak but acceptable"
