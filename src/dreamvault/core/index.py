"""
Inverted index builder for ShadowArchive.
"""

import json
import sqlite3
from typing import Dict, List, Any, Set, Optional
from pathlib import Path
from collections import defaultdict


class IndexBuilder:
    """Inverted index builder for topic and template-based search."""
    
    def __init__(self, index_dir: str = "data/index"):
        """
        Initialize index builder.
        
        Args:
            index_dir: Directory to store index files
        """
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Index database
        self.db_path = self.index_dir / "inverted_index.db"
        self._init_index_db()
    
    def _init_index_db(self) -> None:
        """Initialize the index database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Topics index
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics_index (
                topic TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                confidence REAL NOT NULL,
                mentions INTEGER DEFAULT 1,
                PRIMARY KEY (topic, conversation_id)
            )
        """)
        
        # Templates index
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates_index (
                template TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                mentions INTEGER DEFAULT 1,
                coverage_score REAL DEFAULT 0.0,
                PRIMARY KEY (template, conversation_id)
            )
        """)
        
        # Tags index
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags_index (
                tag TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                PRIMARY KEY (tag, conversation_id)
            )
        """)
        
        # Entities index
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities_index (
                entity_name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                PRIMARY KEY (entity_name, entity_type, conversation_id)
            )
        """)
        
        # Sentiment index
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_index (
                sentiment TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                PRIMARY KEY (sentiment, conversation_id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_topics_topic ON topics_index(topic)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_topics_conv ON topics_index(conversation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_templates_template ON templates_index(template)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_templates_conv ON templates_index(conversation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags_index(tag)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities_index(entity_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_sentiment ON sentiment_index(sentiment)")
        
        conn.commit()
        conn.close()
    
    def build_index_from_summary(self, summary: Dict[str, Any]) -> bool:
        """
        Build index entries from a summary.
        
        Args:
            summary: Summary object to index
            
        Returns:
            True if indexing was successful
        """
        try:
            conversation_id = summary.get("conversation_id")
            if not conversation_id:
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Index topics
            self._index_topics(cursor, conversation_id, summary.get("topics", []))
            
            # Index templates
            self._index_templates(cursor, conversation_id, summary.get("template_coverage", {}))
            
            # Index tags
            self._index_tags(cursor, conversation_id, summary.get("tags", []))
            
            # Index entities
            self._index_entities(cursor, conversation_id, summary.get("entities", []))
            
            # Index sentiment
            self._index_sentiment(cursor, conversation_id, summary.get("sentiment", {}))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error building index for {conversation_id}: {e}")
            return False
    
    def _index_topics(self, cursor: sqlite3.Cursor, conversation_id: str, topics: List[Dict[str, Any]]) -> None:
        """Index topics from summary."""
        for topic_obj in topics:
            topic = topic_obj.get("topic", "")
            confidence = topic_obj.get("confidence", 0.0)
            mentions = topic_obj.get("mentions", 1)
            
            if topic:
                cursor.execute("""
                    INSERT OR REPLACE INTO topics_index 
                    (topic, conversation_id, confidence, mentions)
                    VALUES (?, ?, ?, ?)
                """, (topic, conversation_id, confidence, mentions))
    
    def _index_templates(self, cursor: sqlite3.Cursor, conversation_id: str, template_coverage: Dict[str, Any]) -> None:
        """Index templates from summary."""
        templates_used = template_coverage.get("templates_used", [])
        coverage_score = template_coverage.get("coverage_score", 0.0)
        template_mentions = template_coverage.get("template_mentions", {})
        
        for template in templates_used:
            mentions = template_mentions.get(template, 1)
            cursor.execute("""
                INSERT OR REPLACE INTO templates_index 
                (template, conversation_id, mentions, coverage_score)
                VALUES (?, ?, ?, ?)
            """, (template, conversation_id, mentions, coverage_score))
    
    def _index_tags(self, cursor: sqlite3.Cursor, conversation_id: str, tags: List[str]) -> None:
        """Index tags from summary."""
        for tag in tags:
            if tag:
                cursor.execute("""
                    INSERT OR IGNORE INTO tags_index (tag, conversation_id)
                    VALUES (?, ?)
                """, (tag, conversation_id))
    
    def _index_entities(self, cursor: sqlite3.Cursor, conversation_id: str, entities: List[Dict[str, Any]]) -> None:
        """Index entities from summary."""
        for entity in entities:
            name = entity.get("name", "")
            entity_type = entity.get("type", "")
            confidence = entity.get("confidence", 1.0)
            
            if name and entity_type:
                cursor.execute("""
                    INSERT OR REPLACE INTO entities_index 
                    (entity_name, entity_type, conversation_id, confidence)
                    VALUES (?, ?, ?, ?)
                """, (name, entity_type, conversation_id, confidence))
    
    def _index_sentiment(self, cursor: sqlite3.Cursor, conversation_id: str, sentiment: Dict[str, Any]) -> None:
        """Index sentiment from summary."""
        overall = sentiment.get("overall", "")
        confidence = sentiment.get("confidence", 1.0)
        
        if overall:
            cursor.execute("""
                INSERT OR REPLACE INTO sentiment_index 
                (sentiment, conversation_id, confidence)
                VALUES (?, ?, ?)
            """, (overall, conversation_id, confidence))
    
    def search_by_topic(self, topic: str, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search conversations by topic.
        
        Args:
            topic: Topic to search for
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of matching conversations with scores
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT conversation_id, confidence, mentions
            FROM topics_index 
            WHERE topic LIKE ? AND confidence >= ?
            ORDER BY confidence DESC, mentions DESC
        """, (f"%{topic}%", min_confidence))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "conversation_id": row[0],
                "confidence": row[1],
                "mentions": row[2]
            })
        
        conn.close()
        return results
    
    def search_by_template(self, template: str) -> List[Dict[str, Any]]:
        """
        Search conversations by template.
        
        Args:
            template: Template to search for
            
        Returns:
            List of matching conversations
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT conversation_id, mentions, coverage_score
            FROM templates_index 
            WHERE template LIKE ?
            ORDER BY mentions DESC, coverage_score DESC
        """, (f"%{template}%",))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "conversation_id": row[0],
                "mentions": row[1],
                "coverage_score": row[2]
            })
        
        conn.close()
        return results
    
    def search_by_tag(self, tag: str) -> List[str]:
        """
        Search conversations by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of conversation IDs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT conversation_id
            FROM tags_index 
            WHERE tag LIKE ?
        """, (f"%{tag}%",))
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results
    
    def search_by_entity(self, entity_name: str, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search conversations by entity.
        
        Args:
            entity_name: Entity name to search for
            entity_type: Optional entity type filter
            
        Returns:
            List of matching conversations
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if entity_type:
            cursor.execute("""
                SELECT conversation_id, confidence
                FROM entities_index 
                WHERE entity_name LIKE ? AND entity_type = ?
                ORDER BY confidence DESC
            """, (f"%{entity_name}%", entity_type))
        else:
            cursor.execute("""
                SELECT conversation_id, confidence
                FROM entities_index 
                WHERE entity_name LIKE ?
                ORDER BY confidence DESC
            """, (f"%{entity_name}%",))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "conversation_id": row[0],
                "confidence": row[1]
            })
        
        conn.close()
        return results
    
    def search_by_sentiment(self, sentiment: str) -> List[Dict[str, Any]]:
        """
        Search conversations by sentiment.
        
        Args:
            sentiment: Sentiment to search for
            
        Returns:
            List of matching conversations
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT conversation_id, confidence
            FROM sentiment_index 
            WHERE sentiment = ?
            ORDER BY confidence DESC
        """, (sentiment,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "conversation_id": row[0],
                "confidence": row[1]
            })
        
        conn.close()
        return results
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Count entries in each index
        tables = ["topics_index", "templates_index", "tags_index", "entities_index", "sentiment_index"]
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats[f"{table}_entries"] = count
        
        # Get unique values
        cursor.execute("SELECT COUNT(DISTINCT topic) FROM topics_index")
        stats["unique_topics"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT template) FROM templates_index")
        stats["unique_templates"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT tag) FROM tags_index")
        stats["unique_tags"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT conversation_id) FROM topics_index")
        stats["indexed_conversations"] = cursor.fetchone()[0]
        
        conn.close()
        
        return stats
    
    def remove_conversation_from_index(self, conversation_id: str) -> bool:
        """
        Remove a conversation from all indexes.
        
        Args:
            conversation_id: Conversation ID to remove
            
        Returns:
            True if removal was successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            tables = ["topics_index", "templates_index", "tags_index", "entities_index", "sentiment_index"]
            for table in tables:
                cursor.execute(f"DELETE FROM {table} WHERE conversation_id = ?", (conversation_id,))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error removing conversation {conversation_id} from index: {e}")
            return False
    
    def rebuild_index(self, summaries_dir: str) -> int:
        """
        Rebuild the entire index from summary files.
        
        Args:
            summaries_dir: Directory containing summary files
            
        Returns:
            Number of summaries indexed
        """
        summaries_path = Path(summaries_dir)
        if not summaries_path.exists():
            return 0
        
        # Clear existing index
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        tables = ["topics_index", "templates_index", "tags_index", "entities_index", "sentiment_index"]
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
        conn.commit()
        conn.close()
        
        # Rebuild index
        indexed_count = 0
        for summary_file in summaries_path.glob("*.json"):
            try:
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
                
                if self.build_index_from_summary(summary):
                    indexed_count += 1
            except Exception as e:
                print(f"Error indexing {summary_file}: {e}")
        
        return indexed_count 