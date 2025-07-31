#!/usr/bin/env python3
"""
Login Diagnosis for DreamVault

Helps diagnose login issues and provides solutions.
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

def diagnose_login():
    """Diagnose login issues."""
    print("🔍 Login Diagnosis for DreamVault")
    print("=" * 40)
    
    # Initialize scraper
    scraper = ChatGPTScraper(headless=False)
    
    try:
        with scraper:
            print("✅ Browser started successfully")
            
            # Test ChatGPT access
            print("\n🌐 Testing ChatGPT access...")
            scraper.driver.get("https://chatgpt.com")
            time.sleep(5)
            
            print(f"📄 Current URL: {scraper.driver.current_url}")
            print(f"📄 Page title: {scraper.driver.title}")
            
            # Check for login elements
            print("\n🔍 Checking for login elements...")
            
            login_selectors = [
                "//button[contains(text(), 'Log in')]",
                "//button[contains(text(), 'Sign in')]",
                "//a[contains(text(), 'Log in')]",
                "//a[contains(text(), 'Sign in')]",
                "//div[contains(text(), 'Log in')]",
                "//div[contains(text(), 'Sign in')]"
            ]
            
            login_found = False
            for selector in login_selectors:
                try:
                    elements = scraper.driver.find_elements("xpath", selector)
                    if elements:
                        print(f"✅ Found login element: {selector}")
                        login_found = True
                        break
                except:
                    continue
            
            if not login_found:
                print("❌ No login elements found")
                print("💡 This might indicate:")
                print("   - You're already logged in")
                print("   - Page didn't load completely")
                print("   - ChatGPT interface changed")
            
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
            
            # Check if already logged in
            if "conversation" in page_source or "chat" in page_source:
                print("\n🎉 It looks like you might already be logged in!")
                print("💡 Try running the scraper again - it might work now")
            
            print("\n📋 Recommendations:")
            print("1. Make sure you have a stable internet connection")
            print("2. Try refreshing the page if it doesn't load")
            print("3. Check if you need to complete CAPTCHA")
            print("4. Ensure your ChatGPT account is active")
            print("5. Try running: python run_scraper.py --manual-timeout 600")
            
            # Keep browser open for manual inspection
            print("\n⏰ Keeping browser open for 60 seconds...")
            print("🔍 You can manually inspect the page during this time")
            time.sleep(60)
            
            return True
            
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        return False

if __name__ == "__main__":
    setup_logging()
    success = diagnose_login()
    sys.exit(0 if success else 1) 