#!/usr/bin/env python3
"""
Fix the meme database schema to support the new categories
"""

import sqlite3
import os
import shutil
from datetime import datetime

def fix_database():
    """Fix the database schema to support new categories"""
    
    db_path = "mingus_memes.db"
    backup_path = f"mingus_memes_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    print("🔧 Fixing Mingus Meme Database Schema")
    print("=" * 50)
    
    # Backup existing database if it exists
    if os.path.exists(db_path):
        print(f"📦 Backing up existing database to {backup_path}")
        shutil.copy2(db_path, backup_path)
    
    # Create new database with correct schema
    print("🏗️  Creating new database with updated schema...")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Drop existing tables if they exist
        cursor.execute("DROP TABLE IF EXISTS user_meme_history")
        cursor.execute("DROP TABLE IF EXISTS memes")
        
        # Create memes table with new categories
        cursor.execute("""
            CREATE TABLE memes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_url TEXT NOT NULL,
                category TEXT NOT NULL CHECK (category IN (
                    'faith', 
                    'work_life', 
                    'health',
                    'housing',
                    'transportation',
                    'relationships', 
                    'family'
                )),
                caption TEXT NOT NULL,
                alt_text TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create user_meme_history table
        cursor.execute("""
            CREATE TABLE user_meme_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                meme_id INTEGER NOT NULL,
                viewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, meme_id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX idx_memes_category ON memes(category)")
        cursor.execute("CREATE INDEX idx_memes_active ON memes(is_active)")
        cursor.execute("CREATE INDEX idx_memes_category_active ON memes(category, is_active)")
        cursor.execute("CREATE INDEX idx_memes_created_at ON memes(created_at)")
        cursor.execute("CREATE INDEX idx_user_meme_history_user_id ON user_meme_history(user_id)")
        cursor.execute("CREATE INDEX idx_user_meme_history_meme_id ON user_meme_history(meme_id)")
        cursor.execute("CREATE INDEX idx_user_meme_history_viewed_at ON user_meme_history(viewed_at)")
        cursor.execute("CREATE INDEX idx_user_meme_history_user_viewed ON user_meme_history(user_id, viewed_at)")
        
        # Insert sample memes for each category
        sample_memes = [
            # Faith category
            ('https://example.com/memes/faith/bible_budget.jpg', 'faith', 'When you tithe 10% but your budget is still in the red 📖💰', 'Meme showing Bible with budget spreadsheet, highlighting financial faith struggles', 1),
            ('https://example.com/memes/faith/prayer_credit_score.jpg', 'faith', 'Praying for a good credit score like it\'s a miracle 🙏💳', 'Cartoon person praying with credit score numbers floating above', 1),
            ('https://example.com/memes/faith/trust_god_bills.jpg', 'faith', 'Trusting God with my finances while staring at my bills 😅💸', 'Split image showing peaceful prayer on one side, overwhelming bills on the other', 1),
            
            # Work Life category
            ('https://example.com/memes/work_life/paycheck_vanishes.jpg', 'work_life', 'My paycheck: *exists for 0.2 seconds* *disappears into bills* 💸👻', 'Animated gif showing paycheck appearing and immediately vanishing', 1),
            ('https://example.com/memes/work_life/remote_work_savings.jpg', 'work_life', 'Working from home: Save on gas, spend on snacks. Net result: Still broke 🏠🍕', 'Split screen showing gas savings vs increased food delivery costs', 1),
            ('https://example.com/memes/work_life/meeting_expensive.jpg', 'work_life', 'This meeting could have been an email... and saved me $50 in coffee ☕💸', 'Office worker surrounded by expensive coffee cups during a video call', 1),
            
            # Health category
            ('https://example.com/memes/health/gym_membership.jpg', 'health', 'Gym membership: $50/month, Actually going: Priceless 💪😅', 'Person with gym bag looking at expensive membership card', 1),
            ('https://example.com/memes/health/healthy_food_expensive.jpg', 'health', 'Eating healthy: *wallet starts crying* 🥗💸', 'Person holding expensive organic vegetables with shocked expression', 1),
            ('https://example.com/memes/health/medical_bills.jpg', 'health', 'Medical bills: *exist* My bank account: *ceases to exist* 🏥💸', 'Medical bill with person holding empty wallet', 1),
            
            # Housing category
            ('https://example.com/memes/housing/rent_increase.jpg', 'housing', 'Rent increase: *happens* My budget: *has left the chat* 🏠💸', 'Apartment building with person holding rent increase notice', 1),
            ('https://example.com/memes/housing/mortgage_stress.jpg', 'housing', 'Mortgage payment: *exists* My stress level: *also exists* 🏡😰', 'House with person looking stressed while holding mortgage statement', 1),
            ('https://example.com/memes/housing/utilities_surprise.jpg', 'housing', 'Utility bills: *surprise attack* My bank account: *defeated* ⚡💸', 'Utility bills stacked high with shocked person', 1),
            
            # Transportation category
            ('https://example.com/memes/transportation/gas_prices.jpg', 'transportation', 'Gas prices: *go up* My car: *starts crying* ⛽😭', 'Gas pump showing high prices with car looking sad', 1),
            ('https://example.com/memes/transportation/car_repair.jpg', 'transportation', 'Car repair: *happens* My emergency fund: *disappears* 🚗💸', 'Car in repair shop with person holding expensive repair bill', 1),
            ('https://example.com/memes/transportation/uber_costs.jpg', 'transportation', 'Uber everywhere: *convenient* My bank account: *not convenient* 🚗💸', 'Uber app showing high costs with person looking shocked', 1),
            
            # Relationships category
            ('https://example.com/memes/relationships/date_night_budget.jpg', 'relationships', 'Date night budget: $50, Actual cost: $150, Love: Still priceless 💕💸', 'Romantic dinner scene with shocked expression at the bill', 1),
            ('https://example.com/memes/relationships/anniversary_gift.jpg', 'relationships', 'Anniversary gift: *checks bank account* "How about a nice card?" 💳💝', 'Person holding a simple card while expensive gifts are visible in background', 1),
            ('https://example.com/memes/relationships/wedding_costs.jpg', 'relationships', 'Wedding planning: *bank account starts crying* 💒😭', 'Wedding planner with calculator showing astronomical costs', 1),
            
            # Family category
            ('https://example.com/memes/family/expensive_kids.jpg', 'family', 'Kids: "I want this!" Me: "Do you want to eat this month?" 🍕👶', 'Parent pointing to expensive toy while child looks confused', 1),
            ('https://example.com/memes/family/college_fund.jpg', 'family', 'College fund: $0.00, Emergency fund: $0.00, My sanity: Also $0.00 🎓💸', 'Empty piggy bank with graduation cap and stressed parent', 1),
            ('https://example.com/memes/family/back_to_school.jpg', 'family', 'Back to school shopping: *entire paycheck disappears* 📚💸', 'Shopping cart full of school supplies with shocked parent holding empty wallet', 1),
        ]
        
        cursor.executemany("""
            INSERT INTO memes (image_url, category, caption, alt_text, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, sample_memes)
        
        conn.commit()
        
        # Verify the data
        cursor.execute("SELECT COUNT(*) FROM memes")
        total_memes = cursor.fetchone()[0]
        
        cursor.execute("SELECT category, COUNT(*) FROM memes GROUP BY category ORDER BY category")
        category_counts = cursor.fetchall()
        
        print(f"✅ Database created successfully!")
        print(f"📊 Total memes: {total_memes}")
        print("📂 Memes by category:")
        for category, count in category_counts:
            print(f"   {category}: {count} memes")
    
    print(f"\n🎉 Database fix completed!")
    print(f"📦 Original database backed up to: {backup_path}")
    print(f"🆕 New database created at: {db_path}")

if __name__ == "__main__":
    fix_database()
