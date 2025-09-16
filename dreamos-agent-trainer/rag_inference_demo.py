#!/usr/bin/env python3
"""
Dream.OS RAG Inference Demo
Demonstrates how to use the trained RAG system for retrieval.
"""
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️ sentence-transformers not available. Install with: pip install sentence-transformers")

# Configuration
DB_PATH = Path("dreamos/memory_layers/long_term.sqlite")
EMBED_MODEL = "all-MiniLM-L6-v2"

class DreamOSRAG:
    """Dream.OS RAG retrieval system."""
    
    def __init__(self, db_path: Path, embed_model: str = "all-MiniLM-L6-v2"):
        self.db_path = db_path
        self.embed_model_name = embed_model
        
        if EMBEDDINGS_AVAILABLE:
            self.model = SentenceTransformer(embed_model)
        else:
            self.model = None
            print("⚠️ Using dummy embeddings - install sentence-transformers for real embeddings")
    
    def encode_query(self, query: str) -> np.ndarray:
        """Encode query into embedding vector."""
        if self.model:
            return self.model.encode([query], normalize_embeddings=True)[0]
        else:
            # Dummy embedding
            return np.random.randn(384).astype(np.float32)
    
    def search(self, query: str, k: int = 8, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for relevant passages using semantic similarity.
        
        Args:
            query: Search query
            k: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of relevant passages with metadata
        """
        if not self.db_path.exists():
            print(f"❌ Database not found: {self.db_path}")
            print("Run 02_chunk_embed_rag.py first to create the RAG index.")
            return []
        
        # Encode query
        query_emb = self.encode_query(query)
        
        # Search database
        results = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT pid, turn_id, source, role, text, timestamp, message_id, emb
                FROM rag
            """)
            
            for row in cursor.fetchall():
                # Get embedding
                emb_blob = row["emb"]
                passage_emb = np.frombuffer(emb_blob, dtype=np.float32)
                
                # Calculate similarity
                similarity = float(np.dot(query_emb, passage_emb))
                
                if similarity >= similarity_threshold:
                    results.append({
                        "pid": row["pid"],
                        "turn_id": row["turn_id"],
                        "source": row["source"],
                        "role": row["role"],
                        "text": row["text"],
                        "timestamp": row["timestamp"],
                        "message_id": row["message_id"],
                        "similarity": similarity
                    })
        
        # Sort by similarity and return top-k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:k]
    
    def get_context(self, query: str, k: int = 8) -> str:
        """Get formatted context for RAG."""
        results = self.search(query, k)
        
        if not results:
            return "No relevant context found."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Context {i}] {result['text']}")
        
        return "\n\n".join(context_parts)

def main():
    """Demo the RAG system."""
    print("🛰️ Dream.OS RAG Inference Demo")
    
    # Initialize RAG system
    rag = DreamOSRAG(DB_PATH, EMBED_MODEL)
    
    # Demo queries
    demo_queries = [
        "How do I orchestrate multiple Cursor agents with .prompt.md?",
        "What is Victor's writing style with ellipses?",
        "How to build a RAG system?",
        "Dream.OS swarm terminology and vibe coding"
    ]
    
    for query in demo_queries:
        print(f"\n🔍 Query: {query}")
        print("─" * 60)
        
        # Search for relevant passages
        results = rag.search(query, k=3)
        
        if results:
            print(f"📊 Found {len(results)} relevant passages:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. Similarity: {result['similarity']:.3f}")
                print(f"   Source: {result['source']}")
                print(f"   Text: {result['text'][:200]}...")
        else:
            print("❌ No relevant passages found.")
        
        # Get formatted context
        context = rag.get_context(query, k=2)
        print(f"\n📝 Context for RAG:")
        print(context[:300] + "..." if len(context) > 300 else context)

if __name__ == "__main__":
    main()