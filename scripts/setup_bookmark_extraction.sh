#!/bin/bash

# Mingus Financial Wellness App - Bookmark Extraction Setup Script

echo "=========================================="
echo "Mingus Bookmark Domain Extraction Setup"
echo "=========================================="
echo ""

echo "This script will help you extract and analyze browser bookmarks"
echo "for integration with the domain approval workflow."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher and try again"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check for browser bookmark files
echo ""
echo "🔍 Checking for browser bookmark files..."

# Chrome bookmarks
CHROME_PATH="$HOME/Library/Application Support/Google/Chrome/Default/Bookmarks"
if [ -f "$CHROME_PATH" ]; then
    echo "✅ Chrome bookmarks found"
    CHROME_AVAILABLE=true
else
    echo "❌ Chrome bookmarks not found"
    CHROME_AVAILABLE=false
fi

# Safari bookmarks
SAFARI_PATH="$HOME/Library/Safari/Bookmarks.plist"
if [ -f "$SAFARI_PATH" ]; then
    echo "✅ Safari bookmarks found (plist format)"
    SAFARI_AVAILABLE=true
else
    echo "❌ Safari bookmarks not found"
    SAFARI_AVAILABLE=false
fi

# Firefox bookmarks
FIREFOX_PATH="$HOME/Library/Application Support/Firefox/Profiles"
if [ -d "$FIREFOX_PATH" ]; then
    echo "✅ Firefox profiles found"
    FIREFOX_AVAILABLE=true
else
    echo "❌ Firefox profiles not found"
    FIREFOX_AVAILABLE=false
fi

echo ""
echo "📋 Manual Export Instructions:"
echo ""

if [ "$SAFARI_AVAILABLE" = true ]; then
    echo "🌐 Safari Bookmarks:"
    echo "   1. Open Safari"
    echo "   2. Go to File > Export Bookmarks"
    echo "   3. Save as 'safari_bookmarks.html'"
    echo "   4. Use: --html-file safari_bookmarks.html"
    echo ""
fi

if [ "$FIREFOX_AVAILABLE" = true ]; then
    echo "🦊 Firefox Bookmarks:"
    echo "   1. Open Firefox"
    echo "   2. Go to Bookmarks > Manage Bookmarks"
    echo "   3. Click Import and Backup > Export Bookmarks to HTML"
    echo "   4. Save as 'firefox_bookmarks.html'"
    echo "   5. Use: --html-file firefox_bookmarks.html"
    echo ""
fi

echo "📁 Create necessary directories..."
mkdir -p ../data
mkdir -p ../reports

echo "✅ Directories created"

# Check if bookmark extraction script exists
if [ -f "extract_bookmarks.py" ]; then
    echo "✅ Bookmark extraction script found"
else
    echo "❌ Bookmark extraction script not found"
    exit 1
fi

echo ""
echo "🚀 Ready to extract bookmarks!"
echo ""

# Ask user what they want to do
echo "Choose an option:"
echo "1. Extract from Chrome only (automatic)"
echo "2. Extract from HTML export file"
echo "3. Extract from Chrome + HTML file"
echo "4. Skip extraction for now"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🔍 Extracting from Chrome bookmarks..."
        python3 extract_bookmarks.py
        ;;
    2)
        read -p "Enter path to HTML bookmarks file: " html_file
        if [ -f "$html_file" ]; then
            echo "🔍 Extracting from HTML file: $html_file"
            python3 extract_bookmarks.py --html-file "$html_file"
        else
            echo "❌ File not found: $html_file"
            exit 1
        fi
        ;;
    3)
        read -p "Enter path to HTML bookmarks file: " html_file
        if [ -f "$html_file" ]; then
            echo "🔍 Extracting from Chrome + HTML file: $html_file"
            python3 extract_bookmarks.py --html-file "$html_file"
        else
            echo "❌ File not found: $html_file"
            exit 1
        fi
        ;;
    4)
        echo "⏭️  Skipping bookmark extraction"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""

if [ $choice -ne 4 ]; then
    echo "Next steps:"
    echo "1. Check the extraction report in ../reports/"
    echo "2. Run the domain approval interface:"
    echo "   python3 step3_domain_approval_interface.py"
    echo "3. Review bookmark domains in the approval interface"
    echo "4. Use bulk operations to quickly process domains"
    echo ""
    echo "📊 The bookmark domains have been merged with existing domains"
    echo "   and are ready for review in the approval interface."
else
    echo "To extract bookmarks later:"
    echo "python3 extract_bookmarks.py --html-file your_bookmarks.html"
fi

echo ""
echo "📚 For detailed instructions, see the script documentation"
echo ""
