"""
Folder validation system for MINGUS folder detection in Mac Notes.
"""

import sqlite3
import logging
import subprocess
import psutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from config import NOTES_DB_PATH, TARGET_FOLDER_NAME, DB_QUERY_TIMEOUT

logger = logging.getLogger(__name__)


class FolderValidator:
    """Validates and queries the MINGUS folder in Mac Notes database."""
    
    def __init__(self):
        self.db_path = Path(NOTES_DB_PATH)
        self.target_folder = TARGET_FOLDER_NAME
        self.setup_instructions = self._get_setup_instructions()
        
    def check_notes_app_running(self) -> bool:
        """
        Check if the Notes app is currently running.
        
        Returns:
            bool: True if Notes app is running, False otherwise
        """
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if 'Notes' in proc.info['name']:
                    return True
            return False
        except Exception as e:
            logger.warning(f"Could not check if Notes app is running: {e}")
            return False
    
    def validate_database_access(self) -> Dict[str, Any]:
        """
        Check if the Notes database is accessible with detailed error reporting.
        
        Returns:
            Dict containing validation results and error details
        """
        result = {
            'accessible': False,
            'error_type': None,
            'error_message': '',
            'suggestions': []
        }
        
        try:
            # Check if Notes app is running
            if self.check_notes_app_running():
                result['error_type'] = 'notes_app_running'
                result['error_message'] = 'Notes app is currently running'
                result['suggestions'] = [
                    'Please quit the Notes app and try again',
                    'The database may be locked while Notes is running'
                ]
                logger.error("Notes app is running - database may be locked")
                return result
            
            # Check if database file exists
            if not self.db_path.exists():
                result['error_type'] = 'database_not_found'
                result['error_message'] = f'Notes database not found at: {self.db_path}'
                result['suggestions'] = [
                    'Ensure you are using macOS with the Notes app',
                    'Check if the database path is correct',
                    'Try running the script from a different user account'
                ]
                logger.error(f"Notes database not found at: {self.db_path}")
                return result
            
            # Check read permissions
            if not os.access(self.db_path, os.R_OK):
                result['error_type'] = 'permission_denied'
                result['error_message'] = f'No read access to database: {self.db_path}'
                result['suggestions'] = [
                    'Grant Full Disk Access to Terminal or your Python environment',
                    'Run the script with appropriate permissions',
                    'Check System Preferences > Security & Privacy > Privacy > Full Disk Access'
                ]
                logger.error(f"No read access to database: {self.db_path}")
                return result
            
            # Test database connection
            try:
                with sqlite3.connect(self.db_path, timeout=DB_QUERY_TIMEOUT) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                    cursor.fetchone()
            except sqlite3.Error as e:
                result['error_type'] = 'database_corrupted'
                result['error_message'] = f'Database connection failed: {e}'
                result['suggestions'] = [
                    'The Notes database may be corrupted',
                    'Try restarting your Mac',
                    'Check if Notes app can open normally'
                ]
                logger.error(f"Database connection failed: {e}")
                return result
            
            result['accessible'] = True
            logger.info(f"Database access validated: {self.db_path}")
            return result
            
        except Exception as e:
            result['error_type'] = 'unexpected_error'
            result['error_message'] = f'Unexpected error: {e}'
            result['suggestions'] = [
                'Check system permissions',
                'Try running as administrator',
                'Contact support if the issue persists'
            ]
            logger.error(f"Error validating database access: {e}")
            return result
    
    def find_mingus_folder(self) -> Dict[str, Any]:
        """
        Query the database to find the MINGUS folder and count its notes.
        
        Returns:
            Dict containing folder info, note count, and error details
        """
        result = {
            'found': False,
            'folder_info': None,
            'error_type': None,
            'error_message': '',
            'suggestions': []
        }
        
        try:
            with sqlite3.connect(self.db_path, timeout=DB_QUERY_TIMEOUT) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Query to find MINGUS folder and count notes (updated for new schema)
                query = """
                SELECT Z_PK, ZNAME as ZTITLE, 
                       (SELECT COUNT(*) FROM ZICCLOUDSYNCINGOBJECT n2 
                        WHERE n2.ZFOLDER = ZICCLOUDSYNCINGOBJECT.Z_PK 
                        AND n2.ZNOTE IS NOT NULL) as note_count
                FROM ZICCLOUDSYNCINGOBJECT
                WHERE ZNAME = ? AND ZFOLDER IS NOT NULL
                """
                
                cursor.execute(query, (self.target_folder,))
                db_result = cursor.fetchone()
                
                if db_result:
                    folder_info = {
                        'folder_id': db_result['Z_PK'],
                        'title': db_result['ZTITLE'],
                        'note_count': db_result['note_count']
                    }
                    result['found'] = True
                    result['folder_info'] = folder_info
                    logger.info(f"Found MINGUS folder: ID={folder_info['folder_id']}, Notes={folder_info['note_count']}")
                else:
                    result['error_type'] = 'folder_not_found'
                    result['error_message'] = f'MINGUS folder not found in Notes app'
                    result['suggestions'] = self.setup_instructions
                    logger.warning(f"MINGUS folder not found in database")
                    
        except sqlite3.Error as e:
            result['error_type'] = 'database_error'
            result['error_message'] = f'Database error while finding MINGUS folder: {e}'
            result['suggestions'] = [
                'Check if Notes app is working properly',
                'Try restarting your Mac',
                'Verify database integrity'
            ]
            logger.error(f"Database error while finding MINGUS folder: {e}")
        except Exception as e:
            result['error_type'] = 'unexpected_error'
            result['error_message'] = f'Unexpected error while finding MINGUS folder: {e}'
            result['suggestions'] = [
                'Check system permissions',
                'Try running the script again',
                'Contact support if the issue persists'
            ]
            logger.error(f"Unexpected error while finding MINGUS folder: {e}")
        
        return result
    
    def get_folder_notes(self, folder_id: int) -> list:
        """
        Get all notes from the specified folder using the enhanced query with ZDATA.
        
        Args:
            folder_id: The folder's primary key
            
        Returns:
            List of note records with binary content data
        """
        try:
            with sqlite3.connect(self.db_path, timeout=DB_QUERY_TIMEOUT) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Enhanced query to get notes with binary content data (updated for new schema)
                query = """
                SELECT 
                    n.Z_PK as note_id,
                    n.ZTITLE as title,
                    n.ZNOTEDATA as content_data,
                    n.ZSNIPPET as body_text,
                    n.ZCREATIONDATE as creation_date,
                    n.ZMODIFICATIONDATE as modification_date
                FROM ZICCLOUDSYNCINGOBJECT n
                JOIN ZICCLOUDSYNCINGOBJECT f ON n.ZFOLDER = f.Z_PK
                WHERE f.ZNAME = 'MINGUS' AND f.ZFOLDER IS NOT NULL
                AND n.ZNOTE IS NOT NULL
                AND n.ZNOTEDATA IS NOT NULL
                ORDER BY n.ZMODIFICATIONDATE DESC
                """
                
                cursor.execute(query)
                notes = cursor.fetchall()
                
                logger.info(f"Retrieved {len(notes)} notes with content data from MINGUS folder")
                return [dict(note) for note in notes]
                
        except sqlite3.Error as e:
            logger.error(f"Database error while retrieving notes: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while retrieving notes: {e}")
            return []
    
    def _get_setup_instructions(self) -> List[str]:
        """Get setup instructions for creating MINGUS folder."""
        return [
            "📝 How to create the MINGUS folder in Notes app:",
            "",
            "1. Open the Notes app on your Mac",
            "2. In the sidebar, right-click on 'iCloud' or 'On My Mac'",
            "3. Select 'New Folder' from the context menu",
            "4. Name the folder exactly 'MINGUS' (case-sensitive)",
            "5. Press Enter to confirm the name",
            "6. Add some notes to the MINGUS folder for testing",
            "",
            "💡 Tips:",
            "• Make sure the folder name is exactly 'MINGUS' (all caps)",
            "• The folder should be at the root level, not inside another folder",
            "• You can add Instagram links, text, or any content to test the extraction",
            "",
            "🔄 After creating the folder, run this script again to extract content."
        ]
    
    def validate_mingus_folder(self) -> Dict[str, Any]:
        """
        Complete validation of the MINGUS folder with comprehensive error handling.
        
        Returns:
            Dict containing validation results, folder information, and detailed error reporting
        """
        result = {
            'valid': False,
            'folder_info': None,
            'notes': [],
            'error_type': None,
            'error_message': '',
            'suggestions': [],
            'validation_report': {}
        }
        
        try:
            # Step 1: Check database access
            logger.info("Validating database access...")
            db_access = self.validate_database_access()
            
            if not db_access['accessible']:
                result['error_type'] = db_access['error_type']
                result['error_message'] = db_access['error_message']
                result['suggestions'] = db_access['suggestions']
                result['validation_report'] = {
                    'database_accessible': False,
                    'database_error': db_access['error_message']
                }
                logger.error(f"Database access failed: {db_access['error_message']}")
                return result
            
            result['validation_report']['database_accessible'] = True
            
            # Step 2: Find MINGUS folder
            logger.info("Searching for MINGUS folder...")
            folder_result = self.find_mingus_folder()
            
            if not folder_result['found']:
                result['error_type'] = folder_result['error_type']
                result['error_message'] = folder_result['error_message']
                result['suggestions'] = folder_result['suggestions']
                result['validation_report']['mingus_folder_found'] = False
                result['validation_report']['folder_error'] = folder_result['error_message']
                logger.error(f"MINGUS folder not found: {folder_result['error_message']}")
                return result
            
            folder_info = folder_result['folder_info']
            result['folder_info'] = folder_info
            result['validation_report']['mingus_folder_found'] = True
            result['validation_report']['folder_id'] = folder_info['folder_id']
            result['validation_report']['note_count'] = folder_info['note_count']
            
            # Step 3: Check if folder is empty
            if folder_info['note_count'] == 0:
                result['error_type'] = 'empty_folder'
                result['error_message'] = 'MINGUS folder is empty'
                result['suggestions'] = [
                    "The MINGUS folder exists but contains no notes",
                    "Add some notes to the MINGUS folder to test the extraction",
                    "You can add Instagram links, text, or any content",
                    "Run the script again after adding content"
                ]
                result['validation_report']['folder_empty'] = True
                logger.warning("MINGUS folder is empty")
                return result
            
            result['validation_report']['folder_empty'] = False
            
            # Step 4: Get notes from the folder
            logger.info(f"Retrieving {folder_info['note_count']} notes from MINGUS folder...")
            notes = self.get_folder_notes(folder_info['folder_id'])
            result['notes'] = notes
            result['validation_report']['notes_retrieved'] = len(notes)
            
            # Step 5: Validate notes retrieval
            if len(notes) != folder_info['note_count']:
                logger.warning(f"Note count mismatch: expected {folder_info['note_count']}, got {len(notes)}")
                result['validation_report']['note_count_mismatch'] = True
            else:
                result['validation_report']['note_count_mismatch'] = False
            
            result['valid'] = True
            result['validation_report']['validation_successful'] = True
            logger.info(f"MINGUS folder validation successful: {folder_info['note_count']} notes found")
            
        except Exception as e:
            result['error_type'] = 'validation_error'
            result['error_message'] = f"Validation error: {str(e)}"
            result['suggestions'] = [
                'Check system permissions',
                'Try running the script again',
                'Contact support if the issue persists'
            ]
            result['validation_report']['validation_successful'] = False
            result['validation_report']['error'] = str(e)
            logger.error(f"MINGUS folder validation failed: {e}")
        
        return result
    
    def generate_validation_report(self, validation_result: Dict[str, Any]) -> str:
        """
        Generate a formatted validation report.
        
        Args:
            validation_result: Result from validate_mingus_folder()
            
        Returns:
            Formatted validation report string
        """
        report = []
        report.append("🔍 MINGUS Folder Validation Report")
        report.append("=" * 40)
        report.append("")
        
        # Database access status
        if validation_result['validation_report'].get('database_accessible', False):
            report.append("✅ Database accessible")
        else:
            report.append("❌ Database not accessible")
            if 'database_error' in validation_result['validation_report']:
                report.append(f"   Error: {validation_result['validation_report']['database_error']}")
        
        # MINGUS folder status
        if validation_result['validation_report'].get('mingus_folder_found', False):
            report.append("✅ MINGUS folder found")
            folder_info = validation_result['folder_info']
            report.append(f"   📊 Folder ID: {folder_info['folder_id']}")
            report.append(f"   📊 Total notes: {folder_info['note_count']}")
            
            # Check if folder is empty
            if validation_result['validation_report'].get('folder_empty', False):
                report.append("⚠️  MINGUS folder is empty")
                report.append("   💡 Add some notes to test the extraction")
            else:
                report.append("📱 Ready for content extraction")
                
                # Notes retrieval status
                notes_retrieved = validation_result['validation_report'].get('notes_retrieved', 0)
                report.append(f"   📝 Notes retrieved: {notes_retrieved}")
                
                # Check for note count mismatch
                if validation_result['validation_report'].get('note_count_mismatch', False):
                    report.append("⚠️  Note count mismatch detected")
        else:
            report.append("❌ MINGUS folder not found")
            if 'folder_error' in validation_result['validation_report']:
                report.append(f"   Error: {validation_result['validation_report']['folder_error']}")
        
        # Overall validation status
        report.append("")
        if validation_result['valid']:
            report.append("🎉 Validation successful!")
        else:
            report.append("❌ Validation failed")
            if validation_result['error_message']:
                report.append(f"   Error: {validation_result['error_message']}")
        
        return "\n".join(report)


# Import os for access check
import os
