#!/usr/bin/env bash
# Build script for Folder Encryptor executable

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Folder Encryptor - Build Script${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}WARNING: Virtual environment not found${NC}"
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade PyInstaller
echo -e "${BLUE}Installing PyInstaller...${NC}"
pip install pyinstaller --upgrade

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt

# Clean previous builds
echo -e "${BLUE}Cleaning previous builds...${NC}"
rm -rf build dist *.spec.backup

# Run PyInstaller
echo -e "\n${BLUE}Building executable with PyInstaller...${NC}"
pyinstaller folder-encryptor.spec --clean

# Check if build was successful
if [ -f "dist/folder-encryptor" ] || [ -d "dist/folder-encryptor.app" ]; then
    echo -e "\n${GREEN}Build successful!${NC}\n"
    
    # Display build information
    echo -e "${BLUE}Build Information:${NC}"
    echo -e "   Output directory: ${YELLOW}dist/${NC}"
    
    if [ -f "dist/folder-encryptor" ]; then
        SIZE=$(du -h "dist/folder-encryptor" | cut -f1)
        echo -e "   Executable: ${YELLOW}dist/folder-encryptor${NC}"
        echo -e "   Size: ${YELLOW}$SIZE${NC}"
        
        # Make executable
        chmod +x dist/folder-encryptor
        
        echo -e "\n${GREEN}Usage:${NC}"
        echo -e "   ${YELLOW}./dist/folder-encryptor --help${NC}"
        echo -e "   ${YELLOW}./dist/folder-encryptor encrypt -i <input> -o <output>${NC}"
        echo -e "   ${YELLOW}./dist/folder-encryptor decrypt -i <encrypted> -o <output>${NC}"
    fi
    
    if [ -d "dist/folder-encryptor.app" ]; then
        SIZE=$(du -sh "dist/folder-encryptor.app" | cut -f1)
        echo -e "   App Bundle: ${YELLOW}dist/folder-encryptor.app${NC}"
        echo -e "   Size: ${YELLOW}$SIZE${NC}"
    fi
    
    # Test the executable
    echo -e "\n${BLUE}Testing executable...${NC}"
    if [ -f "dist/folder-encryptor" ]; then
        ./dist/folder-encryptor --version 2>/dev/null || ./dist/folder-encryptor --help | head -5
    fi
    
    echo -e "\n${GREEN}Build complete!${NC}"
    echo -e "${BLUE}The executable is ready in the ${YELLOW}dist/${BLUE} directory${NC}\n"
else
    echo -e "\n${RED}Build failed!${NC}"
    echo -e "${YELLOW}Check the output above for errors${NC}\n"
    exit 1
fi

# Optional: Create distribution package
read -p "$(echo -e ${YELLOW}Create distribution package? \(y/n\): ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Creating distribution package...${NC}"
    
    DIST_NAME="folder-encryptor-v1.0.0-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m)"
    DIST_DIR="dist/$DIST_NAME"
    
    mkdir -p "$DIST_DIR"
    
    # Copy executable
    if [ -f "dist/folder-encryptor" ]; then
        cp dist/folder-encryptor "$DIST_DIR/"
    fi
    
    # Copy documentation
    cp README.md "$DIST_DIR/" 2>/dev/null || echo "README.md not found"
    cp LICENSE "$DIST_DIR/" 2>/dev/null || echo "LICENSE not found"
    cp config.ini.template "$DIST_DIR/" 2>/dev/null || echo "config.ini.template not found"
    
    # Create archive
    cd dist
    tar -czf "$DIST_NAME.tar.gz" "$DIST_NAME"
    
    echo -e "${GREEN}Distribution package created: ${YELLOW}dist/$DIST_NAME.tar.gz${NC}"
    cd ..
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}   Build process completed!${NC}"
echo -e "${BLUE}========================================${NC}\n"
