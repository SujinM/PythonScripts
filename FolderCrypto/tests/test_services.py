"""Tests for service layer."""

import pytest
import os
from pathlib import Path

from app.services.encrypt_service import EncryptService
from app.services.decrypt_service import DecryptService
from app.core.exceptions import (
    InvalidPasswordError,
    DecryptionError,
    EncryptionError,
)


class TestEncryptService:
    """Tests for EncryptService."""

    def test_encrypt_folder_success(self, temp_dir, sample_files, sample_password):
        """Test successful folder encryption."""
        output_dir = temp_dir / "encrypted"

        service = EncryptService(verify_password_strength=False)
        service.encrypt_folder(
            str(sample_files),
            str(output_dir),
            sample_password,
        )

        # Verify output exists
        assert output_dir.exists()
        assert (output_dir / ".salt").exists()
        assert (output_dir / ".folder_crypto_metadata.enc").exists()

        # Verify encrypted files exist
        assert (output_dir / "file1.txt.encrypted").exists()
        assert (output_dir / "folder1" / "file2.txt.encrypted").exists()

    def test_encrypt_weak_password_rejected(self, temp_dir, sample_files, weak_password):
        """Test that weak password is rejected when verification is enabled."""
        output_dir = temp_dir / "encrypted"

        service = EncryptService(verify_password_strength=True)

        with pytest.raises(InvalidPasswordError):
            service.encrypt_folder(
                str(sample_files),
                str(output_dir),
                weak_password,
            )

    def test_encrypt_weak_password_accepted_when_disabled(
        self, temp_dir, sample_files, weak_password
    ):
        """Test that weak password is accepted when verification is disabled."""
        output_dir = temp_dir / "encrypted"

        service = EncryptService(verify_password_strength=False)
        service.encrypt_folder(
            str(sample_files),
            str(output_dir),
            weak_password,
        )

        assert output_dir.exists()

    def test_encrypt_nonexistent_folder(self, temp_dir, sample_password):
        """Test encryption of nonexistent folder fails."""
        input_dir = temp_dir / "nonexistent"
        output_dir = temp_dir / "encrypted"

        service = EncryptService()

        with pytest.raises(Exception):  # FileProcessingError or similar
            service.encrypt_folder(
                str(input_dir),
                str(output_dir),
                sample_password,
            )


class TestDecryptService:
    """Tests for DecryptService."""

    def test_decrypt_folder_success(self, temp_dir, sample_files, sample_password):
        """Test successful folder decryption."""
        encrypted_dir = temp_dir / "encrypted"
        decrypted_dir = temp_dir / "decrypted"

        # First encrypt
        encrypt_service = EncryptService(verify_password_strength=False)
        encrypt_service.encrypt_folder(
            str(sample_files),
            str(encrypted_dir),
            sample_password,
        )

        # Then decrypt
        decrypt_service = DecryptService()
        decrypt_service.decrypt_folder(
            str(encrypted_dir),
            str(decrypted_dir),
            sample_password,
        )

        # Verify files are restored
        assert decrypted_dir.exists()
        assert (decrypted_dir / "file1.txt").exists()
        assert (decrypted_dir / "folder1" / "file2.txt").exists()
        assert (decrypted_dir / "folder1" / "subfolder" / "file3.txt").exists()

        # Verify content matches
        original_content = (sample_files / "file1.txt").read_text()
        decrypted_content = (decrypted_dir / "file1.txt").read_text()
        assert original_content == decrypted_content

    def test_decrypt_wrong_password(self, temp_dir, sample_files, sample_password):
        """Test decryption with wrong password fails."""
        encrypted_dir = temp_dir / "encrypted"
        decrypted_dir = temp_dir / "decrypted"

        # Encrypt
        encrypt_service = EncryptService(verify_password_strength=False)
        encrypt_service.encrypt_folder(
            str(sample_files),
            str(encrypted_dir),
            sample_password,
        )

        # Try to decrypt with wrong password
        decrypt_service = DecryptService()

        with pytest.raises(DecryptionError):
            decrypt_service.decrypt_folder(
                str(encrypted_dir),
                str(decrypted_dir),
                "WrongPassword123!",
            )

    def test_decrypt_missing_salt(self, temp_dir, sample_password):
        """Test decryption without salt file fails."""
        encrypted_dir = temp_dir / "encrypted"
        encrypted_dir.mkdir()
        decrypted_dir = temp_dir / "decrypted"

        decrypt_service = DecryptService()

        with pytest.raises(DecryptionError):
            decrypt_service.decrypt_folder(
                str(encrypted_dir),
                str(decrypted_dir),
                sample_password,
            )

    def test_encrypt_decrypt_binary_files(self, temp_dir, sample_files, sample_password):
        """Test encryption and decryption of binary files."""
        encrypted_dir = temp_dir / "encrypted"
        decrypted_dir = temp_dir / "decrypted"

        # Encrypt
        encrypt_service = EncryptService(verify_password_strength=False)
        encrypt_service.encrypt_folder(
            str(sample_files),
            str(encrypted_dir),
            sample_password,
        )

        # Decrypt
        decrypt_service = DecryptService()
        decrypt_service.decrypt_folder(
            str(encrypted_dir),
            str(decrypted_dir),
            sample_password,
        )

        # Verify binary file content
        original_binary = (sample_files / "binary.bin").read_bytes()
        decrypted_binary = (decrypted_dir / "binary.bin").read_bytes()
        assert original_binary == decrypted_binary

    def test_encrypt_decrypt_preserves_structure(
        self, temp_dir, sample_files, sample_password
    ):
        """Test that folder structure is preserved."""
        encrypted_dir = temp_dir / "encrypted"
        decrypted_dir = temp_dir / "decrypted"

        # Encrypt
        encrypt_service = EncryptService(verify_password_strength=False)
        encrypt_service.encrypt_folder(
            str(sample_files),
            str(encrypted_dir),
            sample_password,
        )

        # Decrypt
        decrypt_service = DecryptService()
        decrypt_service.decrypt_folder(
            str(encrypted_dir),
            str(decrypted_dir),
            sample_password,
        )

        # Verify structure
        assert (decrypted_dir / "folder1").is_dir()
        assert (decrypted_dir / "folder1" / "subfolder").is_dir()
        assert (decrypted_dir / "folder2").is_dir()
