# Manual Review System for Instagram Content

This system provides a comprehensive solution for manually reviewing Instagram content that doesn't have direct URLs, such as rich text previews from Mac Notes.

## Overview

The manual review system handles Instagram content that appears as rich text previews like:
> "Black and CULTivated on Instagram: '@gabrielbthatguy killed me with this sketch...'"

Rather than direct URLs like:
> "https://www.instagram.com/p/ABC123DEF456/"

## Features

### 🔍 CSV Generation
- Exports rich text content to spreadsheet format
- Includes original text, extracted account names, mentions
- Provides Instagram search suggestions for each item
- Adds category assignments and confidence scores

### 🔗 Search Suggestion Generation
- Creates Instagram search URLs: `https://instagram.com/[username]`
- Generates keyword-based search terms
- Provides Google search alternatives
- Includes time-based search strategies

### 📊 Resolution Workflow
- User manually searches Instagram using suggestions
- Finds actual post URLs that match descriptions
- Fills in resolved_url column in spreadsheet
- Imports completed spreadsheet back into system

### ✅ Quality Control
- Validates resolved URLs are legitimate
- Checks account names align with resolved content
- Flags potential duplicates across entries
- Generates resolution statistics

### 📈 Progress Tracking
- Shows completion percentage of manual review
- Tracks which items still need resolution
- Provides restart capability for interrupted sessions
- Generates final statistics on resolution success

## Quick Start

### 1. Generate Manual Review CSV

Run the main extraction script:
```bash
python extract_instagram.py
```

If manual review is needed, the system will automatically:
- Generate a CSV file with items needing review
- Create detailed instructions
- Provide a quick reference card

### 2. Complete Manual Review

1. Open the generated CSV file in Excel or Google Sheets
2. Read the instructions file for detailed guidance
3. Use the suggested search links to find Instagram URLs
4. Fill in the `resolved_url` and `status` columns
5. Add notes if needed

### 3. Import Resolved CSV

```bash
python import_resolved_csv.py extracted_content/manual_review_YYYYMMDD_HHMMSS.csv
```

### 4. Merge with Direct URLs

```bash
python merge_instagram_content.py extracted_content/resolved_content_YYYYMMDD_HHMMSS.json extracted_content/mingus_notes_YYYYMMDD_HHMMSS.json
```

## CSV Format

The manual review CSV contains the following columns:

| Column | Description |
|--------|-------------|
| `note_id` | Unique identifier for the note |
| `original_text` | The full text from the original note |
| `account_name` | The Instagram account mentioned in the note |
| `mentioned_users` | Other users mentioned in the note |
| `content_description` | Summary with key details |
| `suggested_search` | Pre-generated search links |
| `category` | Content category (comedy, fashion, etc.) |
| `confidence` | Confidence level of categorization |
| `status` | Review status (pending/resolved/not_found/unresolvable) |
| `resolved_url` | Instagram URL when found |
| `notes` | Additional notes or explanations |

## Status Values

- **`pending`**: Not yet reviewed (default)
- **`resolved`**: Found the correct Instagram URL
- **`not_found`**: Could not find the content
- **`unresolvable`**: Content is private, deleted, or inaccessible

## Search Strategies

### 1. Use Suggested Links
- Start with provided Instagram profile links
- Check the account's recent posts
- Look for posts matching the description

### 2. Hashtag Searches
- Use the hashtag search links provided
- Browse recent posts with relevant hashtags
- Look for posts from the mentioned account

### 3. Google Searches
- Use the Google search links for broader results
- Try different combinations of keywords
- Look for Instagram links in the results

### 4. Instagram Search
- Use Instagram's built-in search function
- Search for the account name directly
- Try searching for key phrases from the description

### 5. Time-Based Searches
- Check recent posts first (last few days)
- Look at posts from the last week if not found
- Check older posts if the content seems older

## Quality Tips

### Accuracy
- Double-check that the URL is correct
- Make sure the post matches the description
- Verify the account name matches
- Check that it's the right content type (post vs reel)

