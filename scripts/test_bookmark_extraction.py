#!/usr/bin/env python3
"""
Test version of bookmark extraction to show all bookmarks and filtering process
"""

import json
import urllib.parse
from pathlib import Path

# Financial/career keywords for filtering
FINANCIAL_KEYWORDS = [
    'finance', 'financial', 'money', 'investment', 'investing', 'wealth', 'budget',
    'saving', 'retirement', '401k', 'ira', 'stock', 'market', 'trading', 'portfolio',
    'credit', 'debt', 'loan', 'mortgage', 'insurance', 'tax', 'taxes', 'accounting',
    'banking', 'bank', 'credit union', 'payroll', 'salary', 'income', 'revenue',
    'profit', 'loss', 'expense', 'cash', 'cashflow', 'dividend', 'interest',
    'compound', 'inflation', 'deflation', 'recession', 'economy', 'economic'
]

CAREER_KEYWORDS = [
    'career', 'job', 'employment', 'work', 'professional', 'business', 'entrepreneur',
    'startup', 'company', 'corporate', 'office', 'workplace', 'leadership', 'management',
    'executive', 'ceo', 'cfo', 'cto', 'director', 'manager', 'supervisor', 'team',
    'resume', 'cv', 'interview', 'hiring', 'recruitment', 'hr', 'human resources',
    'salary', 'compensation', 'benefits', 'promotion', 'advancement', 'skills',
    'training', 'education', 'certification', 'degree', 'mba', 'phd', 'mentor',
    'networking', 'linkedin', 'professional development', 'workshop', 'conference',
    'industry', 'sector', 'market', 'competition', 'strategy', 'planning'
]

AFRICAN_AMERICAN_PROFESSIONAL_KEYWORDS = [
    'diversity', 'inclusion', 'equity', 'black', 'african american', 'minority',
    'representation', 'mentorship', 'networking', 'professional development',
    'career advancement', 'leadership', 'executive', 'board', 'director',
    'entrepreneur', 'business owner', 'startup', 'wealth building', 'financial literacy',
    'community', 'advocacy', 'empowerment', 'success', 'achievement', 'excellence',
    'role model', 'inspiration', 'motivation', 'perseverance', 'resilience'
]

def is_relevant_bookmark(bookmark):
    """Check if bookmark is relevant to financial/career content"""
    url = bookmark.get('url', '').lower()
    title = bookmark.get('title', '').lower()
    
    # Check for financial/career keywords
    all_keywords = FINANCIAL_KEYWORDS + CAREER_KEYWORDS + AFRICAN_AMERICAN_PROFESSIONAL_KEYWORDS
    
    for keyword in all_keywords:
        if keyword in url or keyword in title:
            return True
    
    # Check for common financial/career domains
    financial_domains = [
        'bloomberg.com', 'reuters.com', 'wsj.com', 'ft.com', 'cnbc.com',
        'marketwatch.com', 'yahoo.com/finance', 'finance.yahoo.com',
        'morningstar.com', 'fool.com', 'investopedia.com', 'nerdwallet.com',
        'creditkarma.com', 'mint.com', 'personalcapital.com', 'betterment.com',
        'wealthfront.com', 'robinhood.com', 'tdameritrade.com', 'fidelity.com',
        'vanguard.com', 'schwab.com', 'etrade.com', 'linkedin.com',
        'glassdoor.com', 'indeed.com', 'monster.com', 'careerbuilder.com',
        'ziprecruiter.com', 'dice.com', 'angel.co', 'crunchbase.com'
    ]
    
    for domain in financial_domains:
        if domain in url:
            return True
    
    return False

def extract_chrome_bookmarks():
    """Extract all bookmarks from Chrome"""
    bookmarks = []
    
    chrome_path = Path.home() / "Library/Application Support/Google/Chrome/Default/Bookmarks"
    if not chrome_path.exists():
        print(f"❌ Chrome bookmarks not found at: {chrome_path}")
        return bookmarks
    
    try:
        with open(chrome_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        def extract_bookmarks_recursive(obj, folder_name=""):
            if isinstance(obj, dict):
                if obj.get('type') == 'url':
                    bookmark = {
                        'url': obj.get('url', ''),
                        'title': obj.get('name', ''),
                        'date_added': obj.get('date_added', ''),
                        'folder': folder_name,
                        'browser': 'Chrome'
                    }
                    bookmarks.append(bookmark)
                elif obj.get('type') == 'folder':
                    folder_name = obj.get('name', '')
                    for child in obj.get('children', []):
                        extract_bookmarks_recursive(child, folder_name)
                else:
                    for child in obj.get('children', []):
                        extract_bookmarks_recursive(child, folder_name)
        
        # Extract from bookmarks bar
        if 'roots' in data:
            if 'bookmark_bar' in data['roots']:
                extract_bookmarks_recursive(data['roots']['bookmark_bar'], 'Bookmarks Bar')
            if 'other' in data['roots']:
                extract_bookmarks_recursive(data['roots']['other'], 'Other Bookmarks')
        
        return bookmarks
        
    except Exception as e:
        print(f"❌ Error extracting Chrome bookmarks: {e}")
        return bookmarks

def main():
    print("🔍 Testing Bookmark Extraction and Filtering")
    print("=" * 50)
    
    # Extract all bookmarks
    all_bookmarks = extract_chrome_bookmarks()
    print(f"📊 Total bookmarks found: {len(all_bookmarks)}")
    
    if not all_bookmarks:
        print("❌ No bookmarks found in Chrome")
        return
    
    print("\n📋 All Bookmarks:")
    print("-" * 50)
    
    relevant_bookmarks = []
    for i, bookmark in enumerate(all_bookmarks):
        is_relevant = is_relevant_bookmark(bookmark)
        status = "✅ RELEVANT" if is_relevant else "❌ NOT RELEVANT"
        
        print(f"{i+1}. {bookmark['title']}")
        print(f"   URL: {bookmark['url']}")
        print(f"   Folder: {bookmark['folder']}")
        print(f"   Status: {status}")
        print()
        
        if is_relevant:
            relevant_bookmarks.append(bookmark)
    
    print("=" * 50)
    print(f"📈 Summary:")
    print(f"   Total bookmarks: {len(all_bookmarks)}")
    print(f"   Relevant bookmarks: {len(relevant_bookmarks)}")
    print(f"   Relevance rate: {len(relevant_bookmarks)/len(all_bookmarks)*100:.1f}%")
    
    if not relevant_bookmarks:
        print("\n💡 No relevant bookmarks found. This could be because:")
        print("   1. Your bookmarks don't contain financial/career keywords")
        print("   2. The filtering is too strict")
        print("   3. You need to add more financial/career bookmarks")
        print("\n🔍 Keywords the script looks for:")
        print("   Financial: " + ", ".join(FINANCIAL_KEYWORDS[:10]) + "...")
        print("   Career: " + ", ".join(CAREER_KEYWORDS[:10]) + "...")
        print("   Cultural: " + ", ".join(AFRICAN_AMERICAN_PROFESSIONAL_KEYWORDS[:10]) + "...")
    
    print("\n🎯 To add relevant bookmarks, consider bookmarking:")
    print("   - Financial news sites (Bloomberg, Reuters, WSJ)")
    print("   - Career development sites (LinkedIn, Glassdoor)")
    print("   - Investment platforms (Fidelity, Vanguard)")
    print("   - Professional development resources")
    print("   - African American professional content")

if __name__ == "__main__":
    main()
