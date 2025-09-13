"""
Progress tracking and statistics generation for manual review process.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Tracks progress and generates statistics for manual review process."""
    
    def __init__(self, output_dir: Path = Path("extracted_content")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.progress_file = self.output_dir / "manual_review_progress.json"
    
    def initialize_progress(self, total_items: int, csv_filepath: Path) -> Dict[str, Any]:
        """
        Initialize progress tracking for a new manual review session.
        
        Args:
            total_items: Total number of items to review
            csv_filepath: Path to the CSV file being reviewed
            
        Returns:
            Initial progress data
        """
        progress_data = {
            'session_id': self._generate_session_id(),
            'start_time': datetime.now().isoformat(),
            'csv_filepath': str(csv_filepath),
            'total_items': total_items,
            'completed_items': 0,
            'pending_items': total_items,
            'resolved_items': 0,
            'not_found_items': 0,
            'unresolvable_items': 0,
            'invalid_url_items': 0,
            'status_distribution': {
                'resolved': 0,
                'not_found': 0,
                'unresolvable': 0,
                'invalid_url': 0,
                'pending': total_items
            },
            'category_distribution': {},
            'quality_metrics': {
                'valid_urls': 0,
                'invalid_urls': 0,
                'quality_score': 0.0,
                'duplicate_urls': 0,
                'duplicate_content_ids': 0
            },
            'time_estimates': {
                'estimated_total_minutes': total_items * 2.5,
                'estimated_remaining_minutes': total_items * 2.5,
                'average_time_per_item': 2.5
            },
            'last_updated': datetime.now().isoformat()
        }
        
        self._save_progress(progress_data)
        logger.info(f"Initialized progress tracking for {total_items} items")
        
        return progress_data
    
    def update_progress(self, resolved_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update progress based on resolved items.
        
        Args:
            resolved_items: List of resolved items from CSV import
            
        Returns:
            Updated progress data
        """
        # Load current progress
        progress_data = self._load_progress()
        if not progress_data:
            logger.warning("No progress data found, initializing new session")
            return self.initialize_progress(len(resolved_items), Path("unknown"))
        
        # Update counts
        total_items = progress_data['total_items']
        completed_items = len([item for item in resolved_items if item.get('status') != 'pending'])
        pending_items = total_items - completed_items
        
        # Count by status
        status_counts = {
            'resolved': 0,
            'not_found': 0,
            'unresolvable': 0,
            'invalid_url': 0,
            'pending': pending_items
        }
        
        for item in resolved_items:
            status = item.get('status', 'pending')
            if status in status_counts:
                status_counts[status] += 1
        
        # Count by category
        category_counts = {}
        for item in resolved_items:
            category = item.get('category', 'uncategorized')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Update progress data
        progress_data.update({
            'completed_items': completed_items,
            'pending_items': pending_items,
            'resolved_items': status_counts['resolved'],
            'not_found_items': status_counts['not_found'],
            'unresolvable_items': status_counts['unresolvable'],
            'invalid_url_items': status_counts['invalid_url'],
            'status_distribution': status_counts,
            'category_distribution': category_counts,
            'last_updated': datetime.now().isoformat()
        })
        
        # Update time estimates
        if completed_items > 0:
            elapsed_time = self._calculate_elapsed_time(progress_data['start_time'])
            average_time_per_item = elapsed_time / completed_items
            estimated_remaining = pending_items * average_time_per_item
            
            progress_data['time_estimates'].update({
                'elapsed_minutes': elapsed_time,
                'average_time_per_item': average_time_per_item,
                'estimated_remaining_minutes': estimated_remaining
            })
        
        self._save_progress(progress_data)
        logger.info(f"Updated progress: {completed_items}/{total_items} completed")
        
        return progress_data
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of current progress."""
        progress_data = self._load_progress()
        if not progress_data:
            return {'error': 'No progress data found'}
        
        total_items = progress_data['total_items']
        completed_items = progress_data['completed_items']
        pending_items = progress_data['pending_items']
        
        # Calculate percentages
        completion_percentage = (completed_items / total_items * 100) if total_items > 0 else 0
        resolution_percentage = (progress_data['resolved_items'] / total_items * 100) if total_items > 0 else 0
        
        # Calculate time estimates
        time_estimates = progress_data.get('time_estimates', {})
        elapsed_minutes = time_estimates.get('elapsed_minutes', 0)
        estimated_remaining = time_estimates.get('estimated_remaining_minutes', 0)
        
        return {
            'session_id': progress_data.get('session_id', 'unknown'),
            'total_items': total_items,
            'completed_items': completed_items,
            'pending_items': pending_items,
            'completion_percentage': round(completion_percentage, 1),
            'resolution_percentage': round(resolution_percentage, 1),
            'status_breakdown': progress_data['status_distribution'],
            'category_breakdown': progress_data['category_distribution'],
            'time_info': {
                'elapsed_minutes': round(elapsed_minutes, 1),
                'estimated_remaining_minutes': round(estimated_remaining, 1),
                'average_time_per_item': round(time_estimates.get('average_time_per_item', 2.5), 1)
            },
            'quality_metrics': progress_data.get('quality_metrics', {}),
            'last_updated': progress_data.get('last_updated', 'unknown')
        }
    
    def generate_progress_report(self) -> str:
        """Generate a human-readable progress report."""
        summary = self.get_progress_summary()
        if 'error' in summary:
            return f"Error: {summary['error']}"
        
        report = []
        report.append("=" * 60)
        report.append("MANUAL REVIEW PROGRESS REPORT")
        report.append("=" * 60)
        
        # Basic progress
        report.append(f"\nPROGRESS OVERVIEW:")
        report.append(f"  Total items: {summary['total_items']}")
        report.append(f"  Completed: {summary['completed_items']} ({summary['completion_percentage']}%)")
        report.append(f"  Pending: {summary['pending_items']}")
        report.append(f"  Resolution rate: {summary['resolution_percentage']}%")
        
        # Status breakdown
        status_breakdown = summary['status_breakdown']
        report.append(f"\nSTATUS BREAKDOWN:")
        for status, count in status_breakdown.items():
            if count > 0:
                percentage = (count / summary['total_items'] * 100) if summary['total_items'] > 0 else 0
                report.append(f"  {status.title()}: {count} ({percentage:.1f}%)")
        
        # Category breakdown
        category_breakdown = summary['category_breakdown']
        if category_breakdown:
            report.append(f"\nCATEGORY BREAKDOWN:")
            for category, count in category_breakdown.items():
                if count > 0:
                    percentage = (count / summary['total_items'] * 100) if summary['total_items'] > 0 else 0
                    report.append(f"  {category.title()}: {count} ({percentage:.1f}%)")
        
        # Time information
        time_info = summary['time_info']
        report.append(f"\nTIME INFORMATION:")
        report.append(f"  Elapsed time: {time_info['elapsed_minutes']:.1f} minutes")
        report.append(f"  Estimated remaining: {time_info['estimated_remaining_minutes']:.1f} minutes")
        report.append(f"  Average per item: {time_info['average_time_per_item']:.1f} minutes")
        
        # Quality metrics
        quality_metrics = summary['quality_metrics']
        if quality_metrics:
            report.append(f"\nQUALITY METRICS:")
            report.append(f"  Valid URLs: {quality_metrics.get('valid_urls', 0)}")
            report.append(f"  Invalid URLs: {quality_metrics.get('invalid_urls', 0)}")
            report.append(f"  Quality score: {quality_metrics.get('quality_score', 0):.1%}")
            if quality_metrics.get('duplicate_urls', 0) > 0:
                report.append(f"  Duplicate URLs: {quality_metrics['duplicate_urls']}")
            if quality_metrics.get('duplicate_content_ids', 0) > 0:
                report.append(f"  Duplicate content IDs: {quality_metrics['duplicate_content_ids']}")
        
        # Recommendations
        report.extend(self._generate_recommendations(summary))
        
        report.append(f"\nLast updated: {summary['last_updated']}")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on current progress."""
        recommendations = []
        
        completion_percentage = summary['completion_percentage']
        resolution_percentage = summary['resolution_percentage']
        pending_items = summary['pending_items']
        
        if completion_percentage < 25:
            recommendations.append(f"\nRECOMMENDATIONS:")
            recommendations.append(f"  • You're just getting started! Keep going.")
            recommendations.append(f"  • Try to complete at least 5-10 items per session.")
        elif completion_percentage < 50:
            recommendations.append(f"\nRECOMMENDATIONS:")
            recommendations.append(f"  • Good progress! You're about halfway done.")
            recommendations.append(f"  • Consider taking a break if you've been working for a while.")
        elif completion_percentage < 75:
            recommendations.append(f"\nRECOMMENDATIONS:")
            recommendations.append(f"  • Great progress! You're in the final stretch.")
            recommendations.append(f"  • Focus on the remaining {pending_items} items.")
        else:
            recommendations.append(f"\nRECOMMENDATIONS:")
            recommendations.append(f"  • Excellent work! You're almost done.")
            recommendations.append(f"  • Just {pending_items} more items to go!")
        
        # Resolution rate recommendations
        if resolution_percentage < 30:
            recommendations.append(f"  • Your resolution rate is {resolution_percentage:.1f}% - consider:")
            recommendations.append(f"    - Double-checking your search strategies")
            recommendations.append(f"    - Asking for help with difficult items")
            recommendations.append(f"    - Marking more items as 'not_found' if you can't find them")
        elif resolution_percentage > 80:
            recommendations.append(f"  • Excellent resolution rate of {resolution_percentage:.1f}%!")
            recommendations.append(f"  • Keep up the great work!")
        
        return recommendations
    
    def update_quality_metrics(self, quality_metrics: Dict[str, Any]) -> None:
        """Update quality metrics in progress data."""
        progress_data = self._load_progress()
        if not progress_data:
            logger.warning("No progress data found for quality metrics update")
            return
        
        progress_data['quality_metrics'].update(quality_metrics)
        progress_data['last_updated'] = datetime.now().isoformat()
        
        self._save_progress(progress_data)
        logger.info("Updated quality metrics in progress data")
    
    def reset_progress(self) -> None:
        """Reset progress tracking (use with caution)."""
        if self.progress_file.exists():
            self.progress_file.unlink()
            logger.info("Progress tracking reset")
        else:
            logger.info("No progress data to reset")
    
    def export_progress_data(self, output_filepath: Optional[Path] = None) -> Path:
        """Export progress data to a JSON file."""
        progress_data = self._load_progress()
        if not progress_data:
            raise ValueError("No progress data found to export")
        
        if not output_filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filepath = self.output_dir / f"progress_export_{timestamp}.json"
        
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Progress data exported to: {output_filepath}")
        return output_filepath
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"manual_review_{timestamp}"
    
    def _calculate_elapsed_time(self, start_time_str: str) -> float:
        """Calculate elapsed time in minutes."""
        try:
            start_time = datetime.fromisoformat(start_time_str)
            elapsed = datetime.now() - start_time
            return elapsed.total_seconds() / 60
        except Exception as e:
            logger.error(f"Error calculating elapsed time: {e}")
            return 0.0
    
    def _save_progress(self, progress_data: Dict[str, Any]) -> None:
        """Save progress data to file."""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving progress data: {e}")
            raise
    
    def _load_progress(self) -> Optional[Dict[str, Any]]:
        """Load progress data from file."""
        try:
            if not self.progress_file.exists():
                return None
            
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading progress data: {e}")
            return None
    
    def get_completion_estimate(self) -> Dict[str, Any]:
        """Get completion time estimate based on current progress."""
        summary = self.get_progress_summary()
        if 'error' in summary:
            return {'error': summary['error']}
        
        time_info = summary['time_info']
        pending_items = summary['pending_items']
        average_time_per_item = time_info['average_time_per_item']
        
        if average_time_per_item > 0:
            estimated_remaining_minutes = pending_items * average_time_per_item
            estimated_completion_time = datetime.now() + timedelta(minutes=estimated_remaining_minutes)
        else:
            estimated_remaining_minutes = pending_items * 2.5  # Default estimate
            estimated_completion_time = datetime.now() + timedelta(minutes=estimated_remaining_minutes)
        
        return {
            'estimated_remaining_minutes': round(estimated_remaining_minutes, 1),
            'estimated_completion_time': estimated_completion_time.isoformat(),
            'estimated_completion_date': estimated_completion_time.strftime("%Y-%m-%d %H:%M"),
            'pending_items': pending_items,
            'average_time_per_item': round(average_time_per_item, 1)
        }
