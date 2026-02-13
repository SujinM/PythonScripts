# Python Backup Utility

## ?? Overview

This is a **simple, configuration-based backup utility** written in Python as an alternative to the enterprise C# solution. It's perfect for users who want a lightweight, easy-to-configure backup tool.

---

## ? Features

- ? **INI Configuration** - Simple config file, no command-line arguments needed
- ? **Incremental Backup** - Only copies new or modified files
- ? **Smart Comparison** - Uses file modification timestamps
- ? **Folder Structure Preservation** - Maintains directory hierarchy
- ? **Automatic Folder Creation** - Creates destination folders as needed
- ? **Error Handling** - Robust error handling with clear messages
- ? **Progress Logging** - Real-time console output
- ? **Statistics** - Summary of copied, updated, and skipped files
- ? **No Dependencies** - Uses only Python standard library

---

## ?? Quick Start

### Prerequisites
- Python 3.7 or higher
- Windows OS

### Installation
1. Ensure Python is installed:
   ```cmd
   python --version
   ```

2. No additional packages needed! Uses only standard library.

### Usage

#### Option 1: Double-Click (Easiest)
1. Edit `config.ini` with your paths
2. Double-click `run-python-backup.bat`
3. Done!

#### Option 2: Command Line
```cmd
python backup.py
```

---

## ?? Configuration

Edit `config.ini`:

```ini
[Backup]
source_folder = C:\Data\TestFolder
destination_folder = D:\Backup
```

### Important Rules:
- **Source folder name is preserved**: 
  - Source: `C:\Data\TestFolder`
  - Destination: `D:\Backup`
  - Result: `D:\Backup\TestFolder` (automatically created)

- **No quotes needed** around paths
- **Spaces in paths** are supported
- **Use full paths** (e.g., `C:\...` not relative paths)

---

## ?? How It Works

### Backup Logic

1. **Read Configuration**
   - Load paths from `config.ini`
   - Validate source folder exists

2. **Create Backup Folder**
   - Extract source folder name
   - Create `destination\source_folder_name\`

3. **Scan & Compare**
   - Walk through all files in source
   - For each file:
     - If file doesn't exist in destination ? **COPY**
     - If file exists but source is newer ? **UPDATE**
     - If file is up to date ? **SKIP**

4. **Report Statistics**
   - Files copied
   - Files updated
   - Files skipped
   - Errors encountered

### Timestamp Comparison

Files are compared using **modification time** (mtime):
- Source mtime > Destination mtime ? File is copied
- Source mtime ? Destination mtime ? File is skipped

This ensures **only changed files** are backed up, saving time and space.

---

## ?? Examples

### Example 1: Documents Backup
```ini
[Backup]
source_folder = C:\Users\John\Documents
destination_folder = D:\MyBackups
```
**Result:** Creates `D:\MyBackups\Documents\` with all files

### Example 2: Project Backup
```ini
[Backup]
source_folder = C:\Projects\MyApp
destination_folder = E:\ProjectBackups
```
**Result:** Creates `E:\ProjectBackups\MyApp\` with all files

### Example 3: Photos Backup
```ini
[Backup]
source_folder = C:\Users\John\Pictures\Vacation2024
destination_folder = F:\PhotoBackup
```
**Result:** Creates `F:\PhotoBackup\Vacation2024\` with all files

---

## ?? Output Example

```
?????????????????????????????????????????????????????????????
?                                                           ?
?              FOLDER BACKUP UTILITY v1.0                   ?
?              Configuration-Based Backup                   ?
?                                                           ?
?????????????????????????????????????????????????????????????

