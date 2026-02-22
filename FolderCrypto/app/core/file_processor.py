"""File and folder processing for encryption and decryption."""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass, asdict

from .crypto_engine import CryptoEngine
from .exceptions import FileProcessingError, InvalidMetadataError


@dataclass
class FileMetadata:
    """Metadata for an encrypted file."""

    relative_path: str
    original_size: int
    encrypted_size: int
    is_directory: bool
    permissions: Optional[int] = None


class FileProcessor:
    """Handles file and folder processing for encryption/decryption."""

    METADATA_FILENAME = ".folder_crypto_metadata.enc"
    ENCRYPTED_EXTENSION = ".encrypted"

    def __init__(self, crypto_engine: CryptoEngine) -> None:
        """Initialize file processor.

        Args:
            crypto_engine: Crypto engine for encryption/decryption.
        """
        self.crypto_engine = crypto_engine

    def encrypt_folder(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> None:
        """Encrypt an entire folder recursively.

        Args:
            input_path: Input folder path.
            output_path: Output folder path.
            progress_callback: Optional callback(filename, current, total).

        Raises:
            FileProcessingError: If processing fails.
        """
        if not input_path.exists():
            raise FileProcessingError(f"Input path does not exist: {input_path}")

        if not input_path.is_dir():
            raise FileProcessingError(f"Input path is not a directory: {input_path}")

        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)

        # Collect all files and directories
        all_items = self._collect_items(input_path)
        total_items = len(all_items)

        metadata_list: List[FileMetadata] = []

        for idx, item_path in enumerate(all_items, 1):
            relative_path = item_path.relative_to(input_path)

            if progress_callback:
                progress_callback(str(relative_path), idx, total_items)

            if item_path.is_dir():
                # Record directory in metadata
                metadata = FileMetadata(
                    relative_path=str(relative_path),
                    original_size=0,
                    encrypted_size=0,
                    is_directory=True,
                    permissions=item_path.stat().st_mode,
                )
                metadata_list.append(metadata)
            else:
                # Encrypt file
                output_file_path = output_path / (
                    str(relative_path) + self.ENCRYPTED_EXTENSION
                )
                output_file_path.parent.mkdir(parents=True, exist_ok=True)

                original_size = item_path.stat().st_size

                try:
                    with open(item_path, "rb") as input_file:
                        with open(output_file_path, "wb") as output_file:
                            # Use relative path as associated data
                            ad = str(relative_path).encode("utf-8")
                            self.crypto_engine.encrypt_file(
                                input_file, output_file, ad
                            )

                    encrypted_size = output_file_path.stat().st_size

                    metadata = FileMetadata(
                        relative_path=str(relative_path),
                        original_size=original_size,
                        encrypted_size=encrypted_size,
                        is_directory=False,
                        permissions=item_path.stat().st_mode,
                    )
                    metadata_list.append(metadata)

                except Exception as e:
                    raise FileProcessingError(
                        f"Failed to encrypt {relative_path}: {str(e)}"
                    ) from e

        # Save encrypted metadata
        self._save_metadata(output_path, metadata_list)

    def decrypt_folder(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> None:
        """Decrypt an entire folder.

        Args:
            input_path: Encrypted folder path.
            output_path: Output folder path.
            progress_callback: Optional callback(filename, current, total).

        Raises:
            FileProcessingError: If processing fails.
        """
        if not input_path.exists():
            raise FileProcessingError(f"Input path does not exist: {input_path}")

        if not input_path.is_dir():
            raise FileProcessingError(f"Input path is not a directory: {input_path}")

        # Load metadata
        metadata_list = self._load_metadata(input_path)
        total_items = len(metadata_list)

        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)

        for idx, metadata in enumerate(metadata_list, 1):
            relative_path = Path(metadata.relative_path)

            if progress_callback:
                progress_callback(str(relative_path), idx, total_items)

            if metadata.is_directory:
                # Recreate directory
                dir_path = output_path / relative_path
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # Restore permissions if available
                if metadata.permissions:
                    try:
                        os.chmod(dir_path, metadata.permissions)
                    except Exception:
                        pass  # Ignore permission errors
            else:
                # Decrypt file
                encrypted_file_path = input_path / (
                    str(relative_path) + self.ENCRYPTED_EXTENSION
                )
                output_file_path = output_path / relative_path
                output_file_path.parent.mkdir(parents=True, exist_ok=True)

                if not encrypted_file_path.exists():
                    raise FileProcessingError(
                        f"Encrypted file not found: {encrypted_file_path}"
                    )

                try:
                    with open(encrypted_file_path, "rb") as input_file:
                        with open(output_file_path, "wb") as output_file:
                            # Use relative path as associated data
                            ad = str(relative_path).encode("utf-8")
                            self.crypto_engine.decrypt_file(
                                input_file, output_file, ad
                            )

                    # Verify decrypted size
                    decrypted_size = output_file_path.stat().st_size
                    if decrypted_size != metadata.original_size:
                        raise FileProcessingError(
                            f"Size mismatch for {relative_path}: "
                            f"expected {metadata.original_size}, got {decrypted_size}"
                        )

                    # Restore permissions if available
                    if metadata.permissions:
                        try:
                            os.chmod(output_file_path, metadata.permissions)
                        except Exception:
                            pass  # Ignore permission errors

                except FileProcessingError:
                    raise
                except Exception as e:
                    raise FileProcessingError(
                        f"Failed to decrypt {relative_path}: {str(e)}"
                    ) from e

    def _collect_items(self, root_path: Path) -> List[Path]:
        """Collect all files and directories in a folder.

        Args:
            root_path: Root folder path.

        Returns:
            List of paths (directories first, then files).
        """
        directories = []
        files = []

        for item in root_path.rglob("*"):
            if item.is_dir():
                directories.append(item)
            else:
                files.append(item)

        # Return directories first, then files (for proper reconstruction)
        return sorted(directories) + sorted(files)

    def _save_metadata(
        self, output_path: Path, metadata_list: List[FileMetadata]
    ) -> None:
        """Save encrypted metadata file.

        Args:
            output_path: Output folder path.
            metadata_list: List of file metadata.

        Raises:
            FileProcessingError: If saving fails.
        """
        try:
            # Convert metadata to JSON
            metadata_dict = {
                "version": 1,
                "files": [asdict(m) for m in metadata_list],
            }
            metadata_json = json.dumps(metadata_dict, indent=2)
            metadata_bytes = metadata_json.encode("utf-8")

            # Encrypt metadata
            nonce = CryptoEngine.generate_nonce()
            encrypted_metadata = self.crypto_engine.encrypt_metadata(
                metadata_bytes, nonce
            )

            # Write to file
            metadata_path = output_path / self.METADATA_FILENAME
            with open(metadata_path, "wb") as f:
                f.write(nonce)
                f.write(encrypted_metadata)

        except Exception as e:
            raise FileProcessingError(
                f"Failed to save metadata: {str(e)}"
            ) from e

    def _load_metadata(self, input_path: Path) -> List[FileMetadata]:
        """Load and decrypt metadata file.

        Args:
            input_path: Encrypted folder path.

        Returns:
            List of file metadata.

        Raises:
            InvalidMetadataError: If metadata is invalid or corrupted.
        """
        metadata_path = input_path / self.METADATA_FILENAME

        if not metadata_path.exists():
            raise InvalidMetadataError(
                f"Metadata file not found: {metadata_path}"
            )

        try:
            with open(metadata_path, "rb") as f:
                nonce = f.read(CryptoEngine.NONCE_SIZE)
                encrypted_metadata = f.read()

            # Decrypt metadata
            metadata_bytes = self.crypto_engine.decrypt_metadata(
                encrypted_metadata, nonce
            )
            metadata_json = metadata_bytes.decode("utf-8")
            metadata_dict = json.loads(metadata_json)

            # Validate version
            if metadata_dict.get("version") != 1:
                raise InvalidMetadataError(
                    f"Unsupported metadata version: {metadata_dict.get('version')}"
                )

            # Parse metadata
            metadata_list = [
                FileMetadata(**m) for m in metadata_dict.get("files", [])
            ]

            return metadata_list

        except InvalidMetadataError:
            raise
        except Exception as e:
            raise InvalidMetadataError(
                f"Failed to load metadata: {str(e)}"
            ) from e
