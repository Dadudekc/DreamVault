#!/usr/bin/env python3
"""
Test Adaptive Self-Healing System for DreamVault

Tests the adaptive extractor that can self-heal when ChatGPT changes its interface.
"""

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

def test_adaptive_system():
    """Test the adaptive self-healing system."""
    print("🧪 Testing Adaptive Self-Healing System")
    print("=" * 50)
    
    # Initialize scraper
    scraper = ChatGPTScraper(headless=False)  # Use visible browser for testing
    
    try:
        with scraper:
            # Get health status before testing
            print("\n📊 Initial Health Status:")
            health = scraper.get_adaptive_health_status()
            print(f"  Cached selectors: {health['cached_selectors']}")
            print(f"  Selector library size: {health['selector_library_size']}")
            print(f"  Last working URL: {health['last_working_url']}")
            print(f"  Cache file: {health['cache_file']}")
            
            # Ensure login
            print("\n🔐 Ensuring login...")
            if not scraper.ensure_login(allow_manual=True, manual_timeout=300):
                print("❌ Login failed")
                return False
            
            # Test conversation extraction with adaptive system
            print("\n📋 Testing adaptive conversation extraction...")
            conversations = scraper.get_conversation_list()
            
            if conversations:
                print(f"✅ Adaptive system found {len(conversations)} conversations")
                
                # Show first few conversations
                print("\n📝 Sample conversations:")
                for i, conv in enumerate(conversations[:5]):
                    print(f"  {i+1}. {conv['title']} (ID: {conv['id']})")
                
                # Get updated health status
                print("\n📊 Updated Health Status:")
                health = scraper.get_adaptive_health_status()
                print(f"  Cached selectors: {health['cached_selectors']}")
                print(f"  Selector library size: {health['selector_library_size']}")
                print(f"  Last working URL: {health['last_working_url']}")
                print(f"  Cache file: {health['cache_file']}")
                
                print("\n✅ Adaptive system test successful!")
                return True
            else:
                print("❌ Adaptive system found no conversations")
                return False
                
    except Exception as e:
        print(f"❌ Adaptive system test failed: {e}")
        return False

if __name__ == "__main__":
    setup_logging()
    success = test_adaptive_system()
    sys.exit(0 if success else 1) 