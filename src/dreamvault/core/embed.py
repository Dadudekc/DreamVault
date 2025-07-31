"""
Embedding generation for DreamVault.

This module handles the generation of embeddings for conversation summaries
and provides integration points for vector databases.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib


class EmbeddingBuilder:
    """Builds embeddings for conversation summaries."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the embedding builder.
        
        Args:
            config: Configuration dictionary with embedding settings
        """
        self.config = config
        self.embedding_config = config.get("embedding", {})
        self.model = self.embedding_config.get("model", "text-embedding-ada-002")
        self.embedding_dim = self.embedding_config.get("embedding_dim", 1536)
        self.batch_size = self.embedding_config.get("batch_size", 100)
        
        # Setup paths
        paths_config = config.get("paths", {})
        indexes_path = paths_config.get("indexes", "data/index")
        self.embeddings_dir = Path(indexes_path) / "embeddings"
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
    def generate_embedding_id(self, conversation_id: str) -> str:
        """Generate a unique ID for the embedding.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            A unique embedding ID
        """
        return f"embed_{conversation_id}"
    
    def build_embedding(self, summary_data: Dict[str, Any], conversation_id: str) -> Dict[str, Any]:
        """Build embedding data from summary.
        
        Args:
            summary_data: The conversation summary data
            conversation_id: The conversation ID
            
        Returns:
            Dictionary containing embedding metadata and content
        """
        embedding_id = self.generate_embedding_id(conversation_id)
        
        # Extract text content for embedding
        content_parts = []
        
        # Add summary
        if "summary" in summary_data:
            content_parts.append(summary_data["summary"])
            
        # Add topics
        if "topics" in summary_data:
            for topic in summary_data["topics"]:
                if isinstance(topic, dict) and "topic" in topic:
                    content_parts.append(topic["topic"])
                elif isinstance(topic, str):
                    content_parts.append(topic)
            
        # Add tags
        if "tags" in summary_data:
            for tag in summary_data["tags"]:
                if isinstance(tag, str):
                    content_parts.append(tag)
            
        # Add entities
        if "entities" in summary_data:
            for entity in summary_data["entities"]:
                if isinstance(entity, dict) and "name" in entity:
                    content_parts.append(entity["name"])
                elif isinstance(entity, str):
                    content_parts.append(entity)
            
        # Add action items
        if "action_items" in summary_data:
            for action in summary_data["action_items"]:
                if isinstance(action, dict) and "action" in action:
                    content_parts.append(action["action"])
                elif isinstance(action, str):
                    content_parts.append(action)
            
        # Add decisions
        if "decisions" in summary_data:
            for decision in summary_data["decisions"]:
                if isinstance(decision, dict) and "decision" in decision:
                    content_parts.append(decision["decision"])
                elif isinstance(decision, str):
                    content_parts.append(decision)
        
        # Combine all content
        full_content = " ".join(content_parts)
        
        # Generate a hash for content fingerprinting
        content_hash = hashlib.md5(full_content.encode()).hexdigest()
        
        embedding_data = {
            "embedding_id": embedding_id,
            "conversation_id": conversation_id,
            "model": self.model,
            "embedding_dim": self.embedding_dim,
            "content_hash": content_hash,
            "content_length": len(full_content),
            "content_preview": full_content[:200] + "..." if len(full_content) > 200 else full_content,
            "metadata": {
                "summary_length": len(summary_data.get("summary", "")),
                "topics_count": len(summary_data.get("topics", [])),
                "tags_count": len(summary_data.get("tags", [])),
                "entities_count": len(summary_data.get("entities", [])),
                "action_items_count": len(summary_data.get("action_items", [])),
                "decisions_count": len(summary_data.get("decisions", [])),
                "sentiment": summary_data.get("sentiment", "neutral"),
                "template_coverage": summary_data.get("template_coverage", {})
            },
            # Placeholder for actual embedding vector
            "embedding_vector": None,  # Would be populated by actual embedding API
            "created_at": summary_data.get("created_at", ""),
            "version": "1.0"
        }
        
        return embedding_data
    
    def save_embedding(self, embedding_data: Dict[str, Any], conversation_id: str) -> bool:
        """Save embedding data to file.
        
        Args:
            embedding_data: The embedding data to save
            conversation_id: The conversation ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            embedding_file = self.embeddings_dir / f"{conversation_id}.json"
            
            with open(embedding_file, 'w', encoding='utf-8') as f:
                json.dump(embedding_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Saved embedding for conversation {conversation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save embedding for {conversation_id}: {e}")
            return False
    
    def load_embedding(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Load embedding data from file.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            The embedding data or None if not found
        """
        try:
            embedding_file = self.embeddings_dir / f"{conversation_id}.json"
            
            if not embedding_file.exists():
                return None
                
            with open(embedding_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Failed to load embedding for {conversation_id}: {e}")
            return None
    
    def process_summary(self, summary_file: Path, conversation_id: str) -> bool:
        """Process a summary file and generate embedding.
        
        Args:
            summary_file: Path to the summary file
            conversation_id: The conversation ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load summary data
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
            
            # Build embedding
            embedding_data = self.build_embedding(summary_data, conversation_id)
            
            # Save embedding
            return self.save_embedding(embedding_data, conversation_id)
            
        except Exception as e:
            self.logger.error(f"Failed to process summary for {conversation_id}: {e}")
            return False
    
    def batch_process(self, summary_dir: Path) -> Dict[str, Any]:
        """Process all summaries in a directory.
        
        Args:
            summary_dir: Directory containing summary files
            
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            "total_files": 0,
            "processed": 0,
            "failed": 0,
            "errors": []
        }
        
        if not summary_dir.exists():
            self.logger.warning(f"Summary directory {summary_dir} does not exist")
            return stats
        
        for summary_file in summary_dir.glob("*.json"):
            stats["total_files"] += 1
            
            # Extract conversation ID from filename
            conversation_id = summary_file.stem
            
            if self.process_summary(summary_file, conversation_id):
                stats["processed"] += 1
            else:
                stats["failed"] += 1
                stats["errors"].append(f"Failed to process {conversation_id}")
        
        self.logger.info(f"Batch processing complete: {stats['processed']}/{stats['total_files']} successful")
        return stats
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings.
        
        Returns:
            Dictionary with embedding statistics
        """
        try:
            embedding_files = list(self.embeddings_dir.glob("*.json"))
            
            stats = {
                "embeddings_stored": len(embedding_files),
                "embeddings_dir": str(self.embeddings_dir),
                "model": self.model,
                "embedding_dim": self.embedding_dim
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get embedding stats: {e}")
            return {
                "embeddings_stored": 0,
                "embeddings_dir": str(self.embeddings_dir),
                "model": self.model,
                "embedding_dim": self.embedding_dim
            }
    
    def generate_summary_embeddings(self, summary_data: Dict[str, Any], conversation_id: str) -> bool:
        """Generate embeddings for a conversation summary.
        
        Args:
            summary_data: The conversation summary data
            conversation_id: The conversation ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build embedding data
            embedding_data = self.build_embedding(summary_data, conversation_id)
            
            # Save embedding
            return self.save_embedding(embedding_data, conversation_id)
            
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings for {conversation_id}: {e}")
            return False 