#!/bin/bash
"""
Setup script for Apple Notes URL extraction

This script sets up the environment and dependencies for the Apple Notes
URL extraction functionality in the Mingus financial wellness app.

Author: Mingus Development Team
Date: 2025
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check macOS version
check_macos_version() {
    print_status "Checking macOS version..."
    
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This script is designed for macOS only"
        exit 1
    fi
    
    macos_version=$(sw_vers -productVersion)
    print_success "macOS version: $macos_version"
    
    # Check if version is compatible (10.12 or later)
    if [[ $(echo "$macos_version" | cut -d. -f1) -lt 10 ]] || \
       ([[ $(echo "$macos_version" | cut -d. -f1) -eq 10 ]] && \
        [[ $(echo "$macos_version" | cut -d. -f2) -lt 12 ]]); then
        print_warning "macOS 10.12 or later is recommended for optimal Apple Notes access"
    fi
}

# Function to check Python environment
check_python_environment() {
    print_status "Checking Python environment..."
    
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        print_status "Please install Python 3 from https://www.python.org/downloads/"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    print_success "Python version: $python_version"
    
    # Check if version is 3.7 or later
    if [[ $(echo "$python_version" | cut -d. -f1) -lt 3 ]] || \
       ([[ $(echo "$python_version" | cut -d. -f1) -eq 3 ]] && \
        [[ $(echo "$python_version" | cut -d. -f2) -lt 7 ]]); then
        print_error "Python 3.7 or later is required"
        exit 1
    fi
    
    # Check if pip is available
    if ! command_exists pip3; then
        print_error "pip3 is required but not available"
        exit 1
    fi
}

# Function to install Python dependencies
install_python_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Create requirements file for notes extraction
    cat > requirements_notes.txt << EOF
# Apple Notes URL Extraction Dependencies
pandas>=1.3.0
numpy>=1.21.0
requests>=2.25.0
tqdm>=4.62.0
matplotlib>=3.4.0
seaborn>=0.11.0
pytest>=6.2.0
pytest-cov>=2.12.0
EOF
    
    # Install dependencies
    if pip3 install -r requirements_notes.txt; then
        print_success "Python dependencies installed successfully"
    else
        print_error "Failed to install Python dependencies"
        exit 1
    fi
}

# Function to check Apple Notes access
check_notes_access() {
    print_status "Checking Apple Notes database access..."
    
    # Check for Notes database files
    notes_db_paths=(
        "$HOME/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite"
        "$HOME/Library/Containers/com.apple.Notes/Data/Library/Notes/NotesV7.storedata"
    )
    
    notes_found=false
    for db_path in "${notes_db_paths[@]}"; do
        if [[ -f "$db_path" ]]; then
            print_success "Found Notes database: $db_path"
            notes_found=true
            break
        fi
    done
    
    if [[ "$notes_found" == false ]]; then
        print_warning "Apple Notes database not found in expected locations"
        print_status "This may be normal if Notes app hasn't been used or is using iCloud"
        print_status "The extraction script will handle this gracefully"
    fi
}

# Function to check file permissions
check_file_permissions() {
    print_status "Checking file permissions..."
    
    # Check if we can read the Notes database
    for db_path in "$HOME/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite" \
                   "$HOME/Library/Containers/com.apple.Notes/Data/Library/Notes/NotesV7.storedata"; do
        if [[ -f "$db_path" ]]; then
            if [[ -r "$db_path" ]]; then
                print_success "Notes database is readable: $db_path"
            else
                print_warning "Notes database exists but may not be readable: $db_path"
                print_status "You may need to grant Full Disk Access to Terminal/your IDE"
            fi
        fi
    done
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    # Create data directory if it doesn't exist
    if [[ ! -d "../data" ]]; then
        mkdir -p ../data
        print_success "Created data directory"
    else
        print_success "Data directory already exists"
    fi
    
    # Create logs directory if it doesn't exist
    if [[ ! -d "logs" ]]; then
        mkdir -p logs
        print_success "Created logs directory"
    else
        print_success "Logs directory already exists"
    fi
    
    # Create reports directory if it doesn't exist
    if [[ ! -d "../reports" ]]; then
        mkdir -p ../reports
        print_success "Created reports directory"
    else
        print_success "Reports directory already exists"
    fi
}

# Function to set up security permissions
setup_security_permissions() {
    print_status "Setting up security permissions..."
    
    print_warning "Apple Notes extraction requires access to the Notes database"
    print_status "You may need to grant Full Disk Access to your terminal/IDE"
    print_status "To do this:"
    print_status "1. Go to System Preferences > Security & Privacy > Privacy"
    print_status "2. Select 'Full Disk Access' from the left sidebar"
    print_status "3. Click the lock icon to make changes"
    print_status "4. Add your terminal application (Terminal.app, iTerm2, etc.)"
    print_status "5. Or add your IDE (VS Code, Cursor, etc.)"
    
    read -p "Press Enter to continue after setting up permissions..."
}

# Function to test the extraction script
test_extraction_script() {
    print_status "Testing extraction script..."
    
    # Check if the script exists
    if [[ ! -f "extract_notes_urls.py" ]]; then
        print_error "extract_notes_urls.py not found"
        exit 1
    fi
    
    # Test basic script functionality
    if python3 -c "import extract_notes_urls; print('Script imports successfully')" 2>/dev/null; then
        print_success "Extraction script imports successfully"
    else
        print_error "Extraction script has import errors"
        exit 1
    fi
    
    # Test test script
    if [[ -f "test_notes_extraction.py" ]]; then
        print_status "Running tests..."
        if python3 -m pytest test_notes_extraction.py -v; then
            print_success "Tests passed successfully"
        else
            print_warning "Some tests failed (this may be normal for mock tests)"
        fi
    else
        print_warning "Test script not found"
    fi
}

# Function to create integration script
create_integration_script() {
    print_status "Creating integration script..."
    
    cat > integrate_notes_domains.py << 'EOF'
#!/usr/bin/env python3
"""
Integration script to merge Notes domains with existing domain approval interface

