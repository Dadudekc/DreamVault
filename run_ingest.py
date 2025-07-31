#!/usr/bin/env python3
"""
DreamVault - Main entry point for conversation ingestion.

Usage:
    python run_ingest.py --batch-size 50 --max-conversations 100
    python run_ingest.py --status
    python run_ingest.py --cleanup --days 7
    python run_ingest.py --rebuild-indexes
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dreamvault import Config, BatchRunner


def generate_mock_conversation_ids(count: int) -> List[str]:
    """Generate mock conversation IDs for testing."""
    return [f"conv_{i:06d}" for i in range(1, count + 1)]


def main():
    """Main entry point for DreamVault."""
    parser = argparse.ArgumentParser(
        description="DreamVault - Dreamscape's autonomous memory engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_ingest.py --batch-size 50 --max-conversations 100
  python run_ingest.py --status
  python run_ingest.py --cleanup --days 7
  python run_ingest.py --rebuild-indexes
  python run_ingest.py --mock-data 25
        """
    )
    
    # Processing options
    parser.add_argument(
        "--batch-size", 
        type=int, 
        help="Number of conversations to process in each batch"
    )
    parser.add_argument(
        "--max-conversations", 
        type=int, 
        help="Maximum number of conversations to process"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        default="configs/ingest.yaml",
        help="Path to configuration file"
    )
    
    # Mock data generation
    parser.add_argument(
        "--mock-data", 
        type=int, 
        help="Generate mock conversation IDs and add to queue"
    )
    
    # System management
    parser.add_argument(
        "--status", 
        action="store_true",
        help="Show system status and statistics"
    )
    parser.add_argument(
        "--cleanup", 
        action="store_true",
        help="Clean up old data files"
    )
    parser.add_argument(
        "--days", 
        type=int, 
        default=7,
        help="Number of days for cleanup (default: 7)"
    )
    parser.add_argument(
        "--rebuild-indexes", 
        action="store_true",
        help="Rebuild all indexes from summary files"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = Config(args.config)
        config.ensure_directories()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Initialize batch runner
    try:
        runner = BatchRunner(config)
    except Exception as e:
        print(f"Error initializing batch runner: {e}")
        sys.exit(1)
    
    # Handle different commands
    if args.status:
        show_status(runner)
    elif args.cleanup:
        cleanup_data(runner, args.days)
    elif args.rebuild_indexes:
        rebuild_indexes(runner)
    elif args.mock_data:
        generate_mock_data(runner, args.mock_data)
    else:
        # Run batch processing
        run_batch_processing(runner, args.batch_size, args.max_conversations)


def show_status(runner: BatchRunner):
    """Show system status and statistics."""
    print("🔍 DreamVault System Status")
    print("=" * 50)
    
    status = runner.get_queue_status()
    
    # Queue status
    queue_stats = status["queue"]
    print(f"\n📋 Queue Status:")
    print(f"  Total jobs: {queue_stats.get('total', 0)}")
    print(f"  Pending: {queue_stats.get('pending', 0)}")
    print(f"  By status: {queue_stats.get('by_status', {})}")
    
    # Rate limiter status
    rate_stats = status["rate_limiter"]
    print(f"\n⏱️  Rate Limiter:")
    print(f"  Global tokens: {rate_stats.get('global', {}).get('tokens', 0)}")
    print(f"  Global capacity: {rate_stats.get('global', {}).get('capacity', 0)}")
    
    # ChatGPT model status
    chatgpt_models = rate_stats.get("chatgpt_models", {})
    if chatgpt_models:
        print(f"\n🤖 ChatGPT Models:")
        for model_name, model_stats in chatgpt_models.items():
            tokens = model_stats.get("tokens", 0)
            capacity = model_stats.get("capacity", 0)
            utilization = model_stats.get("utilization", 0)
            print(f"  {model_name}: {tokens:.1f}/{capacity} tokens ({utilization:.1%} used)")
    
    # System statistics
    system_stats = runner.get_system_stats()
    
    print(f"\n📊 System Statistics:")
    print(f"  Indexed conversations: {system_stats.get('index_builder', {}).get('indexed_conversations', 0)}")
    print(f"  Unique topics: {system_stats.get('index_builder', {}).get('unique_topics', 0)}")
    print(f"  Unique templates: {system_stats.get('index_builder', {}).get('unique_templates', 0)}")
    print(f"  Embeddings stored: {system_stats.get('embedding_builder', {}).get('embeddings_stored', 0)}")
    
    # Last batch results
    last_batch = status["last_batch"]
    if last_batch.get("started_at"):
        print(f"\n🔄 Last Batch:")
        print(f"  Started: {last_batch.get('started_at', 'N/A')}")
        print(f"  Completed: {last_batch.get('completed_at', 'N/A')}")
        print(f"  Processed: {last_batch.get('total_processed', 0)}")
        print(f"  Successful: {last_batch.get('successful', 0)}")
        print(f"  Failed: {last_batch.get('failed', 0)}")


def cleanup_data(runner: BatchRunner, days: int):
    """Clean up old data files."""
    print(f"🧹 Cleaning up data older than {days} days...")
    
    cleanup_stats = runner.cleanup_old_data(days)
    
    print("Cleanup completed:")
    print(f"  Queue jobs removed: {cleanup_stats.get('queue_jobs_removed', 0)}")
    print(f"  Embedding files removed: {cleanup_stats.get('embedding_files_removed', 0)}")


def rebuild_indexes(runner: BatchRunner):
    """Rebuild all indexes from summary files."""
    print("🔧 Rebuilding indexes from summary files...")
    
    rebuild_stats = runner.rebuild_indexes()
    
    print(f"Index rebuild completed:")
    print(f"  Summaries indexed: {rebuild_stats.get('summaries_indexed', 0)}")


def generate_mock_data(runner: BatchRunner, count: int):
    """Generate mock conversation data for testing."""
    print(f"🎭 Generating {count} mock conversation IDs...")
    
    conversation_ids = generate_mock_conversation_ids(count)
    added_count = runner.add_conversations_to_queue(conversation_ids)
    
    print(f"Added {added_count} conversations to queue")
    print(f"Sample IDs: {conversation_ids[:5]}")


def run_batch_processing(runner: BatchRunner, batch_size: int = None, max_conversations: int = None):
    """Run batch processing of conversations."""
    print("🚀 Starting DreamVault batch processing...")
    
    # Check if queue has jobs
    status = runner.get_queue_status()
    pending_jobs = status["queue"].get("pending", 0)
    
    if pending_jobs == 0:
        print("⚠️  No jobs in queue. Add some conversations first:")
        print("   python run_ingest.py --mock-data 25")
        return
    
    print(f"📋 Found {pending_jobs} pending jobs in queue")
    
    # Run batch processing
    try:
        stats = runner.run_batch(max_conversations, batch_size)
        
        print("\n✅ Batch processing completed!")
        print(f"  Total processed: {stats.get('total_processed', 0)}")
        print(f"  Successful: {stats.get('successful', 0)}")
        print(f"  Failed: {stats.get('failed', 0)}")
        
        if stats.get("errors"):
            print(f"  Errors: {len(stats['errors'])}")
            for error in stats["errors"][:3]:  # Show first 3 errors
                print(f"    - {error.get('conversation_id', 'Unknown')}: {error.get('error', 'Unknown error')}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Batch processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during batch processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 