#!/usr/bin/env python3
"""
Simple Conversation Ingester for DreamVault

This script ingests all conversations into a SQLite database for easy querying.
"""

import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class SimpleIngester:
    """Simple conversation ingester that stores data in SQLite."""
    
    def __init__(self, db_path: str = "data/conversations.db"):
        """Initialize the ingester.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    summary TEXT,
                    tags TEXT,
                    topics TEXT,
                    sentiment TEXT,
                    entities TEXT,
                    action_items TEXT,
                    decisions TEXT,
                    template_coverage TEXT,
                    metadata TEXT,
                    created_at TEXT,
                    processed_at TEXT
                )
            """)
            
            # Create messages table for individual messages
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """)
            
            # Create search index
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS conversations_fts 
                USING fts5(id, summary, tags, topics, entities)
            """)
            
            conn.commit()
    
    def ingest_conversation(self, conversation_data: Dict[str, Any], conversation_id: str) -> bool:
        """Ingest a single conversation into the database.
        
        Args:
            conversation_data: The conversation data
            conversation_id: The conversation ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare data for insertion
                summary = conversation_data.get("summary", "")
                tags = json.dumps(conversation_data.get("tags", []))
                topics = json.dumps(conversation_data.get("topics", []))
                sentiment = json.dumps(conversation_data.get("sentiment", {}))
                entities = json.dumps(conversation_data.get("entities", []))
                action_items = json.dumps(conversation_data.get("action_items", []))
                decisions = json.dumps(conversation_data.get("decisions", []))
                template_coverage = json.dumps(conversation_data.get("template_coverage", {}))
                metadata = json.dumps(conversation_data.get("metadata", {}))
                
                created_at = conversation_data.get("metadata", {}).get("created_at", datetime.now().isoformat())
                processed_at = datetime.now().isoformat()
                
                # Insert conversation
                cursor.execute("""
                    INSERT OR REPLACE INTO conversations 
                    (id, summary, tags, topics, sentiment, entities, action_items, decisions, template_coverage, metadata, created_at, processed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conversation_id, summary, tags, topics, sentiment, entities, 
                    action_items, decisions, template_coverage, metadata, created_at, processed_at
                ))
                
                # Insert messages if available
                if "messages" in conversation_data:
                    for message in conversation_data["messages"]:
                        cursor.execute("""
                            INSERT INTO messages (conversation_id, role, content, timestamp)
                            VALUES (?, ?, ?, ?)
                        """, (
                            conversation_id,
                            message.get("role", "unknown"),
                            message.get("content", ""),
                            datetime.now().isoformat()
                        ))
                
                # Update full-text search index
                cursor.execute("""
                    INSERT OR REPLACE INTO conversations_fts (id, summary, tags, topics, entities)
                    VALUES (?, ?, ?, ?, ?)
                """, (conversation_id, summary, tags, topics, entities))
                
                conn.commit()
                self.logger.info(f"Ingested conversation {conversation_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to ingest conversation {conversation_id}: {e}")
            return False
    
    def ingest_all_conversations(self, summary_dir: str = "data/summary") -> Dict[str, Any]:
        """Ingest all conversations from summary directory.
        
        Args:
            summary_dir: Directory containing conversation summary files
            
        Returns:
            Dictionary with ingestion statistics
        """
        summary_path = Path(summary_dir)
        if not summary_path.exists():
            self.logger.error(f"Summary directory {summary_dir} does not exist")
            return {"error": f"Directory {summary_dir} not found"}
        
        summary_files = list(summary_path.glob("*.json"))
        self.logger.info(f"Found {len(summary_files)} conversation files to ingest")
        
        stats = {
            "total_files": len(summary_files),
            "ingested": 0,
            "failed": 0,
            "errors": []
        }
        
        for summary_file in summary_files:
            conversation_id = summary_file.stem
            
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    conversation_data = json.load(f)
                
                if self.ingest_conversation(conversation_data, conversation_id):
                    stats["ingested"] += 1
                else:
                    stats["failed"] += 1
                    stats["errors"].append(f"Failed to ingest {conversation_id}")
                    
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(f"Error processing {conversation_id}: {e}")
        
        self.logger.info(f"Ingestion complete: {stats['ingested']}/{stats['total_files']} successful")
        return stats
    
    def query_conversations(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Query conversations using full-text search.
        
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
                SELECT * FROM conversations_fts 
                WHERE conversations_fts MATCH ? 
                ORDER BY rank
                LIMIT ?
            """, (query, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append(dict(row))
            
            return results
    
    def get_conversation_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific conversation by ID.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            Conversation data or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM conversations WHERE id = ?
            """, (conversation_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
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
                tags = json.loads(row[0])
                all_tags.extend(tags)
            
            unique_tags = list(set(all_tags))
            
            return {
                "conversations": conversation_count,
                "messages": message_count,
                "unique_tags": len(unique_tags),
                "tags": unique_tags
            }


def main():
    """Main function to run the simple ingester."""
    print("🛰️ DreamVault Simple Ingester")
    print("=" * 40)
    
    # Initialize ingester
    ingester = SimpleIngester()
    
    # Ingest all conversations
    print("📥 Ingesting conversations...")
    stats = ingester.ingest_all_conversations()
    
    if "error" in stats:
        print(f"❌ Error: {stats['error']}")
        return
    
    print(f"✅ Ingested {stats['ingested']}/{stats['total_files']} conversations")
    
    if stats["failed"] > 0:
        print(f"⚠️  Failed to ingest {stats['failed']} conversations")
        for error in stats["errors"][:5]:  # Show first 5 errors
            print(f"  - {error}")
    
    # Show database statistics
    db_stats = ingester.get_stats()
    print(f"\n📊 Database Statistics:")
    print(f"  Conversations: {db_stats['conversations']}")
    print(f"  Messages: {db_stats['messages']}")
    print(f"  Unique tags: {db_stats['unique_tags']}")
    print(f"  Database location: {ingester.db_path}")
    
    # Example queries
    print(f"\n🔍 Example queries you can run:")
    print(f"  python query_db.py --search 'AI'")
    print(f"  python query_db.py --conversation conv_000001")
    print(f"  python query_db.py --stats")


if __name__ == "__main__":
    main() 