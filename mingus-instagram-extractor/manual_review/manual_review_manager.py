"""
Main manager for the manual review system.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .csv_generator import ManualReviewCSVGenerator
from .search_suggestions import SearchSuggestionGenerator
from .resolution_workflow import ResolutionWorkflow
from .quality_control import QualityController
from .user_guidance import UserGuidance
from .progress_tracking import ProgressTracker

logger = logging.getLogger(__name__)


class ManualReviewManager:
    """Main manager for the manual review system."""
    
    def __init__(self, output_dir: Path = Path("extracted_content")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.csv_generator = ManualReviewCSVGenerator(output_dir)
        self.search_suggestions = SearchSuggestionGenerator()
        self.resolution_workflow = ResolutionWorkflow(output_dir)
        self.quality_controller = QualityController()
        self.user_guidance = UserGuidance()
        self.progress_tracker = ProgressTracker(output_dir)
    
    def generate_manual_review_csv(self, analyzed_notes: List[Dict[str, Any]], 
                                 filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate CSV file for manual review with enhanced search suggestions.
        
        Args:
            analyzed_notes: List of analyzed notes from extraction pipeline
            filename: Optional custom filename for CSV
            
        Returns:
            Dictionary with generation results and statistics
        """
        logger.info("Generating manual review CSV with enhanced search suggestions")
        
        # Generate statistics
        review_stats = self.csv_generator.get_review_statistics(analyzed_notes)
        
        # Generate CSV
        csv_filepath = self.csv_generator.generate_manual_review_csv(analyzed_notes, filename)
        
        # Initialize progress tracking
        progress_data = self.progress_tracker.initialize_progress(
            review_stats['notes_needing_manual_review'], 
            csv_filepath
        )
        
        # Generate user guidance
        instructions = self.user_guidance.generate_instructions(review_stats)
        quick_reference = self.user_guidance.generate_quick_reference()
        
        # Save instructions to file
        instructions_file = self.output_dir / "manual_review_instructions.txt"
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        quick_ref_file = self.output_dir / "quick_reference.txt"
        with open(quick_ref_file, 'w', encoding='utf-8') as f:
            f.write(quick_reference)
        
        logger.info(f"Manual review CSV generated: {csv_filepath}")
        logger.info(f"Instructions saved: {instructions_file}")
        logger.info(f"Quick reference saved: {quick_ref_file}")
        
        return {
            'success': True,
            'csv_filepath': csv_filepath,
            'instructions_file': instructions_file,
            'quick_reference_file': quick_ref_file,
            'statistics': review_stats,
            'progress_data': progress_data
        }
    
    def import_resolved_csv(self, csv_filepath: Path) -> Dict[str, Any]:
        """
        Import and process a completed manual review CSV.
        
        Args:
            csv_filepath: Path to the completed CSV file
            
        Returns:
            Dictionary with import results and statistics
        """
        logger.info(f"Importing resolved CSV: {csv_filepath}")
        
        # Import resolved items
        import_result = self.resolution_workflow.import_resolved_csv(csv_filepath)
        
        if not import_result['success']:
            return import_result
        
        # Update progress tracking
        progress_data = self.progress_tracker.update_progress(import_result['processed_items'])
        
        # Perform quality control
        quality_results = self.quality_controller.validate_resolved_urls(import_result['processed_items'])
        
        # Update quality metrics in progress
        self.progress_tracker.update_quality_metrics(quality_results)
        
        # Generate quality report
        quality_report = self.quality_controller.generate_quality_report(quality_results)
        quality_report_file = self.output_dir / "quality_report.txt"
        with open(quality_report_file, 'w', encoding='utf-8') as f:
            f.write(quality_report)
        
        logger.info(f"Resolved CSV imported successfully")
        logger.info(f"Quality report saved: {quality_report_file}")
        
        return {
            'success': True,
            'import_result': import_result,
            'quality_results': quality_results,
            'quality_report_file': quality_report_file,
            'progress_data': progress_data
        }
    
    def merge_with_direct_urls(self, resolved_items: List[Dict[str, Any]], 
                             direct_url_notes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge resolved manual review items with direct URL notes.
        
        Args:
            resolved_items: List of resolved items from manual review
            direct_url_notes: List of notes with direct Instagram URLs
            
        Returns:
            Dictionary with merge results and statistics
        """
        logger.info("Merging resolved items with direct URL notes")
        
        # Merge items
        combined_items = self.resolution_workflow.merge_with_direct_urls(resolved_items, direct_url_notes)
        
        # Generate merge report
        merge_report = self.resolution_workflow.generate_merge_report(combined_items)
        
        # Save combined results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_file = self.output_dir / f"combined_instagram_content_{timestamp}.json"
        
        import json
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump({
                'merge_info': merge_report,
                'combined_items': combined_items
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Combined {len(combined_items)} Instagram content items")
        logger.info(f"Combined results saved: {combined_file}")
        
        return {
            'success': True,
            'combined_items': combined_items,
            'merge_report': merge_report,
            'output_file': combined_file
        }
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary."""
        return self.progress_tracker.get_progress_summary()
    
    def generate_progress_report(self) -> str:
        """Generate human-readable progress report."""
        return self.progress_tracker.generate_progress_report()
    
    def get_completion_estimate(self) -> Dict[str, Any]:
        """Get completion time estimate."""
        return self.progress_tracker.get_completion_estimate()
    
    def export_progress_data(self, output_filepath: Optional[Path] = None) -> Path:
        """Export progress data to JSON file."""
        return self.progress_tracker.export_progress_data(output_filepath)
    
    def reset_progress(self) -> None:
        """Reset progress tracking."""
        self.progress_tracker.reset_progress()
        logger.info("Progress tracking reset")
    
    def generate_enhanced_search_suggestions(self, note_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Generate enhanced search suggestions for a specific note.
        
        Args:
            note_data: Note data with Instagram content metadata
            
        Returns:
            Dictionary with comprehensive search suggestions
        """
        return self.search_suggestions.generate_comprehensive_suggestions(note_data)
    
    def validate_single_url(self, url: str, original_text: str = "", account_name: str = "") -> Dict[str, Any]:
        """
        Validate a single Instagram URL.
        
        Args:
            url: URL to validate
            original_text: Original text for context
            account_name: Account name for context
            
        Returns:
            Validation result dictionary
        """
        # Create a mock item for validation
        mock_item = {
            'resolved_url': url,
            'original_text': original_text,
            'account_name': account_name,
            'note_id': 'validation_test'
        }
        
        return self.quality_controller._validate_single_url(mock_item)
    
    def get_user_guidance(self, review_statistics: Optional[Dict[str, Any]] = None) -> str:
        """
        Get user guidance and instructions.
        
        Args:
            review_statistics: Optional statistics for personalized guidance
            
        Returns:
            Formatted instructions string
        """
        if not review_statistics:
            # Generate default statistics
            review_statistics = {
                'notes_needing_manual_review': 0,
                'estimated_review_time_minutes': 0
            }
        
        return self.user_guidance.generate_instructions(review_statistics)
    
    def get_quick_reference(self) -> str:
        """Get quick reference card."""
        return self.user_guidance.generate_quick_reference()
    
    def get_example_resolutions(self) -> List[Dict[str, str]]:
        """Get example resolutions for common scenarios."""
        return self.user_guidance.generate_example_resolutions()
    
    def generate_comprehensive_report(self, analyzed_notes: List[Dict[str, Any]], 
                                    resolved_items: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Generate a comprehensive report of the entire manual review process.
        
        Args:
            analyzed_notes: Original analyzed notes
            resolved_items: Optional resolved items from manual review
            
        Returns:
            Comprehensive report string
        """
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE MANUAL REVIEW REPORT")
        report.append("=" * 80)
        
        # Original extraction statistics
        from processors.content_analyzer import ContentAnalyzer
        content_analyzer = ContentAnalyzer()
        instagram_summary = content_analyzer.get_instagram_summary(analyzed_notes)
        
        report.append(f"\nORIGINAL EXTRACTION STATISTICS:")
        report.append(f"  Total notes: {instagram_summary['total_notes']}")
        report.append(f"  Instagram-related notes: {instagram_summary['notes_with_instagram']}")
        report.append(f"  Direct Instagram URLs: {instagram_summary['total_instagram_urls']}")
        report.append(f"  Instagram percentage: {instagram_summary['instagram_percentage']:.1f}%")
        
        # Manual review statistics
        review_stats = self.csv_generator.get_review_statistics(analyzed_notes)
        report.append(f"\nMANUAL REVIEW STATISTICS:")
        report.append(f"  Notes needing manual review: {review_stats['notes_needing_manual_review']}")
        report.append(f"  Estimated review time: {review_stats['estimated_review_time_minutes']:.0f} minutes")
        report.append(f"  Items with accounts: {review_stats['items_with_accounts']}")
        report.append(f"  Items with hashtags: {review_stats['items_with_hashtags']}")
        report.append(f"  Items with mentions: {review_stats['items_with_mentions']}")
        
        # Progress information
        progress_summary = self.get_progress_summary()
        if 'error' not in progress_summary:
            report.append(f"\nPROGRESS INFORMATION:")
            report.append(f"  Completion: {progress_summary['completion_percentage']:.1f}%")
            report.append(f"  Resolved items: {progress_summary['status_breakdown']['resolved']}")
            report.append(f"  Pending items: {progress_summary['status_breakdown']['pending']}")
            
            if progress_summary['quality_metrics']:
                quality = progress_summary['quality_metrics']
                report.append(f"  Quality score: {quality.get('quality_score', 0):.1%}")
                report.append(f"  Valid URLs: {quality.get('valid_urls', 0)}")
                report.append(f"  Invalid URLs: {quality.get('invalid_urls', 0)}")
        
        # Resolved items analysis
        if resolved_items:
            report.append(f"\nRESOLVED ITEMS ANALYSIS:")
            report.append(f"  Total resolved items: {len(resolved_items)}")
            
            # Count by status
            status_counts = {}
            for item in resolved_items:
                status = item.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                report.append(f"  {status.title()}: {count}")
        
        # Recommendations
        if resolved_items:
            total_resolved = len([item for item in resolved_items if item.get('status') == 'resolved'])
            resolution_rate = (total_resolved / len(resolved_items) * 100) if resolved_items else 0
            
            report.append(f"\nRECOMMENDATIONS:")
            if resolution_rate < 50:
                report.append(f"  • Resolution rate is {resolution_rate:.1f}% - consider improving search strategies")
            elif resolution_rate > 80:
                report.append(f"  • Excellent resolution rate of {resolution_rate:.1f}%!")
            
            if progress_summary.get('status_breakdown', {}).get('pending', 0) > 0:
                report.append(f"  • {progress_summary['status_breakdown']['pending']} items still pending review")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
