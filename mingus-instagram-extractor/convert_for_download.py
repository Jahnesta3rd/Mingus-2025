#!/usr/bin/env python3
"""
Convert extracted Instagram URLs to format compatible with Instagram downloader
"""

import json
import sys
from pathlib import Path

def convert_instagram_data(input_file, output_file):
    """Convert Instagram data to downloader format."""
    
    # Load the extracted data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert to downloader format
    download_items = []
    
    for note in data['notes']:
        for url in note['instagram_urls']:
            # Determine content type
            if '/reel/' in url:
                content_type = 'video'
            elif '/tv/' in url:
                content_type = 'video'
            elif '/stories/' in url:
                content_type = 'video'
            else:
                content_type = 'image'
            
            # Create download item
            item = {
                'url': url,
                'category': 'uncategorized',
                'caption': note.get('title', 'Untitled'),
                'alt_text': '',
                'creator_credit': '',
                'creator_link': '',
                'permission_status': 'unknown',
                'notes': note.get('content', '')[:200],
                'original_note_id': str(note.get('note_id', '')),
                'content_type': content_type,
                'post_id': url.split('/')[-1].rstrip('/')
            }
            download_items.append(item)
    
    # Save in downloader format
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(download_items, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Converted {len(download_items)} URLs to downloader format")
    print(f"📄 Saved to: {output_file}")
    
    return output_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_for_download.py <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "download_data.json"
    
    convert_instagram_data(input_file, output_file)
