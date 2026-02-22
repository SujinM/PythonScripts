"""Tests for cryptographic components."""

import pytest
import os
from io import BytesIO

from app.core.crypto_engine import CryptoEngine
from app.core.key_derivation import KeyDerivation
from app.core.exceptions import (
    EncryptionError,
    DecryptionError,
    InvalidPasswordError,
)


class TestKeyDerivation:
    """Tests for KeyDerivation class."""

    def test_generate_salt(self):
        """Test salt generation."""
        kd = KeyDerivation()
        salt = kd.generate_salt()

        assert len(salt) == KeyDerivation.SALT_SIZE
        assert isinstance(salt, bytes)

        # Test uniqueness
        salt2 = kd.generate_salt()
        assert salt != salt2

    def test_derive_key_pbkdf2(self, sample_password):
        """Test key derivation with PBKDF2."""
        kd = KeyDerivation(use_argon2=False)
        salt = kd.generate_salt()

        key = kd.derive_key(sample_password, salt)

        assert len(key) == KeyDerivation.KEY_SIZE
        assert isinstance(key, bytes)

    def test_derive_key_deterministic(self, sample_password):
        """Test that key derivation is deterministic."""
        kd = KeyDerivation(use_argon2=False)
        salt = kd.generate_salt()

        key1 = kd.derive_key(sample_password, salt)
        key2 = kd.derive_key(sample_password, salt)

        assert key1 == key2

    def test_derive_key_different_passwords(self):
        """Test different passwords produce different keys."""
        kd = KeyDerivation(use_argon2=False)
        salt = kd.generate_salt()

        key1 = kd.derive_key("password1", salt)
        key2 = kd.derive_key("password2", salt)

        assert key1 != key2

    def test_derive_key_different_salts(self, sample_password):
        """Test different salts produce different keys."""
        kd = KeyDerivation(use_argon2=False)
        salt1 = kd.generate_salt()
        salt2 = kd.generate_salt()

        key1 = kd.derive_key(sample_password, salt1)
        key2 = kd.derive_key(sample_password, salt2)

        assert key1 != key2

    def test_derive_key_empty_password(self):
        """Test empty password raises error."""
        kd = KeyDerivation()
        salt = kd.generate_salt()

        with pytest.raises(InvalidPasswordError):
            kd.derive_key("", salt)

    def test_derive_key_invalid_salt(self, sample_password):
        """Test invalid salt raises error."""
        kd = KeyDerivation()

        with pytest.raises(InvalidPasswordError):
            kd.derive_key(sample_password, b"short")

    def test_verify_password_strength(self):
        """Test password strength verification."""
        kd = KeyDerivation()

        # Too short
        is_valid, msg = kd.verify_password_strength("short")
        assert not is_valid

        # Minimum length
        is_valid, msg = kd.verify_password_strength("12345678")
        assert is_valid

        # Strong password
        is_valid, msg = kd.verify_password_strength("StrongPass123!")
        assert is_valid
        assert "strong" in msg.lower()


