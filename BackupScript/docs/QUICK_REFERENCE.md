# Quick Reference Card - Backup Utility

**Version:** 1.0.0  
**Date:** February 14, 2026

---

## 🎯 Which Script Should I Use?

```
┌────────────────────────────────────────────────────────────┐
│                    DECISION FLOWCHART                       │
└────────────────────────────────────────────────────────────┘

START: Need to build exe?
  │
  ├─→ [Quick testing/development]
  │   └─→ Use: scripts\build-test.bat
  │       Output: 7.1 MB, icon only
  │       Time: 30 seconds
  │
  └─→ [Production/release]
      └─→ Use: scripts\build-production.bat
          Output: 7.45 MB, full metadata
          Time: 60 seconds

Already have exe and need signature?
  └─→ Use: scripts\sign-quick.bat

Need documentation?
  └─→ Read: PROJECT_SUMMARY.md
```

---

## 📝 Build Commands

### Simple Build
```bash
cd scripts
.\build-test.bat
```
**When to use:** Testing, development, quick iterations  
**What you get:** Executable with icon  
**What's missing:** Version info, signature

---

### Complete Build
```bash
cd scripts
.\build-production.bat
```
**When to use:** Production, distribution, releases  
**What you get:** Executable + icon + version + signature  
**Recommended for:** End users

---

### Add Signature Only
```bash
cd scripts
.\sign-quick.bat
```
**When to use:** You have an exe and just need signature  
**What it does:** Creates certificate and signs exe

---

## 🛠️ Common Tasks

### First Time Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Build exe
cd scripts
.\build-complete.bat

# 3. Test exe
..\dist\backup.exe
```

---

### Testing Development Changes
```bash
# Quick rebuild after code changes
cd scripts
.\build-test.bat

# Test
..\dist\backup.exe
```

---

### Creating Release
```bash
# Complete build with metadata
cd scripts
.\build-production.bat

# Verify metadata
..\tools\verify_exe.py

# Test
..\dist\backup.exe

# Distribute
# Copy dist\backup.exe to users
```

---

## 🔍 File Locations

```
📂 BackupScript/
│
├── 📄 PROJECT_GUIDE.md      ← Read this for everything
├── 📄 README.md             ← Quick overview
│
├── 📂 scripts/              ← Build scripts here
│   ├── build-test.bat         ← Simple build
│   ├── build-production.bat   ← Complete build
│   └── sign-quick.bat       ← Add signature
│
├── 📂 src/                  ← Source code
│   └── backup.py
│
├── 📂 assets/               ← Icons
│   └── backup_icon.ico
│
├── 📂 dist/                 ← Built exe here
│   └── backup.exe           ← Final executable
│
└── 📂 tools/                ← Utilities
    ├── png_to_ico.py        ← Icon converter
    └── verify_exe.py        ← Check metadata
```

---

## ⚡ Quick Commands

```bash
# Build simple exe
cd scripts && .\build-test.bat

# Build complete exe
cd scripts && .\build-production.bat

# Sign existing exe
cd scripts && .\sign-quick.bat

# Verify exe metadata
python tools\verify_exe.py

# Run Python directly
python src\backup.py

# Clean builds
rmdir /s /q build dist

# Convert icon
python tools\png_to_ico.py
```

---

## 💡 Pro Tips

1. **Development Workflow**
   - Use `build-test.bat` for quick testing
   - Use `build-production.bat` before releasing

2. **Version Updates**
   - Edit `scripts/version_resource.rc` to change version
   - Rebuild with `build-production.bat`

3. **Icon Changes**
   - Replace `assets/backup_icon.png`
   - Run `python tools\png_to_ico.py`
   - Rebuild exe

4. **Signature Renewal**
   - Certificates expire in 2 years
   - Re-run `sign-quick.bat` to create new cert

5. **Verification**
   - Always run `verify_exe.py` after building
   - Check metadata in Windows Properties

---

## 🐛 Quick Troubleshooting

### "Python not found"
```bash
# Install Python and add to PATH
# Download from: https://python.org
```

### "PyInstaller not found"
```bash
pip install pyinstaller
```

### "rc.exe not found"
```bash
# Option 1: Install Windows SDK
# Option 2: Use simple build instead
cd scripts
.\build-test.bat
```

### "Icon not working"
```bash
# Regenerate icon
python tools\png_to_ico.py
```

### Build fails
```bash
# Clean and retry
rmdir /s /q build
cd scripts
.\build-test.bat
```

---

## 📊 Output Sizes

| Item | Size | Description |
|------|------|-------------|
| backup.py | 13.6 KB | Source Python script |
| backup_icon.png | 28.5 KB | Source icon (512x512) |
| backup_icon.ico | 30.9 KB | Windows icon (multi-res) |
| backup.exe (simple) | 7.1 MB | Exe with icon only |
| backup.exe (complete) | 7.45 MB | Exe with all metadata |

---

## 🔗 External Resources

- **Python:** https://python.org/downloads/
- **PyInstaller:** https://pyinstaller.org/
- **Windows SDK:** https://developer.microsoft.com/windows/downloads/windows-sdk/
- **Pillow (PIL):** https://pillow.readthedocs.io/

---

## ✅ Pre-Release Checklist

Before distributing to users:

- [ ] Run `build-production.bat`
- [ ] Verify version info with `verify_exe.py`
- [ ] Test exe on clean machine
- [ ] Check digital signature (optional)
- [ ] Include `config.ini.template`
- [ ] Create user documentation
- [ ] Test backup functionality
- [ ] Package for distribution

---

**Remember:** 
- 🔵 **build-test.bat** = Quick & Simple (Development)
- 🟢 **build-production.bat** = Full & Professional (Production)

**Documentation:**
- 📖 **PROJECT_SUMMARY.md** = Everything you need to know

---

*Last Updated: February 14, 2026*  
*Keep this as your desk reference!*
