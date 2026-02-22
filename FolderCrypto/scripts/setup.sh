#!/bin/bash
# Setup script for Folder Encryptor
# Run this to set up the development environment

set -e  # Exit on error

echo " Folder Encryptor - Setup Script"
echo "=================================="
echo ""

# Check Python version
echo " Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Check if Python 3.12+ is available
if ! command -v python3.12 &> /dev/null; then
    echo "Warning: Python 3.12 not found, using system Python"
    PYTHON_CMD="python3"
else
    echo "Python 3.12+ found"
    PYTHON_CMD="python3.12"
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
$PYTHON_CMD -m venv venv
echo "Virtual environment created"

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo ""
echo "Installing production dependencies..."
pip install -r requirements.txt

# Install development dependencies (optional)
read -p "Install development dependencies? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing development dependencies..."
    pip install -r requirements-dev.txt
    echo "Development dependencies installed"
fi

# Install Argon2 (optional)
read -p "Install Argon2 support? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing argon2-cffi..."
    pip install argon2-cffi
    echo "Argon2 support installed"
fi

# Verify installation
echo ""
echo "Verifying installation..."
python -c "import cryptography; print('cryptography:', cryptography.__version__)"
python -c "import tqdm; print('tqdm:', tqdm.__version__)"

# Test import
echo ""
echo "Testing application import..."
python -c "from app.cli.main import main; print('Application imports successfully')"

# Run tests (optional)
read -p "Run tests to verify installation? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running tests..."
    pytest tests/ -v --tb=short || echo "Some tests failed (may be expected on first run)"
fi

echo ""
echo "=================================="
echo "Setup completed successfully!"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Try the CLI:"
echo "     python -m app.cli.main --help"
echo ""
echo "  3. Run examples:"
echo "     python examples.py"
echo ""
echo "  4. Read the documentation:"
echo "     - README.md (full documentation)"
echo "     - QUICKSTART.md (quick start guide)"
echo "     - PROJECT_SUMMARY.md (project overview)"
echo ""
