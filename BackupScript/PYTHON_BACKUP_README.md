# Python Backup Utility

A simple Python script to backup files from one folder to another.

## Quick Start

1. Edit `config.ini` with your folder paths:
```ini
[Backup]
source_folder = C:\Data\TestFolder
destination_folder = D:\Backup
```

2. Run the backup:
   - Double-click `run-python-backup.bat`, OR
   - Run `python backup.py`

## Features

- Copies new files
- Updates modified files  
- Skips unchanged files
- Preserves folder structure
- No extra packages needed

## How It Works

The script compares file modification times:
- New files → Copied
- Modified files → Updated
- Unchanged files → Skipped

## Requirements

- Python 3.7 or higher
- Windows OS

## Example Output

```
Files copied:  2
Files updated: 1
Files skipped: 5
Errors:        0
```

## Troubleshooting

**Python not found?** Install from https://www.python.org/downloads/

**Permission denied?** Run as administrator

**Path not found?** Use full paths like `C:\Folder`

---
