#!/usr/bin/env python3
"""
Test DreamVault Integrated System

Demonstrates the integrated ingestion system with sample conversation data.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dreamvault import IntegratedIngester

def create_sample_conversation():
    """Create a sample conversation for testing."""
    return {
        "title": "AI Coding Assistant Discussion",
        "messages": [
            {
                "role": "user",
                "content": "I need help with Python debugging. My code has an error in the authentication module.",
                "timestamp": "2024-01-15T10:30:00Z"
            },
            {
                "role": "assistant", 
                "content": "I can help you debug that! Can you share the error message and the relevant code? Also, what authentication method are you using?",
                "timestamp": "2024-01-15T10:30:30Z"
            },
            {
                "role": "user",
                "content": "The error is 'ModuleNotFoundError: No module named auth'. I'm trying to implement JWT authentication for my Flask app.",
                "timestamp": "2024-01-15T10:31:00Z"
            },
            {
                "role": "assistant",
                "content": "Ah, I see the issue! You need to install the PyJWT library. Run 'pip install PyJWT' and then import it as 'import jwt'. Here's a basic example of JWT authentication in Flask...",
                "timestamp": "2024-01-15T10:31:30Z"
            },
            {
                "role": "user",
                "content": "That's perfect! I also had an idea for a new product - an AI-powered code review tool that automatically detects security vulnerabilities.",
                "timestamp": "2024-01-15T10:32:00Z"
            },
            {
                "role": "assistant",
                "content": "That's a brilliant idea! An AI-powered security code review tool could be very valuable. You could integrate with GitHub, scan for common vulnerabilities like SQL injection, XSS, and insecure dependencies. The market for DevSecOps tools is growing rapidly.",
                "timestamp": "2024-01-15T10:32:30Z"
            }
        ]
    }

def main():
    """Test the integrated system."""
    print("🧪 Testing DreamVault Integrated System")
    print("=" * 50)
    
    # Initialize ingester
    ingester = IntegratedIngester(db_path="data/test_dreamvault.db")
    
    # Create sample conversation
    sample_conv = create_sample_conversation()
    conversation_id = "test_conv_001"
    
    print(f"📝 Processing sample conversation: {conversation_id}")
    
    # Process the conversation
    success = ingester.ingest_conversation(sample_conv, conversation_id)
    
    if success:
        print("✅ Conversation processed successfully!")
        
        # Show statistics
        stats = ingester.get_stats()
        print(f"\n📊 Results:")
        print(f"  Conversations: {stats.get('total_conversations', 0)}")
        print(f"  Messages: {stats.get('total_messages', 0)}")
        print(f"  Words: {stats.get('total_words', 0)}")
        print(f"  IP extractions: {stats.get('total_ip_extractions', 0)}")
        print(f"  Potential value: ${stats.get('total_potential_value', 0):,.2f}")
        
        # Show training data stats
        training_stats = stats.get('training_data', {})
        if training_stats:
            print(f"\n🤖 Training Data Generated:")
            print(f"  Training files: {training_stats.get('total_training_files', 0)}")
            print(f"  Data size: {training_stats.get('training_data_size_mb', 0):.2f} MB")
        
        # Test search
        print(f"\n🔍 Testing search functionality...")
        results = ingester.search_conversations("Python debugging", limit=5)
        if results:
            print(f"  Found {len(results)} conversations matching 'Python debugging'")
            for result in results:
                print(f"    - {result['title']}")
        else:
            print("  No search results found")
        
        # Check training files
        training_dir = Path("data/training")
        if training_dir.exists():
            training_files = list(training_dir.glob(f"{conversation_id}_*.jsonl"))
            print(f"\n📁 Training files created:")
            for file in training_files:
                print(f"  - {file.name}")
        
        print(f"\n✅ Test completed successfully!")
        print(f"Database: data/test_dreamvault.db")
        print(f"Training data: data/training/")
        
    else:
        print("❌ Failed to process conversation")

if __name__ == "__main__":
    main() 