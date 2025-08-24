"""
Image Storage Service
====================
Service for handling image upload, storage, optimization, and CDN integration
for the meme splash page feature.
"""

import os
import io
import uuid
import hashlib
from typing import Optional, Tuple, Dict, Any, BinaryIO
from datetime import datetime, timedelta
import logging
from PIL import Image, ImageOps
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import requests
from urllib.parse import urlparse, urljoin
import mimetypes

logger = logging.getLogger(__name__)

class ImageStorageService:
    """Service for managing image storage and optimization"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the image storage service
        
        Args:
            config: Configuration dictionary containing AWS and image settings
        """
        self.config = config
        self.s3_client = None
        self.bucket_name = config.get('AWS_S3_BUCKET', 'mingus-meme-images')
        self.region = config.get('AWS_REGION', 'us-east-1')
        self.cloudfront_distribution = config.get('AWS_CLOUDFRONT_DISTRIBUTION_ID')
        
        # Image processing settings
        self.max_size_mb = config.get('IMAGE_MAX_SIZE_MB', 10)
        self.allowed_extensions = config.get('IMAGE_ALLOWED_EXTENSIONS', 'jpg,jpeg,png,gif,webp').split(',')
        self.optimization_quality = config.get('IMAGE_OPTIMIZATION_QUALITY', 85)
        self.thumbnail_size = tuple(map(int, config.get('IMAGE_THUMBNAIL_SIZE', '300x300').split('x')))
        self.preview_size = tuple(map(int, config.get('IMAGE_PREVIEW_SIZE', '800x600').split('x')))
        
        # Initialize S3 client if credentials are provided
        self._initialize_s3_client()
    
    def _initialize_s3_client(self) -> None:
        """Initialize AWS S3 client"""
        try:
            aws_access_key = self.config.get('AWS_ACCESS_KEY_ID')
            aws_secret_key = self.config.get('AWS_SECRET_ACCESS_KEY')
            
            if aws_access_key and aws_secret_key:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=self.region
                )
                logger.info("S3 client initialized successfully")
            else:
                logger.warning("AWS credentials not provided, S3 functionality disabled")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def validate_image(self, file: BinaryIO, filename: str) -> Tuple[bool, str]:
        """
        Validate uploaded image file
        
        Args:
            file: File object to validate
            filename: Original filename
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file extension
            file_extension = filename.lower().split('.')[-1]
            if file_extension not in self.allowed_extensions:
                return False, f"File type {file_extension} not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            
            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            max_size_bytes = self.max_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                return False, f"File size {file_size / (1024*1024):.1f}MB exceeds maximum {self.max_size_mb}MB"
            
            # Validate image format
            try:
                with Image.open(file) as img:
                    img.verify()
                file.seek(0)  # Reset after verification
            except Exception as e:
                return False, f"Invalid image format: {str(e)}"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating image: {e}")
            return False, f"Validation error: {str(e)}"
    
    def optimize_image(self, image: Image.Image, format: str = 'JPEG') -> Image.Image:
        """
        Optimize image for web delivery
        
        Args:
            image: PIL Image object
            format: Output format (JPEG, PNG, WEBP)
            
        Returns:
            Optimized PIL Image
        """
        try:
            # Convert to RGB if saving as JPEG
            if format.upper() == 'JPEG':
                if image.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparent images
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
            
            # Auto-orient based on EXIF data
            image = ImageOps.exif_transpose(image)
            
            return image
            
        except Exception as e:
            logger.error(f"Error optimizing image: {e}")
            return image
    
    def create_thumbnail(self, image: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """
        Create thumbnail version of image
        
        Args:
            image: PIL Image object
            size: Target size (width, height)
            
        Returns:
            Thumbnail PIL Image
        """
        try:
            # Calculate aspect ratio preserving resize
            image.thumbnail(size, Image.Resampling.LANCZOS)
            return image
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return image
    
    def upload_to_s3(self, file_data: bytes, key: str, content_type: str, 
                    metadata: Optional[Dict[str, str]] = None) -> bool:
        """
        Upload file to S3
        
        Args:
            file_data: File data as bytes
            key: S3 object key
            content_type: MIME type
            metadata: Optional metadata dictionary
            
        Returns:
            True if upload successful, False otherwise
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return False
        
        try:
            extra_args = {
                'ContentType': content_type,
                'ACL': 'public-read',
                'CacheControl': 'public, max-age=31536000'  # 1 year cache
            }
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_data,
                **extra_args
            )
            
            logger.info(f"Successfully uploaded {key} to S3")
            return True
            
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"Failed to upload to S3: {e}")
            return False
    
    def get_s3_url(self, key: str) -> str:
        """
        Get public URL for S3 object
        
        Args:
            key: S3 object key
            
        Returns:
            Public URL
        """
        if self.cloudfront_distribution:
            # Use CloudFront URL for better performance
            return f"https://{self.cloudfront_distribution}.cloudfront.net/{key}"
        else:
            # Use S3 public URL
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
    
    def process_and_upload_image(self, file: BinaryIO, filename: str, 
                               category: str, meme_id: str) -> Dict[str, Any]:
        """
        Process and upload image with multiple sizes
        
        Args:
            file: File object
            filename: Original filename
            category: Meme category
            meme_id: Unique meme ID
            
        Returns:
            Dictionary with image URLs and metadata
        """
        try:
            # Validate image
            is_valid, error_msg = self.validate_image(file, filename)
            if not is_valid:
                return {'success': False, 'error': error_msg}
            
            # Generate unique filename
            file_extension = filename.lower().split('.')[-1]
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            
            # Determine format and content type
            if file_extension in ['jpg', 'jpeg']:
                format = 'JPEG'
                content_type = 'image/jpeg'
            elif file_extension == 'png':
                format = 'PNG'
                content_type = 'image/png'
            elif file_extension == 'webp':
                format = 'WEBP'
                content_type = 'image/webp'
            else:
                format = 'JPEG'
                content_type = 'image/jpeg'
            
            # Open and process original image
            with Image.open(file) as original_image:
                # Get original dimensions
                original_width, original_height = original_image.size
                
                # Optimize original image
                optimized_image = self.optimize_image(original_image, format)
                
                # Create thumbnail
                thumbnail_image = optimized_image.copy()
                thumbnail_image = self.create_thumbnail(thumbnail_image, self.thumbnail_size)
                
                # Create preview
                preview_image = optimized_image.copy()
                preview_image = self.create_thumbnail(preview_image, self.preview_size)
                
                # Save images to bytes
                original_bytes = io.BytesIO()
                thumbnail_bytes = io.BytesIO()
                preview_bytes = io.BytesIO()
                
                optimized_image.save(original_bytes, format=format, quality=self.optimization_quality, optimize=True)
                thumbnail_image.save(thumbnail_bytes, format=format, quality=self.optimization_quality, optimize=True)
                preview_image.save(preview_bytes, format=format, quality=self.optimization_quality, optimize=True)
                
                # Generate S3 keys
                base_key = f"memes/{category}/{timestamp}_{unique_id}"
                original_key = f"{base_key}_original.{file_extension}"
                thumbnail_key = f"{base_key}_thumbnail.{file_extension}"
                preview_key = f"{base_key}_preview.{file_extension}"
                
                # Upload to S3
                metadata = {
                    'meme_id': meme_id,
                    'category': category,
                    'original_filename': filename,
                    'uploaded_at': datetime.utcnow().isoformat()
                }
                
                upload_success = True
                upload_success &= self.upload_to_s3(
                    original_bytes.getvalue(), original_key, content_type, metadata
                )
                upload_success &= self.upload_to_s3(
                    thumbnail_bytes.getvalue(), thumbnail_key, content_type, metadata
                )
                upload_success &= self.upload_to_s3(
                    preview_bytes.getvalue(), preview_key, content_type, metadata
                )
                
                if not upload_success:
                    return {'success': False, 'error': 'Failed to upload images to S3'}
                
                # Return URLs and metadata
                return {
                    'success': True,
                    'image_url': self.get_s3_url(original_key),
                    'thumbnail_url': self.get_s3_url(thumbnail_key),
                    'preview_url': self.get_s3_url(preview_key),
                    'metadata': {
                        'original_width': original_width,
                        'original_height': original_height,
                        'thumbnail_width': thumbnail_image.size[0],
                        'thumbnail_height': thumbnail_image.size[1],
                        'preview_width': preview_image.size[0],
                        'preview_height': preview_image.size[1],
                        'file_size_bytes': len(original_bytes.getvalue()),
                        'format': format.lower(),
                        'content_type': content_type
                    }
                }
                
        except Exception as e:
            logger.error(f"Error processing and uploading image: {e}")
            return {'success': False, 'error': f'Processing error: {str(e)}'}
    
    def delete_image(self, image_url: str) -> bool:
        """
        Delete image from S3
        
        Args:
            image_url: Full image URL
            
        Returns:
            True if deletion successful, False otherwise
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return False
        
        try:
            # Extract key from URL
            parsed_url = urlparse(image_url)
            key = parsed_url.path.lstrip('/')
            
            # Delete object
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully deleted {key} from S3")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete from S3: {e}")
            return False
    
    def get_image_info(self, image_url: str) -> Optional[Dict[str, Any]]:
        """
        Get image information from S3
        
        Args:
            image_url: Full image URL
            
        Returns:
            Image metadata dictionary or None
        """
        if not self.s3_client:
            return None
        
        try:
            # Extract key from URL
            parsed_url = urlparse(image_url)
            key = parsed_url.path.lstrip('/')
            
            # Get object metadata
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            logger.error(f"Failed to get image info: {e}")
            return None
    
    def generate_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for temporary access
        
        Args:
            key: S3 object key
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL or None
        """
        if not self.s3_client:
            return None
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
