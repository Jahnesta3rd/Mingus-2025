# Step 2: Domain Intelligence Analysis

## Overview

This script performs comprehensive domain intelligence analysis on the 672 domains extracted from Step 1. It provides intelligent recommendations for the Step 3 domain approval interface, with special focus on cultural relevance for African American professionals aged 25-35 earning $40K-$100K.

**Target Audience**: African American professionals aged 25-35 earning $40K-$100K

## Features

### Domain Quality Assessment
- ✅ Content quality scoring based on URL patterns and structure
- ✅ Educational vs commercial content detection
- ✅ Article vs product page identification
- ✅ Content freshness indicators from URL patterns
- ✅ Domain authority estimation using heuristics

### Cultural Relevance Engine
- ✅ Scan domain names and sample URLs for cultural keywords
- ✅ Identify African American professional development content
- ✅ Detect career advancement and financial empowerment themes
- ✅ Score cultural appropriateness and community relevance
- ✅ Flag diversity/inclusion and systemic barrier discussions

### Smart Categorization
**HIGH VALUE - Automatic Approval Candidates:**
- Clear financial education sites (budgeting, investing, career)
- Reputable news sources with financial sections
- Educational institutions and research
- Professional development and career advancement
- Cultural and community-focused financial content

**MEDIUM VALUE - Manual Review Required:**
- Mixed content domains (some good, some commercial)
- Unknown but potentially valuable sources
- Domains with moderate cultural relevance
- New or emerging financial education platforms

**LOW VALUE - Automatic Rejection Candidates:**
- Pure e-commerce and product sales
- Affiliate marketing and referral sites
- Social media and entertainment platforms
- Technical infrastructure (schema.org, tracking domains)
- Spam or suspicious link patterns

**SUSPICIOUS - Security Review:**
- Excessive tracking parameters
- Shortened URLs from unknown sources
- Domains with random character patterns
- High commercial/affiliate content ratio

### Recommendation Engine
- ✅ Intelligent pre-filtering with confidence scoring
- ✅ Auto-approve obvious high-value financial education domains
- ✅ Auto-reject clear commercial/technical domains
- ✅ Flag cultural relevance matches for priority review
- ✅ Identify potential gems in unknown domains

### Bulk Action Suggestions
- ✅ "Approve all educational institutions" recommendations
- ✅ "Reject all tracking/technical domains" suggestions
- ✅ "Review all financial education candidates" priorities
- ✅ "Prioritize cultural relevance matches" highlighting

### Visualization & Reporting
- ✅ Interactive HTML dashboard with comprehensive analytics
- ✅ Domain distribution pie charts (by category)
- ✅ Quality vs relevance scatter plots
- ✅ Top domains bar charts with sample URLs
- ✅ Cultural relevance heat maps
- ✅ Timeline analysis of domain discovery

## Prerequisites

### 1. Step 1 Completion
Ensure Step 1 has been completed successfully and generated:
- `data/raw_urls_complete.csv` (2,754 URLs with metadata)
- `data/domain_analysis_report.csv` (672 unique domains)
- `data/email_processing_summary.json` (processing statistics)

### 2. Python Environment
Ensure you have Python 3.7+ installed:
```bash
python3 --version
```

### 3. Install Dependencies
```bash
cd scripts
pip install -r requirements_step2.txt
```

## Usage

### Basic Usage
```bash
python scripts/step2_domain_intelligence.py
```

