#!/usr/bin/env python3
"""
AWS Configuration for Mingus Meme Splash Page
Handles AWS services setup and configuration
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AWSConfig:
    def __init__(self):
        self.region = os.environ.get('AWS_S3_REGION', 'us-east-1')
        self.bucket_name = os.environ.get('AWS_S3_BUCKET')
        self.access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        self.secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        
        # Initialize clients
        self.s3_client = None
        self.cloudfront_client = None
        self.ses_client = None
        
        if self._has_credentials():
            self._initialize_clients()
    
    def _has_credentials(self) -> bool:
        """Check if AWS credentials are available"""
        return all([self.access_key, self.secret_key])
    
    def _initialize_clients(self):
        """Initialize AWS service clients"""
        try:
            session = boto3.Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            
            self.s3_client = session.client('s3')
            self.cloudfront_client = session.client('cloudfront')
            self.ses_client = session.client('ses', region_name='us-east-1')  # SES is only available in us-east-1
            
            logger.info("AWS clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
    
    def setup_s3_bucket(self) -> Dict[str, Any]:
        """
        Set up S3 bucket with proper configuration
        """
        if not self.s3_client or not self.bucket_name:
            return {'success': False, 'error': 'S3 client or bucket name not configured'}
        
        try:
            # Check if bucket exists
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"Bucket {self.bucket_name} already exists")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    # Create bucket
                    if self.region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    logger.info(f"Created bucket {self.bucket_name}")
                else:
                    raise e
            
            # Configure bucket for public read access
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{self.bucket_name}/memes/*"
                    }
                ]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            # Configure CORS
            cors_configuration = {
                'CORSRules': [
                    {
                        'AllowedHeaders': ['*'],
                        'AllowedMethods': ['GET', 'HEAD'],
                        'AllowedOrigins': ['*'],
                        'ExposeHeaders': ['ETag'],
                        'MaxAgeSeconds': 3000
                    }
                ]
            }
            
            self.s3_client.put_bucket_cors(
                Bucket=self.bucket_name,
                CORSConfiguration=cors_configuration
            )
            
            # Configure lifecycle for cost optimization
            lifecycle_configuration = {
                'Rules': [
                    {
                        'ID': 'DeleteIncompleteMultipartUploads',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': ''},
                        'AbortIncompleteMultipartUpload': {
                            'DaysAfterInitiation': 7
                        }
                    },
                    {
                        'ID': 'TransitionToIA',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': 'memes/'},
                        'Transitions': [
                            {
                                'Days': 30,
                                'StorageClass': 'STANDARD_IA'
                            }
                        ]
                    }
                ]
            }
            
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=lifecycle_configuration
            )
            
            return {
                'success': True,
                'bucket_name': self.bucket_name,
                'region': self.region,
                'url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com"
            }
            
        except Exception as e:
            logger.error(f"S3 bucket setup failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def setup_cloudfront_distribution(self, domain_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Set up CloudFront distribution for CDN
        """
        if not self.cloudfront_client or not self.bucket_name:
            return {'success': False, 'error': 'CloudFront client or bucket name not configured'}
        
        try:
            # Check if distribution already exists
            distributions = self.cloudfront_client.list_distributions()
            existing_dist = None
            
            for dist in distributions.get('DistributionList', {}).get('Items', []):
                if dist['Origins']['Items'][0]['DomainName'] == f"{self.bucket_name}.s3.{self.region}.amazonaws.com":
                    existing_dist = dist
                    break
            
            if existing_dist:
                return {
                    'success': True,
                    'distribution_id': existing_dist['Id'],
                    'domain_name': existing_dist['DomainName'],
                    'url': f"https://{existing_dist['DomainName']}"
                }
            
            # Create new distribution
            distribution_config = {
                'CallerReference': f"mingus-memes-{int(time.time())}",
                'Comment': 'Mingus Meme Splash Page CDN',
                'DefaultRootObject': 'index.html',
                'Origins': {
                    'Quantity': 1,
                    'Items': [
                        {
                            'Id': f"{self.bucket_name}-origin",
                            'DomainName': f"{self.bucket_name}.s3.{self.region}.amazonaws.com",
                            'S3OriginConfig': {
                                'OriginAccessIdentity': ''
                            }
                        }
                    ]
                },
                'DefaultCacheBehavior': {
                    'TargetOriginId': f"{self.bucket_name}-origin",
                    'ViewerProtocolPolicy': 'redirect-to-https',
                    'TrustedSigners': {
                        'Enabled': False,
                        'Quantity': 0
                    },
                    'ForwardedValues': {
                        'QueryString': False,
                        'Cookies': {'Forward': 'none'}
                    },
                    'MinTTL': 0,
                    'DefaultTTL': 86400,  # 1 day
                    'MaxTTL': 31536000    # 1 year
                },
                'CacheBehaviors': {
                    'Quantity': 1,
                    'Items': [
                        {
                            'PathPattern': 'memes/*',
                            'TargetOriginId': f"{self.bucket_name}-origin",
                            'ViewerProtocolPolicy': 'redirect-to-https',
                            'TrustedSigners': {
                                'Enabled': False,
                                'Quantity': 0
                            },
                            'ForwardedValues': {
                                'QueryString': False,
                                'Cookies': {'Forward': 'none'}
                            },
                            'MinTTL': 0,
                            'DefaultTTL': 31536000,  # 1 year for images
                            'MaxTTL': 31536000
                        }
                    ]
                },
                'Enabled': True,
                'PriceClass': 'PriceClass_100'  # Use only North America and Europe
            }
            
            if domain_name:
                distribution_config['Aliases'] = {
                    'Quantity': 1,
                    'Items': [domain_name]
                }
            
            response = self.cloudfront_client.create_distribution(
                DistributionConfig=distribution_config
            )
            
            distribution = response['Distribution']
            
            return {
                'success': True,
                'distribution_id': distribution['Id'],
                'domain_name': distribution['DomainName'],
                'url': f"https://{distribution['DomainName']}",
                'status': distribution['Status']
            }
            
        except Exception as e:
            logger.error(f"CloudFront setup failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def setup_ses(self, verified_email: str) -> Dict[str, Any]:
        """
        Set up SES for email notifications
        """
        if not self.ses_client:
            return {'success': False, 'error': 'SES client not configured'}
        
        try:
            # Verify email address
            self.ses_client.verify_email_identity(EmailAddress=verified_email)
            
            # Get sending quota
            quota = self.ses_client.get_send_quota()
            
            return {
                'success': True,
                'verified_email': verified_email,
                'sending_quota': quota['Max24HourSend'],
                'sent_last_24h': quota['SentLast24Hours'],
                'max_send_rate': quota['MaxSendRate']
            }
            
        except Exception as e:
            logger.error(f"SES setup failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_aws_status(self) -> Dict[str, Any]:
        """Get status of all AWS services"""
        status = {
            'credentials_configured': self._has_credentials(),
            'region': self.region,
            'bucket_name': self.bucket_name,
            's3_available': self.s3_client is not None,
            'cloudfront_available': self.cloudfront_client is not None,
            'ses_available': self.ses_client is not None
        }
        
        if self.s3_client and self.bucket_name:
            try:
                # Test S3 access
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                status['s3_bucket_exists'] = True
            except ClientError:
                status['s3_bucket_exists'] = False
        
        return status

# Global instance
aws_config = AWSConfig()
