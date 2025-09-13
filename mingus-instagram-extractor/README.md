# Instagram Content Extractor for Mingus

A comprehensive system for extracting Instagram content from Mac Notes and downloading it for use with the Mingus application. This tool provides both automated extraction and manual review capabilities to ensure complete Instagram content capture.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Check if everything is set up
python extract_instagram.py validate-folder

# 3. Run the complete pipeline
python extract_instagram.py full-process
```

## 📋 Features

### Core Functionality
- **Mac Notes Integration**: Direct access to Mac Notes database
- **Instagram URL Detection**: Automatic detection of Instagram links and metadata
- **Content Categorization**: Automatic categorization by content type (faith, work_life, friendships, etc.)
- **Manual Review System**: CSV-based workflow for resolving incomplete URLs
- **Instagram Download**: Download images and videos with proper organization
- **Mingus Integration**: Generate CSV files compatible with Mingus database

### Command-Line Interface
- **Comprehensive CLI**: Full command-line interface with subcommands
- **Colored Output**: Beautiful terminal output with colors and emojis
- **Progress Tracking**: Real-time progress bars and status updates
- **Interactive Prompts**: User-friendly confirmation and input prompts
- **Dry-run Mode**: Preview operations before execution
- **Filtering Options**: Process specific categories or limited datasets

### Safety & Reliability
- **Validation**: Comprehensive validation of MINGUS folder and dependencies
- **Error Handling**: Detailed error messages with suggested solutions
- **Backup Creation**: Automatic backup before destructive operations
- **Resume Capability**: Continue interrupted operations
- **Quality Control**: Validation of downloaded content and resolved URLs

## 🛠️ Installation

### Prerequisites
- macOS (for Mac Notes access)
- Python 3.8+
- Terminal access

### Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install download tools
pip install yt-dlp gallery-dl
brew install ffmpeg
```

### Setup
1. Create a folder named "MINGUS" in Mac Notes
2. Add some Instagram content to test with
3. Ensure the Notes app is not running during extraction

## 📖 Usage

### Basic Workflow

```bash
# 1. Validate setup
python extract_instagram.py validate-folder

# 2. Extract content
python extract_instagram.py extract-content

# 3. Download content
python extract_instagram.py download
```

### Advanced Workflow with Manual Review

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
# Test with limited data
python extract_instagram.py extract-content --limit 10
python extract_instagram.py download --limit 5 --dry-run
```

## 📚 Commands

### `validate-folder`
Check MINGUS folder exists and show statistics.

```bash
python extract_instagram.py validate-folder [--verbose]
```

### `extract-content`
Extract Instagram content from MINGUS folder.

```bash
python extract_instagram.py extract-content [--limit N] [--category CATEGORY] [--dry-run] [--verbose]
```

### `manual-review`
Export items needing manual resolution.

```bash
python extract_instagram.py manual-review export [--verbose]
```

### `import-manual`
Import manually resolved URLs.

```bash
python extract_instagram.py import-manual <csv_file> [--verbose]
```

### `download`
Download Instagram content from URLs.

```bash
python extract_instagram.py download [--limit N] [--category CATEGORY] [--dry-run] [--verbose] [--output-dir PATH]
```

### `full-process`
Complete pipeline with user prompts.

```bash
python extract_instagram.py full-process [--interactive] [--limit N] [--category CATEGORY] [--verbose] [--output-dir PATH]
```

## 📁 Output Structure

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

## 🔧 Configuration

### Content Categories
The system automatically categorizes content into these categories:
- `faith`: Religious and spiritual content
- `work_life`: Professional and career content
- `friendships`: Social connections and friendships
- `children`: Family and children-related content
- `relationships`: Romantic and personal relationships
- `going_out`: Social activities and events

### Instagram URL Patterns
The system detects these Instagram URL patterns:
- Posts: `https://instagram.com/p/[ID]/`
- Reels: `https://instagram.com/reel/[ID]/`
- TV: `https://instagram.com/tv/[ID]/`
- Stories: `https://instagram.com/stories/[USER]/[ID]/`

## 🧪 Testing

Run the test suite to verify functionality:

```bash
python test_cli.py
```

## 📊 Statistics and Reporting

The system provides comprehensive statistics:

### Extraction Statistics
- Total notes processed
- Notes with content
- Rich text notes
- Binary decoding success rate
- Instagram content detection

### Download Statistics
- Successful downloads
- Failed downloads
- Skipped downloads
- Total file size
- Category distribution

### Quality Metrics
- URL validation results
- Duplicate detection
- Content validation
- Quality score

## 🚨 Troubleshooting

### Common Issues

1. **"MINGUS folder not found"**
   - Create a folder named "MINGUS" in Mac Notes
   - Ensure the Notes app is not running

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

## 🔒 Security and Privacy

- **Local Processing**: All data processing happens locally on your machine
- **No External Services**: No data is sent to external services
- **Secure Access**: Uses standard macOS database access methods
- **Data Control**: You maintain full control over your data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built for the Mingus application
- Uses yt-dlp and gallery-dl for Instagram downloads
- Integrates with Mac Notes database
- Designed for content creators and personal archiving

## 📞 Support

For support and questions:
1. Check the troubleshooting section
2. Review the CLI usage guide
3. Check the log files for error details
4. Open an issue on GitHub

---

**Note**: This tool is designed to work with Mac Notes and requires macOS. Ensure you have proper permissions to access the Notes database and that you're using the tool in compliance with Instagram's terms of service.