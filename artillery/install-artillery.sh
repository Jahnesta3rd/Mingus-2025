#!/bin/bash
# Artillery Installation Script

echo "=========================================="
echo "Installing Artillery Load Testing Tool"
echo "=========================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    echo ""
    echo "Please install Node.js first:"
    echo "  - Visit: https://nodejs.org/"
    echo "  - Or use Homebrew: brew install node"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed"
    exit 1
fi

echo "✅ npm found: $(npm --version)"
echo ""

# Install Artillery globally
echo "Installing Artillery globally..."
npm install -g artillery

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Artillery installed successfully!"
    echo ""
    echo "Verify installation:"
    echo "  artillery --version"
    echo ""
    echo "You can now run load tests:"
    echo "  artillery run artillery/artillery-config.yml"
else
    echo ""
    echo "❌ Installation failed"
    echo ""
    echo "Try installing with sudo:"
    echo "  sudo npm install -g artillery"
    exit 1
fi
