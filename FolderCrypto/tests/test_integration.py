"""Integration tests."""

import pytest
import os
from pathlib import Path

from app.services.encrypt_service import EncryptService
from app.services.decrypt_service import DecryptService


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_encryption_decryption_cycle(self, temp_dir, sample_files):
        """Test complete encryption-decryption cycle."""
        password = "IntegrationTest123!@#"
        encrypted_dir = temp_dir / "encrypted"
        decrypted_dir = temp_dir / "decrypted"

        # Get original file list and contents
        original_files = list(sample_files.rglob("*"))
        original_contents = {}
        for f in original_files:
            if f.is_file():
                rel_path = f.relative_to(sample_files)
                original_contents[str(rel_path)] = f.read_bytes()

        # Encrypt
        encrypt_service = EncryptService(verify_password_strength=False)
        encrypt_service.encrypt_folder(
            str(sample_files),
            str(encrypted_dir),
            password,
        )

        # Decrypt
        decrypt_service = DecryptService()
        decrypt_service.decrypt_folder(
            str(encrypted_dir),
            str(decrypted_dir),
            password,
        )

        # Verify all files are restored with correct content
        for rel_path_str, original_content in original_contents.items():
            decrypted_file = decrypted_dir / rel_path_str
            assert decrypted_file.exists(), f"Missing file: {rel_path_str}"
            assert (
                decrypted_file.read_bytes() == original_content
            ), f"Content mismatch: {rel_path_str}"

    def test_multiple_encryption_rounds(self, temp_dir, sample_files):
        """Test encrypting the same data multiple times produces different output."""
        password = "MultiRound123!@#"

        encrypted_dir1 = temp_dir / "encrypted1"
        encrypted_dir2 = temp_dir / "encrypted2"

        # Encrypt twice
        encrypt_service = EncryptService(verify_password_strength=False)

        encrypt_service.encrypt_folder(
            str(sample_files),
            str(encrypted_dir1),
            password,
        )

        encrypt_service.encrypt_folder(
            str(sample_files),
            str(encrypted_dir2),
            password,
        )

        # Encrypted data should be different (different salts/nonces)
        enc1_file = encrypted_dir1 / "file1.txt.encrypted"
        enc2_file = encrypted_dir2 / "file1.txt.encrypted"

        assert enc1_file.read_bytes() != enc2_file.read_bytes()

        # But both should decrypt to same content
        decrypted_dir1 = temp_dir / "decrypted1"
        decrypted_dir2 = temp_dir / "decrypted2"

        decrypt_service = DecryptService()

        decrypt_service.decrypt_folder(
            str(encrypted_dir1),
            str(decrypted_dir1),
            password,
        )

        decrypt_service.decrypt_folder(
            str(encrypted_dir2),
            str(decrypted_dir2),
            password,
        )

        # Content should match
        original = (sample_files / "file1.txt").read_text()
        decrypted1 = (decrypted_dir1 / "file1.txt").read_text()
        decrypted2 = (decrypted_dir2 / "file1.txt").read_text()

        assert original == decrypted1 == decrypted2

    def test_empty_folder(self, temp_dir):
        """Test encryption of empty folder."""
        password = "EmptyFolder123!@#"
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        encrypted_dir = temp_dir / "encrypted"
        decrypted_dir = temp_dir / "decrypted"

        # Encrypt
        encrypt_service = EncryptService(verify_password_strength=False)
        encrypt_service.encrypt_folder(
            str(empty_dir),
            str(encrypted_dir),
            password,
        )

        # Decrypt
        decrypt_service = DecryptService()
        decrypt_service.decrypt_folder(
            str(encrypted_dir),
            str(decrypted_dir),
            password,
        )

        # Should have no files (only metadata)
        decrypted_files = list(decrypted_dir.rglob("*"))
        assert len(decrypted_files) == 0

    def test_large_file_handling(self, temp_dir):
        """Test handling of large files (multiple chunks)."""
        password = "LargeFile123!@#"
        input_dir = temp_dir / "input"
        input_dir.mkdir()

        # Create a large file (> 1 MB)
        large_file = input_dir / "large.bin"
        large_data = os.urandom(2 * 1024 * 1024)  # 2 MB
        large_file.write_bytes(large_data)

        encrypted_dir = temp_dir / "encrypted"
        decrypted_dir = temp_dir / "decrypted"

        # Encrypt
        encrypt_service = EncryptService(verify_password_strength=False)
        encrypt_service.encrypt_folder(
            str(input_dir),
            str(encrypted_dir),
            password,
        )

        # Decrypt
        decrypt_service = DecryptService()
        decrypt_service.decrypt_folder(
            str(encrypted_dir),
            str(decrypted_dir),
            password,
        )

        # Verify
        decrypted_data = (decrypted_dir / "large.bin").read_bytes()
        assert decrypted_data == large_data
        assert len(decrypted_data) == 2 * 1024 * 1024
