# Instagram Extraction CLI Usage Guide

## Overview

The Instagram Extraction and Download System provides a comprehensive command-line interface for extracting Instagram content from Mac Notes and downloading it for use with Mingus. The CLI is designed to be intuitive for users with basic command-line experience while providing comprehensive functionality.

## Quick Start

```bash
# Check if everything is set up correctly
python extract_instagram.py validate-folder

# Run the complete pipeline
python extract_instagram.py full-process

# Extract content with a limit for testing
python extract_instagram.py extract-content --limit 10

# Download Instagram content
python extract_instagram.py download --limit 5
```

## Commands

### 1. validate-folder

Check if the MINGUS folder exists and show detailed statistics.

```bash
python extract_instagram.py validate-folder [--verbose]
```

**What it does:**
- Validates that the MINGUS folder exists in Mac Notes
- Checks if the Notes app is running
- Shows folder statistics (total notes, content length, categories)
- Displays recent notes and category breakdown

**Example output:**
```
📊 FOLDER STATISTICS:
   📁 Folder path: /Users/username/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite
   📝 Total notes: 150
   📄 Notes with content: 142
   🎨 Rich text notes: 89
   📏 Total content length: 45,230 characters

🏷️  CATEGORY BREAKDOWN:
   faith: 45 (30.0%)
   work_life: 32 (21.3%)
   friendships: 28 (18.7%)
   children: 25 (16.7%)
   relationships: 15 (10.0%)
   going_out: 5 (3.3%)
```

### 2. extract-content

Extract Instagram content from the MINGUS folder.

```bash
python extract_instagram.py extract-content [options]
```

**Options:**
- `--limit N`: Process only first N items (useful for testing)
- `--category [category]`: Filter by specific category (faith, work_life, friendships, children, relationships, going_out)
- `--dry-run`: Preview operations without execution
- `--verbose`: Detailed logging output
- `--output-dir [path]`: Custom output directory

**Examples:**
```bash
# Extract all content
python extract_instagram.py extract-content

# Extract first 10 notes for testing
python extract_instagram.py extract-content --limit 10

# Extract only faith category notes
python extract_instagram.py extract-content --category faith

# Preview extraction without saving
python extract_instagram.py extract-content --dry-run
```

**What it does:**
- Extracts content from Mac Notes
- Analyzes for Instagram URLs and metadata
- Categorizes content automatically
- Saves results to JSON file
- Shows detailed statistics

### 3. manual-review

Export items that need manual resolution to a CSV file.

```bash
python extract_instagram.py manual-review export [--verbose]
```

**What it does:**
- Identifies notes that have Instagram-related content but no direct URLs
- Generates a CSV file with search suggestions
- Creates instruction files for manual review
- Provides estimated time for completion

**Output files:**
- `manual_review_YYYYMMDD_HHMMSS.csv`: Main CSV file for manual review
- `manual_review_instructions.txt`: Detailed instructions
- `quick_reference.txt`: Quick reference card

**Example workflow:**
1. Run `python extract_instagram.py manual-review export`
2. Open the CSV file in Excel or Google Sheets
3. Use the search suggestions to find Instagram URLs
4. Fill in the `resolved_url` and `status` columns
5. Import back with `python extract_instagram.py import-manual <csv_file>`

### 4. import-manual

Import manually resolved URLs from a completed CSV file.

```bash
python extract_instagram.py import-manual <csv_file> [--verbose]
```

**What it does:**
- Imports completed manual review CSV
- Validates resolved URLs
- Performs quality control checks
- Merges with direct URL notes
- Generates quality report

**Example:**
```bash
python extract_instagram.py import-manual extracted_content/manual_review_20241201_143022.csv
```

### 5. download

Download Instagram content from URLs.

```bash
python extract_instagram.py download [options]
```

**Options:**
- `--limit N`: Process only first N items
- `--category [category]`: Filter by specific category
- `--dry-run`: Preview operations without execution
- `--verbose`: Detailed logging output
- `--output-dir [path]`: Custom output directory

**Examples:**
```bash
# Download all content
python extract_instagram.py download

# Download first 5 items for testing
python extract_instagram.py download --limit 5

# Preview download without actually downloading
python extract_instagram.py download --dry-run

# Download only faith category
python extract_instagram.py download --category faith
```

