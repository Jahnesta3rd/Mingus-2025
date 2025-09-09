#!/usr/bin/env python3
"""
Image Storage Configuration for Mingus Meme Splash Page
Handles AWS S3 upload, image optimization, and CDN integration
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from PIL import Image, ImageOps
import io
import hashlib
import logging
from typing import Optional, Tuple
from werkzeug.utils import secure_filename
import mimetypes

logger = logging.getLogger(__name__)

class ImageStorageManager:
    def __init__(self):
        self.s3_client = None
        self.bucket_name = os.environ.get('AWS_S3_BUCKET')
        self.region = os.environ.get('AWS_S3_REGION', 'us-east-1')
        self.cdn_url = os.environ.get('CDN_URL')
        self.enable_optimization = os.environ.get('ENABLE_IMAGE_OPTIMIZATION', 'true').lower() == 'true'
        
        # Initialize S3 client if credentials are available
        if self._has_aws_credentials():
            self._initialize_s3_client()
    
    def _has_aws_credentials(self) -> bool:
        """Check if AWS credentials are available"""
        return all([
            os.environ.get('AWS_ACCESS_KEY_ID'),
            os.environ.get('AWS_SECRET_ACCESS_KEY'),
            self.bucket_name
        ])
    
    def _initialize_s3_client(self):
        """Initialize S3 client"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name=self.region
            )
            logger.info("S3 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def optimize_image(self, image_data: bytes, max_width: int = 800, max_height: int = 600, quality: int = 85) -> bytes:
        """
        Optimize image for web delivery
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary (for JPEG)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if necessary
            if image.width > max_width or image.height > max_height:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Auto-orient based on EXIF data
            image = ImageOps.exif_transpose(image)
            
            # Save optimized image
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return image_data  # Return original if optimization fails
    
    def generate_unique_filename(self, original_filename: str, user_id: Optional[str] = None) -> str:
        """Generate a unique, secure filename"""
        # Get file extension
        _, ext = os.path.splitext(original_filename)
        ext = ext.lower()
        
        # Generate hash for uniqueness
        hash_input = f"{original_filename}_{user_id}_{os.urandom(16).hex()}"
        file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        
        # Create timestamp-based path
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y/%m/%d')
        
        return f"memes/{timestamp}/{file_hash}{ext}"
    
    def upload_to_s3(self, file_data: bytes, filename: str, content_type: str) -> Optional[str]:
        """
        Upload file to S3 and return the URL
        """
        if not self.s3_client:
            logger.warning("S3 client not available, falling back to local storage")
            return None
        
        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=file_data,
                ContentType=content_type,
                ACL='public-read',  # Make publicly accessible
                CacheControl='max-age=31536000'  # Cache for 1 year
            )
            
            # Return URL
            if self.cdn_url:
                return f"{self.cdn_url.rstrip('/')}/{filename}"
            else:
                return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"
                
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {e}")
            return None
    
    def save_locally(self, file_data: bytes, filename: str, upload_folder: str) -> str:
        """
        Save file to local storage
        """
        # Ensure upload directory exists
        os.makedirs(upload_folder, exist_ok=True)
        
        # Create full path
        file_path = os.path.join(upload_folder, filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        return f"/static/uploads/{filename}"
    
    def process_upload(self, file, user_id: Optional[str] = None, upload_folder: str = 'static/uploads') -> dict:
        """
        Process file upload with optimization and storage
        """
        try:
            # Validate file
            if not file or not file.filename:
                return {'success': False, 'error': 'No file provided'}
            
            # Check file type
            if not self._is_allowed_file(file.filename):
                return {'success': False, 'error': 'File type not allowed'}
            
            # Read file data
            file_data = file.read()
            
            # Check file size (5MB limit)
            max_size = int(os.environ.get('MAX_FILE_SIZE', 5242880))
            if len(file_data) > max_size:
                return {'success': False, 'error': 'File too large'}
            
            # Generate unique filename
            unique_filename = self.generate_unique_filename(file.filename, user_id)
            
            # Optimize image if enabled
            if self.enable_optimization and self._is_image_file(file.filename):
                file_data = self.optimize_image(file_data)
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file.filename)
            if not content_type:
                content_type = 'application/octet-stream'
            
            # Try S3 upload first, fallback to local
            url = self.upload_to_s3(file_data, unique_filename, content_type)
            
            if not url:
                # Fallback to local storage
                local_filename = secure_filename(file.filename)
                url = self.save_locally(file_data, local_filename, upload_folder)
            
            return {
                'success': True,
                'url': url,
                'filename': unique_filename,
                'size': len(file_data),
                'content_type': content_type
            }
            
        except Exception as e:
            logger.error(f"File upload processing failed: {e}")
            return {'success': False, 'error': 'Upload processing failed'}
    
    def delete_file(self, filename: str) -> bool:
        """
        Delete file from storage
        """
        try:
            # If it's an S3 URL, extract the key
            if 's3.amazonaws.com' in filename or (self.cdn_url and self.cdn_url in filename):
                if self.s3_client:
                    # Extract S3 key from URL
                    if self.cdn_url and self.cdn_url in filename:
                        key = filename.replace(f"{self.cdn_url.rstrip('/')}/", "")
                    else:
                        key = filename.split(f"{self.bucket_name}.s3.{self.region}.amazonaws.com/")[-1]
                    
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
                    logger.info(f"Deleted S3 file: {key}")
                    return True
            else:
                # Local file deletion
                if filename.startswith('/static/uploads/'):
                    local_path = filename.replace('/static/uploads/', 'static/uploads/')
                    if os.path.exists(local_path):
                        os.remove(local_path)
                        logger.info(f"Deleted local file: {local_path}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return False
    
    def _is_allowed_file(self, filename: str) -> bool:
        """Check if file type is allowed"""
        allowed_extensions = os.environ.get('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,gif,webp').split(',')
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions
    
    def _is_image_file(self, filename: str) -> bool:
        """Check if file is an image"""
        image_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'}
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in image_extensions
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics"""
        stats = {
            's3_available': self.s3_client is not None,
            'bucket_name': self.bucket_name,
            'region': self.region,
            'cdn_url': self.cdn_url,
            'optimization_enabled': self.enable_optimization
        }
        
        if self.s3_client:
            try:
                # Get bucket size (simplified)
                response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix='memes/')
                stats['s3_objects'] = response.get('KeyCount', 0)
            except Exception as e:
                logger.error(f"Failed to get S3 stats: {e}")
                stats['s3_error'] = str(e)
        
        return stats

# Global instance
image_storage = ImageStorageManager()
