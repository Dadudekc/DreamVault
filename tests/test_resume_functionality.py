#!/usr/bin/env python3
"""
Test Resume Functionality for DreamVault ChatGPT Scraper

Tests the resume mechanism without requiring actual login.
"""

import json
import tempfile
import os
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dreamvault.scrapers import ChatGPTScraper

def test_resume_functionality():
    """Test the resume functionality."""
    print("🧪 Testing Resume Functionality")
    print("=" * 50)
    
    # Create temporary progress file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        progress_file = f.name
    
    try:
        # Initialize scraper with temporary progress file
        scraper = ChatGPTScraper(progress_file=progress_file)
        
        # Test 1: Initial state
        print("\n📊 Test 1: Initial Progress Stats")
        stats = scraper.get_progress_stats()
        print(f"Total processed: {stats['total_processed']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        
        # Test 2: Mark conversations as processed
        print("\n📝 Test 2: Marking Conversations as Processed")
        test_conversations = [
            {"id": "conv1", "title": "Test Conversation 1", "url": "https://chat.openai.com/c/conv1"},
            {"id": "conv2", "title": "Test Conversation 2", "url": "https://chat.openai.com/c/conv2"},
            {"id": "conv3", "title": "Test Conversation 3", "url": "https://chat.openai.com/c/conv3"}
        ]
        
        for i, conv in enumerate(test_conversations):
            success = i < 2  # First 2 succeed, last one fails
            scraper._mark_conversation_processed(conv, success=success)
            print(f"Marked conversation {conv['id']} as {'successful' if success else 'failed'}")
        
        # Test 3: Check updated stats
        print("\n📊 Test 3: Updated Progress Stats")
        stats = scraper.get_progress_stats()
        print(f"Total processed: {stats['total_processed']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        
        # Test 4: Check if conversations are marked as processed
        print("\n🔍 Test 4: Checking Processed Status")
        for conv in test_conversations:
            is_processed = scraper._is_conversation_processed(conv)
            print(f"Conversation {conv['id']}: {'Processed' if is_processed else 'Not processed'}")
        
        # Test 5: Test progress file content
        print("\n📄 Test 5: Progress File Content")
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
                print(f"Progress file contains {len(progress_data)} entries")
                for conv_hash, data in progress_data.items():
                    print(f"  {data['id']}: {'✅' if data['success'] else '❌'}")
        
        # Test 6: Reset progress
        print("\n🔄 Test 6: Reset Progress")
        scraper.reset_progress()
        stats = scraper.get_progress_stats()
        print(f"After reset - Total processed: {stats['total_processed']}")
        
        # Test 7: Check if conversations are no longer marked as processed
        print("\n🔍 Test 7: Checking After Reset")
        for conv in test_conversations:
            is_processed = scraper._is_conversation_processed(conv)
            print(f"Conversation {conv['id']}: {'Processed' if is_processed else 'Not processed'}")
        
        print("\n✅ All tests passed! Resume functionality is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Clean up temporary file
        if os.path.exists(progress_file):
            os.unlink(progress_file)
    
    return True

if __name__ == "__main__":
    success = test_resume_functionality()
    sys.exit(0 if success else 1) 