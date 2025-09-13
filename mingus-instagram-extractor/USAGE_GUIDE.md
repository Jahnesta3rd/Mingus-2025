# Instagram Content Downloader - Complete Usage Guide

This guide provides step-by-step instructions for using the Instagram Content Downloader with your existing Mingus Application.

## 🚀 Quick Start

### 1. Installation

```bash
# Install all dependencies
python install_dependencies.py

# Verify installation
python download_instagram.py --check-tools
```

### 2. Basic Usage

```bash
# Create sample data
python download_instagram.py --create-sample

# Download content
python download_instagram.py sample_urls.json
```

### 3. Complete Workflow

```bash
# Run the complete workflow (extract + download)
python complete_workflow.py
```

## 📋 Detailed Workflow

### Step 1: Extract Instagram URLs from Mac Notes

The existing `extract_instagram.py` script will:
- Access your Mac Notes database
- Find the MINGUS folder
- Extract Instagram URLs and metadata
- Generate JSON files with all found content

```bash
python extract_instagram.py
```

**Output**: `extracted_content/` directory with JSON files containing Instagram URLs and metadata.

### Step 2: Manual Review (if needed)

If some Instagram URLs need manual resolution:

1. The system will generate a CSV file for manual review
2. Open the CSV in Excel or Google Sheets
3. Use the provided search suggestions to find Instagram URLs
4. Fill in the `resolved_url` column
5. Save and import back into the system

### Step 3: Download Instagram Content

```bash
# Using the complete workflow
python complete_workflow.py

# Or manually
python download_instagram.py extracted_content/latest_file.json
```

**Output**: `output/` directory with organized content:
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
    ├── detailed_report.json
    └── mingus_upload.csv
```

## 🔧 Advanced Usage

### Custom Configuration

Edit `config.py` to customize:

```python
# Download settings
DOWNLOAD_DELAY = 2.0  # Seconds between downloads
DOWNLOAD_TIMEOUT = 300  # 5 minutes timeout
MAX_RETRIES = 3  # Retry attempts

# Quality settings
MAX_VIDEO_HEIGHT = 1080  # Maximum video height
THUMBNAIL_SIZE = (320, 240)  # Thumbnail dimensions

# Categories
CONTENT_CATEGORIES = [
    'faith',
    'work_life',
    'friendships',
    'children',
    'relationships',
    'going_out'
]
```

### Batch Processing

Process multiple JSON files:

```bash
for file in extracted_content/*.json; do
    python download_instagram.py "$file" "output_${file##*/}"
done
```

### Custom Output Directory

```bash
python download_instagram.py sample_urls.json my_instagram_content
```

## 📊 Output Files

### 1. Downloaded Content

- **Images**: Organized by category in `images/` folder
- **Videos**: Organized by category in `videos/` folder
- **Thumbnails**: Generated for all videos
- **Metadata**: Preserved from original Instagram posts

### 2. Mingus Integration Files

#### `mingus_upload.csv`
CSV file ready for Mingus database upload with columns:
- `filename`: Downloaded file name
- `category`: Content category
- `caption`: Original Instagram caption
- `alt_text`: Accessibility description
- `creator_credit`: Instagram username
- `creator_link`: Instagram profile URL
- `permission_status`: Permission status
- `notes`: Additional notes
- `file_path`: Full file path
- `file_size`: File size in bytes
- `content_type`: image or video
- `download_timestamp`: When downloaded
- `original_url`: Original Instagram URL

#### `download_report.json`
Detailed download statistics and results.

#### `detailed_report.json`
Comprehensive report with session info, statistics, and results.

## 🛠️ Troubleshooting

### Common Issues

#### 1. Tools Not Found
```bash
# Check tool availability
python download_instagram.py --check-tools

# Install missing tools
python install_dependencies.py
```

#### 2. Permission Denied
```bash
# Check file permissions
ls -la output/
chmod -R 755 output/
```

#### 3. Download Failures
- Check Instagram URLs are accessible
- Verify network connectivity
- Review log files for detailed errors
- Try increasing delays in configuration

#### 4. Rate Limiting
- Increase `DOWNLOAD_DELAY` in config.py
- Reduce concurrent downloads
- Check Instagram's current rate limits

### Debug Mode

Enable detailed logging:

```python
# In config.py
LOG_LEVEL = "DEBUG"
```

### Log Files

- `instagram_downloader.log`: Main downloader logs
- `complete_workflow.log`: Complete workflow logs
- `instagram_extractor.log`: Extraction logs

## 🔄 Integration with Existing Workflow

### 1. With Mac Notes Extraction

The downloader integrates seamlessly with your existing `extract_instagram.py`:

```bash
# Complete workflow
python complete_workflow.py

# Or step by step
python extract_instagram.py
python download_instagram.py extracted_content/latest_file.json
```

### 2. With Manual Review

If manual review is needed:

1. Run extraction: `python extract_instagram.py`
2. Complete manual review CSV
3. Run downloader: `python download_instagram.py resolved_urls.json`

### 3. With Mingus Database

The generated CSV can be directly imported into your Mingus database:

```sql
-- Example SQL import (adjust for your database schema)
LOAD DATA INFILE 'output/metadata/mingus_upload.csv'
INTO TABLE instagram_content
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
```

## 📈 Performance Tips

### 1. Optimize Download Speed
- Use SSD storage for faster I/O
- Ensure stable internet connection
- Adjust `DOWNLOAD_DELAY` based on your connection

### 2. Manage Storage
- Monitor disk space before large downloads
- Use `--output-dir` to specify storage location
- Consider archiving old downloads

### 3. Handle Large Datasets
- Process in batches for very large datasets
- Use `--skip-extraction` for repeated downloads
- Monitor memory usage during processing

## 🔒 Security and Privacy

### 1. Data Protection
- All downloads are stored locally
- No data is sent to external servers
- Original URLs are preserved for attribution

### 2. Instagram Compliance
- Respects Instagram's rate limits
- Uses official APIs through yt-dlp/gallery-dl
- Follows Instagram's terms of service

### 3. Content Rights
- Only download content you have permission to use
- Maintain attribution information
- Respect creator rights and privacy

## 📞 Support

### Getting Help

1. **Check logs**: Review log files for error details
2. **Verify tools**: Run `--check-tools` to ensure everything is installed
3. **Test with sample**: Use `--create-sample` to test with sample data
4. **Review configuration**: Check `config.py` for proper settings

### Common Commands

```bash
# Check everything is working
python download_instagram.py --check-tools

# Create test data
python download_instagram.py --create-sample

# Run complete workflow
python complete_workflow.py

# Get help
python download_instagram.py --help
python complete_workflow.py --help
```

---

**Note**: This tool is designed to work with your existing Mingus Application workflow. It respects Instagram's terms of service and implements proper rate limiting to ensure responsible usage.
