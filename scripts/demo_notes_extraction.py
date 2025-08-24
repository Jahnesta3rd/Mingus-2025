#!/usr/bin/env python3
"""
Demo Apple Notes URL Extraction

This script demonstrates how the Apple Notes extraction would work
with sample data, since we can't access the actual Notes database
due to macOS security permissions.

Author: Mingus Development Team
Date: 2025
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from extract_notes_urls import (
    AppleNotesExtractor, 
    ExtractedNoteURL, 
    NotesDomainAnalysis,
    FINANCIAL_KEYWORDS,
    CAREER_KEYWORDS,
    LIFESTYLE_KEYWORDS
)

def create_demo_data():
    """Create sample data to demonstrate the extraction functionality"""
    
    # Sample extracted URLs
    sample_urls = [
        ExtractedNoteURL(
            url="https://www.investopedia.com/retirement-planning",
            original_url="https://www.investopedia.com/retirement-planning",
            note_title="Retirement Planning Resources",
            note_date="2025-01-15 10:30:00",
            note_id="1",
            surrounding_text="Check out this great resource for retirement planning strategies",
            domain="investopedia.com",
            extraction_confidence=0.9,
            note_quality_score=0.8,
            context_keywords=["retirement", "planning", "financial"]
        ),
        ExtractedNoteURL(
            url="https://www.linkedin.com/learning/financial-literacy",
            original_url="https://www.linkedin.com/learning/financial-literacy",
            note_title="Financial Literacy Course",
            note_date="2025-01-14 15:45:00",
            note_id="2",
            surrounding_text="LinkedIn Learning course on financial literacy for professionals",
            domain="linkedin.com",
            extraction_confidence=0.85,
            note_quality_score=0.7,
            context_keywords=["financial", "literacy", "course", "professional"]
        ),
        ExtractedNoteURL(
            url="https://www.blackenterprise.com/wealth-building",
            original_url="https://www.blackenterprise.com/wealth-building",
            note_title="Wealth Building for Black Professionals",
            note_date="2025-01-13 09:20:00",
            note_id="3",
            surrounding_text="Excellent article on wealth building strategies for African American professionals",
            domain="blackenterprise.com",
            extraction_confidence=0.95,
            note_quality_score=0.9,
            context_keywords=["wealth", "building", "black", "professionals", "african american"]
        ),
        ExtractedNoteURL(
            url="https://www.healthline.com/mental-health/work-life-balance",
            original_url="https://www.healthline.com/mental-health/work-life-balance",
            note_title="Work-Life Balance for Professionals",
            note_date="2025-01-12 14:15:00",
            note_id="4",
            surrounding_text="Important article about maintaining work-life balance and family relationships",
            domain="healthline.com",
            extraction_confidence=0.88,
            note_quality_score=0.75,
            context_keywords=["work", "life", "balance", "family", "relationships", "health"]
        ),
        ExtractedNoteURL(
            url="https://www.faithandfinance.org/investing-with-purpose",
            original_url="https://www.faithandfinance.org/investing-with-purpose",
            note_title="Faith-Based Investment Strategies",
            note_date="2025-01-11 11:30:00",
            note_id="5",
            surrounding_text="Great resource for combining faith values with investment decisions",
            domain="faithandfinance.org",
            extraction_confidence=0.92,
            note_quality_score=0.85,
            context_keywords=["faith", "investment", "values", "purpose", "spirituality"]
        ),
        ExtractedNoteURL(
            url="https://www.parenting.com/financial-planning-for-families",
            original_url="https://www.parenting.com/financial-planning-for-families",
            note_title="Financial Planning for Families with Kids",
            note_date="2025-01-10 16:45:00",
            note_id="6",
            surrounding_text="Essential guide for financial planning when you have children",
            domain="parenting.com",
            extraction_confidence=0.87,
            note_quality_score=0.8,
            context_keywords=["financial", "planning", "family", "kids", "children"]
        )
    ]
    
    return sample_urls

def run_demo():
    """Run the demo extraction with sample data"""
    
    print("🎯 Apple Notes URL Extraction Demo")
    print("=" * 50)
    print()
    
    # Create sample data
    print("📝 Creating sample Notes data...")
    sample_urls = create_demo_data()
    
    # Initialize extractor
    print("🔧 Initializing extractor...")
    extractor = AppleNotesExtractor()
    
    # Analyze domains
    print("🔍 Analyzing domains...")
    domain_analyses = extractor.analyze_domains(sample_urls)
    
    # Save results
    print("💾 Saving results...")
    extractor.save_results(sample_urls, domain_analyses)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 EXTRACTION SUMMARY")
    print("=" * 50)
    print(f"Total URLs extracted: {len(sample_urls)}")
    print(f"Unique domains found: {len(domain_analyses)}")
    print(f"Notes processed: {len(set(url.note_id for url in sample_urls))}")
    
    auto_approve = len([d for d in domain_analyses.values() if d.recommendation == 'AUTO_APPROVE'])
    manual_review = len([d for d in domain_analyses.values() if d.recommendation == 'MANUAL_REVIEW'])
    auto_reject = len([d for d in domain_analyses.values() if d.recommendation == 'AUTO_REJECT'])
    
    print(f"Auto-approve domains: {auto_approve}")
    print(f"Manual review domains: {manual_review}")
    print(f"Auto-reject domains: {auto_reject}")
    
    print("\n" + "=" * 50)
    print("🏆 DOMAIN ANALYSIS RESULTS")
    print("=" * 50)
    
    for domain, analysis in domain_analyses.items():
        print(f"\n🌐 {domain}")
        print(f"   URLs: {analysis.url_count}")
        print(f"   Notes: {analysis.note_count}")
        print(f"   Quality Score: {analysis.avg_note_quality_score:.2f}")
        print(f"   Category: {analysis.category_suggestion}")
        print(f"   Recommendation: {analysis.recommendation}")
        print(f"   Reasoning: {analysis.reasoning}")
        print(f"   Priority: {analysis.priority}")
        print(f"   Sample URLs: {len(analysis.sample_urls)}")
        print(f"   Note Titles: {len(analysis.note_titles)}")
    
    print("\n" + "=" * 50)
    print("📁 OUTPUT FILES CREATED")
    print("=" * 50)
    
    data_dir = Path("../data")
    output_files = [
        "notes_urls_complete.csv",
        "notes_domain_analysis.csv", 
        "notes_recommendations.json",
        "notes_processing_summary.json"
    ]
    
    for filename in output_files:
        file_path = data_dir / filename
        if file_path.exists():
            print(f"✅ {filename}")
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
                print(f"   Rows: {len(df)}")
            elif filename.endswith('.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    print(f"   Keys: {len(data)}")
                else:
                    print(f"   Items: {len(data)}")
        else:
            print(f"❌ {filename} (not found)")
    
    print("\n" + "=" * 50)
    print("🎯 KEYWORD ANALYSIS")
    print("=" * 50)
    
    # Analyze keywords found
    all_keywords = set()
    for url in sample_urls:
        all_keywords.update(url.context_keywords)
    
    print(f"Total unique keywords found: {len(all_keywords)}")
    print(f"Keywords: {', '.join(sorted(all_keywords))}")
    
    # Categorize keywords
    financial_keywords = [kw for kw in all_keywords if kw in FINANCIAL_KEYWORDS]
    career_keywords = [kw for kw in all_keywords if kw in CAREER_KEYWORDS]
    lifestyle_keywords = [kw for kw in all_keywords if kw in LIFESTYLE_KEYWORDS]
    
    print(f"\nFinancial keywords: {len(financial_keywords)} - {', '.join(financial_keywords)}")
    print(f"Career keywords: {len(career_keywords)} - {', '.join(career_keywords)}")
    print(f"Lifestyle keywords: {len(lifestyle_keywords)} - {', '.join(lifestyle_keywords)}")
    
    print("\n" + "=" * 50)
    print("🚀 NEXT STEPS")
    print("=" * 50)
    print("1. To run with real Notes data, grant Full Disk Access permissions")
    print("2. Run: python3 extract_notes_urls.py")
    print("3. Integrate domains: python3 integrate_notes_domains.py")
    print("4. Launch approval interface: python3 step3_domain_approval_interface.py")
    print("\nDemo completed successfully! 🎉")

if __name__ == "__main__":
    run_demo()
