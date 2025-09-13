"""
Configuration settings for Instagram content extraction from Mac Notes.
"""

import os
from pathlib import Path

# Database configuration
NOTES_DB_PATH = os.path.expanduser("~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite")

# Target folder configuration
TARGET_FOLDER_NAME = "MINGUS"

# Output configuration
OUTPUT_DIR = Path("extracted_content")
OUTPUT_DIR.mkdir(exist_ok=True)

# Instagram URL patterns
INSTAGRAM_URL_PATTERNS = [
    r"https?://(?:www\.)?instagram\.com/p/[A-Za-z0-9_-]+/?",
    r"https?://(?:www\.)?instagram\.com/reel/[A-Za-z0-9_-]+/?",
    r"https?://(?:www\.)?instagram\.com/tv/[A-Za-z0-9_-]+/?",
    r"https?://(?:www\.)?instagram\.com/stories/[A-Za-z0-9_.-]+/[0-9]+/?",
]

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Database query timeout (seconds)
DB_QUERY_TIMEOUT = 30

# Instagram Downloader Configuration
DOWNLOAD_OUTPUT_DIR = Path("output")
DOWNLOAD_DELAY = 2.0  # Seconds between downloads for rate limiting
DOWNLOAD_TIMEOUT = 300  # 5 minutes timeout per download
MAX_RETRIES = 3  # Maximum retry attempts for failed downloads

# Content categories for organization
CONTENT_CATEGORIES = [
    'faith',
    'work_life', 
    'friendships',
    'children',
    'relationships',
    'going_out'
]

# Supported file formats
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.webm', '.mov', '.avi']

# Quality settings
MAX_VIDEO_HEIGHT = 1080  # Maximum video height for reasonable file sizes
THUMBNAIL_SIZE = (320, 240)  # Thumbnail dimensions