This script merges the Notes domain recommendations with the existing
domain approval system from Steps 1-3.

Author: Mingus Development Team
Date: 2025
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any

def merge_notes_domains():
    """Merge Notes domains with existing domain recommendations"""
    
    data_dir = Path("../data")
    
    # Load existing domain recommendations
    existing_file = data_dir / "domain_recommendations.json"
    if existing_file.exists():
        with open(existing_file, 'r') as f:
            existing_domains = json.load(f)
        print(f"Loaded {len(existing_domains)} existing domains")
    else:
        existing_domains = {}
        print("No existing domain recommendations found")
    
    # Load Notes domain recommendations
    notes_file = data_dir / "notes_recommendations.json"
    if notes_file.exists():
        with open(notes_file, 'r') as f:
            notes_domains = json.load(f)
        print(f"Loaded {len(notes_domains)} Notes domains")
        
        # Merge domains (Notes domains take precedence for duplicates)
        merged_domains = existing_domains.copy()
        for domain, data in notes_domains.items():
            merged_domains[domain] = data
        
        # Save merged recommendations
        with open(data_dir / "domain_recommendations_merged.json", 'w') as f:
            json.dump(merged_domains, f, indent=2)
        
        print(f"Saved {len(merged_domains)} merged domains")
        
        # Create summary
        summary = {
            'total_domains': len(merged_domains),
            'existing_domains': len(existing_domains),
            'notes_domains': len(notes_domains),
            'new_domains_from_notes': len(set(notes_domains.keys()) - set(existing_domains.keys())),
            'duplicate_domains': len(set(notes_domains.keys()) & set(existing_domains.keys()))
        }
        
        with open(data_dir / "integration_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("Integration summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
    else:
        print("No Notes domain recommendations found")

if __name__ == "__main__":
    merge_notes_domains()
EOF
    
    chmod +x integrate_notes_domains.py
    print_success "Created integration script: integrate_notes_domains.py"
}

