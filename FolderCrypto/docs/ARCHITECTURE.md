# FolderCrypto Application Architecture

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FolderCrypto Application                │
└─────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   GUI Layer  │    │   CLI Layer  │    │ API  Layer   │
│   (PyQt6)    │    │  (argparse)  │    │ (Services)   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
                  ┌──────────────────┐
                  │ Services Layer   │
                  │ ───────────────  │
                  │ EncryptService   │
                  │ DecryptService   │
                  └──────────────────┘
                             │
                             ▼
                  ┌──────────────────┐
                  │   Core Layer     │
                  │ ───────────────  │
                  │ CryptoEngine     │
                  │ KeyDerivation    │
                  │ FileProcessor    │
                  └──────────────────┘
                             │
                             ▼
                  ┌──────────────────┐
                  │ Utilities Layer  │
                  │ ───────────────  │
                  │ Logger           │
                  │ Config           │
                  │ Helpers          │
                  └──────────────────┘
```

## Data Flow

### Encryption Flow

```
User Input (GUI/CLI)
    │
    ├─→ Input Folder Path
    ├─→ Output Folder Path
    └─→ Password
         │
         ▼
EncryptService
    │
    ├─→ KeyDerivation.derive_key(password, salt)
    │       │
    │       └─→ Returns: encryption_key
    │
    ├─→ FileProcessor.list_files(input_folder)
    │       │
    │       └─→ Returns: [file1, file2, ...]
    │
    └─→ For each file:
            │
            └─→ CryptoEngine.encrypt_file(file, key)
                    │
                    ├─→ Generate random nonce
                    ├─→ Encrypt with AES-256-GCM
                    ├─→ Save: file.encrypted
                    └─→ Progress callback
```

### Decryption Flow

```
User Input (GUI/CLI)
    │
    ├─→ Encrypted Folder Path
    ├─→ Output Folder Path
    └─→ Password
         │
         ▼
DecryptService
    │
    ├─→ Read .salt file
    │
    ├─→ KeyDerivation.derive_key(password, salt)
    │       │
    │       └─→ Returns: decryption_key
    │
    ├─→ FileProcessor.list_encrypted_files(input_folder)
    │       │
    │       └─→ Returns: [file1.encrypted, ...]
    │
    └─→ For each encrypted file:
            │
            └─→ CryptoEngine.decrypt_file(file, key)
                    │
                    ├─→ Read nonce and ciphertext
                    ├─→ Decrypt with AES-256-GCM
                    ├─→ Verify authentication tag
                    ├─→ Save: original_filename
                    └─→ Progress callback
```

## Security Architecture

```
Password
    │
    ▼
┌─────────────────────┐
│  Key Derivation     │
│  ───────────────    │
│  • Random Salt      │
│  • PBKDF2-HMAC-256  │
│    (600k iterations)│
│  OR                 │
│  • Argon2id         │
└─────────────────────┘
    │
    ▼
Encryption Key (256-bit)
    │
    ▼
┌─────────────────────┐
│  AES-256-GCM        │
│  ───────────────    │
│  • Random Nonce/IV  │
│  • Authenticated    │
│  • Chunk-based      │
└─────────────────────┘
    │
    ▼
Encrypted Data + Auth Tag
```

## File Structure

```
Input Folder:
    ├── file1.txt
    ├── file2.pdf
    └── subfolder/
        └── file3.docx

        ↓ ENCRYPTION ↓

Encrypted Folder:
    ├── .salt                      # Random salt for key derivation
    ├── .folder_crypto_metadata.enc # Encrypted metadata
    ├── file1.txt.encrypted
    ├── file2.pdf.encrypted
    └── subfolder/
        └── file3.docx.encrypted

        ↓ DECRYPTION ↓

Output Folder:
    ├── file1.txt                  # Original files restored
    ├── file2.pdf
    └── subfolder/
        └── file3.docx
