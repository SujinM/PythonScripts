# Backup Utility - Complete Project Guide

![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Folder Structure](#folder-structure)
- [Features](#features)
- [Quick Start](#quick-start)
- [Build Scripts](#build-scripts)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

**Backup Utility** is a professional Windows application that automates folder backup operations. It copies files from multiple source directories to destination directories while maintaining folder structure, tracking changes, and providing detailed statistics.

### Key Highlights
- ✅ **Professional Windows Executable** - Self-contained, no Python required
- ✅ **Modern Icon Design** - Cloud storage theme with backup kit aesthetics
- ✅ **Complete Metadata** - Version info, copyright, digital signature
- ✅ **Auto-Configuration** - Creates config.ini template on first run
- ✅ **User-Friendly Interface** - Interactive launcher with progress display
- ✅ **Detailed Logging** - Comprehensive backup reports with statistics

---

## 📁 Folder Structure

```
BackupScript/
│
├── 📄 README.md                    # Project overview and quick reference
├── 📄 PROJECT_GUIDE.md             # This comprehensive guide (YOU ARE HERE!)
├── 📄 LICENSE                      # MIT License
├── 📄 requirements.txt             # Python dependencies
├── 📄 setup.py                     # Python package configuration
├── 📄 .gitignore                   # Git exclusions
├── 📄 config.ini                   # User configuration (gitignored)
│
├── 📂 src/                         # Source Code
│   └── backup.py                   # Main Python script (13.6 KB)
│
├── 📂 assets/                      # Resources & Icons
│   ├── backup_icon.png             # Source icon (512x512, 28.5 KB)
│   └── backup_icon.ico             # Windows icon (multi-res, 30.9 KB)
│
├── 📂 config/                      # Configuration Templates
│   └── config.ini.template         # Template for users
│
├── 📂 scripts/                     # Build & Deployment Scripts
│   ├── build-test.bat              # 🔵 SIMPLE BUILD (Quick exe creation)
│   ├── build-production.bat        # 🟢 COMPLETE BUILD (Version + Signature)
│   ├── sign-quick.bat              # Digital signature only
│   ├── sign-helper.ps1             # PowerShell signing helper
│   ├── version_resource.rc         # Windows version resource
│   └── version_resource.res        # Compiled version resource
│
├── 📂 tools/                       # Development Utilities
│   ├── png_to_ico.py               # Icon converter
│   └── verify_exe.py               # Metadata verification
│
├── 📂 docs/                        # Documentation
│   ├── PROJECT_SUMMARY.md
│   ├── QUICK_REFERENCE.md
│
├── 📂 dist/                        # 🎯 OUTPUT (Executable Files)
│   └── backup.exe                  # Final executable (7.45 MB)
│
├── 📂 build/                       # Temporary build files (gitignored)
└── 📂 ResourceHacker/              # External tools (gitignored)
```

### Folder Descriptions

| Folder | Purpose | Contents |
|--------|---------|----------|
| **src/** | Python source code | Main backup script with launcher and auto-config |
| **assets/** | Icons and resources | PNG source and ICO multi-resolution icon |
| **config/** | Configuration templates | Template for config.ini creation |
| **scripts/** | Build automation | Batch files for building, versioning, signing |
| **tools/** | Development utilities | Icon conversion, metadata verification |
| **docs/** | Documentation | Complete guides and references |
| **dist/** | Build output | Final executable ready for distribution |
| **build/** | Temporary files | PyInstaller build artifacts (auto-cleaned) |

---

## ✨ Features

### Core Functionality
- 🔄 **Multi-Folder Backup** - Backup multiple source folders to destinations
- 📊 **Progress Tracking** - Real-time file counts and statistics
- 📝 **Detailed Logging** - Comprehensive backup reports
- ⚙️ **Auto-Configuration** - Creates config template if missing
- 🎨 **Modern UI** - Interactive launcher with ASCII art
- 🔍 **Change Detection** - Only copies modified files
- 📦 **Folder Structure Preservation** - Maintains directory hierarchy

### Executable Features
- 💎 **Professional Icon** - Modern cloud storage theme (512x512 multi-resolution)
- 📋 **Version Information** - Product name, version, copyright, description
- 🔐 **Digital Signature** - Self-signed certificate for authenticity
- 📦 **Single File** - All dependencies bundled (no installation needed)
- 💻 **Windows Optimized** - Native Windows executable

### Configuration
```ini
[Backup1]
source_folder = C:\SourceFolder1
destination_folder = E:\BackupFolder1

[Backup2]
source_folder = C:\SourceFolder2
destination_folder = F:\BackupFolder2
```

---

## 🚀 Quick Start

### For End Users (No Python Required)

1. **Download** `backup.exe` from the `dist/` folder
2. **Run** `backup.exe` - it will create `config.ini` template
3. **Edit** `config.ini` with your folder paths
4. **Run** `backup.exe` again to start backup

### For Developers

#### Prerequisites
```bash
# Install Python 3.7 or higher
# Install required packages
pip install -r requirements.txt
```

#### Build Simple Executable (No Version Info)
```bash
cd scripts
.\build-test.bat
```
**Output:** `dist/backup.exe` (7.1 MB, basic executable with icon)

#### Build Complete Executable (With Version + Signature)
```bash
cd scripts
.\build-production.bat
```
**Output:** `dist/backup.exe` (7.45 MB, full metadata + digital signature)

---

## 🛠️ Build Scripts

### Overview

| Script | Purpose | Output | Time |
|--------|---------|--------|------|
| **build-test.bat** | Simple build | Exe with icon only | ~30 sec |
| **build-production.bat** | Full build | Exe + version + signature | ~60 sec |

### 1. build-test.bat - Simple Build

**Location:** `scripts/build-test.bat`

**What It Does:**
- ✅ Converts PNG icon to ICO format
- ✅ Builds executable with PyInstaller
- ✅ Embeds icon in exe
- ❌ No version information
- ❌ No digital signature

**Usage:**
```bash
cd scripts
.\build-test.bat
```

**Output:**
```
dist/backup.exe
├── Size: 7.1 MB
├── Icon: ✓ Embedded
├── Version Info: ✗ Not included
└── Signature: ✗ Not included
```

**When to Use:**
- Quick testing during development
- You don't need metadata
- Fast iteration on code changes

---

### 2. build-production.bat - Complete Build

**Location:** `scripts/build-production.bat`

**What It Does:**
- ✅ Compiles Windows version resource (with Windows SDK)
- ✅ Converts PNG icon to ICO format
- ✅ Builds executable with PyInstaller
- ✅ Embeds icon in exe
- ✅ Adds version information (Product Name, Version, Copyright, Description)
- ✅ Adds digital signature (self-signed certificate)

**Usage:**
```bash
cd scripts
.\build-production.bat
```

**Output:**
```
dist/backup.exe
├── Size: 7.45 MB
├── Icon: ✓ Embedded (512x512 multi-res)
├── Version Info: ✓ Complete metadata
│   ├── Product Name: Backup Utility
│   ├── Version: 1.0.0.0
│   ├── Copyright: (C) 2026 Sujin
│   ├── Description: Professional Folder Backup Solution
│   └── Company: Sujin
└── Signature: ✓ Digitally signed
    ├── Signer: CN=Backup Utility by Sujin
    └── Valid Until: 2028
```

**When to Use:**
- Creating release builds
- Distributing to users
- Production deployments
- Professional presentation

**Requirements:**
- Windows SDK (for rc.exe)
  - Auto-detected from standard locations
  - Path: `C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\`
- Resource Hacker (auto-downloaded if missing)

---

### 3. sign-quick.bat - Add Signature Only

**Location:** `scripts/sign-quick.bat`

**What It Does:**
- ✅ Creates self-signed certificate
- ✅ Adds certificate to Trusted Root store
- ✅ Signs existing executable

**Usage:**
```bash
cd scripts
.\sign-quick.bat
```

**When to Use:**
- You already have a built exe
- You only need to add/update signature
- Testing signature verification

---

## 🔧 How It Works

### Build Process Flow

#### Simple Build (build.bat)
```
1. Check Python & PyInstaller installed
   └─> Install if missing

2. Convert icon: PNG → ICO
   └─> python tools/png_to_ico.py
   └─> Creates multi-resolution ICO

3. Build executable
   └─> PyInstaller --onefile --icon=assets/backup_icon.ico src/backup.py
   └─> Output: dist/backup.exe (7.1 MB)
```

#### Complete Build (build-complete.bat)
```
1. Find Windows SDK
   └─> Search standard Windows Kit locations
   └─> Add rc.exe to PATH

2. Compile version resource
   └─> rc.exe /fo scripts/version_resource.res scripts/version_resource.rc
   └─> Creates binary resource file

3. Convert icon: PNG → ICO
   └─> python tools/png_to_ico.py
   └─> Creates multi-resolution ICO (256, 128, 64, 32, 16)

4. Build executable with PyInstaller
   └─> python -m PyInstaller --onefile --icon=assets/backup_icon.ico --clean src/backup.py
   └─> Output: dist/backup.exe (7.1 MB)

5. Inject version information
   └─> Download Resource Hacker if needed
   └─> ResourceHacker.exe -open dist/backup.exe -res scripts/version_resource.res
   └─> Adds VERSIONINFO resource
   └─> Output: dist/backup.exe (7.45 MB)

6. Create digital signature
   └─> PowerShell: New-SelfSignedCertificate
   └─> Export certificate
   └─> Add to Trusted Root store
   └─> Sign exe: Set-AuthenticodeSignature
   └─> Output: Signed dist/backup.exe

7. Verify complete
   └─> python tools/verify_exe.py
   └─> Display all metadata
```

---

## ⚙️ Configuration

### config.ini Structure

```ini
[Backup1]
source_folder = C:\Users\YourName\Documents
destination_folder = E:\Backups\Documents

[Backup2]
source_folder = C:\Users\YourName\Pictures
destination_folder = E:\Backups\Pictures

[Backup3]
source_folder = D:\Projects
destination_folder = F:\Backups\Projects
```

### Configuration Rules
- **Section Names:** Must be unique (Backup1, Backup2, etc.)
- **Paths:** Can use forward slashes (/) or backslashes (\\)
- **Spaces:** Allowed in paths
- **Multiple Backups:** Add more [BackupN] sections as needed

### Auto-Configuration
If `config.ini` doesn't exist, the program will:
1. Create a template with 3 example backup sections
2. Display instructions
3. Exit and ask you to edit the config
4. Run again after editing

---

## 💻 Development

### Project Setup

```bash
# Clone repository
git clone <your-repo-url>
cd BackupScript

# Install dependencies
pip install -r requirements.txt

# Create config from template
copy config\config.ini.template config.ini

# Edit config.ini with your paths
notepad config.ini

# Run Python script directly
python src\backup.py
```

### Dependencies

**Runtime (bundled in exe):**
- Python 3.7+
- Standard library only (os, shutil, configparser, pathlib, datetime)

**Development (requirements.txt):**
```txt
pyinstaller>=6.0.0    # Exe creation
Pillow>=10.0.0        # Icon conversion
```

**External Tools (auto-managed):**
- Windows SDK (rc.exe) - Version resource compilation
- Resource Hacker - Version info injection
- PowerShell - Digital signature creation

### Customization

#### Change Version Information
Edit `scripts/version_resource.rc`:
```c
FILEVERSION 1,0,0,0
PRODUCTVERSION 1,0,0,0
  VALUE "CompanyName", "Your Company"
  VALUE "FileDescription", "Your Description"
  VALUE "ProductName", "Your Product Name"
  VALUE "LegalCopyright", "Copyright (C) 2026 Your Name"
```

#### Change Icon
Replace `assets/backup_icon.png` with your icon:
- Recommended size: 512x512 pixels
- Format: PNG with transparency
- Theme: Should represent your application

Then rebuild:
```bash
python tools\png_to_ico.py
cd scripts
.\build.bat
```

#### Change Certificate Name
Edit `scripts/sign-helper.ps1`:
```powershell
$certSubject = "CN=Your Application Name"
```

---

## 🐛 Troubleshooting

### Build Issues

#### "Python not found"
**Cause:** Python not installed or not in PATH

**Solution:**
1. Install Python from https://python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Restart terminal

#### "rc.exe not found"
**Cause:** Windows SDK not installed

**Solution:**
1. Download Windows SDK from Microsoft
2. Install "Windows 10 SDK" component
3. Or use simple build: `.\build.bat` (doesn't need SDK)

#### "PyInstaller not found"
**Cause:** PyInstaller not installed

**Solution:**
```bash
pip install pyinstaller
```

#### "Icon not embedded"
**Cause:** ICO file not found or invalid

**Solution:**
```bash
# Regenerate icon
python tools\png_to_ico.py

# Verify it exists
dir assets\backup_icon.ico
```

### Runtime Issues

#### "config.ini not found"
**Cause:** Config file missing

**Solution:**
1. Run the exe once - it will create a template
2. Or copy from: `config\config.ini.template`
3. Edit with your folder paths

#### "Backup failed"
**Causes:**
- Source folder doesn't exist
- Destination folder no write permission
- Path too long (Windows 260 character limit)

**Solutions:**
- Verify paths in config.ini
- Check folder permissions
- Use shorter paths or enable long path support

#### "No changes detected"
**Cause:** Files haven't changed since last backup

**Solution:** This is normal! The program only copies modified files.

---

## 📖 Additional Documentation

Located in `docs/` folder:

| File | Description |
|------|-------------|
| **PROJECT_SUMMARY.md** | Overview and capabilities |
| **QUICK_REFERENCE.md** | Command reference guide |

---

## 📊 Project Statistics

- **Lines of Code:** ~400 (backup.py)
- **Build Scripts:** 3 batch files + 1 PowerShell script
- **Documentation:** 2 markdown files
- **Executable Size:** 7.1 MB (simple) / 7.45 MB (complete)
- **Build Time:** 30 sec (simple) / 60 sec (complete)
- **Icon Resolutions:** 5 (256, 128, 64, 32, 16)
- **Supported Python:** 3.7 - 3.13+

---

## 🎓 Learning Resources

### Technologies Used
1. **Python** - Core scripting language
2. **PyInstaller** - Converts Python to executable
3. **Windows Resource Compiler (rc.exe)** - Compiles version info
4. **Resource Hacker** - Injects binary resources
5. **PowerShell** - Certificate management and signing
6. **Pillow (PIL)** - Image processing for icons

### Key Concepts
- Windows PE format and resources
- Digital signatures and certificates
- Icon formats (PNG → ICO conversion)
- Batch file scripting
- Python packaging and distribution

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

Copyright (C) 2026 Sujin. All Rights Reserved.

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📞 Support

For issues, questions, or suggestions:
1. Check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
2. Open an issue on GitHub
3. Review existing documentation in `docs/`

---

## 🎉 Quick Command Reference

```bash
# Simple build (quick, no metadata)
cd scripts && .\build-test.bat

# Complete build (everything included)
cd scripts && .\build-production.bat

# Add signature to existing exe
cd scripts && .\sign-quick.bat

# Convert icon
python tools\png_to_ico.py

# Verify exe metadata
python tools\verify_exe.py

# Run Python script directly
python src\backup.py

# Clean build artifacts
rmdir /s /q build dist
```

---

**Last Updated:** February 14, 2026  
**Version:** 1.0.0  
**Author:** Sujin  
**Project Status:** ✅ Production Ready