### Example Output
```
2025-01-15 10:30:15 - INFO - Loading Step 1 data files...
2025-01-15 10:30:16 - INFO - Loaded 672 domains and 2754 URLs
2025-01-15 10:30:16 - INFO - Starting comprehensive domain analysis...
2025-01-15 10:30:45 - INFO - Generating bulk action recommendations...
2025-01-15 10:30:46 - INFO - Creating visualizations...
2025-01-15 10:30:47 - INFO - Generating HTML dashboard...
2025-01-15 10:30:48 - INFO - Exporting analysis results...
2025-01-15 10:30:49 - INFO - Step 2 analysis completed successfully!

================================================================================
🎯 MINGUS DOMAIN INTELLIGENCE ANALYSIS - STEP 2 COMPLETE
================================================================================

📊 ANALYSIS SUMMARY:
   Total domains analyzed: 672
   Auto-approve candidates: 156 (23.2%)
   Auto-reject candidates: 298 (44.3%)
   Manual review required: 218 (32.4%)
   High cultural relevance: 23 (3.4%)

🌟 TOP CULTURALLY RELEVANT DOMAINS:
    1. humbledollar.com                    (Score: 0.245, URLs: 114)
    2. blackenterprise.com                 (Score: 0.198, URLs: 45)
    3. theroot.com                        (Score: 0.187, URLs: 38)
    4. essence.com                        (Score: 0.156, URLs: 32)
    5. ebony.com                          (Score: 0.134, URLs: 28)

⚡ BULK ACTION RECOMMENDATIONS:
   • Approve all high-quality educational domains: 156 domains (Confidence: 85.0%)
   • Reject all low-quality commercial domains: 298 domains (Confidence: 90.0%)
   • Prioritize review of culturally relevant domains: 23 domains (Confidence: 75.0%)
   • Manual review of remaining domains: 218 domains (Confidence: 60.0%)

📈 EFFICIENCY METRICS:
   Estimated articles after filtering: 1,847
   Processing efficiency: 23.2% auto-approve, 44.3% auto-reject
   Manual review burden: 218 domains (32.4%)

📁 OUTPUT FILES GENERATED:
   • reports/domain_intelligence_dashboard.html - Interactive dashboard
   • data/domain_recommendations.json - Structured recommendations
   • data/high_value_domains.csv - Auto-approval candidates
   • data/medium_value_domains.csv - Manual review queue
   • data/low_value_domains.csv - Auto-rejection candidates
   • data/cultural_relevance_analysis.json - Cultural scoring
   • data/bulk_action_suggestions.json - Bulk operations
   • data/step2_intelligence_summary.json - Complete statistics

🚀 READY FOR STEP 3: DOMAIN APPROVAL INTERFACE
================================================================================
```

## Output Files

The script creates the following files:

### 1. `reports/domain_intelligence_dashboard.html`
Interactive HTML dashboard with:
- Domain distribution statistics
- Quality vs cultural relevance scatter plots
- Top domains analysis table
- Bulk action recommendations
- Visual charts and graphs

### 2. `data/domain_recommendations.json`
Structured recommendations for all domains:
```json
{
  "humbledollar.com": {
    "recommendation": "AUTO_APPROVE",
    "confidence": 0.92,
    "reasoning": "High-quality domain with cultural relevance",
    "quality_score": 0.78,
    "cultural_relevance_score": 0.245,
    "url_count": 114,
    "priority": "HIGH"
  }
}
```

### 3. `data/high_value_domains.csv`
Auto-approval candidates with reasoning:
- Domain name
- URL count
- Quality score
- Cultural relevance score
- Confidence level
- Reasoning
- Sample URLs

### 4. `data/medium_value_domains.csv`
Manual review queue with sample URLs:
- Domain name
- URL count
- Quality score
- Cultural relevance score
- Confidence level
- Reasoning
- Priority level
- Sample URLs

### 5. `data/low_value_domains.csv`
Auto-rejection candidates with reasons:
- Domain name
- URL count
- Quality score
- Cultural relevance score
- Confidence level
- Reasoning
- Sample URLs

### 6. `data/cultural_relevance_analysis.json`
Cultural scoring and insights:
```json
{
  "summary": {
    "high_relevance_count": 23,
    "medium_relevance_count": 67,
    "low_relevance_count": 582
  },
  "high_relevance_domains": [
    {
      "domain": "humbledollar.com",
      "cultural_relevance_score": 0.245,
      "category_scores": {
        "identity": 3,
        "career": 2,
        "financial": 4,
        "challenges": 1
      },
      "url_count": 114
    }
  ]
}
```

