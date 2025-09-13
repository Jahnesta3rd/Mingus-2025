#!/usr/bin/env python3
"""
Content Processing Utilities

Handles image and video processing, thumbnail generation, and content optimization.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageOps
import json
from datetime import datetime

# Optional imports for enhanced functionality
try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False
    ffmpeg = None

from config import THUMBNAIL_SIZE, SUPPORTED_IMAGE_FORMATS, SUPPORTED_VIDEO_FORMATS


class ContentProcessor:
    """Handles content processing operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_thumbnail(self, video_path: str, output_path: str, 
                         timestamp: float = 1.0) -> bool:
        """Generate thumbnail for video content."""
        if not FFMPEG_AVAILABLE:
            self.logger.warning("ffmpeg not available, skipping thumbnail generation")
            return False
            
        try:
            # Use ffmpeg to extract thumbnail
            (
                ffmpeg
                .input(video_path, ss=timestamp)
                .output(output_path, vframes=1, format='image2', 
                       vf=f'scale={THUMBNAIL_SIZE[0]}:{THUMBNAIL_SIZE[1]}')
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Verify thumbnail was created
            if Path(output_path).exists():
                self.logger.info(f"Generated thumbnail: {output_path}")
                return True
            else:
                self.logger.warning(f"Thumbnail generation failed: {output_path}")
                return False
                
        except Exception as e:
            self.logger.warning(f"Could not generate thumbnail: {e}")
            return False
    
    def optimize_image(self, image_path: str, output_path: str, 
                      max_size: Tuple[int, int] = (1920, 1080),
                      quality: int = 85) -> bool:
        """Optimize image for web use."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save optimized image
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
                
            self.logger.info(f"Optimized image: {output_path}")
            return True
            
        except Exception as e:
            self.logger.warning(f"Could not optimize image: {e}")
            return False
    
    def get_video_info(self, video_path: str) -> dict:
        """Get video information using ffprobe."""
        try:
            probe = ffmpeg.probe(video_path)
            video_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'video'), 
                None
            )
            
            if video_stream:
                return {
                    'duration': float(video_stream.get('duration', 0)),
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'codec': video_stream.get('codec_name', 'unknown'),
                    'bit_rate': int(video_stream.get('bit_rate', 0))
                }
            else:
                return {}
                
        except Exception as e:
            self.logger.warning(f"Could not get video info: {e}")
            return {}
    
    def get_image_info(self, image_path: str) -> dict:
        """Get image information."""
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.size[0],
                    'height': img.size[1],
                    'mode': img.mode,
                    'format': img.format,
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                }
        except Exception as e:
            self.logger.warning(f"Could not get image info: {e}")
            return {}
    
    def validate_content(self, file_path: str) -> dict:
        """Validate content file and return validation results."""
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            return {'valid': False, 'error': 'File does not exist'}
        
        if file_path_obj.stat().st_size == 0:
            return {'valid': False, 'error': 'File is empty'}
        
        extension = file_path_obj.suffix.lower()
        
        if extension in SUPPORTED_IMAGE_FORMATS:
            return self._validate_image(file_path)
        elif extension in SUPPORTED_VIDEO_FORMATS:
            return self._validate_video(file_path)
        else:
            return {'valid': False, 'error': f'Unsupported file format: {extension}'}
    
    def _validate_image(self, image_path: str) -> dict:
        """Validate image file."""
        try:
            with Image.open(image_path) as img:
                img.verify()
            
            # Get image info
            info = self.get_image_info(image_path)
            
            return {
                'valid': True,
                'type': 'image',
                'info': info
            }
        except Exception as e:
            return {
                'valid': False,
                'error': f'Image validation failed: {str(e)}',
                'type': 'image'
            }
    
    def _validate_video(self, video_path: str) -> dict:
        """Validate video file."""
        try:
            # Try to get video info
            info = self.get_video_info(video_path)
            
            if info:
                return {
                    'valid': True,
                    'type': 'video',
                    'info': info
                }
            else:
                return {
                    'valid': False,
                    'error': 'Could not read video information',
                    'type': 'video'
                }
        except Exception as e:
            return {
                'valid': False,
                'error': f'Video validation failed: {str(e)}',
                'type': 'video'
            }
    
    def create_web_optimized_version(self, original_path: str, 
                                   output_path: str) -> bool:
        """Create web-optimized version of content."""
        try:
            file_path_obj = Path(original_path)
            extension = file_path_obj.suffix.lower()
            
            if extension in SUPPORTED_IMAGE_FORMATS:
                return self.optimize_image(original_path, output_path)
            elif extension in SUPPORTED_VIDEO_FORMATS:
                # For videos, we could add compression here if needed
                # For now, just copy the file
                import shutil
                shutil.copy2(original_path, output_path)
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.warning(f"Could not create web-optimized version: {e}")
            return False
    
    def generate_content_metadata(self, file_path: str, 
                                original_url: str = "",
                                category: str = "",
                                caption: str = "") -> dict:
        """Generate comprehensive metadata for content."""
        file_path_obj = Path(file_path)
        
        # Basic file info
        stat = file_path_obj.stat()
        metadata = {
            'filename': file_path_obj.name,
            'file_path': str(file_path_obj),
            'file_size': stat.st_size,
            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'original_url': original_url,
            'category': category,
            'caption': caption
        }
        
        # Content-specific info
        validation = self.validate_content(file_path)
        if validation['valid']:
            metadata.update({
                'content_type': validation['type'],
                'content_info': validation.get('info', {})
            })
        else:
            metadata.update({
                'content_type': 'unknown',
                'validation_error': validation.get('error', 'Unknown error')
            })
        
        return metadata
