#!/usr/bin/env python3
"""
Get Full Conversation Example

This script shows how to retrieve complete conversation data from the database.
"""

import sqlite3
import json
import sys

def get_full_conversation(conversation_id: str):
    """Get complete conversation data."""
    conn = sqlite3.connect('data/conversations.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get conversation data
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ Conversation {conversation_id} not found")
        return
    
    # Convert to dict and parse JSON fields
    conv_data = dict(row)
    for field in ['tags', 'topics', 'sentiment', 'entities', 'action_items', 'decisions', 'template_coverage', 'metadata']:
        if conv_data.get(field):
            try:
                conv_data[field] = json.loads(conv_data[field])
            except:
                pass
    
    # Get messages
    cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY id", (conversation_id,))
    messages = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # Display full conversation
    print(f"🛰️ Full Conversation: {conversation_id}")
    print("=" * 60)
    
    print(f"📝 Summary: {conv_data.get('summary', 'No summary')}")
    print(f"📅 Created: {conv_data.get('created_at', 'Unknown')}")
    print(f"🔄 Processed: {conv_data.get('processed_at', 'Unknown')}")
    
    if conv_data.get('tags'):
        print(f"\n🏷️  Tags: {', '.join(conv_data['tags'])}")
    
    if conv_data.get('topics'):
        print(f"\n📚 Topics:")
        for topic in conv_data['topics']:
            if isinstance(topic, dict):
                print(f"  • {topic.get('topic', 'Unknown')} (confidence: {topic.get('confidence', 0):.1f})")
            else:
                print(f"  • {topic}")
    
    if conv_data.get('entities'):
        print(f"\n🔍 Entities:")
        for entity in conv_data['entities']:
            if isinstance(entity, dict):
                print(f"  • {entity.get('name', 'Unknown')} ({entity.get('type', 'unknown')})")
            else:
                print(f"  • {entity}")
    
    if conv_data.get('action_items'):
        print(f"\n✅ Action Items:")
        for action in conv_data['action_items']:
            if isinstance(action, dict):
                print(f"  • {action.get('action', 'Unknown')} (priority: {action.get('priority', 'unknown')})")
            else:
                print(f"  • {action}")
    
    if conv_data.get('decisions'):
        print(f"\n🎯 Decisions:")
        for decision in conv_data['decisions']:
            if isinstance(decision, dict):
                print(f"  • {decision.get('decision', 'Unknown')}")
                if decision.get('context'):
                    print(f"    Context: {decision['context']}")
            else:
                print(f"  • {decision}")
    
    if conv_data.get('sentiment'):
        sentiment = conv_data['sentiment']
        if isinstance(sentiment, dict):
            print(f"\n😊 Sentiment: {sentiment.get('overall', 'unknown')} (confidence: {sentiment.get('confidence', 0):.1f})")
            if sentiment.get('scores'):
                scores = sentiment['scores']
                print(f"  Scores: Positive {scores.get('positive', 0):.1f}, Negative {scores.get('negative', 0):.1f}, Neutral {scores.get('neutral', 0):.1f}")
    
    if conv_data.get('template_coverage'):
        template = conv_data['template_coverage']
        if isinstance(template, dict):
            print(f"\n📋 Template Coverage: {template.get('coverage_score', 0):.1f}")
            if template.get('templates_used'):
                print(f"  Templates: {', '.join(template['templates_used'])}")
    
    if conv_data.get('metadata'):
        metadata = conv_data['metadata']
        if isinstance(metadata, dict):
            print(f"\n📊 Metadata:")
            print(f"  Message count: {metadata.get('message_count', 'unknown')}")
            print(f"  Duration: {metadata.get('duration_minutes', 'unknown')} minutes")
            print(f"  Participants: {metadata.get('participant_count', 'unknown')}")
            print(f"  Hash: {metadata.get('hash', 'unknown')[:16]}...")
    
    if messages:
        print(f"\n💬 Messages ({len(messages)}):")
        for i, msg in enumerate(messages, 1):
            print(f"  {i}. [{msg['role']}]: {msg['content']}")
    else:
        print(f"\n💬 No individual messages stored in database")
        print("   (Messages are stored in the summary and structured data)")
    
    print(f"\n✅ Full conversation data retrieved!")

def main():
    """Main function."""
    if len(sys.argv) > 1:
        conversation_id = sys.argv[1]
    else:
        conversation_id = "conv_000001"
    
    get_full_conversation(conversation_id)

if __name__ == "__main__":
    main() 