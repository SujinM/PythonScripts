# FolderCrypto GUI Documentation

## Overview

The FolderCrypto GUI provides a user-friendly graphical interface for encrypting and decrypting folders using the same secure cryptographic engine as the CLI.

## Features

### User Interface

- **Tabbed Interface**: Separate tabs for encryption and decryption operations
- **File Browser Integration**: Browse and select folders using native file dialogs
- **Password Management**: 
  - Secure password input with masking
  - Show/hide password toggle
  - Password strength warnings
- **Progress Tracking**:
  - Real-time progress bar
  - Current file display
  - Percentage completion
- **Operation Logging**: Live log output showing all operations
- **Modern Styling**: Clean, professional UI using Qt Fusion style

### Security Features

- **Same Security as CLI**: Uses identical encryption services
- **No Password Storage**: Passwords are never saved or logged
- **Validation**: Automatic input validation before operations
- **Error Handling**: Clear error messages with actionable guidance
- **Argon2 Support**: Optional Argon2id key derivation

## Installation

### Requirements

```bash
pip install -r requirements.txt
```

This installs PyQt6 along with other dependencies.

### Verification

Test that the GUI launches correctly:

```bash
python gui.py
```

## Usage Guide

### Launching the GUI

**Method 1: Launcher Scripts**

Windows:
```bash
start-gui.bat
```

Linux/Mac:
```bash
./start-gui.sh
```

**Method 2: Direct Python**

```bash
python gui.py
```

**Method 3: Python Module**

```bash
python -m app.gui.main_window
```

### Encrypting a Folder

1. **Open the Encrypt Tab** (default tab on launch)
2. **Select Input Folder**:
   - Click "Browse..." next to Input Folder
   - Navigate to the folder you want to encrypt
   - Click "Select Folder"
3. **Select Output Folder**:
   - Click "Browse..." next to Output Folder
   - Choose where encrypted files will be saved
   - Click "Select Folder"
4. **Enter Password**:
   - Type a strong password (8+ characters recommended)
   - Optionally click "Show password" to verify typing
5. **Optional Settings**:
   - Check "Use Argon2 key derivation" for enhanced security (slower)
6. **Start Encryption**:
   - Click "Encrypt Folder"
   - Monitor progress in the progress bar
   - View detailed logs in the log window
7. **Completion**:
   - Success dialog appears when complete
   - Encrypted files are in the output folder

### Decrypting a Folder

1. **Switch to Decrypt Tab**
2. **Select Encrypted Folder**:
   - Click "Browse..." next to Input Folder
   - Select the folder containing encrypted files
3. **Select Output Folder**:
   - Choose where to restore decrypted files
4. **Enter Password**:
   - Enter the SAME password used for encryption
   - Must match exactly (case-sensitive)
5. **Match Settings**:
   - If Argon2 was used for encryption, check the Argon2 box
6. **Start Decryption**:
   - Click "Decrypt Folder"
   - Monitor progress
7. **Verify**:
   - Check that files are properly restored
   - Compare with originals if available

## GUI Components

### Input/Output Selection

- **Input Path Field**: Shows selected input folder path
- **Output Path Field**: Shows selected output folder path
- **Browse Buttons**: Open native folder selection dialogs
- **Path Validation**: Automatic validation on operation start

### Password Controls

- **Password Input**: Masked text field for password entry
- **Show Password Checkbox**: Toggle password visibility
- **Strength Warning**: Alert if password is weak (<8 characters)

### Progress Display

- **Progress Bar**: Visual percentage completion (0-100%)
- **Current File Label**: Shows which file is being processed
- **File Counter**: Displays progress as "current/total files"

### Log Window

- **Real-time Output**: All operations logged as they occur
- **Auto-scroll**: Automatically scrolls to latest messages
- **Read-only**: Prevents accidental edits
- **Monospace Font**: Easy to read technical output

### Action Buttons

- **Encrypt Folder / Decrypt Folder**: Starts the operation
- **Disabled During Operations**: Prevents multiple simultaneous operations
- **Re-enabled on Completion**: Ready for next operation

## Technical Details

### Threading

The GUI uses Qt threading to keep the interface responsive:

- **Main Thread**: Handles UI updates and user interaction
- **Worker Thread**: Performs encryption/decryption
- **Signal/Slot Communication**: Safe cross-thread updates

