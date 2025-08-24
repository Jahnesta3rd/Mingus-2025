#!/usr/bin/env python3
"""
Analyze article data files to understand the distribution
"""
import json
import os
import sys

def analyze_file(filename):
    """Analyze a JSON file and return article statistics"""
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            return None
            
        print(f"\n📊 {filename}:")
        print(f"   Total articles: {len(data)}")
        
        if len(data) == 0:
            print("   ⚠️  File is empty")
            return None
        
        # Phase distribution
        phases = {}
        difficulties = {}
        domains = {}
        
        for article in data:
            phase = article.get('primary_phase', 'Unknown')
            phases[phase] = phases.get(phase, 0) + 1
            
            difficulty = article.get('difficulty_level', 'Unknown')
            difficulties[difficulty] = difficulties.get(difficulty, 0) + 1
            
            url = article.get('url', '')
            if url:
                domain = url.split('/')[2] if len(url.split('/')) > 2 else 'unknown'
                domains[domain] = domains.get(domain, 0) + 1
        
        print("   Phase distribution:")
        for phase, count in phases.items():
            percentage = (count / len(data)) * 100
            print(f"     {phase}: {count} ({percentage:.1f}%)")
        
        print("   Difficulty distribution:")
        for difficulty, count in difficulties.items():
            percentage = (count / len(data)) * 100
            print(f"     {difficulty}: {count} ({percentage:.1f}%)")
        
        print("   Top domains:")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:3]:
            percentage = (count / len(data)) * 100
            print(f"     {domain}: {count} ({percentage:.1f}%)")
        
        return len(data)
        
    except Exception as e:
        print(f"   ❌ Error reading {filename}: {e}")
        return None

def main():
    """Main analysis function"""
    print("🔍 Article Data Analysis")
    print("=" * 50)
    
    files_to_analyze = [
        'data/classified_articles_complete.json',
        'data/be_phase_articles.json',
        'data/do_phase_articles.json', 
        'data/have_phase_articles.json',
        'data/high_confidence_classifications.json'
    ]
    
    total_articles = 0
    file_counts = {}
    
    for filename in files_to_analyze:
        count = analyze_file(filename)
        if count is not None:
            file_counts[filename] = count
            total_articles += count
    
    print(f"\n📈 Summary:")
    print(f"   Total articles across all files: {total_articles}")
    print(f"   Files with data: {len(file_counts)}")
    
    if file_counts:
        print("   Articles per file:")
        for filename, count in file_counts.items():
            print(f"     {filename}: {count}")

if __name__ == "__main__":
    main()
