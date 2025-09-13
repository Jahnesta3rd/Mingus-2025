#!/usr/bin/env python3
"""
Installation script for Instagram Content Downloader dependencies.

This script helps install all required dependencies and tools.
"""

import subprocess
import sys
import platform
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"Installing {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {description}")
        print(f"   Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def install_python_dependencies():
    """Install Python dependencies from requirements.txt."""
    print("\n📦 Installing Python dependencies...")
    
    # Check if requirements.txt exists
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    # Install dependencies
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Python dependencies"
    )


def install_ytdlp():
    """Install yt-dlp."""
    return run_command(
        f"{sys.executable} -m pip install yt-dlp",
        "yt-dlp"
    )


def install_gallerydl():
    """Install gallery-dl."""
    return run_command(
        f"{sys.executable} -m pip install gallery-dl",
        "gallery-dl"
    )


def install_ffmpeg():
    """Install ffmpeg based on the operating system."""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        print("Installing ffmpeg via Homebrew...")
        return run_command("brew install ffmpeg", "ffmpeg (via Homebrew)")
    
    elif system == "linux":
        print("Installing ffmpeg via apt...")
        return run_command("sudo apt update && sudo apt install -y ffmpeg", "ffmpeg (via apt)")
    
    elif system == "windows":
        print("Installing ffmpeg via chocolatey...")
        return run_command("choco install ffmpeg", "ffmpeg (via Chocolatey)")
    
    else:
        print(f"❌ Unsupported operating system: {system}")
        print("   Please install ffmpeg manually:")
        print("   - macOS: brew install ffmpeg")
        print("   - Ubuntu/Debian: sudo apt install ffmpeg")
        print("   - Windows: choco install ffmpeg")
        return False


def verify_installation():
    """Verify that all tools are installed correctly."""
    print("\n🔍 Verifying installation...")
    
    tools = {
        'yt-dlp': f"{sys.executable} -m yt_dlp --version",
        'gallery-dl': f"{sys.executable} -m gallery_dl --version",
        'ffmpeg': "ffmpeg -version"
    }
    
    all_good = True
    
    for tool, command in tools.items():
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                print(f"✅ {tool}: {version}")
            else:
                print(f"❌ {tool}: Not working properly")
                all_good = False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"❌ {tool}: Not found")
            all_good = False
    
    return all_good


def main():
    """Main installation function."""
    print("🚀 INSTAGRAM CONTENT DOWNLOADER INSTALLATION")
    print("="*60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Install specific tools
    tools_installed = True
    
    if not install_ytdlp():
        print("⚠️  yt-dlp installation failed - will try gallery-dl")
        tools_installed = False
    
    if not install_gallerydl():
        print("⚠️  gallery-dl installation failed")
        tools_installed = False
    
    if not install_ffmpeg():
        print("⚠️  ffmpeg installation failed - video processing may not work")
        tools_installed = False
    
    # Verify installation
    if not verify_installation():
        print("\n⚠️  Some tools may not be working properly")
        print("   Check the error messages above and install manually if needed")
    
    print("\n🎉 INSTALLATION COMPLETED!")
    print("\nNext steps:")
    print("1. Run: python download_instagram.py --check-tools")
    print("2. Create sample data: python download_instagram.py --create-sample")
    print("3. Start downloading: python download_instagram.py sample_urls.json")
    print("\nFor complete workflow:")
    print("   python complete_workflow.py")


if __name__ == "__main__":
    main()
