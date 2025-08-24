#!/bin/bash

# Mingus Financial Wellness App - Step 3 Setup Script
# Domain Approval Interface Setup

echo "=========================================="
echo "Mingus Step 3: Domain Approval Interface"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher and try again"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is not installed"
    echo "Please install pip3 and try again"
    exit 1
fi

echo "✅ pip3 found: $(pip3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv_step3" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv_step3
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv_step3/bin/activate

# Install requirements
echo "📥 Installing dependencies..."
pip install -r requirements_step3.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Error installing dependencies"
    exit 1
fi

# Check for required data files
echo ""
echo "🔍 Checking for required data files..."

DATA_DIR="../data"
REQUIRED_FILES=(
    "domain_recommendations.json"
    "bulk_action_suggestions.json"
    "cultural_relevance_analysis.json"
    "high_value_domains.csv"
    "medium_value_domains.csv"
    "low_value_domains.csv"
)

MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$DATA_DIR/$file" ]; then
        echo "✅ $file found"
    else
        echo "❌ $file missing"
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Warning: Some required files are missing:"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "Please ensure Step 2 has been completed and all data files exist."
    echo "You can still run the application, but some features may not work properly."
fi

# Create necessary directories
echo ""
echo "📁 Creating necessary directories..."
mkdir -p templates
mkdir -p static
mkdir -p ../reports
mkdir -p ../config

echo "✅ Directories created"

# Test Flask installation
echo ""
echo "🧪 Testing Flask installation..."
python3 -c "import flask; print('✅ Flask version:', flask.__version__)" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Flask is working correctly"
else
    echo "❌ Error: Flask is not working correctly"
    exit 1
fi

# Display setup completion
echo ""
echo "=========================================="
echo "🎉 Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv_step3/bin/activate"
echo ""
echo "2. Run the domain approval interface:"
echo "   python3 step3_domain_approval_interface.py"
echo ""
echo "3. Open your browser and go to:"
echo "   http://localhost:5001"
echo ""
echo "4. Start with bulk operations to quickly process domains"
echo ""
echo "📚 For detailed instructions, see README_step3.md"
echo ""

# Check if user wants to run the application now
read -p "Would you like to run the application now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting Mingus Domain Approval Interface..."
    echo "Press Ctrl+C to stop the application"
    echo ""
    python3 step3_domain_approval_interface.py
else
    echo "Setup complete! Run the application when ready."
fi