### 7. `data/bulk_action_suggestions.json`
Recommended bulk operations:
```json
{
  "auto_approve_all_high_quality": {
    "action": "Approve all high-quality educational domains",
    "domains": ["humbledollar.com", "blackenterprise.com"],
    "count": 156,
    "confidence": 0.85,
    "description": "Automatically approve 156 high-quality domains"
  }
}
```

### 8. `data/step2_intelligence_summary.json`
Complete analysis statistics:
```json
{
  "analysis_timestamp": "2025-01-15T10:30:49",
  "total_domains_analyzed": 672,
  "recommendation_breakdown": {
    "auto_approve": 156,
    "auto_reject": 298,
    "manual_review": 218
  },
  "cultural_relevance_breakdown": {
    "high_relevance": 23,
    "medium_relevance": 67,
    "low_relevance": 582
  },
  "estimated_articles_after_filtering": 1847,
  "processing_efficiency": {
    "auto_approve_percentage": 23.2,
    "auto_reject_percentage": 44.3,
    "manual_review_percentage": 32.4
  }
}
```

## Cultural Relevance Keywords

The script analyzes domains for cultural relevance using these keyword categories:

### Identity Keywords
- "black", "african american", "african-american", "black professionals"
- "black entrepreneurs", "black business", "black community"
- "diversity", "inclusion", "representation", "equity"

### Career Keywords
- "corporate culture", "workplace navigation", "career advancement"
- "professional development", "leadership", "executive"
- "corporate ladder", "glass ceiling", "workplace discrimination"
- "salary negotiation", "income optimization"

### Financial Keywords
- "generational wealth", "community investment", "financial equity"
- "systemic barriers", "wealth gap", "financial literacy"
- "student loan debt", "credit repair", "homeownership"
- "investment strategies", "retirement planning"

### Challenge Keywords
- "systemic racism", "discrimination", "bias", "barriers"
- "inequality", "disparities", "access", "opportunity"
- "representation", "inclusion", "diversity"

## Quality Assessment Criteria

### High Value Indicators
- "financial", "education", "career", "professional", "business"
- "investment", "wealth", "money", "finance", "economics"
- "news", "media", "journalism", "research", "university"
- "college", "institute", "foundation", "organization"

### Medium Value Indicators
- "blog", "article", "guide", "tips", "advice", "strategy"
- "platform", "community", "network", "forum", "discussion"

### Low Value Indicators
- "shop", "store", "buy", "sale", "deal", "discount", "offer"
- "product", "service", "affiliate", "referral", "tracking"
- "analytics", "pixel", "beacon", "cookie", "advertisement"

### Suspicious Indicators
- "bit.ly", "tinyurl", "goo.gl", "t.co", "shortened"
- "track", "pixel", "beacon", "analytics", "monitoring"
- "random", "gibberish", "suspicious"

## URL Pattern Analysis

The script analyzes URL patterns to identify content types:

### Article Patterns
- `/article/`, `/post/`, `/blog/`, `/story/`, `/news/`
- `/analysis/`, `/opinion/`, `/commentary/`, `/feature/`
- `/\d{4}/\d{2}/`, `/\d{4}-\d{2}-\d{2}/`, `/page/\d+/`

### Product Patterns
- `/product/`, `/shop/`, `/store/`, `/buy/`, `/purchase/`
- `/cart/`, `/checkout/`, `/order/`, `/price/`, `/sale/`
- `/deal/`, `/offer/`, `/discount/`

### Tracking Patterns
- `utm_source=`, `utm_medium=`, `utm_campaign=`, `utm_term=`
- `utm_content=`, `gclid=`, `fbclid=`, `msclkid=`
- `track/`, `pixel/`, `beacon/`, `analytics/`