### Progress Callbacks

Progress is reported via callbacks:

```python
def progress_callback(filename: str, current: int, total: int):
    # Update progress bar: (current/total) * 100
    # Update status label: filename
    # Add to log: [current/total] filename
```

### Error Handling

Errors are caught and displayed with specific messages:

- **InvalidPasswordError**: "Password is incorrect or files are corrupted"
- **EncryptionError/DecryptionError**: Operation-specific error details
- **FileNotFoundError**: "Selected folder does not exist"
- **PermissionError**: "Insufficient permissions to access folder"

## Troubleshooting

### GUI Won't Launch

**Problem**: Error importing PyQt6

**Solution**:
```bash
pip install --upgrade PyQt6
```

### "Module not found: app"

**Problem**: Running from wrong directory

**Solution**:
```bash
cd /path/to/FolderCrypto
python gui.py
```

### GUI Freezes During Operation

**Problem**: Large folder causes apparent freeze (actually processing)

**Solution**: This is normal for very large folders. Check the log window for progress updates. The GUI uses threading to stay responsive, but very large operations may appear slow.

### Password Wrong but It's Correct

**Problem**: Decryption fails with correct password

**Solutions**:
1. Verify Argon2 setting matches encryption
2. Check for file corruption (check .salt file exists)
3. Ensure encrypted folder structure is intact

### Progress Bar Stuck at 0%

**Problem**: Progress not updating

**Solution**: Check log window - operation may have failed early. Common causes:
- Invalid input folder
- Insufficient disk space
- Permission denied

## Keyboard Shortcuts

While the GUI doesn't currently implement custom shortcuts, standard Qt shortcuts work:

- **Tab**: Navigate between fields
- **Enter**: Activate focused button
- **Ctrl+C**: Copy from log window
- **Ctrl+A**: Select all in input fields

## Programmatic Access

The GUI can also be launched programmatically:

```python
from app.gui.main_window import main

if __name__ == "__main__":
    main()
```

Or integrate into other applications:

```python
from PyQt6.QtWidgets import QApplication
from app.gui.main_window import MainWindow

app = QApplication([])
window = MainWindow()
window.show()
app.exec()
```

## Customization

### Styling

The GUI uses a custom stylesheet defined in `main_window.py`. To customize:

1. Locate the `setStyleSheet()` call in the `MainWindow.__init__()` method
2. Modify colors, fonts, sizes, etc.
3. Reload the GUI to see changes

Example color customization:
```python
# Change primary color from blue to green
# Find: background-color: #0078D4;
# Replace with: background-color: #107C10;
```

### Window Size

Default: 800x700 pixels

To change, modify in `MainWindow.init_ui()`:
```python
self.setGeometry(100, 100, 800, 700)  # x, y, width, height
```

## Future Enhancements

Potential features for future versions:

- [ ] Drag-and-drop folder selection
- [ ] Recent folders list
- [ ] Batch encryption/decryption
- [ ] Password strength meter
- [ ] Dark mode toggle
- [ ] Customizable themes
- [ ] Keyboard shortcuts
- [ ] File exclusion filters
- [ ] Compression before encryption
- [ ] Multi-language support

## Support

For issues or questions:

1. Check this documentation
2. Review [README.md](../README.md)
3. Check [QUICKSTART.md](QUICKSTART.md)
4. Review error messages in log window
5. Check console output for technical details

## Technical Architecture

### Component Structure

```
app/gui/
├── __init__.py          # Package initialization
└── main_window.py       # Main GUI application
    ├── WorkerThread     # Background operation thread
    ├── CryptoTab        # Encryption/decryption tab widget
    └── MainWindow       # Main application window
```

### Class Hierarchy

```
QMainWindow (Qt)
    └── MainWindow
            └── QTabWidget
                    ├── CryptoTab (operation='encrypt')
                    └── CryptoTab (operation='decrypt')

QThread (Qt)
    └── WorkerThread
```

### Signal Flow

```
User clicks "Encrypt Folder"
    ↓
CryptoTab.start_operation()
    ↓
Create WorkerThread
    ↓
WorkerThread.progress → CryptoTab.update_progress()
WorkerThread.log → CryptoTab.log_message()
WorkerThread.finished → CryptoTab.operation_finished()
```
