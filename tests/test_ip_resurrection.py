#!/usr/bin/env python3
"""
Test script for DreamVault IP Resurrection Engine.

This script demonstrates how the IP extractor works with existing conversation data.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dreamvault.resurrection.ip_extractor import IPExtractor


def main():
    """Test the IP Resurrection Engine."""
    print("🛰️ DreamVault IP Resurrection Engine Test")
    print("=" * 50)
    
    # Initialize IP extractor
    config = {
        "paths": {
            "lost_inventions": "data/resurrection/lost_inventions"
        }
    }
    
    ip_extractor = IPExtractor(config)
    
    # Load existing conversation summaries
    summary_dir = Path("data/summary")
    if not summary_dir.exists():
        print("❌ No conversation summaries found. Run ingestion first.")
        return
    
    summary_files = list(summary_dir.glob("*.json"))
    print(f"📋 Found {len(summary_files)} conversation summaries to analyze")
    
    total_value = 0
    total_ideas = 0
    
    for summary_file in summary_files:
        conversation_id = summary_file.stem
        
        print(f"\n🔍 Analyzing conversation {conversation_id}...")
        
        # Load conversation data
        with open(summary_file, 'r', encoding='utf-8') as f:
            conversation_data = json.load(f)
        
        # Extract IP
        extracted_ip = ip_extractor.extract_ip_from_conversation(conversation_data, conversation_id)
        
        # Save extracted IP
        ip_extractor.save_extracted_ip(extracted_ip, conversation_id)
        
        # Display results
        print(f"  💡 Found {len(extracted_ip['product_ideas'])} product ideas")
        print(f"  🔄 Found {len(extracted_ip['workflows'])} workflows")
        print(f"  🏷️  Found {len(extracted_ip['brands_names'])} brand names")
        print(f"  🏗️  Found {len(extracted_ip['schemas'])} schemas")
        print(f"  ⚰️  Found {len(extracted_ip['abandoned_ideas'])} abandoned ideas")
        print(f"  💰 Potential value: ${extracted_ip['potential_value']:,}")
        print(f"  📝 Summary: {extracted_ip['summary']}")
        
        total_value += extracted_ip['potential_value']
        total_ideas += sum(len(extracted_ip[key]) for key in ["product_ideas", "workflows", "brands_names", "schemas", "abandoned_ideas"])
    
    # Display overall summary
    print("\n" + "=" * 50)
    print("🎯 IP Resurrection Summary")
    print("=" * 50)
    print(f"📊 Total conversations analyzed: {len(summary_files)}")
    print(f"💡 Total ideas extracted: {total_ideas}")
    print(f"💰 Total potential value: ${total_value:,}")
    print(f"📈 Average value per conversation: ${total_value // len(summary_files):,}")
    
    # Get detailed summary from IP extractor
    summary_stats = ip_extractor.get_lost_inventions_summary()
    print(f"⚰️  Abandoned ideas found: {summary_stats['abandoned_ideas_count']}")
    print(f"💎 High-value ideas: {summary_stats['high_value_ideas_count']}")
    
    print("\n✅ IP Resurrection Engine test completed!")
    print("📁 Check 'data/resurrection/lost_inventions/' for extracted IP files")


if __name__ == "__main__":
    main() 