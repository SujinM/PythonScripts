# Folder Encryptor

Python application for secure folder encryption and decryption using modern cryptographic standards.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

##  Features

### Core Functionality
-  **Recursive folder encryption/decryption** with full structure preservation
-  **Password-based encryption** with secure key derivation
-  **Chunk-based streaming** for memory-efficient large file handling
-  **Authenticated encryption** using AES-256-GCM
-  **Corruption detection** with automatic integrity verification
-  **Wrong password detection** with clear error messages

### Security (OWASP Best Practices)
-  **AES-256-GCM** - Authenticated encryption (confidentiality + integrity)
-  **PBKDF2-HMAC-SHA256** - 600,000 iterations (OWASP 2023 recommendation)
-  **Optional Argon2id** - Winner of Password Hashing Competition
-  **Random salt** - Unique per encryption session
-  **Random nonce/IV** - Unique per file and chunk
-  **Secure password input** - Never logged or stored
-  **Memory-safe operations** - No sensitive data in logs
-  **Tamper detection** - Automatic authentication tag verification

### Code Quality
-  **Fully typed** with mypy compatibility
-  **Clean architecture** - Separation of concerns
-  **SOLID principles** - Maintainable and extensible
-  **Comprehensive tests** - Unit, integration, and service tests
-  **Google-style docstrings** - Complete documentation
-  **Black formatted** - Consistent code style
-  **Structured logging** - Colorized console output

##  Architecture

```
folder_encryptor/
│
├── app/
│   ├── core/                    # Core cryptographic components
│   │   ├── crypto_engine.py     # AES-256-GCM encryption
│   │   ├── key_derivation.py    # PBKDF2/Argon2id key derivation
│   │   ├── file_processor.py    # File/folder processing
│   │   └── exceptions.py        # Custom exception hierarchy
│   │
│   ├── services/                # Business logic layer
│   │   ├── encrypt_service.py   # Encryption orchestration
│   │   └── decrypt_service.py   # Decryption orchestration
│   │
│   ├── utils/                   # Utilities
│   │   ├── logger.py           # Logging configuration
│   │   └── helpers.py          # Helper functions
│   │
│   └── cli/                    # Command-line interface
│       └── main.py             # CLI entry point
│
├── tests/                      # Comprehensive test suite
│   ├── conftest.py            # Test fixtures
│   ├── test_crypto.py         # Crypto component tests
│   ├── test_services.py       # Service layer tests
│   └── test_integration.py    # End-to-end tests
│
├── pyproject.toml             # Project configuration
├── requirements.txt           # Production dependencies
└── README.md                  # This file
```

##  Installation

### Prerequisites
- Python 3.12 or higher
- pip package manager

### Basic Installation

```bash
# Clone the repository
cd /path/to/FolderCrypto

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install with Argon2 support
pip install argon2-cffi
```

### Development Installation

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Or install with optional dependencies
pip install -e ".[dev,argon2]"
```

##  Usage

### Command Line Interface

#### Encrypt a Folder

```bash
# Basic encryption (interactive password prompt)
python -m app.cli.main encrypt -i ./data -o ./encrypted

# With password argument (less secure - visible in history)
python -m app.cli.main encrypt -i ./data -o ./encrypted -p MyPassword123

# With Argon2id key derivation (requires argon2-cffi)
python -m app.cli.main encrypt -i ./data -o ./encrypted --use-argon2

# Force overwrite existing output
python -m app.cli.main encrypt -i ./data -o ./encrypted -f

# Verbose mode with debug logging
python -m app.cli.main encrypt -i ./data -o ./encrypted -v

# Without progress bar
python -m app.cli.main encrypt -i ./data -o ./encrypted --no-progress
```

#### Decrypt a Folder

```bash
# Basic decryption (interactive password prompt)
python -m app.cli.main decrypt -i ./encrypted -o ./restored

# With password argument
python -m app.cli.main decrypt -i ./encrypted -o ./restored -p MyPassword123

# With Argon2id (must match encryption)
python -m app.cli.main decrypt -i ./encrypted -o ./restored --use-argon2

# Verbose mode
python -m app.cli.main decrypt -i ./encrypted -o ./restored -v
```

#### Help and Options

```bash
# General help
python -m app.cli.main --help

# Encrypt command help
python -m app.cli.main encrypt --help

# Decrypt command help
python -m app.cli.main decrypt --help
```

### Programmatic Usage

```python
from app.services.encrypt_service import EncryptService
from app.services.decrypt_service import DecryptService

# Encrypt a folder
encrypt_service = EncryptService(use_argon2=False)
encrypt_service.encrypt_folder(
    input_path="./data",
    output_path="./encrypted",
    password="YourSecurePassword123!",
)

# Decrypt a folder
decrypt_service = DecryptService(use_argon2=False)
decrypt_service.decrypt_folder(
    input_path="./encrypted",
    output_path="./restored",
    password="YourSecurePassword123!",
)
```

### Progress Callbacks

```python
def my_progress_callback(filename: str, current: int, total: int):
    print(f"Processing {filename} ({current}/{total})")

