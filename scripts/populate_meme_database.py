#!/usr/bin/env python3
"""
Meme Database Population Script for Mingus Application

This script imports extracted memes from CSV files into the Mingus meme database.
"""

import os
import sys
import csv
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict

class MemeDatabasePopulator:
    def __init__(self, csv_file_path: str):
        """
        Initialize the meme database populator.
        
        Args:
            csv_file_path: Path to the CSV file containing extracted memes
        """
        self.csv_file_path = Path(csv_file_path)
        self.db_path = Path("mingus_memes.db")
        
        # Ensure we're in the right directory
        if not self.db_path.exists():
            print(f"❌ Database not found at {self.db_path}")
            print("Make sure you're running this script from the Mingus application root directory.")
            sys.exit(1)
    
    def populate_database(self):
        """Main method to populate the database with memes from CSV"""
        print("🚀 Starting meme database population...")
        print("=" * 50)
        
        # Read CSV file
        memes = self._read_csv_file()
        if not memes:
            print("❌ No memes found in CSV file")
            return
        
        # Connect to database
        conn = self._connect_to_database()
        if not conn:
            return
        
        # Create meme table if it doesn't exist
        self._create_meme_table(conn)
        
        # Insert memes
        inserted_count = self._insert_memes(conn, memes)
        
        # Close connection
        conn.close()
        
        print("=" * 50)
        print(f"✅ Database population complete!")
        print(f"📊 Inserted {inserted_count} memes into the database")
    
    def _read_csv_file(self) -> List[Dict]:
        """Read memes from CSV file"""
        if not self.csv_file_path.exists():
            print(f"❌ CSV file not found: {self.csv_file_path}")
            return []
        
        memes = []
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    memes.append(row)
            
            print(f"📖 Read {len(memes)} memes from {self.csv_file_path}")
            
        except Exception as e:
            print(f"❌ Error reading CSV file: {e}")
            return []
        
        return memes
    
    def _connect_to_database(self) -> sqlite3.Connection:
        """Connect to the meme database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            print(f"🔗 Connected to database: {self.db_path}")
            return conn
        except sqlite3.Error as e:
            print(f"❌ Database connection error: {e}")
            return None
    
    def _create_meme_table(self, conn: sqlite3.Connection):
        """Verify the memes table exists (using existing schema)"""
        try:
            # Check if table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memes'")
            if cursor.fetchone():
                print("📋 Meme table verified (using existing schema)")
            else:
                print("❌ Meme table not found in database")
        except sqlite3.Error as e:
            print(f"❌ Error checking table: {e}")
    
    def _insert_memes(self, conn: sqlite3.Connection, memes: List[Dict]) -> int:
        """Insert memes into the database using existing schema"""
        insert_sql = """
        INSERT INTO memes 
        (image_url, category, caption, alt_text, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        inserted_count = 0
        skipped_count = 0
        
        # Valid categories from the existing schema
        valid_categories = ['faith', 'work_life', 'health', 'housing', 'transportation', 'relationships', 'family']
        
        for meme in memes:
            try:
                # Prepare data for existing schema
                title = meme.get('title', '').strip()
                content = meme.get('body', '').strip()
                meme_score = int(meme.get('meme_score', 0))
                creation_date = meme.get('creation_date', '')
                
                # Skip if no content
                if not title and not content:
                    skipped_count += 1
                    continue
                
                # Create image URL (placeholder for now)
                image_url = f"placeholder_meme_{meme.get('id', 'unknown')}.jpg"
                
                # Determine category based on content (simple keyword matching)
                category = 'work_life'  # default
                content_lower = f"{title} {content}".lower()
                if any(word in content_lower for word in ['faith', 'god', 'prayer', 'church']):
                    category = 'faith'
                elif any(word in content_lower for word in ['work', 'job', 'office', 'monday']):
                    category = 'work_life'
                elif any(word in content_lower for word in ['health', 'exercise', 'doctor', 'medicine']):
                    category = 'health'
                elif any(word in content_lower for word in ['home', 'house', 'rent', 'mortgage']):
                    category = 'housing'
                elif any(word in content_lower for word in ['car', 'drive', 'traffic', 'commute']):
                    category = 'transportation'
                elif any(word in content_lower for word in ['relationship', 'dating', 'marriage', 'partner']):
                    category = 'relationships'
                elif any(word in content_lower for word in ['family', 'kids', 'children', 'parents']):
                    category = 'family'
                
                # Create caption from title and content
                caption = f"{title}: {content}" if title else content
                if len(caption) > 500:  # Truncate if too long
                    caption = caption[:497] + "..."
                
                # Create alt text
                alt_text = f"Meme: {title}" if title else "Meme from Notes"
                
                # Insert into database
                conn.execute(insert_sql, (
                    image_url, category, caption, alt_text, 1, creation_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                inserted_count += 1
                
            except Exception as e:
                print(f"⚠️  Error inserting meme {meme.get('id', 'unknown')}: {e}")
                skipped_count += 1
                continue
        
        # Commit all changes
        conn.commit()
        
        if skipped_count > 0:
            print(f"⚠️  Skipped {skipped_count} memes due to errors or empty content")
        
        return inserted_count
    
    def show_database_stats(self):
        """Show current database statistics"""
        conn = self._connect_to_database()
        if not conn:
            return
        
        try:
            # Get total count
            cursor = conn.execute("SELECT COUNT(*) as total FROM memes")
            total = cursor.fetchone()['total']
            
            # Get category breakdown
            cursor = conn.execute("SELECT category, COUNT(*) as count FROM memes GROUP BY category")
            category_breakdown = cursor.fetchall()
            
            # Get active/inactive breakdown
            cursor = conn.execute("SELECT is_active, COUNT(*) as count FROM memes GROUP BY is_active")
            active_breakdown = cursor.fetchall()
            
            print("\n📊 Database Statistics:")
            print(f"   Total memes: {total}")
            
            print("\n📈 Category Breakdown:")
            for row in category_breakdown:
                print(f"   {row['category']}: {row['count']}")
            
            print("\n🎯 Active/Inactive Breakdown:")
            for row in active_breakdown:
                status = "Active" if row['is_active'] else "Inactive"
                print(f"   {status}: {row['count']}")
            
        except sqlite3.Error as e:
            print(f"❌ Error getting database stats: {e}")
        finally:
            conn.close()

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python populate_meme_database.py <csv_file_path>")
        print("Example: python populate_meme_database.py content_staging/from_notes/extracted_memes.csv")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    
    # Create populator and run
    populator = MemeDatabasePopulator(csv_file_path)
    populator.populate_database()
    
    # Show stats
    populator.show_database_stats()

if __name__ == "__main__":
    main()
