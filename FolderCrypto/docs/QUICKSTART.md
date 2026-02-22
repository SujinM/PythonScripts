# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
cd /path/to/FolderCrypto
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python -m app.cli.main --help
```

You should see the help message with available commands.

### 3. Create Test Data

```bash
mkdir -p test_data
echo "Secret document" > test_data/secret.txt
echo "Confidential" > test_data/confidential.txt
mkdir test_data/subfolder
echo "Nested secret" > test_data/subfolder/nested.txt
```

### 4. Encrypt the Folder

```bash
python -m app.cli.main encrypt -i test_data -o encrypted_data
```

When prompted, enter a password (e.g., `TestPassword123!`)

### 5. Verify Encryption

```bash
ls encrypted_data/
# You should see:
# - .salt
# - .folder_crypto_metadata.enc
# - secret.txt.encrypted
# - confidential.txt.encrypted
# - subfolder/nested.txt.encrypted
```

### 6. Decrypt the Folder

```bash
python -m app.cli.main decrypt -i encrypted_data -o restored_data
```

Enter the same password you used for encryption.

### 7. Verify Restoration

```bash
diff -r test_data restored_data
# No output means files are identical!
```

## Common Use Cases

### Backup Important Documents

```bash
# Encrypt documents
python -m app.cli.main encrypt \
  -i ~/Documents/Important \
  -o ~/Backups/Important_encrypted \
  -v

# Later, restore when needed
python -m app.cli.main decrypt \
  -i ~/Backups/Important_encrypted \
  -o ~/Documents/Important_restored
```

### Archive Old Projects

```bash
# Encrypt old project
python -m app.cli.main encrypt \
  -i ~/Projects/old_project \
  -o ~/Archive/old_project.encrypted \
  --use-argon2  # Extra security

# Delete original after verification
rm -rf ~/Projects/old_project
```

### Secure Cloud Uploads

```bash
# Encrypt before uploading
python -m app.cli.main encrypt \
  -i ~/Photos/Private \
  -o ~/Photos/Private_encrypted

# Upload encrypted folder to cloud
# Download when needed
# Decrypt locally
python -m app.cli.main decrypt \
  -i ~/Downloads/Private_encrypted \
  -o ~/Photos/Private_decrypted
```

## Running Tests

```bash
# Quick test
python scripts.py test-fast

# Full test with coverage
python scripts.py test

# All quality checks
python scripts.py check
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"

**Solution**: Make sure you're in the FolderCrypto directory and virtual environment is activated.

```bash
cd /path/to/FolderCrypto
source venv/bin/activate
```

### "cryptography module not found"

**Solution**: Install dependencies.

```bash
pip install -r requirements.txt
```

### "Wrong password or corrupted data"

**Solutions**:
1. Verify you're using the correct password
2. Check if you used `--use-argon2` during encryption and use it during decryption
3. Ensure encrypted files haven't been modified

### Slow encryption on large folders

**Solutions**:
1. Use `--no-progress` to disable progress bar overhead
2. Ensure you have sufficient disk space
3. Consider encrypting subfolders separately

## Advanced Usage

### Custom Progress Tracking

Create a Python script:

```python
from app.services.encrypt_service import EncryptService

def my_callback(filename, current, total):
    percentage = (current / total) * 100
    print(f"[{percentage:.1f}%] {filename}")

service = EncryptService()
service.encrypt_folder(
    "./data",
    "./encrypted",
    "MyPassword123!",
    progress_callback=my_callback
)
```

### Batch Processing

```bash
#!/bin/bash
# encrypt_all.sh

for dir in folder1 folder2 folder3; do
    echo "Encrypting $dir..."
    python -m app.cli.main encrypt \
        -i "$dir" \
        -o "${dir}_encrypted" \
        -p "YourPassword" \
        --no-progress
done
```

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Review [pyproject.toml](pyproject.toml) for project configuration
3. Explore the codebase starting with [app/cli/main.py](app/cli/main.py)
4. Check out tests in [tests/](tests/) for usage examples
5. Customize logging in [app/utils/logger.py](app/utils/logger.py)

## Security Reminders

**Important**:
- Keep encrypted data AND `.salt` file together
- Use strong, unique passwords
- Test decryption before deleting originals
- Backup encrypted data to multiple locations
- Don't pass passwords via command line in production

**Best Practice**:
```bash
# Good: Interactive password prompt
python -m app.cli.main encrypt -i data -o encrypted

# Avoid: Password in command (visible in history)
python -m app.cli.main encrypt -i data -o encrypted -p MyPassword
```
