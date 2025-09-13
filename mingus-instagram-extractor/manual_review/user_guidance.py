"""
User guidance and documentation for the manual review process.
"""

import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class UserGuidance:
    """Provides guidance and instructions for manual review process."""
    
    def __init__(self):
        self.estimated_time_per_item = 2.5  # minutes
        self.estimated_time_per_batch = 15  # minutes for 5-6 items
    
    def generate_instructions(self, review_statistics: Dict[str, Any]) -> str:
        """
        Generate comprehensive instructions for manual review process.
        
        Args:
            review_statistics: Statistics about items needing review
            
        Returns:
            Formatted instructions string
        """
        instructions = []
        
        # Header
        instructions.append("=" * 80)
        instructions.append("MANUAL REVIEW INSTRUCTIONS")
        instructions.append("=" * 80)
        
        # Overview
        instructions.extend(self._generate_overview_section(review_statistics))
        
        # Process steps
        instructions.extend(self._generate_process_steps())
        
        # Column explanations
        instructions.extend(self._generate_column_explanations())
        
        # Search strategies
        instructions.extend(self._generate_search_strategies())
        
        # Status guidelines
        instructions.extend(self._generate_status_guidelines())
        
        # Quality tips
        instructions.extend(self._generate_quality_tips())
        
        # Time estimates
        instructions.extend(self._generate_time_estimates(review_statistics))
        
        # Troubleshooting
        instructions.extend(self._generate_troubleshooting())
        
        # Footer
        instructions.append("\n" + "=" * 80)
        instructions.append("Good luck with your manual review!")
        instructions.append("=" * 80)
        
        return "\n".join(instructions)
    
    def _generate_overview_section(self, review_statistics: Dict[str, Any]) -> List[str]:
        """Generate overview section of instructions."""
        total_items = review_statistics.get('notes_needing_manual_review', 0)
        estimated_time = review_statistics.get('estimated_review_time_minutes', 0)
        
        return [
            f"\nOVERVIEW:",
            f"  You have {total_items} items that need manual review.",
            f"  Estimated time: {estimated_time:.0f} minutes ({estimated_time/60:.1f} hours)",
            f"  These items contain Instagram content but no direct URLs.",
            f"  Your task is to find the actual Instagram URLs for each item.",
            "",
            "WHAT YOU'LL BE DOING:",
            "  1. Review each item's description and search suggestions",
            "  2. Use the provided search links to find the actual Instagram post",
            "  3. Copy the correct Instagram URL to the 'resolved_url' column",
            "  4. Update the 'status' column based on your findings",
            "  5. Add notes if needed to explain your decision"
        ]
    
    def _generate_process_steps(self) -> List[str]:
        """Generate step-by-step process instructions."""
        return [
            "\nSTEP-BY-STEP PROCESS:",
            "",
            "STEP 1: Open the CSV file",
            "  • Use Excel, Google Sheets, or any spreadsheet application",
            "  • Save a backup copy before making changes",
            "",
            "STEP 2: Review each row",
            "  • Read the 'original_text' to understand the content",
            "  • Check the 'content_description' for key details",
            "  • Look at the 'suggested_search' for search options",
            "",
            "STEP 3: Search for the content",
            "  • Click on the suggested search links",
            "  • Use Instagram's search function",
            "  • Try different search terms if needed",
            "",
            "STEP 4: Find the correct post",
            "  • Look for posts that match the description",
            "  • Check the account name matches",
            "  • Verify the content type (post, reel, story, etc.)",
            "",
            "STEP 5: Copy the URL",
            "  • Copy the full Instagram URL from your browser",
            "  • Paste it into the 'resolved_url' column",
            "  • Update the 'status' column to 'resolved'",
            "",
            "STEP 6: Add notes if needed",
            "  • Use the 'notes' column to explain any issues",
            "  • Note if you found multiple similar posts",
            "  • Explain why you chose a particular post"
        ]
    
    def _generate_column_explanations(self) -> List[str]:
        """Generate explanations for each CSV column."""
        return [
            "\nCOLUMN EXPLANATIONS:",
            "",
            "note_id:",
            "  • Unique identifier for the note",
            "  • Don't modify this column",
            "",
            "original_text:",
            "  • The full text from the original note",
            "  • Use this to understand what content you're looking for",
            "",
            "account_name:",
            "  • The Instagram account mentioned in the note",
            "  • This should match the account of the post you find",
            "",
            "mentioned_users:",
            "  • Other users mentioned in the note",
            "  • These might be in the comments or tags",
            "",
            "content_description:",
            "  • Summary of the content with key details",
            "  • Includes account names, hashtags, and text snippets",
            "",
            "suggested_search:",
            "  • Pre-generated search links to help you find the content",
            "  • Click these links to start your search",
            "  • Includes Instagram profiles, hashtags, and Google searches",
            "",
            "category:",
            "  • Content category (comedy, fashion, food, etc.)",
            "  • Helps you understand what type of content to look for",
            "",
            "confidence:",
            "  • How confident the system is about the categorization",
            "  • Higher confidence = more likely to be correct",
            "",
            "status:",
            "  • Change this based on your findings:",
            "    - 'pending': Not yet reviewed (default)",
            "    - 'resolved': Found the correct Instagram URL",
            "    - 'not_found': Could not find the content",
            "    - 'unresolvable': Content is private, deleted, or inaccessible",
            "",
            "resolved_url:",
            "  • Paste the Instagram URL here when you find it",
            "  • Must be a valid Instagram post/reel/story URL",
            "  • Example: https://www.instagram.com/p/ABC123/",
            "",
            "notes:",
            "  • Add any additional information or explanations",
            "  • Explain why you chose a particular post",
            "  • Note any issues or special circumstances"
        ]
    
    def _generate_search_strategies(self) -> List[str]:
        """Generate search strategy recommendations."""
        return [
            "\nSEARCH STRATEGIES:",
            "",
            "1. USE SUGGESTED LINKS:",
            "  • Start with the provided Instagram profile links",
            "  • Check the account's recent posts",
            "  • Look for posts matching the description",
            "",
            "2. HASHTAG SEARCHES:",
            "  • Use the hashtag search links provided",
            "  • Browse recent posts with relevant hashtags",
            "  • Look for posts from the mentioned account",
            "",
            "3. GOOGLE SEARCHES:",
            "  • Use the Google search links for broader results",
            "  • Try different combinations of keywords",
            "  • Look for Instagram links in the results",
            "",
            "4. INSTAGRAM SEARCH:",
            "  • Use Instagram's built-in search function",
            "  • Search for the account name directly",
            "  • Try searching for key phrases from the description",
            "",
            "5. TIME-BASED SEARCHES:",
            "  • Check recent posts first (last few days)",
            "  • Look at posts from the last week if not found",
            "  • Check older posts if the content seems older",
            "",
            "6. CONTENT TYPE FILTERS:",
            "  • Use Instagram's content type filters (Posts, Reels, etc.)",
            "  • Check both regular posts and reels",
            "  • Look at stories if the content seems recent"
        ]
    
    def _generate_status_guidelines(self) -> List[str]:
        """Generate guidelines for setting status values."""
        return [
            "\nSTATUS GUIDELINES:",
            "",
            "RESOLVED:",
            "  • You found the exact Instagram post/reel/story",
            "  • The content matches the description",
            "  • The account name matches",
            "  • You've copied the URL to 'resolved_url'",
            "",
            "NOT_FOUND:",
            "  • You searched thoroughly but couldn't find the content",
            "  • The account exists but the specific post isn't there",
            "  • The content might be from a different account",
            "  • Add explanation in 'notes' column",
            "",
            "UNRESOLVABLE:",
            "  • The account is private and you can't see posts",
            "  • The content has been deleted",
            "  • The account no longer exists",
            "  • The content is from a different platform",
            "  • Add explanation in 'notes' column",
            "",
            "PENDING:",
            "  • You haven't reviewed this item yet",
            "  • You started but need to come back to it later",
            "  • This is the default status for new items"
        ]
    
    def _generate_quality_tips(self) -> List[str]:
        """Generate quality assurance tips."""
        return [
            "\nQUALITY TIPS:",
            "",
            "ACCURACY:",
            "  • Double-check that the URL is correct",
            "  • Make sure the post matches the description",
            "  • Verify the account name matches",
            "  • Check that it's the right content type (post vs reel)",
            "",
            "URL FORMAT:",
            "  • Instagram URLs should start with https://www.instagram.com/",
            "  • Posts: /p/ followed by the post ID",
            "  • Reels: /reel/ followed by the reel ID",
            "  • Stories: /stories/username/story_id",
            "  • TV: /tv/ followed by the TV ID",
            "",
            "COMMON MISTAKES TO AVOID:",
            "  • Don't copy profile URLs instead of post URLs",
            "  • Don't copy URLs from other social media platforms",
            "  • Don't copy shortened URLs (bit.ly, etc.)",
            "  • Don't copy URLs that redirect to Instagram",
            "",
            "WHEN IN DOUBT:",
            "  • If you find multiple similar posts, choose the most recent one",
            "  • If the account name doesn't match exactly, check if it's a variation",
            "  • If you're unsure, mark as 'not_found' and add notes",
            "  • It's better to be conservative than to guess"
        ]
    
    def _generate_time_estimates(self, review_statistics: Dict[str, Any]) -> List[str]:
        """Generate time estimates for the review process."""
        total_items = review_statistics.get('notes_needing_manual_review', 0)
        estimated_time = review_statistics.get('estimated_review_time_minutes', 0)
        
        return [
            "\nTIME ESTIMATES:",
            "",
            f"TOTAL TIME:",
            f"  • {total_items} items × {self.estimated_time_per_item} minutes = {estimated_time:.0f} minutes",
            f"  • That's about {estimated_time/60:.1f} hours total",
            "",
            "BATCH PROCESSING:",
            f"  • Process {int(60/self.estimated_time_per_item)} items per hour",
            f"  • Take breaks every {self.estimated_time_per_batch} minutes",
            f"  • Work in batches of 5-6 items for best efficiency",
            "",
            "TIME-SAVING TIPS:",
            "  • Use the suggested search links (saves 30-60 seconds per item)",
            "  • Start with the most obvious matches first",
            "  • Skip difficult items and come back to them later",
            "  • Use keyboard shortcuts for copy/paste",
            "  • Keep Instagram open in a separate tab for quick switching",
            "",
            "IF YOU'RE RUNNING BEHIND:",
            "  • Focus on items with high confidence scores first",
            "  • Mark obvious 'not_found' items quickly",
            "  • Come back to difficult items later",
            "  • Consider asking for help with particularly tricky items"
        ]
    
    def _generate_troubleshooting(self) -> List[str]:
        """Generate troubleshooting section."""
        return [
            "\nTROUBLESHOOTING:",
            "",
            "CAN'T FIND THE POST:",
            "  • Try different search terms",
            "  • Check if the account name has variations",
            "  • Look at older posts (scroll down)",
            "  • Check if it's a reel instead of a post",
            "  • Try searching for key phrases from the description",
            "",
            "ACCOUNT NAME DOESN'T MATCH:",
            "  • Check for typos in the original text",
            "  • Look for username variations (underscores, dots, etc.)",
            "  • The account might have changed its name",
            "  • Check if it's a different account with similar content",
            "",
            "MULTIPLE SIMILAR POSTS:",
            "  • Choose the one that best matches the description",
            "  • Pick the most recent one if they're very similar",
            "  • Add a note explaining your choice",
            "  • If unsure, mark as 'not_found' and explain",
            "",
            "PRIVATE ACCOUNTS:",
            "  • Mark as 'unresolvable' if you can't see the posts",
            "  • Add a note explaining the account is private",
            "  • Don't try to guess the content",
            "",
            "TECHNICAL ISSUES:",
            "  • Make sure you're copying the full URL",
            "  • Check that the URL starts with https://",
            "  • Try refreshing the page if links don't work",
            "  • Clear your browser cache if needed",
            "",
            "NEED HELP:",
            "  • Check the 'content_description' for more clues",
            "  • Look at the 'suggested_search' for additional options",
            "  • Ask a colleague for a second opinion",
            "  • Mark as 'not_found' if you've tried everything"
        ]
    
    def generate_quick_reference(self) -> str:
        """Generate a quick reference card for the review process."""
        return """
QUICK REFERENCE CARD
===================

STATUS VALUES:
• resolved    = Found the correct Instagram URL
• not_found   = Searched but couldn't find it
• unresolvable = Private/deleted/inaccessible
• pending     = Not yet reviewed

URL FORMATS:
• Post:  https://www.instagram.com/p/ABC123/
• Reel:  https://www.instagram.com/reel/ABC123/
• Story: https://www.instagram.com/stories/username/123456789/
• TV:    https://www.instagram.com/tv/ABC123/

SEARCH ORDER:
1. Click suggested Instagram profile links
2. Check hashtag search links
3. Try Google search links
4. Use Instagram's search function
5. Try different keywords

QUALITY CHECK:
✓ URL starts with https://www.instagram.com/
✓ Account name matches
✓ Content matches description
✓ Right content type (post/reel/story)

TIME: ~2.5 minutes per item
"""
    
    def generate_example_resolutions(self) -> List[Dict[str, str]]:
        """Generate example resolutions for common scenarios."""
        return [
            {
                "scenario": "Found exact match",
                "original_text": "Black and CULTivated on Instagram: '@gabrielbthatguy killed me with this sketch...'",
                "account_name": "gabrielbthatguy",
                "resolved_url": "https://www.instagram.com/p/ABC123DEF456/",
                "status": "resolved",
                "notes": "Found the exact sketch post from @gabrielbthatguy"
            },
            {
                "scenario": "Found similar content",
                "original_text": "Check out this amazing dance video from @dancer123",
                "account_name": "dancer123",
                "resolved_url": "https://www.instagram.com/reel/XYZ789GHI012/",
                "status": "resolved",
                "notes": "Found a recent dance reel, might be the one referenced"
            },
            {
                "scenario": "Account is private",
                "original_text": "Saw this cool art from @private_artist",
                "account_name": "private_artist",
                "resolved_url": "",
                "status": "unresolvable",
                "notes": "Account is private, cannot see posts"
            },
            {
                "scenario": "Could not find",
                "original_text": "This funny video from @comedian123 was hilarious",
                "account_name": "comedian123",
                "resolved_url": "",
                "status": "not_found",
                "notes": "Searched through recent posts but couldn't find this specific video"
            },
            {
                "scenario": "Multiple similar posts",
                "original_text": "Love this fashion post from @style_guru",
                "account_name": "style_guru",
                "resolved_url": "https://www.instagram.com/p/MNO345PQR678/",
                "status": "resolved",
                "notes": "Found several similar fashion posts, chose the most recent one"
            }
        ]
