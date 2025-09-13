#!/usr/bin/env python3
"""
Generate title suggestions based on content analysis for the Mingus splash screen.
"""

import json
from pathlib import Path
from datetime import datetime
from enhanced_local_notes_processor import EnhancedLocalNotesProcessor

def generate_title_suggestions():
    """Generate title suggestions based on content analysis."""
    
    print("🔍 Analyzing content for title suggestions...")
    
    # Initialize enhanced processor
    processor = EnhancedLocalNotesProcessor()
    result = processor.process_all_local_notes()
    
    if not result['success']:
        print(f"❌ Processing failed: {result['error_message']}")
        return
    
    # Analyze content patterns
    category_counts = result['category_breakdown']
    total_notes = result['total_notes']
    
    # Generate suggestions based on "Be. Do. Have." philosophy
    suggestions = []
    
    # BE - Identity, Character, Values, Mindset
    be_suggestions = [
        "Be Present",
        "Be Authentic", 
        "Be Grateful",
        "Be Mindful",
        "Be Intentional",
        "Be Courageous",
        "Be Kind",
        "Be Patient",
        "Be Curious",
        "Be Resilient",
        "Be Yourself",
        "Be the Change",
        "Be Inspired",
        "Be Grounded",
        "Be Open",
        "Be Strong",
        "Be Gentle",
        "Be Wise",
        "Be Joyful",
        "Be Peaceful"
    ]
    
    # DO - Actions, Habits, Practices, Goals
    do_suggestions = [
        "Do What Matters",
        "Do Your Best",
        "Do the Work",
        "Do Something New",
        "Do It Daily",
        "Do It Now",
        "Do It Right",
        "Do It with Love",
        "Do It Consistently",
        "Do It Mindfully",
        "Do It with Purpose",
        "Do It with Joy",
        "Do It with Gratitude",
        "Do It with Intention",
        "Do It with Passion",
        "Do It with Patience",
        "Do It with Courage",
        "Do It with Kindness",
        "Do It with Focus",
        "Do It with Heart"
    ]
    
    # HAVE - Results, Possessions, Experiences, Achievements
    have_suggestions = [
        "Have Purpose",
        "Have Clarity",
        "Have Peace",
        "Have Joy",
        "Have Balance",
        "Have Growth",
        "Have Connection",
        "Have Gratitude",
        "Have Abundance",
        "Have Wisdom",
        "Have Love",
        "Have Success",
        "Have Fulfillment",
        "Have Freedom",
        "Have Health",
        "Have Wealth",
        "Have Happiness",
        "Have Contentment",
        "Have Impact",
        "Have Legacy"
    ]
    
    # Time-based BE suggestions
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        suggestions.extend([
            "Be Present This Morning",
            "Be Grateful for Today",
            "Be Intentional Today",
            "Be Mindful This Morning"
        ])
    elif 12 <= current_hour < 17:
        suggestions.extend([
            "Be Focused This Afternoon",
            "Be Productive Today",
            "Be Present Now",
            "Be Mindful This Moment"
        ])
    elif 17 <= current_hour < 21:
        suggestions.extend([
            "Be Grateful This Evening",
            "Be Reflective Tonight",
            "Be Peaceful This Evening",
            "Be Present This Moment"
        ])
    else:
        suggestions.extend([
            "Be Still Tonight",
            "Be Grateful Today",
            "Be Mindful This Moment",
            "Be Present Now"
        ])
    
    # Add core BE.DO.HAVE suggestions
    suggestions.extend(be_suggestions[:8])  # Top 8 BE suggestions
    suggestions.extend(do_suggestions[:6])  # Top 6 DO suggestions  
    suggestions.extend(have_suggestions[:6])  # Top 6 HAVE suggestions
    
    # Category-based BE.DO.HAVE suggestions
    top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    for category, count in top_categories:
        if category == 'faith':
            suggestions.extend([
                "Be Faithful",
                "Do God's Work",
                "Have Spiritual Peace",
                "Be Grateful for Grace",
                "Do What's Right",
                "Have Divine Purpose"
            ])
        elif category == 'work_life':
            suggestions.extend([
                "Be Professional",
                "Do Your Best Work",
                "Have Career Success",
                "Be Productive",
                "Do What Matters",
                "Have Professional Growth"
            ])
        elif category == 'children':
            suggestions.extend([
                "Be a Loving Parent",
                "Do What's Best for Them",
                "Have Family Joy",
                "Be Patient",
                "Do It with Love",
                "Have Precious Moments"
            ])
        elif category == 'friendships':
            suggestions.extend([
                "Be a Good Friend",
                "Do What Friends Do",
                "Have True Connections",
                "Be Supportive",
                "Do It Together",
                "Have Lasting Bonds"
            ])
        elif category == 'relationships':
            suggestions.extend([
                "Be Loving",
                "Do It with Heart",
                "Have Deep Connection",
                "Be Committed",
                "Do It Daily",
                "Have True Love"
            ])
        elif category == 'going_out':
            suggestions.extend([
                "Be Adventurous",
                "Do New Things",
                "Have Amazing Experiences",
                "Be Curious",
                "Do It with Joy",
                "Have Wonderful Memories"
            ])
    
    # Content-based BE.DO.HAVE suggestions
    if result['notes_with_instagram'] > 0:
        suggestions.extend([
            "Be Visual",
            "Do It Creatively",
            "Have Beautiful Moments",
            "Be Inspiring",
            "Do It with Style",
            "Have Visual Stories"
        ])
    
    # Personalization based on content volume
    if total_notes > 1000:
        suggestions.extend([
            "Be Rich in Content",
            "Do It Consistently",
            "Have a Rich Collection",
            "Be Abundant",
            "Do It Daily",
            "Have a Full Life"
        ])
    
    # Remove duplicates and limit to 20 suggestions
    suggestions = list(dict.fromkeys(suggestions))[:20]
    
    # Create title suggestions data
    title_data = {
        "title_suggestions": {
            "generated_at": datetime.now().isoformat(),
            "total_notes_analyzed": total_notes,
            "categories_analyzed": len(category_counts),
            "suggestions": suggestions,
            "category_breakdown": category_counts,
            "top_categories": [cat for cat, _ in top_categories]
        }
    }
    
    # Save to API directory
    api_dir = Path("mingus_api")
    api_dir.mkdir(exist_ok=True)
    
    with open(api_dir / "title_suggestions.json", "w") as f:
        json.dump(title_data, f, indent=2)
    
    print(f"✅ Generated {len(suggestions)} title suggestions")
    print(f"📄 Saved to: {api_dir / 'title_suggestions.json'}")
    
    # Display suggestions
    print(f"\n🎯 Title Suggestions:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"   {i:2d}. {suggestion}")
    
    return title_data

if __name__ == "__main__":
    generate_title_suggestions()
