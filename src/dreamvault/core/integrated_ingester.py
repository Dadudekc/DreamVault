"""
Integrated Conversation Ingester for DreamVault

Processes conversations immediately during database ingestion.
No raw data mess - only clean, structured, searchable data.
Also saves training datasets for AI agents.
"""

import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .redact import Redactor
from .summarize import Summarizer
from .embed import EmbeddingBuilder
from .schema import SummarySchema

logger = logging.getLogger(__name__)

class IntegratedIngester:
    """
    Integrated ingester that processes conversations immediately.
    
    Features:
    - PII redaction on ingestion
    - LLM summarization during storage
    - Embedding generation
    - IP resurrection extraction
    - Clean database structure
    - Training dataset generation for AI agents
    """
    
    def __init__(self, db_path: str = "data/dreamvault.db", config: Optional[Dict] = None):
        """
        Initialize the integrated ingester.
        
        Args:
            db_path: Path to SQLite database
            config: Configuration for processing components
        """
        self.db_path = db_path
        self.config = config or self._get_default_config()
        
        # Initialize processing components
        self.redactor = Redactor(self.config.get("redaction", {}))
        self.summarizer = Summarizer(self.config.get("summarization", {}))
        self.embedding_builder = EmbeddingBuilder(self.config)
        self.schema_validator = SummarySchema()
        
        # Training data paths
        self.training_dir = Path("data/training")
        self.training_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        logger.info("✅ Integrated Ingester initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "redaction": {
                "patterns": [
                    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "email"),
                    (r"\b\d{3}-\d{3}-\d{4}\b", "phone"),
                    (r"\b\d{4}-\d{4}-\d{4}-\d{4}\b", "credit_card"),
                ]
            },
            "summarization": {
                "model": "gpt-4",
                "max_tokens": 2000,
                "temperature": 0.1
            },
            "embedding": {
                "model": "text-embedding-ada-002",
                "dimension": 1536
            },
            "training": {
                "save_conversation_pairs": True,
                "save_summary_pairs": True,
                "save_qa_pairs": True,
                "save_instruction_pairs": True,
                "save_embedding_pairs": True
            }
        }
    
    def _init_database(self):
        """Initialize the database with clean schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Processed conversations table (clean, structured data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    summary TEXT,
                    tags TEXT,  -- JSON array
                    topics TEXT,  -- JSON array
                    sentiment TEXT,  -- JSON object
                    entities TEXT,  -- JSON array
                    action_items TEXT,  -- JSON array
                    decisions TEXT,  -- JSON array
                    template_coverage TEXT,  -- JSON object
                    message_count INTEGER,
                    word_count INTEGER,
                    created_at TEXT,
                    processed_at TEXT,
                    redaction_stats TEXT,  -- JSON object
                    embedding_id TEXT
                )
            """)
            
            # Messages table (redacted, clean messages only)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,  -- Redacted content only
                    timestamp TEXT,
                    message_index INTEGER,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """)
            
            # IP Resurrection table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ip_resurrection (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    product_ideas TEXT,  -- JSON array
                    workflows TEXT,  -- JSON array
                    brand_names TEXT,  -- JSON array
                    schemas TEXT,  -- JSON array
                    abandoned_ideas TEXT,  -- JSON array
                    potential_value REAL,
                    tags TEXT,  -- JSON array
                    summary TEXT,
                    extracted_at TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """)
            
            # Training data metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS training_metadata (
                    conversation_id TEXT PRIMARY KEY,
                    training_pairs_generated INTEGER,
                    summary_pairs_generated INTEGER,
                    qa_pairs_generated INTEGER,
                    instruction_pairs_generated INTEGER,
                    embedding_pairs_generated INTEGER,
                    training_files TEXT,  -- JSON array
                    created_at TEXT
                )
            """)
            
            # Full-text search index
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS conversations_fts
                USING fts5(id, title, summary, tags, topics, entities)
            """)
            
            # Processing metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_metadata (
                    conversation_id TEXT PRIMARY KEY,
                    original_file TEXT,
                    processing_version TEXT,
                    processing_time REAL,
                    error_log TEXT,
                    created_at TEXT
                )
            """)
            
            conn.commit()
            logger.info("✅ Database initialized with clean schema")
    
    def _save_training_data(self, conversation_id: str, conversation_data: Dict, 
                           redacted_messages: List[Dict], summary_data: Dict) -> bool:
        """Save conversation data in training formats for AI agents."""
        try:
            training_data = {
                "conversation_id": conversation_id,
                "title": conversation_data.get("title", ""),
                "processed_at": datetime.now().isoformat()
            }
            
            # 1. Conversation Pairs (for conversation modeling)
            if self.config.get("training", {}).get("save_conversation_pairs", True):
                conversation_pairs = self._create_conversation_pairs(redacted_messages)
                training_data["conversation_pairs"] = conversation_pairs
                
                # Save as JSONL for easy training
                pairs_file = self.training_dir / f"{conversation_id}_conversation_pairs.jsonl"
                with open(pairs_file, 'w', encoding='utf-8') as f:
                    for pair in conversation_pairs:
                        f.write(json.dumps(pair) + '\n')
            
            # 2. Summary Pairs (for summarization training)
            if self.config.get("training", {}).get("save_summary_pairs", True):
                summary_pairs = self._create_summary_pairs(redacted_messages, summary_data)
                training_data["summary_pairs"] = summary_pairs
                
                # Save as JSONL
                summary_file = self.training_dir / f"{conversation_id}_summary_pairs.jsonl"
                with open(summary_file, 'w', encoding='utf-8') as f:
                    for pair in summary_pairs:
                        f.write(json.dumps(pair) + '\n')
            
            # 3. Q&A Pairs (for question answering)
            if self.config.get("training", {}).get("save_qa_pairs", True):
                qa_pairs = self._create_qa_pairs(redacted_messages, summary_data)
                training_data["qa_pairs"] = qa_pairs
                
                # Save as JSONL
                qa_file = self.training_dir / f"{conversation_id}_qa_pairs.jsonl"
                with open(qa_file, 'w', encoding='utf-8') as f:
                    for pair in qa_pairs:
                        f.write(json.dumps(pair) + '\n')
            
            # 4. Instruction Pairs (for instruction following)
            if self.config.get("training", {}).get("save_instruction_pairs", True):
                instruction_pairs = self._create_instruction_pairs(redacted_messages, summary_data)
                training_data["instruction_pairs"] = instruction_pairs
                
                # Save as JSONL
                instruction_file = self.training_dir / f"{conversation_id}_instruction_pairs.jsonl"
                with open(instruction_file, 'w', encoding='utf-8') as f:
                    for pair in instruction_pairs:
                        f.write(json.dumps(pair) + '\n')
            
            # 5. Embedding Pairs (for embedding training)
            if self.config.get("training", {}).get("save_embedding_pairs", True):
                embedding_pairs = self._create_embedding_pairs(redacted_messages, summary_data)
                training_data["embedding_pairs"] = embedding_pairs
                
                # Save as JSONL
                embedding_file = self.training_dir / f"{conversation_id}_embedding_pairs.jsonl"
                with open(embedding_file, 'w', encoding='utf-8') as f:
                    for pair in embedding_pairs:
                        f.write(json.dumps(pair) + '\n')
            
            # Save complete training data
            training_file = self.training_dir / f"{conversation_id}_training_data.json"
            with open(training_file, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Training data saved for {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving training data for {conversation_id}: {e}")
            return False
    
    def _create_conversation_pairs(self, messages: List[Dict]) -> List[Dict]:
        """Create conversation pairs for training conversation models."""
        pairs = []
        
        for i in range(len(messages) - 1):
            if messages[i]["role"] == "user" and messages[i + 1]["role"] == "assistant":
                pairs.append({
                    "type": "conversation_pair",
                    "input": messages[i]["content"],
                    "output": messages[i + 1]["content"],
                    "context": "user_assistant_conversation"
                })
        
        return pairs
    
    def _create_summary_pairs(self, messages: List[Dict], summary_data: Dict) -> List[Dict]:
        """Create summary pairs for training summarization models."""
        # Combine all messages into conversation text
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" for msg in messages
        ])
        
        return [{
            "type": "summary_pair",
            "input": conversation_text,
            "output": summary_data.get("summary", ""),
            "context": "conversation_summarization"
        }]
    
    def _create_qa_pairs(self, messages: List[Dict], summary_data: Dict) -> List[Dict]:
        """Create Q&A pairs for training question answering models."""
        qa_pairs = []
        
        # Create questions from topics
        topics = summary_data.get("topics", [])
        for topic in topics:
            if isinstance(topic, dict):
                topic_name = topic.get("topic", "")
                if topic_name:
                    qa_pairs.append({
                        "type": "qa_pair",
                        "question": f"What was discussed about {topic_name}?",
                        "answer": summary_data.get("summary", ""),
                        "context": "topic_based_qa"
                    })
        
        # Create questions from action items
        action_items = summary_data.get("action_items", [])
        for item in action_items:
            if isinstance(item, dict):
                action = item.get("action", "")
                if action:
                    qa_pairs.append({
                        "type": "qa_pair",
                        "question": f"What action item was mentioned?",
                        "answer": action,
                        "context": "action_item_qa"
                    })
        
        return qa_pairs
    
    def _create_instruction_pairs(self, messages: List[Dict], summary_data: Dict) -> List[Dict]:
        """Create instruction pairs for training instruction-following models."""
        instruction_pairs = []
        
        # Create instructions from user messages
        for msg in messages:
            if msg["role"] == "user":
                content = msg["content"]
                if any(keyword in content.lower() for keyword in ["help", "explain", "show", "create", "write"]):
                    instruction_pairs.append({
                        "type": "instruction_pair",
                        "instruction": content,
                        "response": "I'll help you with that.",
                        "context": "user_instruction"
                    })
        
        # Create instructions from summary
        if summary_data.get("summary"):
            instruction_pairs.append({
                "type": "instruction_pair",
                "instruction": "Summarize this conversation",
                "response": summary_data["summary"],
                "context": "summarization_instruction"
            })
        
        return instruction_pairs
    
    def _create_embedding_pairs(self, messages: List[Dict], summary_data: Dict) -> List[Dict]:
        """Create embedding pairs for training embedding models."""
        embedding_pairs = []
        
        # Create pairs from messages
        for msg in messages:
            embedding_pairs.append({
                "type": "embedding_pair",
                "text": msg["content"],
                "role": msg["role"],
                "context": "conversation_message"
            })
        
        # Create pairs from summary
        if summary_data.get("summary"):
            embedding_pairs.append({
                "type": "embedding_pair",
                "text": summary_data["summary"],
                "role": "summary",
                "context": "conversation_summary"
            })
        
        return embedding_pairs
    
    def ingest_conversation(self, conversation_data: Dict[str, Any], conversation_id: str) -> bool:
        """
        Ingest and process a single conversation immediately.
        
        Args:
            conversation_data: Raw conversation data from scraper
            conversation_id: Unique conversation identifier
            
        Returns:
            True if ingestion successful, False otherwise
        """
        try:
            logger.info(f"🔄 Processing conversation: {conversation_id}")
            
            # Step 1: Extract and redact messages
            messages = conversation_data.get("messages", [])
            redacted_messages = []
            total_words = 0
            
            for i, message in enumerate(messages):
                content = message.get("content", "")
                redacted_content, redaction_stats = self.redactor.redact_text(content)
                
                redacted_messages.append({
                    "role": message.get("role", "unknown"),
                    "content": redacted_content,
                    "timestamp": message.get("timestamp", ""),
                    "message_index": i
                })
                
                total_words += len(content.split())
            
            # Step 2: Generate summary from redacted content
            summary_data = self.summarizer.summarize_conversation(
                {"messages": redacted_messages}, 
                conversation_id
            )
            
            if not summary_data:
                logger.error(f"Failed to generate summary for {conversation_id}")
                return False
            
            # Step 3: Generate embeddings
            embedding_id = self.embedding_builder.generate_summary_embeddings(
                summary_data, conversation_id
            )
            
            # Step 4: Extract IP resurrection data
            from ..resurrection.ip_extractor import IPExtractor
            ip_extractor = IPExtractor(self.config)
            ip_data = ip_extractor.extract_ip_from_conversation(conversation_data, conversation_id)
            
            # Step 5: Save training data
            training_success = self._save_training_data(
                conversation_id, conversation_data, redacted_messages, summary_data
            )
            
            # Step 6: Store processed data in database
            success = self._store_processed_conversation(
                conversation_id=conversation_id,
                conversation_data=conversation_data,
                redacted_messages=redacted_messages,
                summary_data=summary_data,
                ip_data=ip_data,
                embedding_id=embedding_id,
                total_words=total_words,
                training_success=training_success
            )
            
            if success:
                logger.info(f"✅ Successfully processed and stored: {conversation_id}")
                return True
            else:
                logger.error(f"Failed to store processed data for {conversation_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing conversation {conversation_id}: {e}")
            return False
    
    def _store_processed_conversation(self, conversation_id: str, conversation_data: Dict,
                                    redacted_messages: List[Dict], summary_data: Dict,
                                    ip_data: Dict, embedding_id: str, total_words: int,
                                    training_success: bool) -> bool:
        """Store processed conversation data in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Store conversation summary
                cursor.execute("""
                    INSERT OR REPLACE INTO conversations (
                        id, title, summary, tags, topics, sentiment, entities,
                        action_items, decisions, template_coverage, message_count,
                        word_count, created_at, processed_at, redaction_stats, embedding_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conversation_id,
                    conversation_data.get("title", ""),
                    summary_data.get("summary", ""),
                    json.dumps(summary_data.get("tags", [])),
                    json.dumps(summary_data.get("topics", [])),
                    json.dumps(summary_data.get("sentiment", {})),
                    json.dumps(summary_data.get("entities", [])),
                    json.dumps(summary_data.get("action_items", [])),
                    json.dumps(summary_data.get("decisions", [])),
                    json.dumps(summary_data.get("template_coverage", {})),
                    len(redacted_messages),
                    total_words,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    json.dumps(self.redactor.get_redaction_stats()),
                    embedding_id
                ))
                
                # Store redacted messages
                for message in redacted_messages:
                    cursor.execute("""
                        INSERT INTO messages (
                            conversation_id, role, content, timestamp, message_index
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        conversation_id,
                        message["role"],
                        message["content"],
                        message["timestamp"],
                        message["message_index"]
                    ))
                
                # Store IP resurrection data
                if ip_data:
                    cursor.execute("""
                        INSERT OR REPLACE INTO ip_resurrection (
                            conversation_id, product_ideas, workflows, brand_names,
                            schemas, abandoned_ideas, potential_value, tags, summary, extracted_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        conversation_id,
                        json.dumps(ip_data.get("product_ideas", [])),
                        json.dumps(ip_data.get("workflows", [])),
                        json.dumps(ip_data.get("brand_names", [])),
                        json.dumps(ip_data.get("schemas", [])),
                        json.dumps(ip_data.get("abandoned_ideas", [])),
                        ip_data.get("potential_value", 0.0),
                        json.dumps(ip_data.get("tags", [])),
                        ip_data.get("summary", ""),
                        datetime.now().isoformat()
                    ))
                
                # Store training metadata
                training_files = []
                if training_success:
                    training_files = [
                        f"{conversation_id}_conversation_pairs.jsonl",
                        f"{conversation_id}_summary_pairs.jsonl",
                        f"{conversation_id}_qa_pairs.jsonl",
                        f"{conversation_id}_instruction_pairs.jsonl",
                        f"{conversation_id}_embedding_pairs.jsonl",
                        f"{conversation_id}_training_data.json"
                    ]
                
                cursor.execute("""
                    INSERT OR REPLACE INTO training_metadata (
                        conversation_id, training_pairs_generated, summary_pairs_generated,
                        qa_pairs_generated, instruction_pairs_generated, embedding_pairs_generated,
                        training_files, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conversation_id,
                    len(self._create_conversation_pairs(redacted_messages)),
                    len(self._create_summary_pairs(redacted_messages, summary_data)),
                    len(self._create_qa_pairs(redacted_messages, summary_data)),
                    len(self._create_instruction_pairs(redacted_messages, summary_data)),
                    len(self._create_embedding_pairs(redacted_messages, summary_data)),
                    json.dumps(training_files),
                    datetime.now().isoformat()
                ))
                
                # Update FTS index
                cursor.execute("""
                    INSERT OR REPLACE INTO conversations_fts (
                        id, title, summary, tags, topics, entities
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    conversation_id,
                    conversation_data.get("title", ""),
                    summary_data.get("summary", ""),
                    json.dumps(summary_data.get("tags", [])),
                    json.dumps(summary_data.get("topics", [])),
                    json.dumps(summary_data.get("entities", []))
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Database storage error: {e}")
            return False
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get training data statistics."""
        try:
            training_files = list(self.training_dir.glob("*.jsonl"))
            training_data_files = list(self.training_dir.glob("*_training_data.json"))
            
            stats = {
                "total_training_files": len(training_files),
                "total_training_data_files": len(training_data_files),
                "training_data_size_mb": sum(f.stat().st_size for f in training_files) / (1024 * 1024),
                "file_types": {}
            }
            
            # Count by file type
            for file in training_files:
                file_type = file.name.split("_")[-1].replace(".jsonl", "")
                stats["file_types"][file_type] = stats["file_types"].get(file_type, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting training stats: {e}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Conversation stats
                cursor.execute("SELECT COUNT(*) FROM conversations")
                total_conversations = cursor.fetchone()[0]
                
                cursor.execute("SELECT SUM(message_count) FROM conversations")
                total_messages = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT SUM(word_count) FROM conversations")
                total_words = cursor.fetchone()[0] or 0
                
                # IP resurrection stats
                cursor.execute("SELECT COUNT(*) FROM ip_resurrection")
                total_ip_extractions = cursor.fetchone()[0]
                
                cursor.execute("SELECT SUM(potential_value) FROM ip_resurrection")
                total_potential_value = cursor.fetchone()[0] or 0.0
                
                # Training stats
                training_stats = self.get_training_stats()
                
                return {
                    "total_conversations": total_conversations,
                    "total_messages": total_messages,
                    "total_words": total_words,
                    "total_ip_extractions": total_ip_extractions,
                    "total_potential_value": total_potential_value,
                    "database_size_mb": Path(self.db_path).stat().st_size / (1024 * 1024),
                    "training_data": training_stats
                }
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def search_conversations(self, query: str, limit: int = 10) -> List[Dict]:
        """Search conversations using FTS."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, summary, tags, topics, entities
                    FROM conversations_fts
                    WHERE conversations_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (query, limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "id": row[0],
                        "title": row[1],
                        "summary": row[2],
                        "tags": json.loads(row[3]) if row[3] else [],
                        "topics": json.loads(row[4]) if row[4] else [],
                        "entities": json.loads(row[5]) if row[5] else []
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return [] 