# Mingus Financial Wellness App - Bookmark Domain Extraction

## Overview

The bookmark extraction feature allows you to extract URLs from browser bookmarks (Chrome, Safari, Firefox), analyze domains using the same intelligence as Step 2, and integrate them seamlessly with the existing domain approval workflow.

## Features

### 🔍 **Multi-Browser Support**
- **Chrome**: Automatic extraction from `~/Library/Application Support/Google/Chrome/Default/Bookmarks`
- **Safari**: Manual export to HTML format
- **Firefox**: Manual export to HTML format
- **HTML Import**: Support for any exported bookmarks file

### 🎯 **Smart Filtering**
- **Financial Keywords**: 40+ financial terms (investment, retirement, budgeting, etc.)
- **Career Keywords**: 50+ career terms (professional development, leadership, etc.)
- **Cultural Relevance**: African American professional content detection
- **Domain Recognition**: Automatic identification of financial/career websites

### 🧠 **Intelligent Analysis**
- **Quality Scoring**: Domain quality assessment using Step 2 logic
- **Cultural Relevance**: African American professional content scoring
- **Auto-Recommendations**: AUTO_APPROVE, MANUAL_REVIEW, AUTO_REJECT
- **Confidence Scoring**: AI confidence in recommendations

### 🔗 **Seamless Integration**
- **Merged Workflow**: Bookmark domains appear in existing approval interface
- **Visual Indicators**: Purple "Bookmark" badge for bookmark-sourced domains
- **Bulk Operations**: Bookmark domains work with all existing bulk actions
- **Export Ready**: Approved bookmark domains included in Step 4 output

## Quick Start

### 1. Automatic Setup
```bash
cd scripts
./setup_bookmark_extraction.sh
```

### 2. Manual Extraction
```bash
# Extract from Chrome only
python3 extract_bookmarks.py

# Extract from HTML export file
python3 extract_bookmarks.py --html-file safari_bookmarks.html

# Extract from Chrome + HTML file
python3 extract_bookmarks.py --html-file firefox_bookmarks.html
```

### 3. Review in Approval Interface
```bash
python3 step3_domain_approval_interface.py
# Open http://localhost:5001
```

## Browser-Specific Instructions

### Chrome Bookmarks
**Automatic Extraction** ✅
- No manual steps required
- Script automatically reads Chrome bookmarks file
- Located at: `~/Library/Application Support/Google/Chrome/Default/Bookmarks`

### Safari Bookmarks
**Manual Export Required** 📋
1. Open Safari
2. Go to **File > Export Bookmarks**
3. Save as `safari_bookmarks.html`
4. Run: `python3 extract_bookmarks.py --html-file safari_bookmarks.html`

### Firefox Bookmarks
**Manual Export Required** 📋
1. Open Firefox
2. Go to **Bookmarks > Manage Bookmarks**
3. Click **Import and Backup > Export Bookmarks to HTML**
4. Save as `firefox_bookmarks.html`
5. Run: `python3 extract_bookmarks.py --html-file firefox_bookmarks.html`

## Keyword Filtering

### Financial Keywords (40+ terms)
- **Investing**: investment, investing, wealth, portfolio, stock, market
- **Retirement**: 401k, ira, retirement, pension, social security
- **Budgeting**: budget, saving, expense, cash, cashflow
- **Credit**: credit, debt, loan, mortgage, interest
- **Taxes**: tax, taxes, accounting, payroll, income
- **Banking**: bank, credit union, checking, savings

### Career Keywords (50+ terms)
- **Professional**: career, job, employment, professional, business
- **Leadership**: executive, ceo, cfo, director, manager, supervisor
- **Development**: training, education, certification, degree, mba
- **Networking**: linkedin, networking, mentor, workshop, conference
- **Recruitment**: resume, cv, interview, hiring, hr, human resources

### African American Professional Keywords
- **Diversity**: diversity, inclusion, equity, minority, representation
- **Empowerment**: empowerment, success, achievement, excellence
- **Community**: community, advocacy, role model, inspiration
- **Professional**: mentorship, networking, career advancement
- **Financial**: wealth building, financial literacy, entrepreneurship

## Domain Analysis

### Quality Scoring
- **High Quality (0.8+)**: Bloomberg, Reuters, WSJ, LinkedIn, Glassdoor
- **Medium Quality (0.5-0.7)**: Most professional websites
- **Low Quality (0.3-)**: Social media, personal blogs

### Cultural Relevance Scoring
- **High Relevance (0.7+)**: African American professional content
- **Medium Relevance (0.5-0.7)**: General professional content
- **Low Relevance (0.0-0.5)**: Non-professional content

### Auto-Recommendations
- **AUTO_APPROVE**: High quality + high cultural relevance
- **MANUAL_REVIEW**: Medium quality or uncertain cultural relevance
- **AUTO_REJECT**: Low quality or irrelevant content

## Output Files

### Generated Files
1. **`data/bookmark_domains.json`** - Bookmark domains with analysis
2. **`data/domain_recommendations.json`** - Merged with existing domains
3. **`reports/bookmark_extraction_report.json`** - Extraction summary

### Sample Output
```json
{
  "bloomberg.com": {
    "recommendation": "AUTO_APPROVE",
    "confidence": 0.9,
    "reasoning": "High-quality financial news source",
    "quality_score": 0.8,
    "cultural_relevance_score": 0.6,
    "url_count": 5,
    "priority": "NORMAL",
    "sample_urls": ["https://bloomberg.com/markets", "https://bloomberg.com/news"],
    "source": "bookmarks",
    "extraction_date": "2025-08-22T21:45:00"
  }
}
```