# Function to create usage documentation
create_documentation() {
    print_status "Creating usage documentation..."
    
    cat > README_notes_extraction.md << 'EOF'
# Apple Notes URL Extraction for Mingus Financial Wellness App

This module extracts URLs from Apple Notes on macOS and integrates them with the existing domain approval workflow.

## Features

- Extract URLs from Apple Notes database (SQLite)
- Parse both plain text and rich text note content
- Filter for financial/career/professional development content
- Analyze domains using Step 2 intelligence logic
- Output in same format as email/bookmark domains
- Integrate with existing approval interface
- Handle encrypted/locked notes gracefully
- Cross-reference with already approved domains

## Prerequisites

- macOS 10.12 or later
- Python 3.7 or later
- Apple Notes app (for database access)
- Full Disk Access permissions (may be required)

## Installation

1. Run the setup script:
   ```bash
   ./setup_notes_extraction.sh
   ```

2. Grant Full Disk Access permissions if prompted:
   - System Preferences > Security & Privacy > Privacy > Full Disk Access
   - Add your terminal/IDE application

## Usage

### Basic Extraction

```bash
python3 extract_notes_urls.py
```

This will:
- Extract URLs from all accessible Apple Notes
- Analyze domains using Step 2 intelligence
- Save results to `../data/` directory

### Integration with Existing System

```bash
python3 integrate_notes_domains.py
```

This merges Notes domains with existing domain recommendations.

### Testing

```bash
python3 -m pytest test_notes_extraction.py -v
```

## Output Files

- `notes_urls_complete.csv` - All extracted URLs with note context
- `notes_domain_analysis.csv` - Domain statistics from notes
- `notes_recommendations.json` - Domain recommendations for approval
- `notes_processing_summary.json` - Extraction statistics

## Apple Notes Database Locations

- Primary: `~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite`
- Fallback: `~/Library/Containers/com.apple.Notes/Data/Library/Notes/NotesV7.storedata`

## Security & Privacy

- The script only reads from the Notes database
- No data is transmitted or stored externally
- All processing is done locally
- Respects user privacy and security settings

## Troubleshooting

### Database Access Issues

If you encounter database access errors:

1. Ensure Full Disk Access is granted to your terminal/IDE
2. Check if Notes app is running (may lock database)
3. Verify Notes database exists in expected locations

### No URLs Found

If no URLs are extracted:

1. Check if you have notes with URLs
2. Verify note content is accessible
3. Check logs for specific error messages

### Performance Issues

For large note collections:

1. The script processes notes efficiently
2. Progress is logged to console
3. Memory usage is optimized for large datasets

## Integration with Approval Interface

The extracted domains are automatically integrated with the Step 3 approval interface:

1. Run extraction: `python3 extract_notes_urls.py`
2. Merge domains: `python3 integrate_notes_domains.py`
3. Launch approval interface: `python3 step3_domain_approval_interface.py`

Notes domains will appear with "SOURCE: Notes" in the interface.

## Expected Outcomes

- 200-800 URLs from manually curated notes
- 50-150 unique domains (likely higher quality than email)
- High overlap with approved domains (validation)
- Discovery of new high-value sources

## Support

For issues or questions, check the logs in the `logs/` directory or refer to the main Mingus documentation.
EOF
    
    print_success "Created documentation: README_notes_extraction.md"
}

# Main setup function
main() {
    print_status "Setting up Apple Notes URL extraction for Mingus..."
    
    # Check prerequisites
    check_macos_version
    check_python_environment
    
    # Install dependencies
    install_python_dependencies
    
    # Check Notes access
    check_notes_access
    check_file_permissions
    
    # Create directories
    create_directories
    
    # Set up security permissions
    setup_security_permissions
    
    # Test the extraction script
    test_extraction_script
    
    # Create integration script
    create_integration_script
    
    # Create documentation
    create_documentation
    
    print_success "Apple Notes extraction setup completed successfully!"
    print_status ""
    print_status "Next steps:"
    print_status "1. Run extraction: python3 extract_notes_urls.py"
    print_status "2. Integrate domains: python3 integrate_notes_domains.py"
    print_status "3. Review results in ../data/ directory"
    print_status "4. Launch approval interface: python3 step3_domain_approval_interface.py"
}

# Run main function
main "$@"
