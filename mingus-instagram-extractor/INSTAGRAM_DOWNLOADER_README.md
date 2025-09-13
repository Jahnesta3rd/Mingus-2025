# Instagram Content Downloader

A comprehensive tool for downloading Instagram content using `yt-dlp` and `gallery-dl` with proper organization, attribution preservation, and quality assurance.

## Features

### 🔧 Download Tool Integration
- **Primary tool**: `yt-dlp` for high-quality downloads
- **Fallback tool**: `gallery-dl` for additional compatibility
- Automatic tool availability checking with installation guidance
- Support for both images and videos from Instagram

### 📁 Content Organization
- Organized file structure by category and content type
- Categories: `faith`, `work_life`, `friendships`, `children`, `relationships`, `going_out`
- Separate folders for `images` and `videos`
- Unique filename generation to prevent conflicts

### 🎯 Content Processing
- Support for multiple formats (jpg, png, gif, mp4, webm, etc.)
- Automatic thumbnail generation for videos
- Image optimization for web use
- Quality validation and file integrity checking

### 📊 Attribution Preservation
- Maintains original Instagram URLs
- Tracks content creators and account names
- Generates attribution metadata
- Includes download timestamps

### 🎯 Quality Assurance
- Validates downloaded files are valid
- Checks file sizes and formats
- Verifies content matches expected descriptions
- Generates comprehensive success/failure reports

### 🔗 Mingus Integration
- Generates CSV compatible with Mingus database upload
- Format: `filename,category,caption,alt_text,creator_credit,creator_link,permission_status,notes`
- Creates accessibility alt-text descriptions
- Organizes files for web application serving

### ⚡ Error Handling
- Network connectivity issues
- Instagram rate limiting (2-second delays)
- Private or deleted content handling
- Tool execution failures
- Disk space limitations
- Comprehensive retry logic

### 📈 Progress Reporting
- Real-time download progress
- Success/failure statistics
- Category distribution tracking
- Final summary with next steps
- Comprehensive logging throughout

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install download tools**:
   ```bash
   # Install yt-dlp (primary tool)
   pip install yt-dlp
   
   # Install gallery-dl (fallback tool)
   pip install gallery-dl
   
   # Install ffmpeg for video processing
   brew install ffmpeg  # macOS
   # or
   sudo apt install ffmpeg  # Ubuntu/Debian
   ```

3. **Verify installation**:
   ```bash
   python instagram_downloader.py --check-tools
   ```

## Usage

### Basic Usage

```bash
python instagram_downloader.py <json_file> [output_dir]
```

- `json_file`: Path to JSON file containing URLs and metadata
- `output_dir`: Output directory (default: "output")

### Input JSON Format

Create a JSON file with the following structure:

```json
[
  {
    "url": "https://www.instagram.com/p/ABC123DEF456/",
    "category": "faith",
    "caption": "Beautiful sunset from my morning walk #grateful #blessed",
    "alt_text": "Instagram post showing a beautiful sunset during a morning walk",
    "creator_credit": "@nature_lover",
    "creator_link": "https://www.instagram.com/nature_lover/",
    "permission_status": "granted",
    "notes": "Personal photo from morning meditation walk",
    "original_note_id": "note_001",
    "content_type": "image",
    "post_id": "ABC123DEF456"
  }
]
```

### Example Usage

```bash
# Download content from sample file
python instagram_downloader.py sample_urls.json

# Download to custom output directory
python instagram_downloader.py sample_urls.json my_instagram_content
```

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
    ├── detailed_report.json
    └── mingus_upload.csv
```

## Configuration

Edit `config.py` to customize:

- **Download settings**: Timeouts, delays, retry counts
- **Quality settings**: Maximum video height, thumbnail sizes
- **Categories**: Add or modify content categories
- **File formats**: Supported image and video formats

## Rate Limiting

The downloader implements Instagram-friendly rate limiting:
- 2-second delays between downloads
- Configurable sleep intervals
- Respects Instagram's terms of service

## Error Handling

The tool handles various error scenarios:
- **Network issues**: Automatic retry with exponential backoff
- **Rate limiting**: Increased delays and retry attempts
- **Private content**: Graceful failure with detailed error messages
- **Tool failures**: Automatic fallback to alternative tools
- **Disk space**: Pre-download space checking

## Progress Reporting

Real-time progress updates include:
- Current item being processed
- Success/failure counts
- Download speed and estimated time remaining
- Category and content type distribution
- File size statistics

## Logging

Comprehensive logging to both console and file:
- **Console**: Real-time progress and important updates
- **File**: Detailed debug information and error traces
- **Log levels**: Configurable verbosity

## Mingus Integration

The tool generates a CSV file compatible with Mingus database upload:

| Column | Description |
|--------|-------------|
| filename | Downloaded file name |
| category | Content category |
| caption | Original Instagram caption |
| alt_text | Accessibility description |
| creator_credit | Instagram username |
| creator_link | Instagram profile URL |
| permission_status | Permission status |
| notes | Additional notes |
| file_path | Full file path |
| file_size | File size in bytes |
| content_type | image or video |
| download_timestamp | When downloaded |
| original_url | Original Instagram URL |

## Troubleshooting

### Common Issues

1. **Tool not found**:
   ```bash
   # Check if tools are installed
   yt-dlp --version
   gallery-dl --version
   ffmpeg -version
   ```

2. **Permission denied**:
   - Ensure output directory is writable
   - Check file permissions

3. **Download failures**:
   - Verify Instagram URLs are accessible
   - Check network connectivity
   - Review log files for detailed error messages

4. **Rate limiting**:
   - Increase delays in configuration
   - Reduce concurrent downloads

### Debug Mode

Enable debug logging:
```python
# In config.py
LOG_LEVEL = "DEBUG"
```

## Advanced Usage

### Custom Categories

Add new categories in `config.py`:
```python
CONTENT_CATEGORIES = [
    'faith',
    'work_life',
    'friendships',
    'children',
    'relationships',
    'going_out',
    'your_custom_category'  # Add here
]
```

### Quality Settings

Adjust video quality in `config.py`:
```python
MAX_VIDEO_HEIGHT = 1080  # Maximum video height
THUMBNAIL_SIZE = (320, 240)  # Thumbnail dimensions
```

### Batch Processing

Process multiple JSON files:
```bash
for file in *.json; do
    python instagram_downloader.py "$file" "output_${file%.json}"
done
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Mingus Application suite.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for error details
3. Create an issue with detailed information

---

**Note**: This tool is designed to respect Instagram's terms of service and rate limits. Use responsibly and only download content you have permission to use.
