"""Test configuration and fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def sample_password():
    """Sample password for tests."""
    return "TestPassword123!@#"


@pytest.fixture
def weak_password():
    """Weak password for tests."""
    return "weak"


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    # Create directory structure
    (temp_dir / "folder1").mkdir()
    (temp_dir / "folder1" / "subfolder").mkdir()
    (temp_dir / "folder2").mkdir()

    # Create files with different sizes
    (temp_dir / "file1.txt").write_text("Hello World!")
    (temp_dir / "folder1" / "file2.txt").write_text("Test content in folder1")
    (temp_dir / "folder1" / "subfolder" / "file3.txt").write_text("Nested file content")
    (temp_dir / "folder2" / "file4.txt").write_text("Another test file")

    # Create a binary file
    (temp_dir / "binary.bin").write_bytes(b"\x00\x01\x02\x03" * 1000)

    return temp_dir
