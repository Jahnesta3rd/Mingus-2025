#!/usr/bin/env python3
"""
Local Notes Processor - extracts Instagram content from all local Notes.
This bypasses folder detection issues by processing all local notes directly.
"""

import sqlite3
import logging
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import NOTES_DB_PATH, DB_QUERY_TIMEOUT, INSTAGRAM_URL_PATTERNS

logger = logging.getLogger(__name__)

class LocalNotesProcessor:
    """Processes all local Notes to extract Instagram content."""
    
    def __init__(self):
        self.db_path = Path(NOTES_DB_PATH)
        self.instagram_patterns = [re.compile(pattern) for pattern in INSTAGRAM_URL_PATTERNS]
        
    def validate_database_access(self) -> Dict[str, Any]:
        """Check if the local Notes database is accessible."""
        result = {
            'accessible': False,
            'error_type': None,
            'error_message': '',
            'suggestions': []
        }
        
        try:
            if not self.db_path.exists():
                result['error_type'] = 'database_not_found'
                result['error_message'] = f'Notes database not found at: {self.db_path}'
                result['suggestions'] = [
                    'Ensure you are using macOS with the Notes app',
                    'Check if the database path is correct'
                ]
                return result
            
            if not os.access(self.db_path, os.R_OK):
                result['error_type'] = 'permission_denied'
                result['error_message'] = f'No read access to database: {self.db_path}'
                result['suggestions'] = [
                    'Grant Full Disk Access to Terminal or your Python environment',
                    'Check System Preferences > Security & Privacy > Privacy > Full Disk Access'
                ]
                return result
            
            # Test database connection
            with sqlite3.connect(self.db_path, timeout=DB_QUERY_TIMEOUT) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                cursor.fetchone()
            
            result['accessible'] = True
            logger.info(f"Local database access validated: {self.db_path}")
            return result
            
        except Exception as e:
            result['error_type'] = 'unexpected_error'
            result['error_message'] = f'Unexpected error: {e}'
            result['suggestions'] = [
                'Check system permissions',
                'Try running as administrator'
            ]
            logger.error(f"Error validating local database access: {e}")
            return result
    
    def get_all_local_notes(self) -> List[Dict[str, Any]]:
        """Get all notes from local Notes (Account = NULL or 0)."""
        try:
            with sqlite3.connect(self.db_path, timeout=DB_QUERY_TIMEOUT) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Query to get all local notes - updated to work with actual database structure
                query = """
                SELECT 
                    Z_PK as note_id,
                    ZTITLE as title,
                    ZNOTEDATA as content_data,
                    ZSNIPPET as body_text,
                    ZCREATIONDATE as creation_date,
                    ZMODIFICATIONDATE as modification_date,
                    ZFOLDER as folder_id
                FROM ZICCLOUDSYNCINGOBJECT
                WHERE ZNOTE IS NOT NULL
                AND (ZACCOUNT IS NULL OR ZACCOUNT = 0)
                AND (ZTITLE IS NOT NULL OR ZSNIPPET IS NOT NULL)
                ORDER BY ZMODIFICATIONDATE DESC
                """
                
                cursor.execute(query)
                notes = cursor.fetchall()
                
                logger.info(f"Retrieved {len(notes)} local notes")
                return [dict(note) for note in notes]
                
        except sqlite3.Error as e:
            logger.error(f"Database error while retrieving local notes: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while retrieving local notes: {e}")
            return []
    
    def extract_instagram_urls(self, text: str) -> List[str]:
        """Extract Instagram URLs from text using regex patterns."""
        urls = []
        if not text:
            return urls
            
        for pattern in self.instagram_patterns:
            matches = pattern.findall(text)
            urls.extend(matches)
        
        return list(set(urls))  # Remove duplicates
    
    def process_note_content(self, note: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single note to extract Instagram content."""
        result = {
            'note_id': note['note_id'],
            'title': note['title'],
            'body_text': note['body_text'],
            'creation_date': note['creation_date'],
            'modification_date': note['modification_date'],
            'folder_id': note['folder_id'],
            'instagram_urls': [],
            'has_instagram_content': False,
            'content_preview': ''
        }
        
        # Extract Instagram URLs from title
        if note['title']:
            title_urls = self.extract_instagram_urls(note['title'])
            result['instagram_urls'].extend(title_urls)
        
        # Extract Instagram URLs from body text
        if note['body_text']:
            body_urls = self.extract_instagram_urls(note['body_text'])
            result['instagram_urls'].extend(body_urls)
        
        # Extract Instagram URLs from content data (if available)
        if note['content_data']:
            try:
                # Content data is binary, we'll need to decode it
                # This is a simplified approach - in practice, you might need more sophisticated parsing
                content_str = str(note['content_data'])
                content_urls = self.extract_instagram_urls(content_str)
                result['instagram_urls'].extend(content_urls)
            except Exception as e:
                logger.warning(f"Could not process content data for note {note['note_id']}: {e}")
        
        # Remove duplicates and update flags
        result['instagram_urls'] = list(set(result['instagram_urls']))
        result['has_instagram_content'] = len(result['instagram_urls']) > 0
        
        # Create content preview
        if note['body_text']:
            result['content_preview'] = note['body_text'][:200] + "..." if len(note['body_text']) > 200 else note['body_text']
        elif note['title']:
            result['content_preview'] = note['title'][:200] + "..." if len(note['title']) > 200 else note['title']
        
        return result
    
    def process_all_local_notes(self) -> Dict[str, Any]:
        """Process all local notes to extract Instagram content."""
        result = {
            'success': False,
            'total_notes': 0,
            'notes_with_instagram': 0,
            'total_instagram_urls': 0,
            'processed_notes': [],
            'error_type': None,
            'error_message': '',
            'suggestions': []
        }
        
        try:
            # Step 1: Validate database access
            logger.info("Validating local database access...")
            db_access = self.validate_database_access()
            
            if not db_access['accessible']:
                result['error_type'] = db_access['error_type']
                result['error_message'] = db_access['error_message']
                result['suggestions'] = db_access['suggestions']
                logger.error(f"Local database access failed: {db_access['error_message']}")
                return result
            
            # Step 2: Get all local notes
            logger.info("Retrieving all local notes...")
            notes = self.get_all_local_notes()
            
            if not notes:
                result['error_type'] = 'no_notes_found'
                result['error_message'] = 'No local notes found'
                result['suggestions'] = [
                    'Make sure you have local Notes (On My Mac)',
                    'Create some notes in local Notes to test'
                ]
                logger.warning("No local notes found")
                return result
            
            result['total_notes'] = len(notes)
            logger.info(f"Processing {len(notes)} local notes...")
            
            # Step 3: Process each note
            processed_notes = []
            notes_with_instagram = 0
            total_instagram_urls = 0
            
            for note in notes:
                processed_note = self.process_note_content(note)
                processed_notes.append(processed_note)
                
                if processed_note['has_instagram_content']:
                    notes_with_instagram += 1
                    total_instagram_urls += len(processed_note['instagram_urls'])
                    logger.info(f"Note {processed_note['note_id']} contains {len(processed_note['instagram_urls'])} Instagram URLs")
            
            result['processed_notes'] = processed_notes
            result['notes_with_instagram'] = notes_with_instagram
            result['total_instagram_urls'] = total_instagram_urls
            result['success'] = True
            
            logger.info(f"Processing complete: {notes_with_instagram}/{len(notes)} notes contain Instagram content")
            logger.info(f"Total Instagram URLs found: {total_instagram_urls}")
            
        except Exception as e:
            result['error_type'] = 'processing_error'
            result['error_message'] = f"Error processing local notes: {str(e)}"
            result['suggestions'] = [
                'Check system permissions',
                'Try running the script again'
            ]
            logger.error(f"Error processing local notes: {e}")
        
        return result
    
    def generate_processing_report(self, result: Dict[str, Any]) -> str:
        """Generate a formatted processing report."""
        report = []
        report.append("🔍 Local Notes Instagram Content Extraction Report")
        report.append("=" * 55)
        report.append("")
        
        if result['success']:
            report.append("✅ Processing completed successfully!")
            report.append("")
            report.append(f"📊 Statistics:")
            report.append(f"   • Total notes processed: {result['total_notes']}")
            report.append(f"   • Notes with Instagram content: {result['notes_with_instagram']}")
            report.append(f"   • Total Instagram URLs found: {result['total_instagram_urls']}")
            report.append("")
            
            if result['notes_with_instagram'] > 0:
                report.append("📱 Notes containing Instagram content:")
                report.append("")
                
                for note in result['processed_notes']:
                    if note['has_instagram_content']:
                        report.append(f"   📝 Note ID: {note['note_id']}")
                        report.append(f"      Title: {note['title'] or 'No title'}")
                        report.append(f"      Instagram URLs: {len(note['instagram_urls'])}")
                        for url in note['instagram_urls']:
                            report.append(f"         • {url}")
                        if note['content_preview']:
                            report.append(f"      Preview: {note['content_preview']}")
                        report.append("")
            else:
                report.append("ℹ️  No Instagram content found in local notes")
                report.append("   • Add some Instagram links to your local notes to test")
                report.append("   • Make sure you're using local Notes (On My Mac), not iCloud")
        else:
            report.append("❌ Processing failed")
            if result['error_message']:
                report.append(f"   Error: {result['error_message']}")
            if result['suggestions']:
                report.append("   Suggestions:")
                for suggestion in result['suggestions']:
                    report.append(f"      • {suggestion}")
        
        return "\n".join(report)

if __name__ == "__main__":
    # Test the local notes processor
    processor = LocalNotesProcessor()
    result = processor.process_all_local_notes()
    print(processor.generate_processing_report(result))