### URL Format
- Instagram URLs should start with `https://www.instagram.com/`
- Posts: `/p/` followed by the post ID
- Reels: `/reel/` followed by the reel ID
- Stories: `/stories/username/story_id`
- TV: `/tv/` followed by the TV ID

### Common Mistakes to Avoid
- Don't copy profile URLs instead of post URLs
- Don't copy URLs from other social media platforms
- Don't copy shortened URLs (bit.ly, etc.)
- Don't copy URLs that redirect to Instagram

## Time Estimates

- **Per item**: ~2.5 minutes
- **Per batch**: ~15 minutes (5-6 items)
- **Total time**: Varies based on number of items

### Time-Saving Tips
- Use the suggested search links (saves 30-60 seconds per item)
- Start with the most obvious matches first
- Skip difficult items and come back to them later
- Use keyboard shortcuts for copy/paste
- Keep Instagram open in a separate tab for quick switching

## Troubleshooting

### Can't Find the Post
- Try different search terms
- Check if the account name has variations
- Look at older posts (scroll down)
- Check if it's a reel instead of a post
- Try searching for key phrases from the description

### Account Name Doesn't Match
- Check for typos in the original text
- Look for username variations (underscores, dots, etc.)
- The account might have changed its name
- Check if it's a different account with similar content

### Multiple Similar Posts
- Choose the one that best matches the description
- Pick the most recent one if they're very similar
- Add a note explaining your choice
- If unsure, mark as 'not_found' and explain

### Private Accounts
- Mark as 'unresolvable' if you can't see the posts
- Add a note explaining the account is private
- Don't try to guess the content

## File Structure

```
manual_review/
├── __init__.py
├── csv_generator.py          # CSV generation for manual review
├── search_suggestions.py     # Search suggestion generation
├── resolution_workflow.py    # Import and process resolved CSVs
├── quality_control.py        # Quality control and validation
├── user_guidance.py          # User instructions and guidance
├── progress_tracking.py      # Progress tracking and statistics
└── manual_review_manager.py  # Main manager class
```

## Output Files

The system generates several output files:

- **`manual_review_YYYYMMDD_HHMMSS.csv`**: CSV file for manual review
- **`manual_review_instructions.txt`**: Detailed instructions
- **`quick_reference.txt`**: Quick reference card
- **`resolved_content_YYYYMMDD_HHMMSS.json`**: Processed resolved items
- **`quality_report.txt`**: Quality control report
- **`combined_instagram_content_YYYYMMDD_HHMMSS.json`**: Final combined results

## Example Workflow

1. **Extract content**: Run `python extract_instagram.py`
2. **Review CSV**: Open the generated CSV file
3. **Search Instagram**: Use suggested links to find posts
4. **Fill in URLs**: Copy Instagram URLs to resolved_url column
5. **Update status**: Mark items as resolved/not_found/unresolvable
6. **Import results**: Run `python import_resolved_csv.py`
7. **Merge content**: Run `python merge_instagram_content.py`
8. **Use results**: Process the combined Instagram URLs

## Best Practices

1. **Work in batches**: Process 5-6 items at a time
2. **Take breaks**: Don't work for more than 30 minutes straight
3. **Be consistent**: Use the same criteria for marking items
4. **Document issues**: Add notes for difficult or unusual cases
5. **Double-check**: Verify URLs before marking as resolved
6. **Ask for help**: Don't spend too much time on difficult items

## Support

If you encounter issues:

1. Check the log file for error messages
2. Review the quality report for validation issues
3. Consult the instructions file for detailed guidance
4. Use the quick reference card for quick help
5. Check the troubleshooting section above

## Statistics and Reporting

The system provides comprehensive statistics:

- **Progress tracking**: Completion percentage, time estimates
- **Quality metrics**: Valid URLs, duplicate detection
- **Resolution rates**: Success rates by category
- **Time analysis**: Average time per item, remaining estimates

Use these statistics to:
- Track your progress
- Identify areas for improvement
- Estimate completion times
- Monitor quality of resolutions
