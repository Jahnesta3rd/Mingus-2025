#!/usr/bin/env python3
"""
Script for importing completed manual review CSV files.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import LOG_LEVEL, LOG_FORMAT
from manual_review.manual_review_manager import ManualReviewManager


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('instagram_extractor.log')
        ]
    )


def main():
    """Main execution function for importing resolved CSV."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting manual review CSV import")
    logger.info("=" * 60)
    
    try:
        # Get CSV file path from command line argument
        if len(sys.argv) < 2:
            print("Usage: python import_resolved_csv.py <csv_file_path>")
            print("Example: python import_resolved_csv.py extracted_content/manual_review_20241201_143022.csv")
            return 1
        
        csv_filepath = Path(sys.argv[1])
        
        if not csv_filepath.exists():
            print(f"❌ CSV file not found: {csv_filepath}")
            return 1
        
        # Initialize manual review manager
        manual_review_manager = ManualReviewManager()
        
        # Import resolved CSV
        print(f"📥 Importing resolved CSV: {csv_filepath}")
        import_result = manual_review_manager.import_resolved_csv(csv_filepath)
        
        if not import_result['success']:
            print(f"❌ Import failed: {import_result.get('error', 'Unknown error')}")
            return 1
        
        # Display import results
        print(f"\n✅ Import completed successfully!")
        
        # Show statistics
        import_stats = import_result['import_result']['statistics']
        print(f"\n📊 Import Statistics:")
        print(f"   Total items: {import_stats['total_items']}")
        print(f"   Processed items: {import_stats['processed_items']}")
        print(f"   Resolved items: {import_stats['resolved_items']}")
        print(f"   Success rate: {import_stats['success_rate']:.1f}%")
        
        # Show status distribution
        status_dist = import_stats['status_distribution']
        print(f"\n📈 Status Distribution:")
        for status, count in status_dist.items():
            if count > 0:
                percentage = (count / import_stats['total_items'] * 100) if import_stats['total_items'] > 0 else 0
                print(f"   {status.title()}: {count} ({percentage:.1f}%)")
        
        # Show quality metrics
        quality_results = import_result['quality_results']
        print(f"\n🔍 Quality Control Results:")
        print(f"   Valid URLs: {quality_results['valid_urls']}")
        print(f"   Invalid URLs: {quality_results['invalid_urls']}")
        print(f"   Quality Score: {quality_results['quality_score']:.1%}")
        
        if quality_results['duplicate_detection']['total_duplicate_urls'] > 0:
            print(f"   Duplicate URLs: {quality_results['duplicate_detection']['total_duplicate_urls']}")
        
        if quality_results['duplicate_detection']['total_duplicate_content_ids'] > 0:
            print(f"   Duplicate Content IDs: {quality_results['duplicate_detection']['total_duplicate_content_ids']}")
        
        # Show quality issues
        quality_issues = quality_results['quality_issues']
        if quality_issues:
            print(f"\n⚠️  Quality Issues ({len(quality_issues)} found):")
            
            # Group by severity
            by_severity = {}
            for issue in quality_issues:
                severity = issue['severity']
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(issue)
            
            for severity in ['error', 'warning', 'info']:
                if severity in by_severity:
                    issues = by_severity[severity]
                    print(f"\n   {severity.upper()} ({len(issues)} issues):")
                    for issue in issues[:5]:  # Show first 5
                        print(f"     • {issue['message']} (Note ID: {issue['note_id']})")
                    if len(issues) > 5:
                        print(f"     ... and {len(issues) - 5} more")
        
        # Show progress information
        progress_summary = manual_review_manager.get_progress_summary()
        if 'error' not in progress_summary:
            print(f"\n📈 Progress Summary:")
            print(f"   Completion: {progress_summary['completion_percentage']:.1f}%")
            print(f"   Pending items: {progress_summary['pending_items']}")
            
            if progress_summary['time_info']['elapsed_minutes'] > 0:
                print(f"   Elapsed time: {progress_summary['time_info']['elapsed_minutes']:.1f} minutes")
                print(f"   Average per item: {progress_summary['time_info']['average_time_per_item']:.1f} minutes")
        
        # Show output files
        print(f"\n📄 Output Files:")
        print(f"   Processed results: {import_result['import_result']['output_file']}")
        print(f"   Quality report: {import_result['quality_report_file']}")
        
        # Show next steps
        print(f"\n💡 Next Steps:")
        print(f"   1. Review the quality report for any issues")
        print(f"   2. Check the processed results file")
        print(f"   3. If satisfied, you can merge with direct URLs")
        print(f"   4. Use the combined results for further processing")
        
        logger.info("Manual review CSV import completed successfully")
        print(f"\n🎉 Import completed successfully!")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Import interrupted by user")
        print(f"\n⚠️  Import interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Unexpected error during import: {e}")
        print(f"\n❌ Unexpected error: {e}")
        print(f"   Please check the log file for more details")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