**What it does:**
- Downloads Instagram images and videos
- Organizes content by category
- Generates thumbnails for videos
- Creates Mingus-compatible CSV
- Provides detailed progress reporting

### 6. full-process

Run the complete pipeline with interactive prompts.

```bash
python extract_instagram.py full-process [options]
```

**Options:**
- `--interactive`: Interactive mode with prompts
- `--limit N`: Process only first N items
- `--category [category]`: Filter by specific category
- `--verbose`: Detailed logging output
- `--output-dir [path]`: Custom output directory

**What it does:**
1. Validates MINGUS folder
2. Extracts Instagram content
3. Checks if manual review is needed
4. Downloads Instagram content
5. Generates final reports

## Common Workflows

### Basic Workflow (All Direct URLs)

```bash
# 1. Validate setup
python extract_instagram.py validate-folder

# 2. Extract content
python extract_instagram.py extract-content

# 3. Download content
python extract_instagram.py download
```

### Workflow with Manual Review

```bash
# 1. Extract content
python extract_instagram.py extract-content

# 2. Export manual review
python extract_instagram.py manual-review export

# 3. [Complete manual review in Excel/Google Sheets]

# 4. Import resolved URLs
python extract_instagram.py import-manual results.csv

# 5. Download content
python extract_instagram.py download
```

### Testing Workflow

```bash
# 1. Test with limited data
python extract_instagram.py extract-content --limit 5

# 2. Preview download
python extract_instagram.py download --limit 3 --dry-run

# 3. Actual download
python extract_instagram.py download --limit 3
```

### Category-Specific Workflow

```bash
# Extract and download only faith category
python extract_instagram.py extract-content --category faith
python extract_instagram.py download --category faith
```

## Command Options

### Global Options

- `--verbose`: Enable detailed logging output
- `--help`: Show help for the command

### Filtering Options

- `--limit N`: Process only first N items (useful for testing)
- `--category [category]`: Filter by specific category
- `--dry-run`: Preview operations without execution

### Output Options

- `--output-dir [path]`: Custom output directory

## Output Structure

```
output/
├── images/
│   ├── faith/
│   ├── work_life/
│   ├── friendships/
│   ├── children/
│   ├── relationships/
│   └── going_out/
├── videos/
│   ├── faith/
│   ├── work_life/
│   ├── friendships/
│   ├── children/
│   ├── relationships/
│   └── going_out/
└── metadata/
    ├── download_report.json
    ├── mingus_upload.csv
    └── quality_report.txt
```

## Troubleshooting

### Common Issues

1. **"MINGUS folder not found"**
   - Ensure you have a folder named "MINGUS" in Mac Notes
   - Check that the Notes app is not running

2. **"No download tools available"**
   - Install yt-dlp: `pip install yt-dlp`
   - Install gallery-dl: `pip install gallery-dl`
   - Install ffmpeg: `brew install ffmpeg`

3. **"Permission denied"**
   - Grant Terminal full disk access in System Preferences
   - Ensure you have permission to access the Notes database

4. **"No content found"**
   - Check that your MINGUS folder has notes with Instagram content
   - Try running with `--verbose` for more details

### Getting Help

- Run any command with `--help` for detailed help
- Check the log file `instagram_extractor.log` for detailed error information
- Use `--verbose` flag for detailed logging

## Integration with Mingus

The system generates a `mingus_upload.csv` file in the metadata directory that can be imported into Mingus. This CSV includes:

- Filename and file path
- Category and content type
- Caption and alt text
- Creator credit and permission status
- Notes and metadata
- Download timestamp

## Safety Features

- **Confirmation prompts**: For destructive operations
- **Dry-run mode**: Preview operations before execution
- **Backup creation**: Before overwriting files
- **Resume capability**: For interrupted operations
- **Clear logging**: All activities are logged

## Performance Tips

- Use `--limit` for testing with small datasets
- Use `--category` to process specific categories
- Use `--dry-run` to preview operations
- Monitor disk space for large downloads
- Use `--verbose` for detailed progress information