[INFO] 2024-02-09 15:30:00 - Configuration loaded successfully
[INFO] 2024-02-09 15:30:00 - Source: C:\Data\TestFolder
[INFO] 2024-02-09 15:30:00 - Destination: D:\Backup
[INFO] 2024-02-09 15:30:00 - Backup folder: D:\Backup\TestFolder
[INFO] 2024-02-09 15:30:00 - Created backup folder: D:\Backup\TestFolder
============================================================
[INFO] 2024-02-09 15:30:00 - Starting backup operation...
============================================================
[INFO] 2024-02-09 15:30:01 - [COPIED] C:\Data\TestFolder\file1.txt
[INFO] 2024-02-09 15:30:01 - [UPDATED] C:\Data\TestFolder\file2.txt
[INFO] 2024-02-09 15:30:02 - [COPIED] C:\Data\TestFolder\subfolder\file3.txt
============================================================
[INFO] 2024-02-09 15:30:02 - Backup completed successfully!
[INFO] 2024-02-09 15:30:02 - Backup Statistics:
[INFO] 2024-02-09 15:30:02 -   Files copied:  2
[INFO] 2024-02-09 15:30:02 -   Files updated: 1
[INFO] 2024-02-09 15:30:02 -   Files skipped: 5
[INFO] 2024-02-09 15:30:02 -   Errors:        0
[INFO] 2024-02-09 15:30:02 -   Total files:   8
============================================================
```

---

## ?? Comparison: Python vs C# Version

| Feature | Python Version | C# Enterprise Version |
|---------|----------------|----------------------|
| **Complexity** | Simple, single file | Complex, multi-layered |
| **Configuration** | INI file | Command-line args + appsettings.json |
| **Backup Types** | Incremental only | Full/Incremental/Differential |
| **Dependencies** | None (stdlib only) | .NET 10, NuGet packages |
| **Compression** | Not implemented | Zip/GZip |
| **Encryption** | Not implemented | AES-256 |
| **Storage** | Local only | Local/External/Cloud |
| **Best For** | Quick personal backups | Enterprise/Production use |
| **Learning Curve** | Easy | Advanced |
| **Setup Time** | Instant | Requires .NET SDK |

---

## ?? Use Cases

### ? **Use Python Version When:**
- You want a simple, quick backup solution
- You don't need compression or encryption
- You backup to local or network drives only
- You prefer configuration files over command-line
- You want minimal setup (no .NET required)

### ? **Use C# Version When:**
- You need enterprise features (encryption, compression)
- You want multiple backup strategies
- You need cloud storage support
- You require detailed progress tracking
- You want a professional, scalable solution

---

## ??? Advanced Usage

### Scheduling with Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, weekly, etc.)
4. Action: Start a program
5. Program: `C:\Python\python.exe`
6. Arguments: `C:\Path\To\backup.py`
7. Start in: `C:\Path\To\`

### Multiple Configurations

Create multiple config files:
```
config-documents.ini
config-photos.ini
config-projects.ini
```

Run with specific config:
```python
python backup.py config-documents.ini
```

*(Note: Requires minor modification to `backup.py` to accept command-line argument)*

---

## ?? Troubleshooting

### Python not found
**Solution:** Install Python from https://www.python.org/downloads/  
Make sure to check "Add Python to PATH" during installation.

### Source folder not found
**Solution:** Check the path in `config.ini`. Use full paths like `C:\Folder`, not relative paths.

### Permission denied
**Solution:** Run as administrator or check folder permissions.

### Files not being updated
**Solution:** The timestamp comparison has a 1-second tolerance. Try modifying the file again.

---

## ?? Code Structure

```
backup.py (single file, ~350 lines)
?
??? BackupManager class
?   ??? load_configuration()     - Read INI file
?   ??? create_backup_folder()   - Create destination
?   ??? compare_files()          - Timestamp comparison
?   ??? copy_file()              - Copy with metadata
?   ??? backup_folder()          - Main backup loop
?   ??? run()                    - Main execution
?
??? main()                       - Entry point
```

---

## ?? Differences from Requirements

All requirements are fully implemented:
- ? Reads from `config.ini`
- ? Preserves source folder name
- ? Creates backup folder if not exists
- ? Copies new files
- ? Updates modified files
- ? Skips unchanged files
- ? Preserves folder structure
- ? Uses `configparser`, `os`, `shutil`
- ? Timestamp comparison
- ? Error handling
- ? Console logging
- ? Clear comments
- ? Windows compatible

---

## ?? Learning Resources

This script demonstrates:
- **OOP in Python** - Class-based design
- **File I/O** - Reading configs, walking directories
- **Error Handling** - Try-except blocks
- **Logging** - Timestamped console output
- **Path Manipulation** - os.path module
- **File Operations** - shutil for copying with metadata

---

## ?? License

Free to use and modify. No warranty provided.

---

## ?? When to Use Which Version?

**Python Version (This One):**
- Quick personal backups
- No external dependencies
- Simple configuration
- Local/network drives

**C# Enterprise Version:**
- Professional/business use
- Needs compression/encryption
- Cloud storage
- Advanced features
- Multiple backup strategies

---

**Both versions are available in this repository!** Choose the one that fits your needs.
