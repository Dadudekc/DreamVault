#!/usr/bin/env python3
"""
DreamVault ChatGPT Scraper Runner

Simple script to run the integrated ChatGPT scraper with cookies, manual login, 
rate limits, and model selection.
"""

import argparse
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
            logging.FileHandler('scraper.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def progress_callback(current: int, total: int):
    """Progress callback for extraction."""
    print(f"📊 Progress: {current}/{total} ({current/total*100:.1f}%)")

def main():
    """Main function to run the scraper."""
    parser = argparse.ArgumentParser(description="DreamVault ChatGPT Scraper")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--username", help="ChatGPT username/email")
    parser.add_argument("--password", help="ChatGPT password")
    parser.add_argument("--totp-secret", help="TOTP secret for 2FA")
    parser.add_argument("--cookie-file", default="data/cookies.json", help="Cookie file path")
    parser.add_argument("--model", help="ChatGPT model to use (e.g., gpt-4o, gpt-4o-mini)")
    parser.add_argument("--limit", type=int, help="Limit number of conversations to extract")
    parser.add_argument("--output-dir", default="data/raw", help="Output directory")
    parser.add_argument("--rate-limit", type=float, default=2.0, help="Rate limit delay (seconds)")
    parser.add_argument("--manual-timeout", type=int, default=60, help="Manual login timeout")
    parser.add_argument("--no-manual", action="store_true", help="Disable manual login")
    parser.add_argument("--no-resume", action="store_true", help="Disable resume functionality (process all conversations)")
    parser.add_argument("--reset-progress", action="store_true", help="Reset progress tracking")
    parser.add_argument("--progress-file", default="data/scraper_progress.json", help="Progress tracking file")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🛰️ DreamVault ChatGPT Scraper")
    print("=" * 50)
    
    # Initialize scraper
    scraper = ChatGPTScraper(
        headless=args.headless,
        username=args.username,
        password=args.password,
        totp_secret=args.totp_secret,
        cookie_file=args.cookie_file,
        rate_limit_delay=args.rate_limit,
        progress_file=args.progress_file
    )
    
    try:
        # Start scraper
        with scraper:
            # Ensure login
            logger.info("🔐 Ensuring login...")
            if not scraper.ensure_login(allow_manual=not args.no_manual, manual_timeout=args.manual_timeout):
                logger.error("❌ Login failed")
                return 1
            
            # Handle progress reset
            if args.reset_progress:
                logger.info("🔄 Resetting progress tracking...")
                scraper.reset_progress()
            
            # Select model if specified
            if args.model:
                logger.info(f"🤖 Selecting model: {args.model}")
                scraper.select_model(args.model)
            
            # Show progress stats
            progress_stats = scraper.get_progress_stats()
            if progress_stats["total_processed"] > 0:
                print(f"📊 Progress: {progress_stats['successful']} successful, {progress_stats['failed']} failed")
            
            # Extract conversations
            logger.info("📋 Starting conversation extraction...")
            stats = scraper.extract_all_conversations(
                limit=args.limit,
                output_dir=args.output_dir,
                progress_callback=progress_callback,
                skip_processed=not args.no_resume
            )
            
            # Display results
            print("\n" + "=" * 50)
            print("📊 Extraction Results")
            print("=" * 50)
            print(f"Total conversations: {stats['total']}")
            print(f"Successfully extracted: {stats['extracted']}")
            print(f"Failed: {stats['failed']}")
            if 'skipped' in stats:
                print(f"Skipped (already processed): {stats['skipped']}")
            
            if stats['errors']:
                print(f"\n❌ Errors:")
                for error in stats['errors'][:5]:  # Show first 5 errors
                    print(f"  - {error}")
            
            # Rate limiting info
            rate_info = scraper.get_rate_limit_info()
            print(f"\n⏱️ Rate Limiting:")
            print(f"  Total requests: {rate_info['request_count']}")
            print(f"  Rate limit delay: {rate_info['rate_limit_delay']}s")
            
            print(f"\n✅ Extraction complete!")
            print(f"📁 Check '{args.output_dir}' for extracted conversations")
            
            return 0
            
    except KeyboardInterrupt:
        logger.info("⏹️ Scraper interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Scraper error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 