```

## GUI Component Hierarchy

```
MainWindow (QMainWindow)
    │
    ├─→ Header (QLabel)
    │       └─→ " FolderCrypto"
    │
    ├─→ Subtitle (QLabel)
    │       └─→ "Secure AES-256-GCM..."
    │
    ├─→ QTabWidget
    │       │
    │       ├─→ CryptoTab (operation='encrypt')
    │       │       │
    │       │       ├─→ Input Folder Group
    │       │       │       ├─→ Path LineEdit
    │       │       │       └─→ Browse Button
    │       │       │
    │       │       ├─→ Output Folder Group
    │       │       │       ├─→ Path LineEdit
    │       │       │       └─→ Browse Button
    │       │       │
    │       │       ├─→ Password Group
    │       │       │       ├─→ Password LineEdit
    │       │       │       ├─→ Show Password Checkbox
    │       │       │       └─→ Argon2 Checkbox
    │       │       │
    │       │       ├─→ Progress Group
    │       │       │       ├─→ Progress Bar
    │       │       │       └─→ Current File Label
    │       │       │
    │       │       ├─→ Log Group
    │       │       │       └─→ Log TextEdit
    │       │       │
    │       │       └─→ Encrypt Button
    │       │
    │       └─→ CryptoTab (operation='decrypt')
    │               └─→ (Same structure as encrypt)
    │
    └─→ Footer (QLabel)
            └─→ "Powered by AES-256-GCM..."
```

## Threading Model

```
Main Thread (GUI Event Loop)
    │
    ├─→ UI Updates
    ├─→ User Interactions
    └─→ Signal Reception
         │
         │ signals
         │ ◄─────────────┐
         │               │
         ▼               │
Worker Thread            │
    │                    │
    ├─→ EncryptService ──┤ progress signal
    ├─→ DecryptService ──┤ log signal
    └─→ File Operations ─┘ finished signal
```

## Error Handling Flow

```
Operation Start
    │
    ├─→ Validate Input
    │       │
    │       ├─→  Invalid → Show Warning Dialog → Stop
    │       └─→  Valid → Continue
    │
    ├─→ Start Worker Thread
    │       │
    │       └─→ Try Operation
    │               │
    │               ├─→  Exception Caught
    │               │       │
    │               │       ├─→ InvalidPasswordError
    │               │       │       └─→ "Invalid password or corrupted data"
    │               │       │
    │               │       ├─→ EncryptionError/DecryptionError
    │               │       │       └─→ Operation-specific error
    │               │       │
    │               │       └─→ Generic Exception
    │               │               └─→ "Unexpected error: ..."
    │               │
    │               └─→  Success
    │                       └─→ "Operation completed successfully!"
    │
    └─→ Show Result Dialog
            │
            ├─→ Success → Information Dialog
            └─→ Failure → Error Dialog
```

## Module Dependencies

```
main_window.py
    │
    ├─→ PyQt6.QtWidgets (UI components)
    ├─→ PyQt6.QtCore (Threading, signals)
    ├─→ PyQt6.QtGui (Fonts, cursors)
    │
    ├─→ app.services.encrypt_service
    │       └─→ app.core.*
    │               └─→ cryptography
    │
    ├─→ app.services.decrypt_service
    │       └─→ app.core.*
    │               └─→ cryptography
    │
    └─→ app.utils.logger
            └─→ logging
```

## Configuration Flow

```
Application Start
    │
    ├─→ setup_logging(verbose=True)
    │       │
    │       └─→ Console Handler
    │               ├─→ Formatting
    │               └─→ Color Output
    │
    ├─→ QApplication.setStyle("Fusion")
    │       └─→ Modern cross-platform theme
    │
    └─→ MainWindow.setStyleSheet(...)
            └─→ Custom CSS styling
```

## Future Architecture Enhancements

### Potential Additions

1. **Plugin System**
   ```
   app/plugins/
       ├── compression/
       ├── cloud_sync/
       └── notification/
   ```

2. **Settings Manager**
   ```
   app/settings/
       ├── user_preferences.py
       └── application_config.py
   ```

3. **Database Layer**
   ```
   app/database/
       ├── session_history.py
       └── favorites.py
   ```

4. **Network Layer**
   ```
   app/network/
       ├── cloud_storage.py
       └── remote_backup.py
   ```

## Design Patterns Used

- **Service Layer Pattern**: Services orchestrate core components
- **Strategy Pattern**: Pluggable key derivation (PBKDF2/Argon2)
- **Factory Pattern**: Exception creation and handling
- **Observer Pattern**: Progress callbacks
- **Command Pattern**: CLI command structure
- **MVC Pattern**: GUI separates model (services) from view (Qt widgets)

## Performance Characteristics

### Memory Usage
- **Chunk-based Processing**: ~64MB per operation
- **Streaming**: Large files don't load entirely into memory
- **Threading**: Worker thread isolated from UI

### Speed
- **PBKDF2**: ~2-3 seconds for key derivation
- **Argon2**: ~5-10 seconds for key derivation
- **Encryption**: ~50-100 MB/s (depends on disk speed)
- **UI**: Remains responsive during operations

### Scalability
- **File Count**: Handles thousands of files
- **File Size**: Handles GB-sized files
- **Folder Depth**: No practical limit on nesting