### Newsletter Patterns
- `/newsletter/`, `/email/`, `/subscribe/`, `/signup/`
- `/optin/`, `/lead/`, `/capture/`, `/form/`

## Recommendation Logic

### Auto-Approve Conditions
1. High quality score (≥0.6) AND high/medium cultural relevance
2. High quality score (≥0.6) with educational/financial content
3. High cultural relevance with acceptable quality

### Auto-Reject Conditions
1. Suspicious domain with tracking/security concerns
2. Low quality score (≤-0.2) with commercial content
3. Excessive tracking parameters or shortened URLs

### Manual Review Conditions
1. Medium quality with unknown cultural relevance
2. High cultural relevance requiring quality verification
3. Mixed indicators requiring human assessment

## Performance Optimization

### Processing Efficiency
- **Small dataset (100 domains)**: 30-60 seconds
- **Medium dataset (500 domains)**: 2-5 minutes
- **Large dataset (1000+ domains)**: 10-30 minutes

### Memory Management
- Efficient data structures for large domain sets
- Streaming analysis for memory-constrained environments
- Caching of analysis results for repeated runs

## Troubleshooting

### Common Issues

#### 1. Missing Step 1 Data
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw_urls_complete.csv'
```

**Solution**: 
- Ensure Step 1 has been completed successfully
- Verify all required files exist in the `data/` directory
- Check file permissions and paths

#### 2. Visualization Errors
```
ImportError: No module named 'matplotlib'
```

**Solution**:
- Install required dependencies: `pip install -r requirements_step2.txt`
- Ensure matplotlib and seaborn are properly installed
- Check Python environment and virtual environment

#### 3. Memory Issues
```
MemoryError: Unable to allocate array
```

**Solution**:
- Process domains in smaller batches
- Reduce sample URL count for analysis
- Increase system memory or use cloud processing

#### 4. Cultural Relevance Scoring Issues
```
ZeroDivisionError: division by zero
```

**Solution**:
- Check cultural keyword definitions
- Verify domain data integrity
- Review scoring algorithm parameters

### Debug Mode

For detailed debugging, modify the logging level:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    # ... rest of configuration
)
```

## Integration with Step 3

This script prepares data for Step 3: Domain Approval Interface by providing:

1. **Structured Recommendations**: JSON format with confidence scores
2. **Bulk Action Suggestions**: Efficient processing recommendations
3. **Cultural Relevance Analysis**: Prioritized review queue
4. **Quality Assessment**: Automated filtering criteria
5. **Sample URLs**: Preview content for manual review
6. **Interactive Dashboard**: Visual analysis and reporting

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the detailed log file: `logs/step2_intelligence.log`
3. Verify Step 1 data files are complete and valid
4. Ensure all dependencies are installed correctly
5. Check system resources and memory availability

## Next Steps

After successful analysis:

1. Review `reports/domain_intelligence_dashboard.html` for visual insights
2. Examine `data/domain_recommendations.json` for structured recommendations
3. Use `data/bulk_action_suggestions.json` for efficient processing
4. Prioritize `data/cultural_relevance_analysis.json` for cultural content
5. Proceed to Step 3: Domain Approval Interface
6. Use the exported data for automated and manual review processes

## Cultural Context

This analysis is specifically designed for the Mingus target audience:

### African American Professional Challenges
- Student loan debt and credit repair content
- Corporate career navigation and advancement
- Salary negotiation and income optimization
- Entrepreneurship and side hustle development
- Generational wealth building strategies
- Financial stress and mental health connections

### Income Range Considerations ($40K-$100K)
- Early career financial planning content
- Mid-level professional development resources
- Income scaling and optimization strategies
- Investment approaches for growing incomes
- Lifestyle inflation management

### Cultural Context Keywords
- "Black professionals", "African American", "diversity", "inclusion"
- "Corporate culture", "workplace navigation", "career advancement"
- "Generational wealth", "community investment", "financial equity"
- "Systemic barriers", "professional development", "leadership"
