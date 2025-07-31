#!/usr/bin/env python3
"""
Debug Conversation Detection for DreamVault

Tests conversation detection without requiring login.
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

def debug_conversation_detection():
    """Debug conversation detection."""
    print("🔍 Debug Conversation Detection")
    print("=" * 40)
    
    # Initialize scraper
    scraper = ChatGPTScraper(headless=False)
    
    try:
        with scraper:
            print("✅ Browser started successfully")
            
            # Navigate to ChatGPT
            print("\n🌐 Navigating to ChatGPT...")
            scraper.driver.get("https://chatgpt.com")
            time.sleep(5)
            
            print(f"📄 Current URL: {scraper.driver.current_url}")
            print(f"📄 Page title: {scraper.driver.title}")
            
            # Test conversation detection
            print("\n🔍 Testing conversation detection...")
            
            # Test different selectors
            selectors = [
                "//a[contains(@href, '/c/')]//span",
                "//a[contains(@href, '/c/')]",
                "//div[contains(@class, 'conversation')]//a",
                "//nav//a[contains(@href, '/c/')]",
                "//a[contains(@href, 'chatgpt.com/c/')]",
                "//a[contains(@href, 'chat.openai.com/c/')]",
                "//div[contains(@class, 'group')]//a[contains(@href, '/c/')]",
                "//div[contains(@class, 'flex')]//a[contains(@href, '/c/')]",
                "//nav//div[contains(@class, 'conversation')]//a",
                "//div[contains(@class, 'conversation')]//div[contains(@class, 'title')]//a",
                "//a[contains(@href, '/c/')]//div[contains(@class, 'text')]",
                "//div[contains(@class, 'conversation')]//a[contains(@href, '/c/')]",
                "//nav//div[contains(@class, 'conversation')]//a",
                "//div[contains(@class, 'conversation')]//div[contains(@class, 'title')]//a",
                "//a[contains(@href, '/c/')]//span",
                "//div[contains(@class, 'conversation')]//span",
                "//nav//span",
                "//a[contains(@href, '/c/')]//div",
                "//div[contains(@class, 'conversation')]//div",
                "//nav//div"
            ]
            
            for i, selector in enumerate(selectors):
                try:
                    elements = scraper.driver.find_elements("xpath", selector)
                    if elements:
                        print(f"✅ Selector {i+1}: {selector}")
                        print(f"   Found {len(elements)} elements")
                        
                        # Show first few elements
                        for j, element in enumerate(elements[:3]):
                            try:
                                text = element.text.strip()
                                href = element.get_attribute("href") if element.tag_name == "a" else "N/A"
                                print(f"   Element {j+1}: '{text}' -> {href}")
                            except:
                                print(f"   Element {j+1}: [Error reading element]")
                        
                        if len(elements) > 3:
                            print(f"   ... and {len(elements) - 3} more elements")
                        
                        print()
                    else:
                        print(f"❌ Selector {i+1}: {selector} - No elements found")
                        
                except Exception as e:
                    print(f"❌ Selector {i+1}: {selector} - Error: {e}")
            
            # Check page source for clues
            print("\n📄 Analyzing page content...")
            page_source = scraper.driver.page_source.lower()
            
            if "login" in page_source:
                print("✅ 'Login' text found on page")
            if "sign in" in page_source:
                print("✅ 'Sign in' text found on page")
            if "chat" in page_source:
                print("✅ 'Chat' text found on page")
            if "conversation" in page_source:
                print("✅ 'Conversation' text found on page")
            if "/c/" in page_source:
                print("✅ '/c/' conversation links found in page source")
            
            # Keep browser open for manual inspection
            print("\n⏰ Keeping browser open for 60 seconds...")
            print("🔍 You can manually inspect the page during this time")
            time.sleep(60)
            
            return True
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return False

if __name__ == "__main__":
    setup_logging()
    success = debug_conversation_detection()
    sys.exit(0 if success else 1) 