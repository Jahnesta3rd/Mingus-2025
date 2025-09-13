#!/usr/bin/env python3
"""
Create a test folder and note to verify the database structure.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

# Database path
DB_PATH = os.path.expanduser("~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite")

def create_test_folder():
    """Create a test folder and note to understand the database structure."""
    
    print("🧪 Creating test folder and note...")
    print("Please follow these steps:")
    print()
    print("1. Open Notes app")
    print("2. Make sure you're in local Notes (On My Mac)")
    print("3. Right-click on 'On My Mac' in the sidebar")
    print("4. Select 'New Folder'")
    print("5. Name it 'TESTFOLDER' (all caps)")
    print("6. Press Enter")
    print("7. Click on the TESTFOLDER")
    print("8. Create a new note (Cmd+N)")
    print("9. Add some text like 'This is a test note'")
    print("10. Save the note")
    print()
    print("Press Enter when you've completed these steps...")
    input()
    
    print("🔍 Checking database for TESTFOLDER...")
    
    if not Path(DB_PATH).exists():
        print(f"❌ Database not found at: {DB_PATH}")
        return
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Look for TESTFOLDER
            cursor.execute("""
                SELECT Z_PK, ZNAME, ZFOLDER, ZTITLE, ZTYPE, ZACCOUNT, ZCREATIONDATE, ZMODIFICATIONDATE
                FROM ZICCLOUDSYNCINGOBJECT 
                WHERE (ZACCOUNT IS NULL OR ZACCOUNT = 0)
                AND (LOWER(ZNAME) LIKE '%testfolder%' OR LOWER(ZTITLE) LIKE '%testfolder%')
                ORDER BY ZCREATIONDATE DESC
            """)
            
            test_entries = cursor.fetchall()
            
            if test_entries:
                print(f"✅ Found {len(test_entries)} entries containing 'testfolder':")
                for entry in test_entries:
                    creation_date = datetime.fromtimestamp(entry['ZCREATIONDATE'] / 1000000000) if entry['ZCREATIONDATE'] else 'None'
                    print(f"    - ID: {entry['Z_PK']}, Name: '{entry['ZNAME']}', Title: '{entry['ZTITLE']}', Account: {entry['ZACCOUNT']}, Created: {creation_date}")
            else:
                print("❌ No entries containing 'testfolder' found")
            
            # Look for recent entries
            print("\n🕐 Looking for recent entries (last 5 minutes):")
            
            current_time = datetime.now()
            five_minutes_ago = current_time.timestamp() - 300  # 5 minutes ago
            five_minutes_ago_ns = int(five_minutes_ago * 1000000000)
            
            cursor.execute("""
                SELECT Z_PK, ZNAME, ZFOLDER, ZTITLE, ZTYPE, ZACCOUNT, ZCREATIONDATE, ZMODIFICATIONDATE
                FROM ZICCLOUDSYNCINGOBJECT 
                WHERE (ZACCOUNT IS NULL OR ZACCOUNT = 0)
                AND (ZCREATIONDATE > ? OR ZMODIFICATIONDATE > ?)
                ORDER BY ZCREATIONDATE DESC, ZMODIFICATIONDATE DESC
                LIMIT 10
            """, (five_minutes_ago_ns, five_minutes_ago_ns))
            
            recent_entries = cursor.fetchall()
            
            if recent_entries:
                print(f"Found {len(recent_entries)} recent entries:")
                for entry in recent_entries:
                    creation_date = datetime.fromtimestamp(entry['ZCREATIONDATE'] / 1000000000) if entry['ZCREATIONDATE'] else 'None'
                    mod_date = datetime.fromtimestamp(entry['ZMODIFICATIONDATE'] / 1000000000) if entry['ZMODIFICATIONDATE'] else 'None'
                    print(f"    - ID: {entry['Z_PK']}, Name: '{entry['ZNAME']}', Title: '{entry['ZTITLE']}', Account: {entry['ZACCOUNT']}")
                    print(f"      Created: {creation_date}, Modified: {mod_date}")
            else:
                print("❌ No recent entries found")
            
            # Look for any entries with non-empty names
            print("\n📝 Looking for entries with non-empty names:")
            
            cursor.execute("""
                SELECT Z_PK, ZNAME, ZFOLDER, ZTITLE, ZTYPE, ZACCOUNT, ZCREATIONDATE, ZMODIFICATIONDATE
                FROM ZICCLOUDSYNCINGOBJECT 
                WHERE (ZACCOUNT IS NULL OR ZACCOUNT = 0)
                AND ZNAME IS NOT NULL
                AND ZNAME != 'None'
                AND ZNAME != ''
                ORDER BY ZCREATIONDATE DESC
                LIMIT 10
            """)
            
            named_entries = cursor.fetchall()
            
            if named_entries:
                print(f"Found {len(named_entries)} entries with non-empty names:")
                for entry in named_entries:
                    creation_date = datetime.fromtimestamp(entry['ZCREATIONDATE'] / 1000000000) if entry['ZCREATIONDATE'] else 'None'
                    print(f"    - ID: {entry['Z_PK']}, Name: '{entry['ZNAME']}', Title: '{entry['ZTITLE']}', Account: {entry['ZACCOUNT']}, Created: {creation_date}")
            else:
                print("❌ No entries with non-empty names found")
            
    except Exception as e:
        print(f"❌ Error accessing database: {e}")

if __name__ == "__main__":
    create_test_folder()