encrypt_service = EncryptService()
encrypt_service.encrypt_folder(
    input_path="./data",
    output_path="./encrypted",
    password="password",
    progress_callback=my_progress_callback,
)
```

##  Security Details

### Encryption Scheme

**Algorithm**: AES-256-GCM (Galois/Counter Mode)
- Provides both encryption and authentication
- 256-bit key size
- 96-bit nonce (unique per chunk)
- 128-bit authentication tag

### Key Derivation

**Default: PBKDF2-HMAC-SHA256**
- 600,000 iterations (OWASP 2023)
- 256-bit salt (random per session)
- 256-bit output key
- SHA-256 hash function

**Optional: Argon2id**
- Memory-hard algorithm (resistant to GPU/ASIC attacks)
- 64 MB memory cost
- 3 iterations
- 4 parallel threads
- 256-bit output key

### File Format

**Encrypted File Structure:**
```
[Version:1B][Nonce:12B][FileSize:8B][Chunk1][Chunk2]...[ChunkN]
```

**Each Chunk:**
```
[ChunkSize:4B][EncryptedData+Tag]
```

**Metadata File:** `.folder_crypto_metadata.enc`
- Contains encrypted folder structure
- File sizes and permissions
- Integrity verification data

**Salt File:** `.salt`
- Contains random 256-bit salt
- Used for key derivation
- Must be preserved with encrypted data

### Security Guarantees

 **Confidentiality** - Data encrypted with AES-256
 **Integrity** - GCM authentication tags prevent tampering
 **Authenticity** - Wrong password detected immediately
 **Uniqueness** - Each encryption produces different ciphertext
 **Forward Secrecy** - Keys derived fresh from password
 **Side-Channel Resistance** - Constant-time operations where possible

### What This Does NOT Protect Against

 **Weak passwords** - Use strong, unique passwords
 **Keyloggers** - Protect your system from malware
 **Physical access** - Secure your encrypted files
 **Metadata leakage** - File sizes visible in encrypted form
 **Access timestamps** - Not encrypted or protected

##  Testing

### Run All Tests

```bash
# Run full test suite
pytest

# With coverage report
pytest --cov=app --cov-report=html

# Verbose output
pytest -v

# Run specific test file
pytest tests/test_crypto.py

# Run specific test
pytest tests/test_crypto.py::TestCryptoEngine::test_encrypt_decrypt_small_file
```

### Type Checking

```bash
# Run mypy type checker
mypy app/

# Check specific file
mypy app/core/crypto_engine.py
```

### Code Formatting

```bash
# Format code with Black
black app/ tests/

# Check formatting without changes
black --check app/ tests/

# Run ruff linter
ruff check app/ tests/
```

### Code Quality Checks

```bash
# Run all quality checks
black --check app/ tests/
ruff check app/ tests/
mypy app/
pytest --cov=app
```

##  Performance

### Benchmarks (Approximate)

- **Small files (< 1 MB)**: ~100-200 files/second
- **Large files (> 100 MB)**: Limited by disk I/O
- **Memory usage**: ~100 MB baseline + chunk buffer
- **Chunk size**: 64 KB (optimized for speed/memory)

### Performance Optimization

The application uses:
- **Streaming encryption** - Files processed in 64KB chunks
- **Minimal memory footprint** - Never loads entire file
- **Native cryptography** - Hardware AES-NI when available
- **Progress feedback** - tqdm progress bars

### Future Improvements

- [ ] Multiprocessing for parallel file encryption
- [ ] Compression before encryption (optional)
- [ ] Custom chunk size configuration
- [ ] Resume interrupted operations
- [ ] Cloud storage integration

##  Error Handling

### Common Errors

**Wrong Password**
```
DecryptionError: Decryption failed: wrong password or corrupted data
```
→ Verify password, check if Argon2 flag matches encryption

**Missing Salt File**
```
DecryptionError: Salt file not found. Invalid encrypted folder.
```
→ Ensure `.salt` file is present in encrypted folder

**Corrupted Data**
```
DecryptionError: Invalid file: corrupted chunk data
```
→ Data integrity compromised, restore from backup

**Invalid Path**
```
FileProcessingError: Input path does not exist
```
→ Check path exists and is accessible

##  Best Practices

### Password Selection

 **DO:**
- Use at least 12 characters
- Include uppercase, lowercase, numbers, symbols
- Use a password manager
- Use unique passwords for different folders

 **DON'T:**
- Reuse passwords across services
- Use dictionary words or common patterns
- Store passwords in plain text
- Share passwords via insecure channels

### Operational Security

 **DO:**
- Keep encrypted data and salt file together
- Backup encrypted data to multiple locations
- Test decryption before deleting original
- Use secure password input (getpass)
- Review logs for errors

 **DON'T:**
- Pass passwords via command-line arguments in production
- Leave decrypted data unattended
- Delete encrypted backups without verification
- Ignore decryption errors

##  Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Format code (`black app/ tests/`)
6. Type check (`mypy app/`)
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

##  Acknowledgments

- **[cryptography](https://cryptography.io/)** - Modern cryptography library
- **[OWASP](https://owasp.org/)** - Security best practices
- **[NIST](https://www.nist.gov/)** - Cryptographic standards
- **[tqdm](https://github.com/tqdm/tqdm)** - Progress bar library

##  Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review test cases for examples

##  Version History

### v1.0.0 (2026-02-22)
- Initial release
- AES-256-GCM encryption
- PBKDF2-HMAC-SHA256 key derivation
- Optional Argon2id support
- Comprehensive test suite
- CLI interface
- Production-ready architecture

---
