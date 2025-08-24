#!/bin/bash

# Step 1: Mac Email URL Extractor Setup Script
# This script automates the setup process for the email extractor

set -e  # Exit on any error

echo "Step 1: Mac Email URL Extractor - Setup Script"
echo "================================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    echo "Please install Python 3.7+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION found"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed or not in PATH"
    echo "Please install pip and try again"
    exit 1
fi

echo "✅ pip3 found"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements_step1.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Run setup verification
echo ""
echo "Running setup verification..."
python3 test_step1_setup.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Set up your app-specific password:"
    echo "   - Go to https://appleid.apple.com"
    echo "   - Security → App-Specific Passwords"
    echo "   - Generate password for 'Mingus Email Extractor'"
    echo ""
    echo "2. Set environment variables (optional):"
    echo "   export MAC_EMAIL='your_email@mac.com'"
    echo "   export MAC_APP_PASSWORD='your-app-specific-password'"
    echo ""
    echo "3. Run the extractor:"
    echo "   python3 step1_mac_email_extractor.py"
    echo ""
    echo "For detailed instructions, see README_step1.md"
else
    echo ""
    echo "❌ Setup verification failed"
    echo "Please check the error messages above and try again"
    exit 1
fi
