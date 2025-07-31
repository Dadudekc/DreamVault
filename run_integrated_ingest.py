#!/usr/bin/env python3
"""
DreamVault Integrated Ingestion Script

Processes conversations immediately during database ingestion.
No raw data mess - only clean, structured, searchable data.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dreamvault.core import IntegratedIngester
from dreamvault.scrapers import ChatGPTScraper

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('integrated_ingest.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_conversation_from_file(file_path: str) -> Dict:
    """Load conversation data from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load {file_path}: {e}")
        return {}

def main():
    """Main function for integrated ingestion."""
    parser = argparse.ArgumentParser(description="DreamVault Integrated Ingestion")
    parser.add_argument("--db-path", default="data/dreamvault.db", help="Database path")
    parser.add_argument("--input-dir", default="data/raw", help="Input directory with raw conversations")
    parser.add_argument("--limit", type=int, help="Limit number of conversations to process")
    parser.add_argument("--extract-first", action="store_true", help="Extract conversations first, then process")
    parser.add_argument("--username", help="ChatGPT username for extraction")
    parser.add_argument("--password", help="ChatGPT password for extraction")
    parser.add_argument("--model", help="ChatGPT model to use")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--search", help="Search conversations")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🛰️ DreamVault Integrated Ingestion")
    print("=" * 50)
    
    # Initialize integrated ingester
    ingester = IntegratedIngester(db_path=args.db_path)
    
    if args.stats:
        # Show statistics
        stats = ingester.get_stats()
        print("\n📊 Database Statistics")
        print("=" * 30)
        print(f"Total conversations: {stats.get('total_conversations', 0)}")
        print(f"Total messages: {stats.get('total_messages', 0)}")
        print(f"Total words: {stats.get('total_words', 0)}")
        print(f"IP extractions: {stats.get('total_ip_extractions', 0)}")
        print(f"Total potential value: ${stats.get('total_potential_value', 0):,.2f}")
        print(f"Database size: {stats.get('database_size_mb', 0):.2f} MB")
        
        # Show training data statistics
        training_stats = stats.get('training_data', {})
        if training_stats:
            print(f"\n🤖 Training Data Statistics")
            print("=" * 30)
            print(f"Total training files: {training_stats.get('total_training_files', 0)}")
            print(f"Training data files: {training_stats.get('total_training_data_files', 0)}")
            print(f"Training data size: {training_stats.get('training_data_size_mb', 0):.2f} MB")
            
            file_types = training_stats.get('file_types', {})
            if file_types:
                print(f"Training file types:")
                for file_type, count in file_types.items():
                    print(f"  - {file_type}: {count} files")
        
        return
    
    if args.search:
        # Search conversations
        results = ingester.search_conversations(args.search, limit=10)
        print(f"\n🔍 Search Results for: '{args.search}'")
        print("=" * 40)
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   Summary: {result['summary'][:100]}...")
            print(f"   Tags: {', '.join(result['tags'][:3])}")
            print()
        return
    
    if args.extract_first:
        # Extract conversations first, then process
        print("📋 Extracting conversations from ChatGPT...")
        
        scraper = ChatGPTScraper(
            username=args.username,
            password=args.password,
            rate_limit_delay=2.0
        )
        
        with scraper:
            # Ensure login
            if not scraper.ensure_login():
                logger.error("❌ Login failed")
                return 1
            
            # Select model if specified
            if args.model:
                scraper.select_model(args.model)
            
            # Extract conversations
            stats = scraper.extract_all_conversations(
                limit=args.limit,
                output_dir=args.input_dir
            )
            
            print(f"✅ Extracted {stats['extracted']} conversations")
    
    # Process conversations from input directory
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return 1
    
    conversation_files = list(input_dir.glob("*.json"))
    if args.limit:
        conversation_files = conversation_files[:args.limit]
    
    print(f"🔄 Processing {len(conversation_files)} conversations...")
    
    processed = 0
    failed = 0
    
    for i, file_path in enumerate(conversation_files, 1):
        try:
            # Extract conversation ID from filename
            conversation_id = file_path.stem
            
            # Load conversation data
            conversation_data = load_conversation_from_file(str(file_path))
            if not conversation_data:
                failed += 1
                continue
            
            # Process and store immediately
            if ingester.ingest_conversation(conversation_data, conversation_id):
                processed += 1
                print(f"✅ {i}/{len(conversation_files)}: {conversation_id}")
            else:
                failed += 1
                print(f"❌ {i}/{len(conversation_files)}: {conversation_id}")
                
        except Exception as e:
            failed += 1
            logger.error(f"Error processing {file_path}: {e}")
    
    # Show final statistics
    print("\n" + "=" * 50)
    print("📊 Processing Complete")
    print("=" * 50)
    print(f"Processed: {processed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {processed/(processed+failed)*100:.1f}%")
    
    # Show database stats
    stats = ingester.get_stats()
    print(f"\n📊 Database Statistics")
    print(f"Total conversations: {stats.get('total_conversations', 0)}")
    print(f"Total messages: {stats.get('total_messages', 0)}")
    print(f"Total words: {stats.get('total_words', 0)}")
    print(f"IP extractions: {stats.get('total_ip_extractions', 0)}")
    print(f"Total potential value: ${stats.get('total_potential_value', 0):,.2f}")
    print(f"Database size: {stats.get('database_size_mb', 0):.2f} MB")
    
    # Show training data stats
    training_stats = stats.get('training_data', {})
    if training_stats:
        print(f"\n🤖 Training Data Generated")
        print(f"Total training files: {training_stats.get('total_training_files', 0)}")
        print(f"Training data size: {training_stats.get('training_data_size_mb', 0):.2f} MB")
        print(f"Check 'data/training/' for AI agent training datasets")
    
    print(f"\n✅ Clean database AND training data ready!")
    print(f"Search: python run_integrated_ingest.py --search 'AI coding'")
    print(f"Train AI: Use files in 'data/training/' for agent training")

if __name__ == "__main__":
    sys.exit(main()) 