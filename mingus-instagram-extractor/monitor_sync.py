#!/usr/bin/env python3
"""
Monitor iCloud sync status and look for MINGUS folder changes.
"""

import sqlite3
import os
import time
from pathlib import Path
from datetime import datetime, timedelta

# Database path
DB_PATH = os.path.expanduser("~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite")

def monitor_sync():
    """Monitor for sync changes and MINGUS folder."""
    
    print("🔄 Monitoring iCloud sync for MINGUS folder...")
    print("Press Ctrl+C to stop monitoring")
    print()
    
    last_check = None
    
    try:
        while True:
            if not Path(DB_PATH).exists():
                print("❌ Database not found")
                time.sleep(10)
                continue
            
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Check for recent changes
                    current_time = datetime.now()
                    one_hour_ago = current_time - timedelta(hours=1)
                    one_hour_ago_ns = int(one_hour_ago.timestamp() * 1000000000)
                    
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM ZICCLOUDSYNCINGOBJECT 
                        WHERE ZCREATIONDATE > ? OR ZMODIFICATIONDATE > ?
                    """, (one_hour_ago_ns, one_hour_ago_ns))
                    
                    recent_count = cursor.fetchone()['count']
                    
                    # Check for MINGUS folder
                    cursor.execute("""
                        SELECT Z_PK, ZNAME, ZFOLDER, ZTITLE, ZTYPE, ZACCOUNT, ZCREATIONDATE, ZMODIFICATIONDATE
                        FROM ZICCLOUDSYNCINGOBJECT 
                        WHERE ZFOLDER IS NOT NULL
                        AND (LOWER(ZNAME) LIKE '%mingus%' OR LOWER(ZTITLE) LIKE '%mingus%')
                    """)
                    
                    mingus_folders = cursor.fetchall()
                    
                    # Check for any folders with non-empty names
                    cursor.execute("""
                        SELECT Z_PK, ZNAME, ZFOLDER, ZTITLE, ZTYPE, ZACCOUNT, ZCREATIONDATE, ZMODIFICATIONDATE
                        FROM ZICCLOUDSYNCINGOBJECT 
                        WHERE ZFOLDER IS NOT NULL
                        AND ZNAME IS NOT NULL
                        AND ZNAME != 'None'
                        AND ZNAME != ''
                        ORDER BY ZCREATIONDATE DESC
                        LIMIT 5
                    """)
                    
                    named_folders = cursor.fetchall()
                    
                    current_time_str = current_time.strftime("%H:%M:%S")
                    
                    if recent_count > 0:
                        print(f"🕐 {current_time_str} - Found {recent_count} recent changes")
                    
                    if mingus_folders:
                        print(f"🎯 {current_time_str} - Found MINGUS folder(s):")
                        for folder in mingus_folders:
                            creation_date = datetime.fromtimestamp(folder['ZCREATIONDATE'] / 1000000000) if folder['ZCREATIONDATE'] else 'None'
                            print(f"    - ID: {folder['Z_PK']}, Name: '{folder['ZNAME']}', Title: '{folder['ZTITLE']}', Account: {folder['ZACCOUNT']}, Created: {creation_date}")
                        print("✅ MINGUS folder detected! You can now run the validation.")
                        break
                    
                    if named_folders:
                        print(f"📁 {current_time_str} - Found {len(named_folders)} named folders:")
                        for folder in named_folders:
                            creation_date = datetime.fromtimestamp(folder['ZCREATIONDATE'] / 1000000000) if folder['ZCREATIONDATE'] else 'None'
                            print(f"    - ID: {folder['Z_PK']}, Name: '{folder['ZNAME']}', Title: '{folder['ZTITLE']}', Account: {folder['ZACCOUNT']}, Created: {creation_date}")
                    
                    if last_check != recent_count:
                        last_check = recent_count
                        print(f"🔄 {current_time_str} - Sync activity detected: {recent_count} recent entries")
                    
                    time.sleep(30)  # Check every 30 seconds
                    
            except Exception as e:
                print(f"❌ Error checking database: {e}")
                time.sleep(10)
                
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")

if __name__ == "__main__":
    monitor_sync()
