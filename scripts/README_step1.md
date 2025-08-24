# Step 1: Mac Email URL Extractor

## Overview

This script extracts all URLs from emails in your .mac email account's "Mingus" folder, performs comprehensive domain analysis, and prepares data for Step 2 of the Mingus financial wellness app's article library implementation.

**Target Audience**: African American professionals aged 25-35 earning $40K-$100K

## Features

### Email Processing
- ✅ Connects to iCloud IMAP (imap.mail.me.com, port 993, SSL)
- ✅ Authenticates with .mac email and app-specific password
- ✅ Accesses "Mingus" folder specifically
- ✅ Handles HTML and plain text email formats
- ✅ Processes multipart emails and extracts from all parts
- ✅ Parses email metadata (subject, sender, date, message-id)
- ✅ Handles different email encodings (UTF-8, ASCII, etc.)

### URL Processing
- ✅ Extracts all HTTP/HTTPS URLs using robust regex
- ✅ Cleans tracking parameters (utm_source, utm_medium, etc.)
- ✅ Handles URLs wrapped across multiple lines
- ✅ Expands shortened URLs (bit.ly, tinyurl, etc.) where possible
- ✅ Records which specific email each URL came from

### Domain Analysis
- ✅ Extracts and counts all unique domains and subdomains
- ✅ Calculates URL frequency per domain and percentages
- ✅ Tracks first/last appearance dates for each domain
- ✅ Maps domains to email senders for source analysis
- ✅ Identifies domain categories automatically

### Security & Authentication
- ✅ Secure password input using getpass (no echo to terminal)
- ✅ Support for environment variables (MAC_EMAIL, MAC_APP_PASSWORD)
- ✅ Clear error messages for authentication failures
- ✅ Graceful handling of network timeouts and connection issues

## Prerequisites

### 1. App-Specific Password Setup

You need to generate an app-specific password for your .mac account:

1. Go to [Apple ID website](https://appleid.apple.com)
2. Sign in with your .mac email address
3. Go to "Security" → "App-Specific Passwords"
4. Click "Generate Password"
5. Give it a name like "Mingus Email Extractor"
6. Copy the generated password (format: xxxx-xxxx-xxxx-xxxx)

### 2. Python Environment

Ensure you have Python 3.7+ installed:

```bash
python3 --version
```

### 3. Install Dependencies

```bash
cd scripts
pip install -r requirements_step1.txt
```

## Usage

### Basic Usage

```bash
python scripts/step1_mac_email_extractor.py
```

The script will prompt you for:
- Your .mac email address
- Your app-specific password

### Environment Variables (Recommended)

Set these environment variables to avoid typing credentials:

```bash
export MAC_EMAIL="your_email@mac.com"
export MAC_APP_PASSWORD="your-app-specific-password"
```

Then run:
```bash
python scripts/step1_mac_email_extractor.py
```

### Example Output

```
Mac Email URL Extractor for Mingus Financial Wellness App
============================================================
Enter .mac email address: johnnie_watson_3rd@mac.com
Enter app-specific password: ********
2025-01-15 10:30:15 - INFO - Connecting to imap.mail.me.com:993
2025-01-15 10:30:16 - INFO - Successfully connected and authenticated
2025-01-15 10:30:16 - INFO - Found Mingus folder: Mingus
2025-01-15 10:30:16 - INFO - Found 156 emails in Mingus
2025-01-15 10:30:16 - INFO - Processing 156 emails...
Processing emails: [████████████████████] 100% (156/156) ETA: 0:00
2025-01-15 10:32:45 - INFO - Analyzing domains...
2025-01-15 10:32:46 - INFO - Exporting raw URLs to CSV...
2025-01-15 10:32:47 - INFO - Exporting domain analysis to CSV...
2025-01-15 10:32:47 - INFO - Exporting processing summary to JSON...
2025-01-15 10:32:48 - INFO - Exporting top domains preview...
2025-01-15 10:32:48 - INFO - All results exported successfully

============================================================
EXTRACTION COMPLETE - SUMMARY
============================================================
Emails processed: 156/156
URLs extracted: 1,247
Unique domains: 89
Processing time: 153.2 seconds
Success rate: 100.0%

Top 5 domains:
  1. bloomberg.com (45 URLs, 3.6%)
  2. cnbc.com (38 URLs, 3.0%)
  3. marketwatch.com (32 URLs, 2.6%)
  4. linkedin.com (28 URLs, 2.2%)
  5. forbes.com (25 URLs, 2.0%)

Results saved to data/ directory
Ready for Step 2: Domain Intelligence Analysis
============================================================
```

## Output Files

The script creates the following files in the `data/` directory:

### 1. `raw_urls_complete.csv`
All extracted URLs with metadata:
- `url`: Cleaned and expanded URL
- `original_url`: Original URL as found in email
- `email_subject`: Subject line of source email
- `email_date`: Date of source email
- `sender_name`: Name of email sender
- `sender_email`: Email address of sender
- `domain`: Extracted domain
- `email_id`: Internal email identifier
- `extraction_confidence`: Confidence score (0.0-1.0)

### 2. `domain_analysis_report.csv`
Complete domain statistics:
- `domain`: Domain name
- `url_count`: Total URLs from this domain
- `unique_url_count`: Unique URLs from this domain
- `percentage_of_total`: Percentage of total URLs
- `first_seen`: First appearance date
- `last_seen`: Last appearance date
- `primary_senders`: Top 3 email senders containing this domain
- `category_suggestion`: Automatic category classification
- `sample_urls`: Sample URLs from this domain

### 3. `email_processing_summary.json`
Processing statistics:
```json
{
  "total_emails_processed": 156,
  "total_urls_extracted": 1247,
  "unique_domains_found": 89,
  "processing_time_seconds": 153.2,
  "success_rate": 100.0,
  "error_count": 0
}
```

### 4. `top_domains_preview.txt`
Human-readable summary of top 20 domains for quick review.

### 5. `logs/step1_extraction.log`
Detailed processing log with timestamps and error information.

## Domain Categories

The script automatically categorizes domains based on keywords:

- **financial**: banks, credit, loans, investments, trading, finance
- **news_media**: news sites, journalism, reporting
- **educational**: .edu domains, universities, courses
- **career**: LinkedIn, job sites, professional development
- **social_media**: Facebook, Twitter, Instagram, YouTube
- **ecommerce**: Amazon, eBay, shopping sites
- **government**: .gov domains, official sites
- **blog_platform**: WordPress, Medium, Substack
- **unknown**: Unclassified domains for manual review

## Troubleshooting

### Common Issues

#### 1. Authentication Failed
```
IMAP authentication failed: [AUTHENTICATIONFAILED] Invalid credentials
```

**Solution**: 
- Verify your app-specific password is correct
- Generate a new app-specific password
- Ensure you're using your .mac email address (not iCloud.com)

#### 2. Folder Not Found
```
Could not find folder named 'Mingus'
```

**Solution**:
- Verify the folder exists in your .mac email account
- Check folder name spelling (case-insensitive)
- Ensure the folder is accessible via IMAP

#### 3. Connection Timeout
```
Connection failed: [Errno 60] Operation timed out
```

**Solution**:
- Check your internet connection
- Verify firewall settings allow IMAP connections
- Try again later (iCloud may be experiencing issues)

#### 4. No URLs Extracted
```
No URLs extracted from emails
```

**Solution**:
- Verify emails in the Mingus folder contain URLs
- Check if emails are in HTML format (URLs may be in links)
- Review the log file for specific error messages

### Debug Mode

For detailed debugging, modify the logging level in the script:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    # ... rest of configuration
)
```

### Network Issues

If you experience network connectivity issues:

1. **Check IMAP Settings**:
   - Server: imap.mail.me.com
   - Port: 993
   - Security: SSL/TLS

2. **Firewall Configuration**:
   - Allow outbound connections to port 993
   - Allow IMAP protocol

3. **DNS Issues**:
   - Try using IP address instead of hostname
   - Check DNS resolution

## Performance Optimization

### Large Email Collections

For folders with 1000+ emails:

1. **Batch Processing**: The script processes emails in batches to manage memory
2. **Progress Tracking**: Real-time progress bars show processing status
3. **Error Recovery**: Continues processing even if individual emails fail
4. **Memory Management**: Efficient URL storage and domain analysis

### Processing Time Estimates

- **Small folder (50 emails)**: 30-60 seconds
- **Medium folder (200 emails)**: 2-5 minutes
- **Large folder (500+ emails)**: 10-30 minutes

## Security Considerations

### Credential Security

- ✅ Passwords are never logged or displayed
- ✅ Environment variables are cleared after use
- ✅ No credentials stored in output files
- ✅ Secure IMAP connection with SSL/TLS

### Data Privacy

- ✅ Only URL and metadata extraction (no email content)
- ✅ No personal information in output files
- ✅ Logs contain only processing information
- ✅ All data stays on your local machine

## Integration with Step 2

This script prepares data for Step 2: Domain Intelligence Analysis by providing:

1. **Complete URL Dataset**: All discovered URLs with source tracking
2. **Domain Intelligence**: Comprehensive domain analysis and categorization
3. **Source Analysis**: Email sender patterns and frequency
4. **Temporal Data**: First/last appearance dates for trend analysis
5. **Quality Metrics**: Extraction confidence and processing statistics

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the detailed log file: `logs/step1_extraction.log`
3. Verify your .mac account settings and app-specific password
4. Ensure all dependencies are installed correctly

## Next Steps

After successful extraction:

1. Review `data/top_domains_preview.txt` for quick domain overview
2. Examine `data/domain_analysis_report.csv` for detailed domain statistics
3. Proceed to Step 2: Domain Intelligence Analysis
4. Use the extracted data for cultural relevance analysis and filtering decisions
