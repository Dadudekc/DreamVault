#!/usr/bin/env python3
"""
DreamVault Database Query Tool

This script provides easy querying of the conversation database.
"""

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any


class DatabaseQuery:
    """Simple database query interface."""
    
    def __init__(self, db_path: str = "data/conversations.db"):
        """Initialize the query interface.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
    
    def search_conversations(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search conversations using full-text search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching conversations
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT c.* FROM conversations c
                JOIN conversations_fts fts ON c.id = fts.id
                WHERE fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                # Parse JSON fields
                for field in ['tags', 'topics', 'sentiment', 'entities', 'action_items', 'decisions', 'template_coverage', 'metadata']:
                    if result.get(field):
                        try:
                            result[field] = json.loads(result[field])
                        except:
                            pass
                results.append(result)
            
            return results
    
    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Get a specific conversation by ID.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            Conversation data
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM conversations WHERE id = ?
            """, (conversation_id,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                # Parse JSON fields
                for field in ['tags', 'topics', 'sentiment', 'entities', 'action_items', 'decisions', 'template_coverage', 'metadata']:
                    if result.get(field):
                        try:
                            result[field] = json.loads(result[field])
                        except:
                            pass
                return result
            return None
    
    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            List of messages
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM messages WHERE conversation_id = ? ORDER BY id
            """, (conversation_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get conversation count
            cursor.execute("SELECT COUNT(*) FROM conversations")
            conversation_count = cursor.fetchone()[0]
            
            # Get message count
            cursor.execute("SELECT COUNT(*) FROM messages")
            message_count = cursor.fetchone()[0]
            
            # Get unique tags
            cursor.execute("SELECT tags FROM conversations WHERE tags != '[]'")
            all_tags = []
            for row in cursor.fetchall():
                try:
                    tags = json.loads(row[0])
                    all_tags.extend(tags)
                except:
                    pass
            
            unique_tags = list(set(all_tags))
            
            return {
                "conversations": conversation_count,
                "messages": message_count,
                "unique_tags": len(unique_tags),
                "tags": sorted(unique_tags)
            }
    
    def list_conversations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent conversations.
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, summary, created_at, processed_at FROM conversations 
                ORDER BY processed_at DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def search_by_tag(self, tag: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search conversations by tag.
        
        Args:
            tag: Tag to search for
            limit: Maximum number of results
            
        Returns:
            List of matching conversations
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM conversations 
                WHERE tags LIKE ?
                ORDER BY processed_at DESC
                LIMIT ?
            """, (f'%"{tag}"%', limit))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                # Parse JSON fields
                for field in ['tags', 'topics', 'sentiment', 'entities', 'action_items', 'decisions', 'template_coverage', 'metadata']:
                    if result.get(field):
                        try:
                            result[field] = json.loads(result[field])
                        except:
                            pass
                results.append(result)
            
            return results


def print_conversation_summary(conversation: Dict[str, Any]):
    """Print a formatted conversation summary."""
    print(f"\n📋 Conversation: {conversation['id']}")
    print(f"📅 Created: {conversation.get('created_at', 'Unknown')}")
    print(f"📝 Summary: {conversation.get('summary', 'No summary')}")
    
    if conversation.get('tags'):
        print(f"🏷️  Tags: {', '.join(conversation['tags'])}")
    
    if conversation.get('topics'):
        print(f"📚 Topics: {len(conversation['topics'])} topics")
        for topic in conversation['topics'][:3]:  # Show first 3
            if isinstance(topic, dict):
                print(f"  • {topic.get('topic', 'Unknown')} (confidence: {topic.get('confidence', 0):.1f})")
            else:
                print(f"  • {topic}")
    
    if conversation.get('entities'):
        print(f"🔍 Entities: {len(conversation['entities'])} entities")
        for entity in conversation['entities'][:3]:  # Show first 3
            if isinstance(entity, dict):
                print(f"  • {entity.get('name', 'Unknown')} ({entity.get('type', 'unknown')})")
            else:
                print(f"  • {entity}")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Query DreamVault conversation database")
    parser.add_argument("--search", help="Search conversations")
    parser.add_argument("--conversation", help="Get specific conversation by ID")
    parser.add_argument("--messages", help="Get messages for conversation ID")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--list", action="store_true", help="List recent conversations")
    parser.add_argument("--tag", help="Search conversations by tag")
    parser.add_argument("--limit", type=int, default=10, help="Limit number of results")
    parser.add_argument("--db", default="data/conversations.db", help="Database path")
    
    args = parser.parse_args()
    
    # Check if database exists
    if not Path(args.db).exists():
        print(f"❌ Database not found: {args.db}")
        print("Run 'python simple_ingest.py' first to create the database.")
        return
    
    query = DatabaseQuery(args.db)
    
    if args.search:
        print(f"🔍 Searching for: '{args.search}'")
        results = query.search_conversations(args.search, args.limit)
        print(f"Found {len(results)} conversations:")
        
        for conv in results:
            print_conversation_summary(conv)
    
    elif args.conversation:
        print(f"📋 Getting conversation: {args.conversation}")
        conv = query.get_conversation(args.conversation)
        if conv:
            print_conversation_summary(conv)
            
            # Show messages if available
            messages = query.get_messages(args.conversation)
            if messages:
                print(f"\n💬 Messages ({len(messages)}):")
                for msg in messages:
                    print(f"  [{msg['role']}]: {msg['content'][:100]}...")
        else:
            print(f"❌ Conversation {args.conversation} not found")
    
    elif args.messages:
        print(f"💬 Getting messages for: {args.messages}")
        messages = query.get_messages(args.messages)
        if messages:
            for msg in messages:
                print(f"[{msg['role']}]: {msg['content']}")
        else:
            print(f"❌ No messages found for {args.messages}")
    
    elif args.stats:
        print("📊 Database Statistics:")
        stats = query.get_stats()
        print(f"  Conversations: {stats['conversations']}")
        print(f"  Messages: {stats['messages']}")
        print(f"  Unique tags: {stats['unique_tags']}")
        print(f"  Tags: {', '.join(stats['tags'][:20])}...")  # Show first 20 tags
    
    elif args.list:
        print("📋 Recent Conversations:")
        conversations = query.list_conversations(args.limit)
        for conv in conversations:
            print(f"  {conv['id']}: {conv['summary'][:80]}...")
    
    elif args.tag:
        print(f"🏷️  Searching by tag: '{args.tag}'")
        results = query.search_by_tag(args.tag, args.limit)
        print(f"Found {len(results)} conversations with tag '{args.tag}':")
        
        for conv in results:
            print_conversation_summary(conv)
    
    else:
        print("🛰️ DreamVault Database Query Tool")
        print("=" * 40)
        print("Usage examples:")
        print("  python query_db.py --search 'AI'")
        print("  python query_db.py --conversation conv_000001")
        print("  python query_db.py --messages conv_000001")
        print("  python query_db.py --stats")
        print("  python query_db.py --list")
        print("  python query_db.py --tag 'technical'")


if __name__ == "__main__":
    main() 