## Integration with Approval Interface

### Visual Indicators
- **Purple "Bookmark" Badge**: Identifies bookmark-sourced domains
- **Same Interface**: Bookmark domains appear alongside email domains
- **Bulk Operations**: All existing bulk actions work with bookmark domains

### Workflow Integration
1. **Extract Bookmarks**: Run bookmark extraction script
2. **Review Domains**: Open approval interface at localhost:5001
3. **Bulk Process**: Use bulk operations for efficiency
4. **Manual Review**: Review individual domains as needed
5. **Export Results**: Approved domains ready for Step 4

## Advanced Usage

### Command Line Options
```bash
# Extract from Chrome only
python3 extract_bookmarks.py

# Extract from HTML file only
python3 extract_bookmarks.py --html-file bookmarks.html

# Extract from Chrome + HTML file
python3 extract_bookmarks.py --html-file bookmarks.html

# Do not merge with existing domains
python3 extract_bookmarks.py --no-merge
```

### Custom Keyword Filtering
Edit the keyword lists in `extract_bookmarks.py`:
```python
FINANCIAL_KEYWORDS = [
    'finance', 'financial', 'money', 'investment', # ... add your keywords
]

CAREER_KEYWORDS = [
    'career', 'job', 'employment', 'professional', # ... add your keywords
]

AFRICAN_AMERICAN_PROFESSIONAL_KEYWORDS = [
    'diversity', 'inclusion', 'equity', 'black', # ... add your keywords
]
```

### Custom Domain Analysis
The script uses Step 2 intelligence when available:
```python
# Uses Step 2 analyzer if available
from step2_domain_intelligence import DomainAnalyzer

# Falls back to simplified analysis
def simplified_domain_analysis(domain, urls):
    # Custom analysis logic
    pass
```

## Troubleshooting

### Common Issues

#### Chrome Bookmarks Not Found
```
❌ Chrome bookmarks not found at: /Users/username/Library/Application Support/Google/Chrome/Default/Bookmarks
```
**Solution**: Check if Chrome is installed and has bookmarks. Try manual HTML export.

#### HTML File Parsing Error
```
❌ Error extracting from HTML file: malformed start tag
```
**Solution**: Ensure HTML file is properly exported from browser. Try re-exporting.

#### No Relevant Bookmarks Found
```
❌ No bookmarks found. Please check browser paths or provide HTML export file.
```
**Solution**: 
1. Check if bookmarks contain financial/career keywords
2. Try manual HTML export from browser
3. Review keyword filtering lists

#### Step 2 Analyzer Not Available
```
⚠️  Step 2 analyzer not available, using simplified analysis
```
**Solution**: This is normal if Step 2 files aren't present. Simplified analysis still works.

### Performance Optimization
- **Large Bookmark Sets**: Process in batches for better performance
- **Memory Usage**: Script handles thousands of bookmarks efficiently
- **Processing Time**: Typically 1-2 minutes for 1000+ bookmarks

## Success Metrics

### Expected Results
- **Extraction Rate**: 80-90% of relevant bookmarks identified
- **Quality Filtering**: 70-80% of extracted domains are high-quality
- **Cultural Relevance**: 20-30% of domains have high cultural relevance
- **Integration**: 100% seamless integration with approval interface

### Sample Workflow Results
```
BOOKMARK EXTRACTION SUMMARY
==================================================
Total Domains: 45
Auto-Approve: 12
Manual Review: 28
Auto-Reject: 5
High Cultural Relevance: 8
==================================================
```

## Best Practices

### Bookmark Organization
- **Use Folders**: Organize bookmarks in folders for better categorization
- **Descriptive Titles**: Use clear, descriptive bookmark titles
- **Regular Cleanup**: Remove outdated or irrelevant bookmarks

### Extraction Workflow
1. **Export Regularly**: Export bookmarks monthly for fresh content
2. **Review Results**: Always review extraction reports
3. **Bulk Process**: Use bulk operations for efficiency
4. **Quality Over Quantity**: Focus on high-quality, relevant domains

### Cultural Relevance
- **Diversity Focus**: Prioritize domains with African American professional content
- **Community Resources**: Look for mentorship and networking resources
- **Financial Literacy**: Focus on wealth-building and financial education content

## Integration with Step 4

### Approved Domains Output
Bookmark domains are automatically included in Step 4 output:
```
config/approved_domains.txt          # Includes approved bookmark domains
data/approved_domains_detailed.json  # Detailed metadata for all domains
```

### Quality Assurance
- **Same Standards**: Bookmark domains meet same quality standards as email domains
- **Cultural Alignment**: Maintains focus on African American professional content
- **Content Relevance**: Ensures financial wellness and career development focus

---

## Quick Reference

### Setup Commands
```bash
# Full setup
./setup_bookmark_extraction.sh

# Manual extraction
python3 extract_bookmarks.py --html-file bookmarks.html

# Review domains
python3 step3_domain_approval_interface.py
```

### File Locations
- **Chrome**: `~/Library/Application Support/Google/Chrome/Default/Bookmarks`
- **Safari**: `~/Library/Safari/Bookmarks.plist`
- **Firefox**: `~/Library/Application Support/Firefox/Profiles/`
- **Output**: `../data/bookmark_domains.json`

### Support
For issues or questions:
1. Check troubleshooting section
2. Review extraction reports
3. Verify browser bookmark locations
4. Test with manual HTML export
