"""Core cryptographic engine using AES-256-GCM."""

import os
import struct
from typing import BinaryIO, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

from .exceptions import EncryptionError, DecryptionError


class CryptoEngine:
    """Handles encryption and decryption using AES-256-GCM.
    
    AES-GCM provides authenticated encryption with associated data (AEAD),
    which ensures both confidentiality and integrity.
    """

    # Constants
    KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits (recommended for GCM)
    TAG_SIZE = 16  # 128 bits (authentication tag)
    CHUNK_SIZE = 64 * 1024  # 64 KB chunks for streaming
    
    # File format version
    VERSION = 1

    def __init__(self, key: bytes) -> None:
        """Initialize the crypto engine with a key.

        Args:
            key: 256-bit encryption key.

        Raises:
            EncryptionError: If key is invalid.
        """
        if len(key) != self.KEY_SIZE:
            raise EncryptionError(
                f"Key must be exactly {self.KEY_SIZE} bytes, got {len(key)}"
            )

        self._aesgcm = AESGCM(key)

    @staticmethod
    def generate_nonce() -> bytes:
        """Generate a cryptographically secure random nonce.

        Returns:
            Random nonce bytes.
        """
        return os.urandom(CryptoEngine.NONCE_SIZE)

    def encrypt_file(
        self,
        input_file: BinaryIO,
        output_file: BinaryIO,
        associated_data: bytes = b"",
    ) -> None:
        """Encrypt a file using AES-256-GCM with streaming.

        Args:
            input_file: Input file object (opened in binary read mode).
            output_file: Output file object (opened in binary write mode).
            associated_data: Additional authenticated data (not encrypted).

        Raises:
            EncryptionError: If encryption fails.
        """
        try:
            # Generate unique nonce for this file
            nonce = self.generate_nonce()

            # Write file format header
            # Format: [version:1byte][nonce:12bytes][file_size:8bytes]
            input_file.seek(0, 2)  # Seek to end
            file_size = input_file.tell()
            input_file.seek(0)  # Seek back to start

            output_file.write(struct.pack("B", self.VERSION))
            output_file.write(nonce)
            output_file.write(struct.pack("<Q", file_size))

            # Encrypt file in chunks
            chunk_number = 0
            while True:
                chunk = input_file.read(self.CHUNK_SIZE)
                if not chunk:
                    break

                # Include chunk number in associated data to prevent reordering
                chunk_ad = associated_data + struct.pack("<Q", chunk_number)

                # Encrypt chunk with nonce + chunk_number for unique nonce
                chunk_nonce = self._derive_chunk_nonce(nonce, chunk_number)
                encrypted_chunk = self._aesgcm.encrypt(
                    chunk_nonce, chunk, chunk_ad
                )

                # Write chunk size and encrypted data
                output_file.write(struct.pack("<I", len(encrypted_chunk)))
                output_file.write(encrypted_chunk)

                chunk_number += 1

        except Exception as e:
            raise EncryptionError(f"Encryption failed: {str(e)}") from e

    def decrypt_file(
        self,
        input_file: BinaryIO,
        output_file: BinaryIO,
        associated_data: bytes = b"",
    ) -> None:
        """Decrypt a file using AES-256-GCM with streaming.

        Args:
            input_file: Encrypted input file object.
            output_file: Decrypted output file object.
            associated_data: Additional authenticated data.

        Raises:
            DecryptionError: If decryption fails or authentication fails.
        """
        try:
            # Read and verify header
            version_bytes = input_file.read(1)
            if not version_bytes:
                raise DecryptionError("Invalid file: empty or corrupted")

            version = struct.unpack("B", version_bytes)[0]
            if version != self.VERSION:
                raise DecryptionError(
                    f"Unsupported file version: {version} (expected {self.VERSION})"
                )

            # Read nonce and file size
            nonce = input_file.read(self.NONCE_SIZE)
            if len(nonce) != self.NONCE_SIZE:
                raise DecryptionError("Invalid file: corrupted header")

            file_size_bytes = input_file.read(8)
            if len(file_size_bytes) != 8:
                raise DecryptionError("Invalid file: corrupted header")

            expected_file_size = struct.unpack("<Q", file_size_bytes)[0]

            # Decrypt file in chunks
            chunk_number = 0
            total_decrypted = 0

            while True:
                # Read chunk size
                chunk_size_bytes = input_file.read(4)
                if not chunk_size_bytes:
                    break  # End of file

                if len(chunk_size_bytes) != 4:
                    raise DecryptionError("Invalid file: corrupted chunk size")

                chunk_size = struct.unpack("<I", chunk_size_bytes)[0]

                # Read encrypted chunk
                encrypted_chunk = input_file.read(chunk_size)
                if len(encrypted_chunk) != chunk_size:
                    raise DecryptionError("Invalid file: corrupted chunk data")

                # Decrypt chunk
                chunk_ad = associated_data + struct.pack("<Q", chunk_number)
                chunk_nonce = self._derive_chunk_nonce(nonce, chunk_number)

                try:
                    decrypted_chunk = self._aesgcm.decrypt(
                        chunk_nonce, encrypted_chunk, chunk_ad
                    )
                except Exception as e:
                    raise DecryptionError(
                        "Decryption failed: wrong password or corrupted data"
                    ) from e

                output_file.write(decrypted_chunk)
                total_decrypted += len(decrypted_chunk)
                chunk_number += 1

            # Verify total size matches expected
            if total_decrypted != expected_file_size:
                raise DecryptionError(
                    f"File size mismatch: expected {expected_file_size}, "
                    f"got {total_decrypted}"
                )

        except DecryptionError:
            raise
        except Exception as e:
            raise DecryptionError(f"Decryption failed: {str(e)}") from e

    def _derive_chunk_nonce(self, base_nonce: bytes, chunk_number: int) -> bytes:
        """Derive a unique nonce for each chunk.

        Args:
            base_nonce: Base nonce for the file.
            chunk_number: Chunk sequence number.

        Returns:
            Derived nonce for the chunk.
        """
        # XOR the chunk number into the last 8 bytes of the nonce
        nonce = bytearray(base_nonce)
        chunk_bytes = struct.pack("<Q", chunk_number)
        
        for i in range(8):
            nonce[-(8-i)] ^= chunk_bytes[i]
        
        return bytes(nonce)

    def encrypt_metadata(self, data: bytes, nonce: bytes) -> bytes:
        """Encrypt metadata using AES-256-GCM.

        Args:
            data: Metadata to encrypt.
            nonce: Nonce for encryption.

        Returns:
            Encrypted metadata.

        Raises:
            EncryptionError: If encryption fails.
        """
        try:
            return self._aesgcm.encrypt(nonce, data, b"metadata")
        except Exception as e:
            raise EncryptionError(f"Metadata encryption failed: {str(e)}") from e

    def decrypt_metadata(self, encrypted_data: bytes, nonce: bytes) -> bytes:
        """Decrypt metadata using AES-256-GCM.

        Args:
            encrypted_data: Encrypted metadata.
            nonce: Nonce for decryption.

        Returns:
            Decrypted metadata.

        Raises:
            DecryptionError: If decryption fails.
        """
        try:
            return self._aesgcm.decrypt(nonce, encrypted_data, b"metadata")
        except Exception as e:
            raise DecryptionError(
                f"Metadata decryption failed: wrong password or corrupted data"
            ) from e
