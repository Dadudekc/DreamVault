#!/usr/bin/env python3
"""
ShadowArchive Search Demo

Demonstrates the search capabilities of the inverted index.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shadowarchive import IndexBuilder


def demo_search():
    """Demonstrate search capabilities."""
    print("🔍 ShadowArchive Search Demo")
    print("=" * 50)
    
    # Initialize index builder
    index_builder = IndexBuilder()
    
    # Search by topic
    print("\n📚 Searching by topic: 'architecture'")
    topic_results = index_builder.search_by_topic("architecture")
    for result in topic_results[:3]:  # Show top 3
        print(f"  - {result['conversation_id']} (confidence: {result['confidence']:.2f})")
    
    # Search by template
    print("\n📋 Searching by template: 'code_review'")
    template_results = index_builder.search_by_template("code_review")
    for result in template_results[:3]:
        print(f"  - {result['conversation_id']} (mentions: {result['mentions']})")
    
    # Search by tag
    print("\n🏷️  Searching by tag: 'technical'")
    tag_results = index_builder.search_by_tag("technical")
    for conv_id in tag_results[:3]:
        print(f"  - {conv_id}")
    
    # Search by entity
    print("\n🏢 Searching by entity: 'API Gateway'")
    entity_results = index_builder.search_by_entity("API Gateway")
    for result in entity_results[:3]:
        print(f"  - {result['conversation_id']} (confidence: {result['confidence']:.2f})")
    
    # Search by sentiment
    print("\n😊 Searching by sentiment: 'positive'")
    sentiment_results = index_builder.search_by_sentiment("positive")
    for result in sentiment_results[:3]:
        print(f"  - {result['conversation_id']} (confidence: {result['confidence']:.2f})")
    
    # Show index statistics
    print("\n📊 Index Statistics:")
    stats = index_builder.get_index_stats()
    print(f"  Indexed conversations: {stats.get('indexed_conversations', 0)}")
    print(f"  Unique topics: {stats.get('unique_topics', 0)}")
    print(f"  Unique templates: {stats.get('unique_templates', 0)}")
    print(f"  Unique tags: {stats.get('unique_tags', 0)}")


if __name__ == "__main__":
    demo_search() 