class TestCryptoEngine:
    """Tests for CryptoEngine class."""

    def test_generate_nonce(self):
        """Test nonce generation."""
        nonce = CryptoEngine.generate_nonce()

        assert len(nonce) == CryptoEngine.NONCE_SIZE
        assert isinstance(nonce, bytes)

        # Test uniqueness
        nonce2 = CryptoEngine.generate_nonce()
        assert nonce != nonce2

    def test_encrypt_decrypt_small_file(self):
        """Test encryption and decryption of small file."""
        key = os.urandom(CryptoEngine.KEY_SIZE)
        crypto = CryptoEngine(key)

        # Create test data
        test_data = b"Hello, World! This is a test."
        input_file = BytesIO(test_data)
        encrypted_file = BytesIO()

        # Encrypt
        crypto.encrypt_file(input_file, encrypted_file)

        # Verify encrypted data is different
        encrypted_data = encrypted_file.getvalue()
        assert encrypted_data != test_data
        assert len(encrypted_data) > len(test_data)

        # Decrypt
        encrypted_file.seek(0)
        decrypted_file = BytesIO()
        crypto.decrypt_file(encrypted_file, decrypted_file)

        # Verify decrypted data matches original
        decrypted_data = decrypted_file.getvalue()
        assert decrypted_data == test_data

    def test_encrypt_decrypt_large_file(self):
        """Test encryption and decryption of large file (multiple chunks)."""
        key = os.urandom(CryptoEngine.KEY_SIZE)
        crypto = CryptoEngine(key)

        # Create large test data (multiple chunks)
        test_data = os.urandom(CryptoEngine.CHUNK_SIZE * 3 + 1000)
        input_file = BytesIO(test_data)
        encrypted_file = BytesIO()

        # Encrypt
        crypto.encrypt_file(input_file, encrypted_file)

        # Decrypt
        encrypted_file.seek(0)
        decrypted_file = BytesIO()
        crypto.decrypt_file(encrypted_file, decrypted_file)

        # Verify
        assert decrypted_file.getvalue() == test_data

    def test_encrypt_with_associated_data(self):
        """Test encryption with associated data."""
        key = os.urandom(CryptoEngine.KEY_SIZE)
        crypto = CryptoEngine(key)

        test_data = b"Test data"
        associated_data = b"metadata"

        input_file = BytesIO(test_data)
        encrypted_file = BytesIO()

        # Encrypt with AD
        crypto.encrypt_file(input_file, encrypted_file, associated_data)

        # Decrypt with correct AD
        encrypted_file.seek(0)
        decrypted_file = BytesIO()
        crypto.decrypt_file(encrypted_file, decrypted_file, associated_data)

        assert decrypted_file.getvalue() == test_data

        # Decrypt with wrong AD should fail
        encrypted_file.seek(0)
        decrypted_file2 = BytesIO()
        with pytest.raises(DecryptionError):
            crypto.decrypt_file(encrypted_file, decrypted_file2, b"wrong")

    def test_decrypt_wrong_key(self):
        """Test decryption with wrong key fails."""
        key1 = os.urandom(CryptoEngine.KEY_SIZE)
        key2 = os.urandom(CryptoEngine.KEY_SIZE)

        crypto1 = CryptoEngine(key1)
        crypto2 = CryptoEngine(key2)

        test_data = b"Test data"
        input_file = BytesIO(test_data)
        encrypted_file = BytesIO()

        # Encrypt with key1
        crypto1.encrypt_file(input_file, encrypted_file)

        # Try to decrypt with key2
        encrypted_file.seek(0)
        decrypted_file = BytesIO()

        with pytest.raises(DecryptionError):
            crypto2.decrypt_file(encrypted_file, decrypted_file)

    def test_decrypt_corrupted_data(self):
        """Test decryption of corrupted data fails."""
        key = os.urandom(CryptoEngine.KEY_SIZE)
        crypto = CryptoEngine(key)

        test_data = b"Test data for corruption check"
        input_file = BytesIO(test_data)
        encrypted_file = BytesIO()

        # Encrypt
        crypto.encrypt_file(input_file, encrypted_file)

        # Corrupt encrypted data (flip bits in the middle of encrypted content)
        encrypted_data = bytearray(encrypted_file.getvalue())
        # Corrupt at a safe index (after header: 1 byte version + 12 bytes nonce + 8 bytes size = 21)
        corruption_index = min(25, len(encrypted_data) - 1)
        encrypted_data[corruption_index] ^= 0xFF  # Flip bits
        corrupted_file = BytesIO(bytes(encrypted_data))

        # Try to decrypt
        decrypted_file = BytesIO()
        with pytest.raises(DecryptionError):
            crypto.decrypt_file(corrupted_file, decrypted_file)

    def test_encrypt_metadata(self):
        """Test metadata encryption and decryption."""
        key = os.urandom(CryptoEngine.KEY_SIZE)
        crypto = CryptoEngine(key)

        metadata = b"Important metadata"
        nonce = CryptoEngine.generate_nonce()

        # Encrypt
        encrypted = crypto.encrypt_metadata(metadata, nonce)
        assert encrypted != metadata

        # Decrypt
        decrypted = crypto.decrypt_metadata(encrypted, nonce)
        assert decrypted == metadata

    def test_invalid_key_size(self):
        """Test that invalid key size raises error."""
        with pytest.raises(EncryptionError):
            CryptoEngine(b"short_key")

        with pytest.raises(EncryptionError):
            CryptoEngine(b"x" * 64)  # Too long
