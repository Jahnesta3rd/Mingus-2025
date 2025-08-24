#!/usr/bin/env python3
"""
Step 1: Mac Email URL Extractor for Mingus Financial Wellness App

This script connects to iCloud email via IMAP, extracts all URLs from emails
in the "Mingus" folder, performs comprehensive domain analysis, and prepares
data for Step 2 domain intelligence analysis.

Target Audience: African American professionals aged 25-35 earning $40K-$100K
"""

import os
import sys
import re
import json
import csv
import logging
import getpass
import time
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import imaplib
import email
from email.header import decode_header
import ssl
from urllib.parse import urlparse, parse_qs, urlencode
import requests
from tqdm import tqdm
import concurrent.futures
from collections import defaultdict, Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/step1_extraction.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ExtractedURL:
    """Data structure for extracted URL information"""
    url: str
    original_url: str
    email_subject: str
    email_date: str
    sender_name: str
    sender_email: str
    domain: str
    email_id: str
    extraction_confidence: float

@dataclass
class DomainAnalysis:
    """Data structure for domain analysis results"""
    domain: str
    url_count: int
    unique_url_count: int
    percentage_of_total: float
    first_seen: str
    last_seen: str
    primary_senders: str
    category_suggestion: str
    sample_urls: str

class MacEmailExtractor:
    """Main class for extracting URLs from .mac email accounts"""
    
    def __init__(self, email_address: str, app_password: str):
        self.email_address = email_address
        self.app_password = app_password
        self.imap_server = "imap.mail.me.com"
        self.imap_port = 993
        self.folder_name = "Mingus"
        self.connection = None
        
        # URL extraction patterns
        self.url_patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            r'www\.[^\s<>"{}|\\^`\[\]]+',
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.url_patterns]
        
        # Domain categories for automatic classification
        self.domain_categories = {
            'financial': ['bank', 'credit', 'loan', 'mortgage', 'investment', 'trading', 'finance', 'wealth', 'money'],
            'news_media': ['news', 'times', 'post', 'journal', 'tribune', 'herald', 'press', 'media', 'reuters', 'bloomberg'],
            'educational': ['.edu', 'university', 'college', 'school', 'academy', 'institute', 'course', 'learning'],
            'career': ['linkedin', 'indeed', 'glassdoor', 'monster', 'career', 'job', 'employment', 'professional'],
            'social_media': ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok', 'snapchat'],
            'ecommerce': ['amazon', 'ebay', 'shop', 'store', 'buy', 'purchase', 'retail', 'marketplace'],
            'government': ['.gov', 'government', 'federal', 'state', 'city', 'official'],
            'blog_platform': ['wordpress', 'blogger', 'medium', 'substack', 'ghost', 'blog'],
        }
        
        # Create necessary directories
        self.create_directories()
    
    def create_directories(self):
        """Create necessary directories for output files"""
        directories = ['data', 'logs']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def connect_to_imap(self) -> bool:
        """Connect to iCloud IMAP server"""
        try:
            logger.info(f"Connecting to {self.imap_server}:{self.imap_port}")
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to IMAP server
            self.connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, ssl_context=context)
            
            # Authenticate
            self.connection.login(self.email_address, self.app_password)
            logger.info("Successfully connected and authenticated")
            return True
            
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def find_mingus_folder(self) -> Optional[str]:
        """Find the Mingus folder in the email account"""
        try:
            # List all folders
            status, folders = self.connection.list()
            if status != 'OK':
                logger.error("Failed to list folders")
                return None
            
            # Search for Mingus folder (case-insensitive)
            mingus_folder = None
            for folder in folders:
                # Handle both bytes and string folder names
                if isinstance(folder, bytes):
                    folder_str = folder.decode('utf-8')
                else:
                    folder_str = str(folder)
                
                folder_name = folder_str.split('"')[-2] if '"' in folder_str else folder_str.split()[-1]
                if folder_name.lower() == self.folder_name.lower():
                    mingus_folder = folder_name
                    break
            
            if mingus_folder:
                logger.info(f"Found Mingus folder: {mingus_folder}")
                return mingus_folder
            else:
                logger.error(f"Could not find folder named '{self.folder_name}'")
                return None
                
        except Exception as e:
            logger.error(f"Error finding Mingus folder: {e}")
            return None
    
    def get_email_count(self, folder_name: str) -> int:
        """Get the total number of emails in the folder"""
        try:
            self.connection.select(folder_name)
            status, messages = self.connection.search(None, 'ALL')
            if status == 'OK':
                email_count = len(messages[0].split())
                logger.info(f"Found {email_count} emails in {folder_name}")
                return email_count
            else:
                logger.error("Failed to get email count")
                return 0
        except Exception as e:
            logger.error(f"Error getting email count: {e}")
            return 0
    
    def decode_email_header(self, header_value: str) -> str:
        """Decode email header values"""
        try:
            # Handle case where header_value might be an int
            if isinstance(header_value, int):
                return str(header_value)
            
            # Handle case where header_value is None
            if header_value is None:
                return ''
            
            # Handle case where decode_header returns an int
            decoded_parts = decode_header(header_value)
            if isinstance(decoded_parts, int):
                return str(decoded_parts)
            
            # Handle case where decode_header returns a string directly
            if isinstance(decoded_parts, str):
                return decoded_parts
            
            decoded_string = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        try:
                            decoded_string += part.decode(encoding)
                        except (UnicodeDecodeError, LookupError):
                            decoded_string += part.decode('utf-8', errors='ignore')
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += str(part)
            return decoded_string
        except Exception as e:
            logger.warning(f"Failed to decode header: {e}")
            return str(header_value)
    
    def extract_urls_from_text(self, text: str, email_id: str) -> List[str]:
        """Extract URLs from text content"""
        urls = []
        
        # Handle case where text might be an int
        if isinstance(text, int):
            text = str(text)
        
        try:
            for pattern in self.compiled_patterns:
                matches = pattern.findall(text)
                for match in matches:
                    # Clean up the URL
                    url = match.strip()
                    
                    # Add protocol if missing
                    if url.startswith('www.'):
                        url = 'https://' + url
                    
                    # Basic URL validation
                    if self.is_valid_url(url):
                        urls.append(url)
        except Exception as e:
            logger.debug(f"Error extracting URLs from text: {e}")
        
        return list(set(urls))  # Remove duplicates
    
    def is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def clean_url(self, url: str) -> str:
        """Clean URL by removing tracking parameters"""
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # Remove common tracking parameters
            tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                             'fbclid', 'gclid', 'msclkid', 'ref', 'source', 'campaign']
            
            cleaned_params = {k: v for k, v in query_params.items() if k not in tracking_params}
            
            # Reconstruct URL
            cleaned_query = urlencode(cleaned_params, doseq=True) if cleaned_params else ''
            cleaned_url = parsed._replace(query=cleaned_query).geturl()
            
            return cleaned_url
        except Exception:
            return url
    
    def expand_shortened_url(self, url: str) -> str:
        """Expand shortened URLs where possible"""
        try:
            # Skip if already expanded or not a known shortener
            shorteners = ['bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'is.gd', 'v.gd']
            if not any(shortener in url for shortener in shorteners):
                return url
            
            # Follow redirects to get final URL
            response = requests.head(url, allow_redirects=True, timeout=10)
            expanded_url = response.url
            
            if expanded_url != url:
                logger.debug(f"Expanded {url} to {expanded_url}")
                return expanded_url
            
        except Exception as e:
            logger.debug(f"Failed to expand URL {url}: {e}")
        
        return url
    
    def categorize_domain(self, domain: str) -> str:
        """Automatically categorize domain based on keywords"""
        domain_lower = domain.lower()
        
        for category, keywords in self.domain_categories.items():
            for keyword in keywords:
                if keyword in domain_lower:
                    return category
        
        return 'unknown'
    
    def process_email(self, email_id: str) -> Tuple[List[ExtractedURL], Dict]:
        """Process a single email and extract URLs"""
        urls = []
        email_info = {
            'subject': '',
            'date': '',
            'sender_name': '',
            'sender_email': '',
            'processing_error': None
        }
        
        try:
            # Fetch email using BODY[1] instead of RFC822
            status, data = self.connection.fetch(email_id, '(BODY[1])')
            if status != 'OK':
                email_info['processing_error'] = f"Failed to fetch email: {status}"
                return urls, email_info
            
            # Check if we got actual email data
            if len(data) == 0 or len(data[0]) < 2:
                email_info['processing_error'] = "No email data received"
                return urls, email_info
            
            if isinstance(data[0][1], int):
                email_info['processing_error'] = f"Email data is integer: {data[0][1]}"
                return urls, email_info
            
            # Parse email
            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Extract email metadata with safe handling
            try:
                subject = email_message.get('Subject', '')
                email_info['subject'] = self.decode_email_header(subject) if subject else ''
            except Exception:
                email_info['subject'] = str(email_message.get('Subject', ''))
            
            try:
                date = email_message.get('Date', '')
                email_info['date'] = str(date) if date else ''
            except Exception:
                email_info['date'] = str(email_message.get('Date', ''))
            
            # Extract sender information with safe handling
            try:
                from_header = email_message.get('From', '')
                email_info['sender_name'], email_info['sender_email'] = self.parse_sender(from_header)
            except Exception:
                from_header = str(email_message.get('From', ''))
                email_info['sender_name'], email_info['sender_email'] = self.parse_sender(from_header)
            
            # Extract URLs from email body
            urls = self.extract_urls_from_email_body(email_message, email_id, email_info)
            
        except Exception as e:
            email_info['processing_error'] = str(e)
            logger.error(f"Error processing email {email_id}: {e}")
        
        return urls, email_info
    
    def parse_sender(self, from_header: str) -> Tuple[str, str]:
        """Parse sender name and email from From header"""
        try:
            # Handle case where from_header might be an int
            if isinstance(from_header, int):
                return '', str(from_header)
            
            # Handle format: "Name <email@domain.com>"
            if '<' in from_header and '>' in from_header:
                name_part = from_header.split('<')[0].strip().strip('"')
                email_part = from_header.split('<')[1].split('>')[0].strip()
                return name_part, email_part
            else:
                # Handle format: email@domain.com
                return '', from_header.strip()
        except Exception:
            return '', str(from_header).strip()
    
    def extract_urls_from_email_body(self, email_message, email_id: str, email_info: Dict) -> List[ExtractedURL]:
        """Extract URLs from email body parts"""
        urls = []
        
        def process_part(part):
            content_type = part.get_content_type()
            
            try:
                if content_type == 'text/plain':
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        text = payload.decode('utf-8', errors='ignore')
                    elif isinstance(payload, int):
                        text = str(payload)
                    else:
                        text = str(payload)
                    extracted_urls = self.extract_urls_from_text(text, email_id)
                    
                elif content_type == 'text/html':
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        text = payload.decode('utf-8', errors='ignore')
                    elif isinstance(payload, int):
                        text = str(payload)
                    else:
                        text = str(payload)
                    extracted_urls = self.extract_urls_from_text(text, email_id)
                    
                else:
                    extracted_urls = []
                
                return extracted_urls
            except Exception as e:
                logger.debug(f"Error processing part {content_type}: {e}")
                return []
        
        # Handle multipart emails
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                
                try:
                    extracted_urls = process_part(part)
                    for url in extracted_urls:
                        urls.append(self.create_extracted_url(url, email_id, email_info))
                except Exception as e:
                    logger.debug(f"Error processing multipart: {e}")
                    continue
        else:
            try:
                extracted_urls = process_part(email_message)
                for url in extracted_urls:
                    urls.append(self.create_extracted_url(url, email_id, email_info))
            except Exception as e:
                logger.debug(f"Error processing single part: {e}")
        
        return urls
    
    def create_extracted_url(self, url: str, email_id: str, email_info: Dict) -> ExtractedURL:
        """Create ExtractedURL object from raw URL"""
        original_url = url
        cleaned_url = self.clean_url(url)
        expanded_url = self.expand_shortened_url(cleaned_url)
        
        # Extract domain
        try:
            domain = urlparse(expanded_url).netloc
        except Exception:
            domain = 'unknown'
        
        # Calculate extraction confidence
        confidence = 1.0
        if original_url != expanded_url:
            confidence = 0.9  # Slightly lower confidence for expanded URLs
        
        return ExtractedURL(
            url=expanded_url,
            original_url=original_url,
            email_subject=email_info['subject'],
            email_date=email_info['date'],
            sender_name=email_info['sender_name'],
            sender_email=email_info['sender_email'],
            domain=domain,
            email_id=email_id,
            extraction_confidence=confidence
        )
    
    def process_all_emails(self, folder_name: str) -> Tuple[List[ExtractedURL], Dict]:
        """Process all emails in the folder"""
        all_urls = []
        processing_stats = {
            'total_emails': 0,
            'processed_emails': 0,
            'failed_emails': 0,
            'total_urls': 0,
            'start_time': time.time()
        }
        
        try:
            # Select the folder
            self.connection.select(folder_name)
            
            # Search for all emails
            status, messages = self.connection.search(None, 'ALL')
            if status != 'OK':
                logger.error("Failed to search emails")
                return all_urls, processing_stats
            
            email_ids = messages[0].split()
            processing_stats['total_emails'] = len(email_ids)
            
            logger.info(f"Processing {len(email_ids)} emails...")
            
            # Process emails with progress bar
            with tqdm(total=len(email_ids), desc="Processing emails") as pbar:
                for email_id in email_ids:
                    # Convert email_id to string if it's bytes
                    if isinstance(email_id, bytes):
                        email_id_str = email_id.decode('utf-8')
                    else:
                        email_id_str = str(email_id)
                    
                    urls, email_info = self.process_email(email_id_str)
                    
                    if email_info.get('processing_error'):
                        processing_stats['failed_emails'] += 1
                        logger.warning(f"Failed to process email {email_id_str}: {email_info['processing_error']}")
                    else:
                        processing_stats['processed_emails'] += 1
                        all_urls.extend(urls)
                    
                    pbar.update(1)
            
            processing_stats['total_urls'] = len(all_urls)
            processing_stats['processing_time'] = time.time() - processing_stats['start_time']
            
        except Exception as e:
            logger.error(f"Error processing emails: {e}")
        
        return all_urls, processing_stats
    
    def analyze_domains(self, urls: List[ExtractedURL]) -> List[DomainAnalysis]:
        """Analyze domains from extracted URLs"""
        domain_stats = defaultdict(lambda: {
            'urls': [],
            'unique_urls': set(),
            'senders': set(),
            'dates': []
        })
        
        # Collect domain statistics
        for url_obj in urls:
            domain = url_obj.domain
            domain_stats[domain]['urls'].append(url_obj)
            domain_stats[domain]['unique_urls'].add(url_obj.url)
            domain_stats[domain]['senders'].add(url_obj.sender_email)
            domain_stats[domain]['dates'].append(url_obj.email_date)
        
        # Calculate total URLs for percentage calculation
        total_urls = len(urls)
        
        # Create domain analysis objects
        domain_analyses = []
        for domain, stats in domain_stats.items():
            url_count = len(stats['urls'])
            unique_url_count = len(stats['unique_urls'])
            percentage = (url_count / total_urls * 100) if total_urls > 0 else 0
            
            # Get date range
            dates = [d for d in stats['dates'] if d]
            first_seen = min(dates) if dates else ''
            last_seen = max(dates) if dates else ''
            
            # Get primary senders
            primary_senders = ', '.join(list(stats['senders'])[:3])  # Top 3 senders
            
            # Get sample URLs
            sample_urls = ', '.join(list(stats['unique_urls'])[:5])  # Top 5 URLs
            
            # Categorize domain
            category = self.categorize_domain(domain)
            
            domain_analysis = DomainAnalysis(
                domain=domain,
                url_count=url_count,
                unique_url_count=unique_url_count,
                percentage_of_total=percentage,
                first_seen=first_seen,
                last_seen=last_seen,
                primary_senders=primary_senders,
                category_suggestion=category,
                sample_urls=sample_urls
            )
            domain_analyses.append(domain_analysis)
        
        # Sort by URL count (descending)
        domain_analyses.sort(key=lambda x: x.url_count, reverse=True)
        
        return domain_analyses
    
    def export_results(self, urls: List[ExtractedURL], domain_analyses: List[DomainAnalysis], 
                      processing_stats: Dict) -> None:
        """Export results to various file formats"""
        
        # 1. Export raw URLs to CSV
        logger.info("Exporting raw URLs to CSV...")
        with open('data/raw_urls_complete.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['url', 'original_url', 'email_subject', 'email_date', 'sender_name', 
                         'sender_email', 'domain', 'email_id', 'extraction_confidence']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for url_obj in urls:
                writer.writerow(asdict(url_obj))
        
        # 2. Export domain analysis to CSV
        logger.info("Exporting domain analysis to CSV...")
        with open('data/domain_analysis_report.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['domain', 'url_count', 'unique_url_count', 'percentage_of_total', 
                         'first_seen', 'last_seen', 'primary_senders', 'category_suggestion', 'sample_urls']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for domain_analysis in domain_analyses:
                writer.writerow(asdict(domain_analysis))
        
        # 3. Export processing summary to JSON
        logger.info("Exporting processing summary to JSON...")
        summary = {
            "total_emails_processed": processing_stats['processed_emails'],
            "total_urls_extracted": processing_stats['total_urls'],
            "unique_domains_found": len(domain_analyses),
            "processing_time_seconds": processing_stats['processing_time'],
            "success_rate": (processing_stats['processed_emails'] / processing_stats['total_emails'] * 100) if processing_stats['total_emails'] > 0 else 0,
            "error_count": processing_stats['failed_emails']
        }
        
        with open('data/email_processing_summary.json', 'w', encoding='utf-8') as jsonfile:
            json.dump(summary, jsonfile, indent=2)
        
        # 4. Export top domains preview
        logger.info("Exporting top domains preview...")
        with open('data/top_domains_preview.txt', 'w', encoding='utf-8') as txtfile:
            txtfile.write("TOP 20 DOMAINS BY URL COUNT\n")
            txtfile.write("=" * 50 + "\n\n")
            
            for i, domain_analysis in enumerate(domain_analyses[:20], 1):
                txtfile.write(f"{i:2d}. {domain_analysis.domain}\n")
                txtfile.write(f"    URLs: {domain_analysis.url_count} ({domain_analysis.percentage_of_total:.1f}%)\n")
                txtfile.write(f"    Category: {domain_analysis.category_suggestion}\n")
                txtfile.write(f"    Sample: {domain_analysis.sample_urls[:100]}...\n")
                txtfile.write(f"    Senders: {domain_analysis.primary_senders}\n\n")
        
        logger.info("All results exported successfully")
    
    def run(self) -> bool:
        """Main execution method"""
        try:
            logger.info("Starting Mac Email URL Extractor for Mingus")
            
            # Connect to IMAP
            if not self.connect_to_imap():
                return False
            
            # Find Mingus folder
            folder_name = self.find_mingus_folder()
            if not folder_name:
                return False
            
            # Get email count
            email_count = self.get_email_count(folder_name)
            if email_count == 0:
                logger.warning("No emails found in Mingus folder")
                return True
            
            # Process all emails
            urls, processing_stats = self.process_all_emails(folder_name)
            
            if not urls:
                logger.warning("No URLs extracted from emails")
                return True
            
            # Analyze domains
            logger.info("Analyzing domains...")
            domain_analyses = self.analyze_domains(urls)
            
            # Export results
            self.export_results(urls, domain_analyses, processing_stats)
            
            # Display summary
            self.display_summary(processing_stats, domain_analyses)
            
            return True
            
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            return False
        
        finally:
            if self.connection:
                try:
                    self.connection.logout()
                    logger.info("Disconnected from IMAP server")
                except Exception as e:
                    logger.warning(f"Error during logout: {e}")
    
    def display_summary(self, processing_stats: Dict, domain_analyses: List[DomainAnalysis]) -> None:
        """Display processing summary"""
        print("\n" + "=" * 60)
        print("EXTRACTION COMPLETE - SUMMARY")
        print("=" * 60)
        print(f"Emails processed: {processing_stats['processed_emails']}/{processing_stats['total_emails']}")
        print(f"URLs extracted: {processing_stats['total_urls']:,}")
        print(f"Unique domains: {len(domain_analyses)}")
        print(f"Processing time: {processing_stats['processing_time']:.1f} seconds")
        print(f"Success rate: {processing_stats['processed_emails']/processing_stats['total_emails']*100:.1f}%")
        
        if domain_analyses:
            print(f"\nTop 5 domains:")
            for i, domain in enumerate(domain_analyses[:5], 1):
                print(f"  {i}. {domain.domain} ({domain.url_count} URLs, {domain.percentage_of_total:.1f}%)")
        
        print(f"\nResults saved to data/ directory")
        print("Ready for Step 2: Domain Intelligence Analysis")
        print("=" * 60)


def get_credentials() -> Tuple[str, str]:
    """Get email credentials from user or environment"""
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Mac Email URL Extractor for Mingus')
    parser.add_argument('--email', help='.mac email address')
    parser.add_argument('--password', help='app-specific password')
    args = parser.parse_args()
    
    # Try command line arguments first
    if args.email and args.password:
        logger.info("Using credentials from command line arguments")
        return args.email, args.password
    
    # Try environment variables
    email_address = os.getenv('MAC_EMAIL')
    app_password = os.getenv('MAC_APP_PASSWORD')
    
    if email_address and app_password:
        logger.info("Using credentials from environment variables")
        return email_address, app_password
    
    # Prompt user for credentials
    print("Mac Email URL Extractor for Mingus Financial Wellness App")
    print("=" * 60)
    
    email_address = input("Enter .mac email address: ").strip()
    app_password = getpass.getpass("Enter app-specific password: ").strip()
    
    return email_address, app_password


def main():
    """Main entry point"""
    try:
        # Get credentials
        email_address, app_password = get_credentials()
        
        if not email_address or not app_password:
            print("Error: Email address and password are required")
            sys.exit(1)
        
        # Create extractor and run
        extractor = MacEmailExtractor(email_address, app_password)
        success = extractor.run()
        
        if success:
            print("\nExtraction completed successfully!")
            sys.exit(0)
        else:
            print("\nExtraction failed. Check logs for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nExtraction interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
