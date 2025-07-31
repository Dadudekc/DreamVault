#!/usr/bin/env python3
"""
Test script for DreamVault IP Resurrection Engine with sample data.

This script demonstrates the IP extractor with conversation data that contains
actual IP patterns like product ideas, abandoned concepts, etc.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dreamvault.resurrection.ip_extractor import IPExtractor


def create_sample_conversation():
    """Create a sample conversation with IP patterns."""
    return {
        "conversation_id": "sample_conv_001",
        "summary": "Discussed building a new AI-powered task management app that could revolutionize productivity. Also talked about creating a workflow for automated code reviews and abandoned a blockchain-based identity system due to complexity.",
        "topics": [
            {"topic": "AI task management app development", "confidence": 0.9},
            {"topic": "automated code review workflow", "confidence": 0.8},
            {"topic": "blockchain identity system", "confidence": 0.7}
        ],
        "entities": [
            {"name": "TaskMaster AI", "type": "product_name"},
            {"name": "CodeReviewBot", "type": "tool_name"},
            {"name": "IdentityChain", "type": "abandoned_project"}
        ],
        "action_items": [
            {"action": "Build prototype for TaskMaster AI app"},
            {"action": "Design automated code review workflow"},
            {"action": "Research blockchain identity solutions"}
        ],
        "decisions": [
            {"decision": "Use microservices architecture for TaskMaster AI"},
            {"decision": "Abandon blockchain identity system due to complexity"},
            {"decision": "Create brand name 'TaskMaster AI' for the app"}
        ]
    }


def main():
    """Test the IP Resurrection Engine with sample data."""
    print("🛰️ DreamVault IP Resurrection Engine Test (Sample Data)")
    print("=" * 60)
    
    # Initialize IP extractor
    config = {
        "paths": {
            "lost_inventions": "data/resurrection/lost_inventions"
        }
    }
    
    ip_extractor = IPExtractor(config)
    
    # Create sample conversation with IP patterns
    sample_conversation = create_sample_conversation()
    
    print("📋 Sample conversation content:")
    print(f"  Summary: {sample_conversation['summary']}")
    print(f"  Topics: {[t['topic'] for t in sample_conversation['topics']]}")
    print(f"  Entities: {[e['name'] for e in sample_conversation['entities']]}")
    print(f"  Actions: {[a['action'] for a in sample_conversation['action_items']]}")
    print(f"  Decisions: {[d['decision'] for d in sample_conversation['decisions']]}")
    
    print("\n🔍 Extracting IP from sample conversation...")
    
    # Extract IP
    extracted_ip = ip_extractor.extract_ip_from_conversation(sample_conversation, "sample_conv_001")
    
    # Save extracted IP
    ip_extractor.save_extracted_ip(extracted_ip, "sample_conv_001")
    
    # Display results
    print("\n💡 Extracted IP Results:")
    print("=" * 40)
    
    if extracted_ip['product_ideas']:
        print(f"  🚀 Product Ideas ({len(extracted_ip['product_ideas'])}):")
        for idea in extracted_ip['product_ideas']:
            print(f"    • {idea['text']} (confidence: {idea['confidence']:.1f})")
    
    if extracted_ip['workflows']:
        print(f"  🔄 Workflows ({len(extracted_ip['workflows'])}):")
        for workflow in extracted_ip['workflows']:
            print(f"    • {workflow['text']} (confidence: {workflow['confidence']:.1f})")
    
    if extracted_ip['brands_names']:
        print(f"  🏷️  Brand Names ({len(extracted_ip['brands_names'])}):")
        for brand in extracted_ip['brands_names']:
            print(f"    • {brand['text']} (confidence: {brand['confidence']:.1f})")
    
    if extracted_ip['schemas']:
        print(f"  🏗️  Schemas ({len(extracted_ip['schemas'])}):")
        for schema in extracted_ip['schemas']:
            print(f"    • {schema['text']} (confidence: {schema['confidence']:.1f})")
    
    if extracted_ip['abandoned_ideas']:
        print(f"  ⚰️  Abandoned Ideas ({len(extracted_ip['abandoned_ideas'])}):")
        for abandoned in extracted_ip['abandoned_ideas']:
            print(f"    • {abandoned['text']} (confidence: {abandoned['confidence']:.1f})")
    
    print(f"\n💰 Potential Value: ${extracted_ip['potential_value']:,}")
    print(f"🏷️  Tags: {', '.join(extracted_ip['tags'])}")
    print(f"📝 Summary: {extracted_ip['summary']}")
    
    # Get overall summary
    summary_stats = ip_extractor.get_lost_inventions_summary()
    print(f"\n📊 Overall Statistics:")
    print(f"  Total conversations analyzed: {summary_stats['total_conversations_analyzed']}")
    print(f"  Total ideas extracted: {summary_stats['total_ideas_extracted']}")
    print(f"  Total potential value: ${summary_stats['total_potential_value']:,}")
    print(f"  Abandoned ideas: {summary_stats['abandoned_ideas_count']}")
    print(f"  High-value ideas: {summary_stats['high_value_ideas_count']}")
    
    print("\n✅ IP Resurrection Engine test completed!")
    print("📁 Check 'data/resurrection/lost_inventions/sample_conv_001_ip.json' for extracted IP")


if __name__ == "__main__":
    main() 