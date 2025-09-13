#!/usr/bin/env python3
"""
Demo script for the Instagram Extraction CLI

This script demonstrates the CLI functionality with sample commands.
"""

import subprocess
import sys
import time
from pathlib import Path

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*80}")
    print(f"{title.center(80)}")
    print(f"{'='*80}")

def print_step(step, description):
    """Print a step description."""
    print(f"\n🔹 STEP {step}: {description}")
    print("-" * 60)

def run_demo_command(cmd, description, show_output=True):
    """Run a demo command."""
    print(f"\n💻 Command: {cmd}")
    print(f"📝 Description: {description}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if show_output and result.stdout:
            print(f"\n📤 Output:")
            print(result.stdout)
        
        if result.stderr and "error" in result.stderr.lower():
            print(f"\n⚠️  Warnings/Errors:")
            print(result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out (this is normal for some commands)")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run the demo."""
    print_header("INSTAGRAM EXTRACTION CLI DEMO")
    
    print("""
This demo will show you the main features of the Instagram Extraction CLI.
The commands will be run with safe options to demonstrate functionality.

Note: Some commands may take time or require actual data to work properly.
This is a demonstration of the interface and command structure.
    """)
    
    # Auto-continue for non-interactive demo
    print("Running demo automatically...")
    time.sleep(1)
    
    # Step 1: Help and basic commands
    print_step(1, "Help and Basic Commands")
    
    demo_commands = [
        ("python extract_instagram.py --help", "Main help - shows all available commands"),
        ("python extract_instagram.py validate-folder --help", "Validate folder help"),
        ("python extract_instagram.py extract-content --help", "Extract content help"),
        ("python extract_instagram.py download --help", "Download help"),
    ]
    
    for cmd, description in demo_commands:
        run_demo_command(cmd, description, show_output=False)
        time.sleep(0.5)  # Brief pause between commands
    
    # Step 2: Validation
    print_step(2, "Folder Validation")
    
    print("""
The validate-folder command checks if your MINGUS folder exists and shows statistics.
This is the first step in any workflow.
    """)
    
    run_demo_command(
        "python extract_instagram.py validate-folder",
        "Validate MINGUS folder (may show errors if folder doesn't exist - this is normal for demo)"
    )
    
    time.sleep(1)
    
    # Step 3: Extraction with dry run
    print_step(3, "Content Extraction (Dry Run)")
    
    print("""
The extract-content command extracts Instagram content from your MINGUS folder.
Using --dry-run shows what would be done without actually doing it.
    """)
    
    run_demo_command(
        "python extract_instagram.py extract-content --dry-run --limit 5",
        "Extract content with dry run and limit (safe for demo)"
    )
    
    time.sleep(1)
    
    # Step 4: Manual review
    print_step(4, "Manual Review Export")
    
    print("""
The manual-review command exports items that need manual resolution to a CSV file.
This is used when Instagram URLs can't be automatically detected.
    """)
    
    run_demo_command(
        "python extract_instagram.py manual-review export",
        "Export manual review CSV (may show 'no content found' if no extraction data exists)"
    )
    
    time.sleep(1)
    
    # Step 5: Download with dry run
    print_step(5, "Content Download (Dry Run)")
    
    print("""
The download command downloads Instagram content from URLs.
Using --dry-run shows what would be downloaded without actually downloading.
    """)
    
    run_demo_command(
        "python extract_instagram.py download --dry-run --limit 3",
        "Download content with dry run and limit (safe for demo)"
    )
    
    time.sleep(1)
    
    # Step 6: Full process
    print_step(6, "Full Process Pipeline")
    
    print("""
The full-process command runs the complete pipeline with interactive prompts.
This is the recommended way to use the system for the first time.
    """)
    
    print("""
Note: The full-process command is interactive and will ask for confirmation.
For this demo, we'll just show the help to avoid interrupting the flow.
    """)
    
    run_demo_command(
        "python extract_instagram.py full-process --help",
        "Full process help (shows all options for the complete pipeline)"
    )
    
    time.sleep(1)
    
    # Step 7: Advanced options
    print_step(7, "Advanced Options and Filtering")
    
    print("""
The CLI supports various filtering and output options for different use cases.
    """)
    
    advanced_commands = [
        ("python extract_instagram.py extract-content --category faith --limit 10", "Extract only faith category with limit"),
        ("python extract_instagram.py download --category work_life --dry-run", "Download only work_life category (dry run)"),
        ("python extract_instagram.py extract-content --verbose --limit 3", "Extract with verbose logging"),
    ]
    
    for cmd, description in advanced_commands:
        run_demo_command(cmd, description, show_output=False)
        time.sleep(0.5)  # Brief pause between commands
    
    # Final summary
    print_header("DEMO COMPLETE")
    
    print("""
🎉 Demo completed! Here's what you learned:

1. ✅ Help system - Get help for any command with --help
2. ✅ Validation - Check your MINGUS folder setup
3. ✅ Extraction - Extract Instagram content from Mac Notes
4. ✅ Manual Review - Export items needing manual resolution
5. ✅ Download - Download Instagram content with progress tracking
6. ✅ Full Process - Complete pipeline with interactive prompts
7. ✅ Filtering - Use categories and limits for targeted processing

🚀 Next Steps:
1. Create a MINGUS folder in Mac Notes
2. Add some Instagram content to test with
3. Run: python extract_instagram.py validate-folder
4. Run: python extract_instagram.py full-process

📚 For more information:
- Read CLI_USAGE_GUIDE.md for detailed usage instructions
- Read README.md for complete system overview
- Run any command with --help for specific help

Happy Instagram content extracting! 🎊
    """)

if __name__ == "__main__":
    main()
