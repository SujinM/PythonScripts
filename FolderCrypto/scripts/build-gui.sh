#!/bin/bash
# Build script for FolderCrypto GUI executable (Linux/Mac)

set -e

# Change to project root
cd "$(dirname "$0")/.."

echo ""
echo "========================================"
echo "  FolderCrypto GUI - Build Script"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "WARNING: Virtual environment not found"
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade PyInstaller
echo "Installing PyInstaller..."
pip install pyinstaller --upgrade

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Clean previous builds
echo "Cleaning previous GUI builds..."
rm -rf build/FolderCrypto-GUI
rm -f dist/FolderCrypto-GUI

# Check if .spec file exists
if [ ! -f "folder-crypto-gui.spec" ]; then
    echo ""
    echo "ERROR: folder-crypto-gui.spec not found!"
    echo "Please ensure the spec file exists in the project root."
    exit 1
fi

# Run PyInstaller
echo ""
echo "Building GUI executable with PyInstaller..."
echo "This may take a few minutes..."
echo ""
pyinstaller folder-crypto-gui.spec --clean

# Check if build was successful
if [ -f "dist/FolderCrypto-GUI" ]; then
    echo ""
    echo "========================================"
    echo "  Build Successful!"
    echo "========================================"
    echo ""
    
    # Display build information
    echo "Build Information:"
    echo "  Output directory: dist/"
    
    SIZE=$(stat -f%z "dist/FolderCrypto-GUI" 2>/dev/null || stat -c%s "dist/FolderCrypto-GUI")
    SIZE_MB=$((SIZE / 1048576))
    echo "  Executable: dist/FolderCrypto-GUI"
    echo "  Size: ~${SIZE_MB} MB"
    
    echo ""
    echo "Usage:"
    echo "  ./dist/FolderCrypto-GUI"
    
    echo ""
    echo "The GUI application is a standalone executable"
    echo "No Python installation required on target machines"
    
    echo ""
    echo "========================================"
    echo "  Build Complete!"
    echo "========================================"
    echo ""
    
    # Offer to run the executable
    read -p "Run the GUI now? (y/N): " RUN_GUI
    if [ "$RUN_GUI" = "y" ] || [ "$RUN_GUI" = "Y" ]; then
        echo ""
        echo "Launching FolderCrypto GUI..."
        ./dist/FolderCrypto-GUI &
    fi
    
else
    echo ""
    echo "========================================"
    echo "  Build Failed!"
    echo "========================================"
    echo ""
    echo "Check the output above for errors."
    echo ""
    echo "Common issues:"
    echo "  - Missing dependencies (run: pip install -r requirements.txt)"
    echo "  - PyQt6 not installed (run: pip install PyQt6)"
    echo ""
    exit 1
fi

echo ""
