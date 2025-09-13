#!/usr/bin/env python3
"""
Progress Reporting and Logging

Provides real-time progress reporting, statistics tracking, and comprehensive logging.
"""

import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class ProgressStats:
    """Statistics for progress tracking."""
    total_items: int = 0
    completed_items: int = 0
    successful_downloads: int = 0
    failed_downloads: int = 0
    skipped_downloads: int = 0
    total_size_bytes: int = 0
    start_time: float = 0
    current_item: str = ""
    categories: Dict[str, int] = None
    content_types: Dict[str, int] = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = {}
        if self.content_types is None:
            self.content_types = {}
        if self.start_time == 0:
            self.start_time = time.time()
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    @property
    def completion_percentage(self) -> float:
        """Get completion percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.completed_items / self.total_items) * 100
    
    @property
    def success_rate(self) -> float:
        """Get success rate percentage."""
        if self.completed_items == 0:
            return 0.0
        return (self.successful_downloads / self.completed_items) * 100
    
    @property
    def estimated_remaining_time(self) -> float:
        """Estimate remaining time in seconds."""
        if self.completed_items == 0:
            return 0.0
        
        avg_time_per_item = self.elapsed_time / self.completed_items
        remaining_items = self.total_items - self.completed_items
        return avg_time_per_item * remaining_items
    
    @property
    def total_size_mb(self) -> float:
        """Get total size in MB."""
        return self.total_size_bytes / (1024 * 1024)


class ProgressReporter:
    """Handles progress reporting and statistics."""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.stats = ProgressStats()
        self.last_update_time = 0
        self.update_interval = 5.0  # Update every 5 seconds
        
    def start_download_session(self, total_items: int):
        """Start a new download session."""
        self.stats = ProgressStats(total_items=total_items)
        self.logger.info(f"Starting download session with {total_items} items")
        self._print_header()
    
    def update_progress(self, item_name: str = "", success: bool = None, 
                       file_size: int = 0, category: str = "", 
                       content_type: str = ""):
        """Update progress with new information."""
        current_time = time.time()
        
        # Update current item
        if item_name:
            self.stats.current_item = item_name
        
        # Update counters
        if success is not None:
            self.stats.completed_items += 1
            if success:
                self.stats.successful_downloads += 1
                self.stats.total_size_bytes += file_size
                
                # Update category and content type stats
                if category:
                    self.stats.categories[category] = self.stats.categories.get(category, 0) + 1
                if content_type:
                    self.stats.content_types[content_type] = self.stats.content_types.get(content_type, 0) + 1
            else:
                self.stats.failed_downloads += 1
        
        # Print progress update if enough time has passed
        if current_time - self.last_update_time >= self.update_interval:
            self._print_progress_update()
            self.last_update_time = current_time
    
    def mark_skipped(self, item_name: str = "", category: str = ""):
        """Mark an item as skipped."""
        self.stats.completed_items += 1
        self.stats.skipped_downloads += 1
        
        if category:
            self.stats.categories[category] = self.stats.categories.get(category, 0) + 1
        
        self.logger.info(f"Skipped: {item_name}")
    
    def _print_header(self):
        """Print session header."""
        print("\n" + "="*80)
        print("📱 INSTAGRAM CONTENT DOWNLOADER")
        print("="*80)
        print(f"Total items: {self.stats.total_items}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
    
    def _print_progress_update(self):
        """Print progress update."""
        elapsed = self.stats.elapsed_time
        remaining = self.stats.estimated_remaining_time
        
        print(f"\n📊 Progress Update:")
        print(f"   Completed: {self.stats.completed_items}/{self.stats.total_items} "
              f"({self.stats.completion_percentage:.1f}%)")
        print(f"   Successful: {self.stats.successful_downloads}")
        print(f"   Failed: {self.stats.failed_downloads}")
        print(f"   Skipped: {self.stats.skipped_downloads}")
        print(f"   Success rate: {self.stats.success_rate:.1f}%")
        print(f"   Total size: {self.stats.total_size_mb:.1f} MB")
        print(f"   Elapsed: {self._format_time(elapsed)}")
        print(f"   Remaining: {self._format_time(remaining)}")
        
        if self.stats.current_item:
            print(f"   Current: {self.stats.current_item}")
    
    def _format_time(self, seconds: float) -> str:
        """Format time in a human-readable way."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def print_final_summary(self):
        """Print final summary."""
        print("\n" + "="*80)
        print("🎉 DOWNLOAD SESSION COMPLETED")
        print("="*80)
        
        print(f"Total items processed: {self.stats.completed_items}")
        print(f"Successful downloads: {self.stats.successful_downloads}")
        print(f"Failed downloads: {self.stats.failed_downloads}")
        print(f"Skipped downloads: {self.stats.skipped_downloads}")
        print(f"Success rate: {self.stats.success_rate:.1f}%")
        print(f"Total size downloaded: {self.stats.total_size_mb:.1f} MB")
        print(f"Total time: {self._format_time(self.stats.elapsed_time)}")
        
        if self.stats.categories:
            print(f"\n📁 Category distribution:")
            for category, count in sorted(self.stats.categories.items()):
                percentage = (count / self.stats.completed_items * 100) if self.stats.completed_items > 0 else 0
                print(f"   {category}: {count} ({percentage:.1f}%)")
        
        if self.stats.content_types:
            print(f"\n🎬 Content type distribution:")
            for content_type, count in sorted(self.stats.content_types.items()):
                percentage = (count / self.stats.completed_items * 100) if self.stats.completed_items > 0 else 0
                print(f"   {content_type}: {count} ({percentage:.1f}%)")
        
        print("="*80)
    
    def save_detailed_report(self, output_dir: Path, results: Dict[str, Any]):
        """Save detailed report to file."""
        report_data = {
            'session_info': {
                'start_time': datetime.fromtimestamp(self.stats.start_time).isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_duration_seconds': self.stats.elapsed_time,
                'total_items': self.stats.total_items
            },
            'statistics': {
                'completed_items': self.stats.completed_items,
                'successful_downloads': self.stats.successful_downloads,
                'failed_downloads': self.stats.failed_downloads,
                'skipped_downloads': self.stats.skipped_downloads,
                'success_rate': self.stats.success_rate,
                'total_size_bytes': self.stats.total_size_bytes,
                'total_size_mb': self.stats.total_size_mb,
                'categories': self.stats.categories,
                'content_types': self.stats.content_types
            },
            'download_results': results
        }
        
        # Save JSON report
        report_path = output_dir / 'metadata' / 'detailed_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Detailed report saved to: {report_path}")
        return report_path
    
    def log_error(self, error_message: str, item_url: str = "", 
                  category: str = ""):
        """Log an error with context."""
        context = []
        if item_url:
            context.append(f"URL: {item_url}")
        if category:
            context.append(f"Category: {category}")
        
        context_str = f" ({', '.join(context)})" if context else ""
        self.logger.error(f"{error_message}{context_str}")
    
    def log_warning(self, warning_message: str, item_url: str = "", 
                   category: str = ""):
        """Log a warning with context."""
        context = []
        if item_url:
            context.append(f"URL: {item_url}")
        if category:
            context.append(f"Category: {category}")
        
        context_str = f" ({', '.join(context)})" if context else ""
        self.logger.warning(f"{warning_message}{context_str}")
    
    def log_success(self, success_message: str, item_url: str = "", 
                   file_size: int = 0):
        """Log a success with context."""
        context = []
        if item_url:
            context.append(f"URL: {item_url}")
        if file_size > 0:
            context.append(f"Size: {file_size / (1024*1024):.1f} MB")
        
        context_str = f" ({', '.join(context)})" if context else ""
        self.logger.info(f"✓ {success_message}{context_str}")


class DownloadLogger:
    """Enhanced logging for download operations."""
    
    def __init__(self, log_file: str = "instagram_downloader.log"):
        self.logger = logging.getLogger("instagram_downloader")
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger."""
        return self.logger
