#!/usr/bin/env python3
"""
Generate a detailed categorization report for the enhanced local notes processor.
"""

import json
from pathlib import Path
from enhanced_local_notes_processor import EnhancedLocalNotesProcessor

def generate_categorization_report():
    """Generate a detailed categorization report."""
    
    print("🔍 Generating detailed categorization report...")
    
    # Initialize enhanced processor
    processor = EnhancedLocalNotesProcessor()
    result = processor.process_all_local_notes()
    
    if not result['success']:
        print(f"❌ Processing failed: {result['error_message']}")
        return 1
    
    print(f"✅ Processed {result['total_notes']} notes")
    
    # Generate detailed report
    report = []
    report.append("📊 DETAILED CATEGORIZATION REPORT")
    report.append("=" * 50)
    report.append("")
    
    # Overall statistics
    report.append("📈 OVERALL STATISTICS:")
    report.append(f"   • Total notes processed: {result['total_notes']}")
    report.append(f"   • Notes with Instagram content: {result['notes_with_instagram']}")
    report.append(f"   • Total Instagram URLs found: {result['total_instagram_urls']}")
    report.append("")
    
    # Category breakdown
    report.append("🏷️  CATEGORY BREAKDOWN:")
    total_notes = result['total_notes']
    for category, count in sorted(result['category_breakdown'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_notes * 100) if total_notes > 0 else 0
        report.append(f"   • {category}: {count} notes ({percentage:.1f}%)")
    report.append("")
    
    # Sample notes from each category
    report.append("📝 SAMPLE NOTES BY CATEGORY:")
    report.append("")
    
    # Group notes by category
    notes_by_category = {}
    for note in result['processed_notes']:
        category = note['category']
        if category not in notes_by_category:
            notes_by_category[category] = []
        notes_by_category[category].append(note)
    
    # Show samples from each category
    for category in sorted(notes_by_category.keys()):
        notes = notes_by_category[category]
        report.append(f"   🏷️  {category.upper()} ({len(notes)} notes):")
        
        # Show first 3 notes from this category
        for i, note in enumerate(notes[:3], 1):
            title = note['title'] or 'No title'
            preview = note['content_preview'][:100] + "..." if note['content_preview'] and len(note['content_preview']) > 100 else note['content_preview']
            confidence = note['categorization']['confidence_level']
            keywords = note['categorization']['matched_keywords']
            
            report.append(f"      {i}. {title}")
            if preview:
                report.append(f"         Preview: {preview}")
            report.append(f"         Confidence: {confidence}")
            if keywords:
                report.append(f"         Keywords: {', '.join(keywords[:5])}")
            report.append("")
        
        if len(notes) > 3:
            report.append(f"      ... and {len(notes) - 3} more notes")
        report.append("")
    
    # High confidence categorizations
    report.append("🎯 HIGH CONFIDENCE CATEGORIZATIONS:")
    high_confidence_notes = [
        note for note in result['processed_notes'] 
        if note['categorization']['confidence_level'] in ['high', 'very_high']
    ]
    
    if high_confidence_notes:
        report.append(f"   Found {len(high_confidence_notes)} notes with high confidence categorization:")
        for note in high_confidence_notes[:5]:  # Show first 5
            title = note['title'] or 'No title'
            category = note['category']
            confidence = note['categorization']['confidence_level']
            keywords = note['categorization']['matched_keywords']
            
            report.append(f"   • {title} → {category} ({confidence})")
            if keywords:
                report.append(f"     Keywords: {', '.join(keywords[:3])}")
    else:
        report.append("   No high confidence categorizations found")
    report.append("")
    
    # Save report to file
    report_content = "\n".join(report)
    report_file = Path("categorization_report.txt")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(report_content)
    print(f"\n📄 Detailed report saved to: {report_file.absolute()}")
    
    return 0

if __name__ == "__main__":
    generate_categorization_report()
