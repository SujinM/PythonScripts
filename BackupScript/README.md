# Backup Utility

Professional folder backup solution with incremental backup, modern GUI, and Windows executable support.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## ✨ Features

- **📂 Incremental Backup**: Only copies new or modified files
- **🎨 Modern Icon**: Professional cloud + folder design
- **⚙️ Auto-Configuration**: Creates config file template on first run
- **🖥️ User-Friendly Interface**: Beautiful launcher with version display
- **📦 Standalone EXE**: No Python installation required for end users
- **🔐 Digital Signature**: Self-signed certificate support
- **📝 Version Metadata**: Product name, copyright, description embedded
- **📊 Smart Comparison**: Uses timestamps for efficient file detection

## 🚀 Quick Start

### For End Users (EXE)

1. Download `backup.exe` from `dist/` folder
2. Double-click to run - config file auto-creates
3. Edit `config.ini` with your paths:
   ```ini
   [Backup1]
   source_folder = C:\Your\Source\Folder
   destination_folder = D:\Your\Backup\Location
   ```
4. Run `backup.exe` again to perform backup

### For Developers (Python)

```bash
# Clone the repository
git clone <repository-url>
cd BackupScript

# Install dependencies
pip install -r requirements.txt

# Run the script
python src/backup.py
```

## 📁 Project Structure

```
BackupScript/
├── README.md                # Quick overview (you are here)
├── PROJECT_GUIDE.md         # Complete documentation
├── LICENSE                  # MIT License
├── requirements.txt         # Python dependencies
├── setup.py                 # Package configuration
├── .gitignore              # Git ignore rules
│
├── src/                    # Source code
│   └── backup.py           # Main backup script
│
├── assets/                 # Icons and resources
│   ├── backup_icon.png     # Source icon (512x512)
│   └── backup_icon.ico     # Windows icon (multi-resolution)
│
├── config/                 # Configuration templates
│   └── config.ini.template # Default config template
│
├── scripts/                # Build scripts (2 simple options)
│   ├── build-test.bat        # 🔵 Simple build (quick, no metadata)
│   ├── build-production.bat  # 🟢 Complete build (version + signature)
│   ├── sign-quick.bat      # Digital signature only
│   ├── sign-helper.ps1     # PowerShell signing helper
│   └── version_resource.rc # Windows version resource
│
├── tools/                  # Development utilities
│   ├── png_to_ico.py       # Icon converter
│   └── verify_exe.py       # Metadata verification
│
├── docs/                   # Documentation
│   ├── PROJECT_SUMMARY.md  # Complete overview
│   └── QUICK_REFERENCE.md  # Command reference
│
└── dist/                   # Built executables
    └── backup.exe          # Final executable
```

**📖 For complete documentation, see [PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)**

## 🔧 Building the EXE

### Option 1: Simple Build (Quick, No Metadata)

```bash
cd scripts
.\build-test.bat
```

**Output:** `dist/backup.exe` (7.1 MB)
- ✅ Icon embedded
- ❌ No version info
- ❌ No signature
- ⚡ Fast (30 seconds)

### Option 2: Complete Build (Production Ready)

```bash
cd scripts
.\build-production.bat
```

**Output:** `dist/backup.exe` (7.45 MB)
- ✅ Icon embedded (512x512 multi-resolution)
- ✅ Version metadata (Product, Copyright, Description)
- ✅ Digital signature (optional, prompted)
- 🎯 Production ready (60 seconds)

### Add Signature to Existing EXE

```bash
cd scripts
.\sign-quick.bat
```

**📖 See [PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md) for detailed instructions**

## 📝 Configuration

Edit `config.ini` in the same directory as the executable:

```ini
[Backup1]
# Source folder to backup
source_folder = C:\Your\Source\Folder

# Destination folder (source folder name will be appended)
destination_folder = D:\Your\Backup\Location

[Backup2]
# Add more sections for multiple backup tasks
source_folder = C:\Another\Folder
destination_folder = E:\Another\Backup
```

**Example:**
- Source: `C:\Projects\MyApp`
- Destination: `D:\Backups`
- Creates: `D:\Backups\MyApp\`

## 📊 Features in Detail

### Incremental Backup
- Compares file modification times
- Only copies new/changed files
- Preserves folder structure
- Reports statistics (New, Updated, Unchanged)

### Auto-Configuration
- Creates `config.ini` template on first run
- Includes helpful comments and examples
- No manual file creation needed

### Version Information
- **Product Name:** Backup Utility
- **Version:** 1.0.0.0
- **Copyright:** Copyright (C) 2026 Sujin
- **Description:** Professional Folder Backup Solution

### Digital Signature
- Self-signed certificate generation
- Trusted by adding to Windows certificate store
- Shows in Properties → Digital Signatures tab

## 🛠️ Development

### Prerequisites

- Python 3.7+
- PyInstaller 6.18.0+
- Pillow (PIL) for icon generation
- Windows SDK (optional, for version info)

### Install Development Dependencies

```bash
pip install -r requirements.txt
```

### Run Tests

```bash
# Test the Python script
python src/backup.py

# Verify EXE metadata
python tools/verify_exe.py
```

### Modify Icon

```bash
# Edit assets/backup_icon.png (512x512)
# Then convert to ICO
python tools/png_to_ico.py
```

### Rebuild EXE

```bash
cd scripts
.\build-test.bat
```

## 📖 Documentation

- **[PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)** - Complete project overview
- **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Command quick reference

## ⚙️ System Requirements

### For EXE Users
- Windows 7 or later
- No additional software required

### For Python Development
- Windows 7 or later
- Python 3.7+
- 100 MB disk space

### For Building EXE
- Python 3.7+
- PyInstaller 6.18.0+
- Windows SDK (optional, for version metadata)

## 🔍 Troubleshooting

### Config File Not Found
- Run the executable once - it auto-creates `config.ini`
- Or copy from `config/config.ini.template`

### Build Errors
- Ensure PyInstaller is installed: `pip install pyinstaller`
- Check icon file exists: `assets/backup_icon.ico`
- See [PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md) for detailed troubleshooting

### Version Info Issues
- Use `build-complete.bat` for version metadata
- See [PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md) for complete instructions
- Simple `build.bat` doesn't include version info (by design)

## 📄 License

MIT License - See LICENSE file for details

## 👤 Author

**Sujin**

## 🙏 Acknowledgments

- PyInstaller for executable creation
- Pillow (PIL) for icon processing
- Windows SDK for resource compilation

## 📞 Support

For issues, questions, or contributions:
- Read [PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md) for complete documentation
- Check [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) for commands
- Open an issue on GitHub

---

**Status:** ✅ Production Ready | **Version:** 1.0.0 | **Last Updated:** February 14, 2026
