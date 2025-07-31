#!/usr/bin/env python3
"""
Simple Browser Test for DreamVault

Tests basic browser functionality without login requirements.
"""

import time
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dreamvault.scrapers import ChatGPTScraper

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_browser_simple():
    """Test basic browser functionality."""
    print("🧪 Simple Browser Test")
    print("=" * 30)
    
    # Initialize scraper
    scraper = ChatGPTScraper(headless=False)  # Use visible browser
    
    try:
        with scraper:
            print("✅ Browser started successfully")
            
            # Test basic navigation
            print("🌐 Testing navigation...")
            scraper.driver.get("https://www.google.com")
            time.sleep(3)
            
            print(f"📄 Current URL: {scraper.driver.current_url}")
            print(f"📄 Page title: {scraper.driver.title}")
            
            # Test ChatGPT navigation
            print("\n🤖 Testing ChatGPT navigation...")
            scraper.driver.get("https://chatgpt.com")
            time.sleep(5)
            
            print(f"📄 Current URL: {scraper.driver.current_url}")
            print(f"📄 Page title: {scraper.driver.title}")
            
            print("\n✅ Browser test successful!")
            print("📝 Browser automation is working correctly")
            print("📝 You should see a browser window with ChatGPT open")
            
            # Keep browser open for manual inspection
            print("\n⏰ Keeping browser open for 30 seconds for manual inspection...")
            time.sleep(30)
            
            return True
            
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        return False

if __name__ == "__main__":
    setup_logging()
    success = test_browser_simple()
    sys.exit(0 if success else 1) 