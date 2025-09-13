#!/usr/bin/env python3
"""
Test script to extract Instagram content from all notes, not just MINGUS folder
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import NOTES_DB_PATH

def test_database_access():
    """Test database access and show available folders and notes."""
    print("🔍 Testing Mac Notes Database Access")
    print("=" * 50)
    
    try:
        with sqlite3.connect(NOTES_DB_PATH, timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check total notes
            cursor.execute("SELECT COUNT(*) FROM ZICCLOUDSYNCINGOBJECT WHERE ZNOTE IS NOT NULL")
            total_notes = cursor.fetchone()[0]
            print(f"📝 Total notes in database: {total_notes}")
            
            # Check for folders
            cursor.execute("""
                SELECT ZNAME, COUNT(*) as note_count
                FROM ZICCLOUDSYNCINGOBJECT 
                WHERE ZFOLDER IS NOT NULL AND ZNAME IS NOT NULL
                GROUP BY ZNAME
                ORDER BY note_count DESC
                LIMIT 10
            """)
            folders = cursor.fetchall()
            
            if folders:
                print(f"\n📁 Available folders:")
                for folder in folders:
                    print(f"   • {folder['ZNAME']}: {folder['note_count']} notes")
            else:
                print(f"\n📁 No folders found with standard structure")
            
            # Check for notes with Instagram content
            cursor.execute("""
                SELECT ZTITLE, ZSNIPPET, ZCREATIONDATE
                FROM ZICCLOUDSYNCINGOBJECT 
                WHERE ZNOTE IS NOT NULL 
                AND (ZTITLE LIKE '%instagram%' OR ZSNIPPET LIKE '%instagram%' 
                     OR ZTITLE LIKE '%ig%' OR ZSNIPPET LIKE '%ig%')
                ORDER BY ZCREATIONDATE DESC
                LIMIT 5
            """)
            instagram_notes = cursor.fetchall()
            
            if instagram_notes:
                print(f"\n📱 Notes with Instagram content:")
                for note in instagram_notes:
                    title = note['ZTITLE'] or 'Untitled'
                    snippet = note['ZSNIPPET'] or ''
                    print(f"   • {title[:50]}...")
                    if snippet:
                        print(f"     {snippet[:100]}...")
            else:
                print(f"\n📱 No notes with Instagram content found")
            
            # Check for notes with Mingus content
            cursor.execute("""
                SELECT ZTITLE, ZSNIPPET, ZCREATIONDATE
                FROM ZICCLOUDSYNCINGOBJECT 
                WHERE ZNOTE IS NOT NULL 
                AND (ZTITLE LIKE '%mingus%' OR ZSNIPPET LIKE '%mingus%')
                ORDER BY ZCREATIONDATE DESC
                LIMIT 5
            """)
            mingus_notes = cursor.fetchall()
            
            if mingus_notes:
                print(f"\n🎵 Notes with Mingus content:")
                for note in mingus_notes:
                    title = note['ZTITLE'] or 'Untitled'
                    snippet = note['ZSNIPPET'] or ''
                    print(f"   • {title[:50]}...")
                    if snippet:
                        print(f"     {snippet[:100]}...")
            
            # Check recent notes
            cursor.execute("""
                SELECT ZTITLE, ZSNIPPET, ZCREATIONDATE
                FROM ZICCLOUDSYNCINGOBJECT 
                WHERE ZNOTE IS NOT NULL 
                ORDER BY ZCREATIONDATE DESC
                LIMIT 5
            """)
            recent_notes = cursor.fetchall()
            
            if recent_notes:
                print(f"\n📅 Recent notes:")
                for note in recent_notes:
                    title = note['ZTITLE'] or 'Untitled'
                    snippet = note['ZSNIPPET'] or ''
                    print(f"   • {title[:50]}...")
                    if snippet:
                        print(f"     {snippet[:100]}...")
            
            print(f"\n✅ Database access successful!")
            return True
            
    except Exception as e:
        print(f"❌ Database access failed: {e}")
        return False

if __name__ == "__main__":
    test_database_access()
